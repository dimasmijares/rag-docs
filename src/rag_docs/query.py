from __future__ import annotations

import re
from typing import Literal

from rag_docs.authorization import SingleTenantAuthorization
from rag_docs.contracts import (
    AnswerClaim,
    AuthorizationPort,
    Citation,
    QueryResult,
    RetrievalDiagnostic,
    Scope,
    SearchHit,
)
from rag_docs.embeddings import Embedder
from rag_docs.generation import (
    GeneratedResponse,
    GenerationError,
    Generator,
    InvalidGeneratedResponse,
)
from rag_docs.grounding import AnswerValidator, ContextBuilder
from rag_docs.language import SupportedLanguage, infer_question_language
from rag_docs.lexical import BM25Index, reciprocal_rank_fusion
from rag_docs.reranking import Reranker
from rag_docs.vector_store import VectorStore

__all__ = [
    "AnswerClaim",
    "Citation",
    "QueryResult",
    "QueryService",
    "RetrievalDiagnostic",
]


class QueryService:
    """Orchestrator over retrieval, generation and grounding (``ADR-RAG-010``).

    Selection, citation/context assembly and evidence-hint construction live in
    ``ContextBuilder``; grounding validation and the extractive fallback live in
    ``AnswerValidator`` — both pure pieces behind the shape of ``GroundingPort``.
    ``QueryService`` itself only sequences embedding, retrieval, context
    building, generation and validation; it does not implement any of that
    logic directly. ``authorizer`` resolves the ``Scope`` every search is
    prefiltered by (``ADR-RAG-009``, ``WRK-TASK-082``); the ``v0.3.0``
    implementation is single-tenant, and ``v1.5.0`` can replace it without
    touching this class. ``retrieval_strategy`` selects between the dense
    vector search used since the PoC and the BM25+dense hybrid of
    ``WRK-TASK-037``, fused by reciprocal rank fusion (``rag_docs.lexical``);
    it defaults to ``"dense"`` because hybrid is adopted only where a
    measured comparison shows it wins (``RFC-001`` gate G2), not by default.
    ``reranker`` (``WRK-TASK-038``) is an optional cross-encoder step applied
    after retrieval and before context building; it defaults to ``None``
    (no reranking) for the same reason — adoption follows measurement, not
    the other way around.
    """

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        generator: Generator,
        top_k: int = 8,
        context_chunks: int = 5,
        min_score: float = 0.45,
        generation_strategy: Literal["llm", "extractive_fallback"] = "llm",
        authorizer: AuthorizationPort | None = None,
        retrieval_strategy: Literal["dense", "hybrid"] = "dense",
        reranker: Reranker | None = None,
        rerank_top_n: int | None = None,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.generator = generator
        self.top_k = top_k
        self.min_score = min_score
        self.generation_strategy = generation_strategy
        self.authorizer = authorizer or SingleTenantAuthorization()
        self.retrieval_strategy = retrieval_strategy
        self.reranker = reranker
        self.rerank_top_n = rerank_top_n if rerank_top_n is not None else context_chunks
        self.context_builder = ContextBuilder(context_chunks=context_chunks)
        self.validator = AnswerValidator()

    @property
    def context_chunks(self) -> int:
        return self.context_builder.context_chunks

    def _generate_validated(
        self,
        question: str,
        context: str,
        expected_language: SupportedLanguage,
        valid_references: set[int],
        evidence_by_reference: dict[int, str],
    ) -> GeneratedResponse | None:
        feedback: str | None = None
        for attempt in range(2):
            try:
                generated = self.generator.generate(
                    question,
                    context,
                    validation_feedback=feedback,
                )
            except InvalidGeneratedResponse:
                if attempt == 0:
                    feedback = (
                        "La salida anterior no respetó el esquema JSON. Devuelve exactamente "
                        "el esquema solicitado y conserva todos los hechos técnicos."
                    )
                    continue
                return None
            except GenerationError:
                if attempt == 0:
                    feedback = "El servicio falló temporalmente. Repite la respuesta completa."
                    continue
                raise
            errors = self.validator.validation_errors(
                generated,
                question,
                expected_language,
                valid_references,
                evidence_by_reference,
            )
            if not errors:
                return generated
            feedback = " ".join(errors)
        return None

    @staticmethod
    def _render_claims(generated: GeneratedResponse) -> tuple[str, list[AnswerClaim]]:
        rendered: list[str] = []
        claims: list[AnswerClaim] = []
        for generated_claim in generated.claims:
            text = re.sub(
                r"\s*(?:\[\d+\][,; ]*)+$", "", generated_claim.text.strip()
            )
            references = sorted(set(generated_claim.citations))
            rendered.append(f"{text} {' '.join(f'[{ref}]' for ref in references)}")
            claims.append(AnswerClaim(text=text, citations=references))
        return "\n\n".join(rendered), claims

    def _retrieve(self, question: str, vector: list[float], scope: Scope) -> list[SearchHit]:
        """Dense search, or dense+BM25 fused by reciprocal rank fusion when
        ``retrieval_strategy`` is ``"hybrid"`` (``WRK-TASK-037``). The dense
        phase drops ``min_score`` for hybrid: RRF scores and cosine
        similarity live on different scales, so the threshold tuned for one
        is meaningless for the other, and ``ContextBuilder`` already bounds
        and deduplicates whatever comes out of either path. When ``reranker``
        is set, the cross-encoder step (``WRK-TASK-038``) runs last, over
        whichever list dense or hybrid retrieval produced, and narrows it to
        ``rerank_top_n``.
        """
        if self.retrieval_strategy == "dense":
            hits = self.store.search(vector, self.top_k, self.min_score, scope)
        else:
            dense_hits = self.store.search(vector, self.top_k, None, scope)
            lexical_index = BM25Index(self.store.scan_chunks(scope))
            lexical_hits = lexical_index.search(question, self.top_k)
            hits = reciprocal_rank_fusion(dense_hits, lexical_hits, limit=self.top_k)
        if self.reranker is not None:
            hits = self.reranker.rerank(question, hits, self.rerank_top_n)
        return hits

    def query(self, question: str) -> QueryResult:
        question = question.strip()
        if not question:
            raise ValueError("La pregunta no puede estar vacía")
        expected_language = infer_question_language(question)
        vector = self.embedder.embed_query(question)
        scope = self.authorizer.resolve_scope(None)
        hits = self._retrieve(question, vector, scope)
        built = self.context_builder.build(question, hits)

        if not built.selected:
            answer = (
                "No hay evidencia suficiente en la documentación indexada para responder."
                if expected_language == "es"
                else "There is not enough evidence in the indexed documentation to answer."
            )
            return QueryResult(
                answer_status="insufficient_evidence",
                answer=answer,
                citations=[],
                model=None,
                embedding_model=self.embedder.model_name,
                answer_language=expected_language,
                claims=[],
                generation_mode="none",
                retrieval_diagnostics=built.retrieval_diagnostics,
            )

        generation_mode: Literal["llm", "extractive_fallback"] = (
            "extractive_fallback"
            if self.generation_strategy == "extractive_fallback"
            else "llm"
        )
        evidence_by_reference = {
            citation.reference: hit.chunk.text
            for citation, hit in zip(built.citations, built.selected, strict=True)
        }
        generated = None
        if self.generation_strategy == "llm":
            generated = self._generate_validated(
                question,
                built.context,
                expected_language,
                {citation.reference for citation in built.citations},
                evidence_by_reference,
            )
        if generated is None:
            generated = self.validator.extractive_technical_fallback(
                question, built.citations, built.selected, expected_language
            )
            if generated is not None:
                generation_mode = "extractive_fallback"
        if generated is None:
            answer = (
                "No se pudo generar una respuesta completa y verificable con la evidencia "
                "recuperada."
                if expected_language == "es"
                else "A complete and verifiable answer could not be generated from the "
                "retrieved evidence."
            )
            return QueryResult(
                answer_status="insufficient_evidence",
                answer=answer,
                citations=built.citations,
                model=self.generator.model_name,
                embedding_model=self.embedder.model_name,
                answer_language=expected_language,
                claims=[],
                generation_mode="none",
                retrieval_diagnostics=built.retrieval_diagnostics,
            )

        answer, claims = self._render_claims(generated)
        if generated.status == "insufficient_evidence":
            missing = "; ".join(generated.unanswered_parts)
            if expected_language == "es":
                suffix = "La evidencia no cubre: " + (missing or "la pregunta completa.")
            else:
                suffix = "The evidence does not cover: " + (
                    missing or "the complete question."
                )
            answer = f"{answer}\n\n{suffix}" if answer else suffix
            return QueryResult(
                answer_status="insufficient_evidence",
                answer=answer,
                citations=built.citations,
                model=self.generator.model_name,
                embedding_model=self.embedder.model_name,
                answer_language=expected_language,
                claims=claims,
                generation_mode=generation_mode,
                retrieval_diagnostics=built.retrieval_diagnostics,
            )

        return QueryResult(
            answer_status="grounded",
            answer=answer,
            citations=built.citations,
            model=self.generator.model_name,
            embedding_model=self.embedder.model_name,
            answer_language=expected_language,
            claims=claims,
            generation_mode=generation_mode,
            retrieval_diagnostics=built.retrieval_diagnostics,
        )
