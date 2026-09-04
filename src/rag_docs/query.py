from __future__ import annotations

import re
import unicodedata
from typing import Literal

from rag_docs.contracts import (
    AnswerClaim,
    Citation,
    QueryResult,
    RetrievalDiagnostic,
    SearchHit,
)
from rag_docs.embeddings import Embedder
from rag_docs.generation import (
    GeneratedClaim,
    GeneratedResponse,
    GenerationError,
    Generator,
    InvalidGeneratedResponse,
)
from rag_docs.language import (
    SupportedLanguage,
    infer_question_language,
    text_matches_language,
)
from rag_docs.vector_store import VectorStore

__all__ = [
    "AnswerClaim",
    "Citation",
    "QueryResult",
    "QueryService",
    "RetrievalDiagnostic",
]


class QueryService:
    _TECHNICAL_IDENTIFIER = re.compile(
        r"\b(?:[A-Za-z][\w]*::[\w]+|(?:[A-Za-z][\w]*\.)+[A-Za-z][\w]*|"
        r"[A-Za-z][A-Za-z0-9]*_(?:[A-Za-z0-9]+_?)+)\b"
    )
    _TECHNICAL_QUESTION = re.compile(
        r"(?:\b(?:en|por)\s+qué\s+(?:campo|tabla|tablas)\b|"
        r"\b(?:qué|cuál|cuáles|what|which)\s+"
        r"(?:(?:es|son|is|are)\s+)?(?:(?:la|las|el|los|the)\s+)?"
        r"(?:campo|etl|path|procedimiento|procedure|ruta|table|tabla|tablas|variable)\b|"
        r"\b(?:dónde|where)\b.{0,80}\b(?:etl|path|procedimiento|procedure|ruta)\b)",
        re.IGNORECASE,
    )
    _QUESTION_STOPWORDS = {
        "actualidad",
        "campo",
        "campos",
        "contiene",
        "cual",
        "cuales",
        "desde",
        "donde",
        "para",
        "proceso",
        "tabla",
        "tablas",
        "variable",
        "variables",
        "what",
        "where",
        "which",
    }

    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        generator: Generator,
        top_k: int = 8,
        context_chunks: int = 5,
        min_score: float = 0.45,
        generation_strategy: Literal["llm", "extractive_fallback"] = "llm",
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.generator = generator
        self.top_k = top_k
        self.context_chunks = context_chunks
        self.min_score = min_score
        self.generation_strategy = generation_strategy

    @staticmethod
    def _content_fingerprint(text: str) -> str:
        decomposed = unicodedata.normalize("NFKD", text.casefold())
        unaccented = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return " ".join(re.findall(r"[a-z0-9]+", unaccented))

    def _select_hits(
        self, hits: list[SearchHit]
    ) -> tuple[list[SearchHit], dict[int, str], list[int]]:
        selected: list[SearchHit] = []
        selected_ranks: list[int] = []
        discarded: dict[int, str] = {}
        seen: dict[str, SearchHit] = {}
        for rank, hit in enumerate(hits, start=1):
            fingerprint = self._content_fingerprint(hit.chunk.text)
            duplicate = seen.get(fingerprint)
            if duplicate is not None:
                discarded[rank] = (
                    "duplicate_chunk"
                    if duplicate.chunk.document_id == hit.chunk.document_id
                    else "equivalent_document"
                )
                continue
            if len(selected) == self.context_chunks:
                discarded[rank] = "context_limit"
                continue
            seen[fingerprint] = hit
            selected.append(hit)
            selected_ranks.append(rank)
        return selected, discarded, selected_ranks

    @staticmethod
    def _retrieval_diagnostics(
        hits: list[SearchHit],
        selected: list[SearchHit],
        raw_rank_by_hit: dict[int, int],
        discarded: dict[int, str],
    ) -> list[RetrievalDiagnostic]:
        context_ranks = {
            raw_rank_by_hit[id(hit)]: context_rank
            for context_rank, hit in enumerate(selected, start=1)
        }
        diagnostics: list[RetrievalDiagnostic] = []
        for rank, hit in enumerate(hits, start=1):
            context_rank = context_ranks.get(rank)
            diagnostics.append(
                RetrievalDiagnostic(
                    rank=rank,
                    score=round(hit.score, 6),
                    chunk_id=hit.chunk.chunk_id,
                    document_id=hit.chunk.document_id,
                    source_id=hit.chunk.source_id,
                    relative_path=hit.chunk.relative_path,
                    locator=hit.chunk.locator,
                    section=hit.chunk.section,
                    selected=context_rank is not None,
                    context_rank=context_rank,
                    discard_reason=discarded.get(rank),  # type: ignore[arg-type]
                )
            )
        return diagnostics

    def _prioritize_context(self, question: str, hits: list[SearchHit]) -> list[SearchHit]:
        if not self._TECHNICAL_QUESTION.search(question):
            return hits
        return sorted(
            hits,
            key=lambda hit: (
                len(self._TECHNICAL_IDENTIFIER.findall(hit.chunk.text)),
                hit.score,
            ),
            reverse=True,
        )

    def _technical_evidence_hints(
        self,
        question: str,
        citations: list[Citation],
        hits: list[SearchHit],
    ) -> str:
        if not self._TECHNICAL_QUESTION.search(question):
            return ""
        lines: list[str] = []
        seen: set[str] = set()
        for citation, hit in zip(citations, hits, strict=True):
            for raw_line in hit.chunk.text.splitlines():
                line = " ".join(raw_line.split())
                if not line or not self._TECHNICAL_IDENTIFIER.search(line):
                    continue
                normalized = line.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                lines.append(f"[{citation.reference}] {line}")
                if len(lines) == 12:
                    return "EVIDENCIA TÉCNICA LITERAL\n" + "\n".join(lines)
        return "EVIDENCIA TÉCNICA LITERAL\n" + "\n".join(lines) if lines else ""

    @classmethod
    def _content_terms(cls, text: str) -> set[str]:
        decomposed = unicodedata.normalize("NFKD", text.casefold())
        normalized = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        terms: set[str] = set()
        for token in re.findall(r"[a-z0-9]+", normalized):
            if len(token) < 4 or token in cls._QUESTION_STOPWORDS:
                continue
            if len(token) > 5 and token.endswith("es"):
                token = token[:-2]
            elif len(token) > 4 and token.endswith("s"):
                token = token[:-1]
            terms.add(token)
        return terms

    def _extractive_technical_fallback(
        self,
        question: str,
        citations: list[Citation],
        hits: list[SearchHit],
        expected_language: SupportedLanguage,
    ) -> GeneratedResponse | None:
        if not self._TECHNICAL_QUESTION.search(question):
            return None
        question_terms = self._content_terms(question)
        requested_variable = bool(re.search(r"\bvariables?\b", question, re.IGNORECASE))
        candidates: list[tuple[int, int, float, int, str]] = []
        seen: set[str] = set()
        for citation, hit in zip(citations, hits, strict=True):
            for raw_line in hit.chunk.text.splitlines():
                line = " ".join(raw_line.split())
                identifiers = self._TECHNICAL_IDENTIFIER.findall(line)
                if not line or not identifiers:
                    continue
                normalized = line.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                overlap = len(question_terms.intersection(self._content_terms(line)))
                if overlap:
                    type_priority = int(
                        requested_variable and any("::" in value for value in identifiers)
                    )
                    candidates.append(
                        (type_priority, overlap, hit.score, citation.reference, line)
                    )
        if not candidates:
            return None
        candidates.sort(
            key=lambda candidate: (candidate[0], candidate[1], candidate[2]),
            reverse=True,
        )
        selected = candidates[:5]
        prefix = (
            "La evidencia técnica indica:"
            if expected_language == "es"
            else "The technical evidence states:"
        )
        claims = [
            GeneratedClaim(text=f"{prefix} {line}", citations=[reference])
            for _, _, _, reference, line in selected
        ]
        fallback = GeneratedResponse(
            status="grounded",
            language=expected_language,
            claims=claims,
            unanswered_parts=[],
        )
        errors = self._validation_errors(
            fallback,
            question,
            expected_language,
            {citation.reference for citation in citations},
            {
                citation.reference: hit.chunk.text
                for citation, hit in zip(citations, hits, strict=True)
            },
        )
        return fallback if not errors else None

    @staticmethod
    def _minimum_claims(question: str) -> int:
        second_question = re.search(
            r"\b(?:y|e|and)\s+(?:(?:en|por)\s+)?"
            r"(?:cómo|cuál|cuáles|cuánto|cuántos|dónde|qué|how|what|where|which)\b",
            question.casefold(),
        )
        return 2 if second_question else 1

    def _validation_errors(
        self,
        generated: GeneratedResponse,
        question: str,
        expected_language: SupportedLanguage,
        valid_references: set[int],
        evidence_by_reference: dict[int, str],
    ) -> list[str]:
        errors: list[str] = []
        if generated.language != expected_language:
            errors.append(
                f"El idioma declarado debe ser {expected_language}, no {generated.language}."
            )

        claim_text = " ".join(claim.text for claim in generated.claims)
        if claim_text and not text_matches_language(claim_text, expected_language):
            errors.append("El texto mezcla idiomas o no usa el idioma de la pregunta.")

        for claim in generated.claims:
            invalid = set(claim.citations).difference(valid_references)
            if invalid:
                errors.append(f"La afirmación usa citas inexistentes: {sorted(invalid)}.")
                continue
            claim_identifiers = self._TECHNICAL_IDENTIFIER.findall(claim.text)
            cited_evidence = "\n".join(
                evidence_by_reference[reference] for reference in claim.citations
            )
            for identifier in claim_identifiers:
                if identifier.casefold() not in cited_evidence.casefold():
                    errors.append(
                        f"La cita no contiene literalmente el identificador {identifier}."
                    )
                    continue
                evidence_identifiers = self._TECHNICAL_IDENTIFIER.findall(cited_evidence)
                expanded = next(
                    (
                        candidate
                        for candidate in evidence_identifiers
                        if candidate.casefold().endswith("." + identifier.casefold())
                    ),
                    None,
                )
                if expanded:
                    errors.append(
                        f"Usa el identificador completo {expanded} en lugar de {identifier}."
                    )

            if self._TECHNICAL_QUESTION.search(question) and not claim_identifiers:
                errors.append(
                    "Cada afirmación solicitada sobre tablas, variables, campos, ETL, "
                    "procedimientos o rutas debe incluir su identificador técnico literal."
                )

        if generated.status == "grounded":
            minimum = self._minimum_claims(question)
            if len(generated.claims) < minimum:
                errors.append(
                    f"La pregunta es compuesta y necesita al menos {minimum} afirmaciones."
                )
            if generated.unanswered_parts:
                errors.append("No puede ser grounded si deja partes sin responder.")
        elif self._TECHNICAL_QUESTION.search(question) and any(
            self._TECHNICAL_IDENTIFIER.search(evidence)
            for evidence in evidence_by_reference.values()
        ):
            errors.append(
                "Antes de declarar evidencia insuficiente, revisa EVIDENCIA TÉCNICA "
                "LITERAL: los fragmentos recuperados sí contienen identificadores candidatos."
            )
        return errors

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
            errors = self._validation_errors(
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

    def query(self, question: str) -> QueryResult:
        question = question.strip()
        if not question:
            raise ValueError("La pregunta no puede estar vacía")
        expected_language = infer_question_language(question)
        vector = self.embedder.embed_query(question)
        hits = self.store.search(vector, self.top_k, self.min_score)
        selected, discarded, selected_ranks = self._select_hits(hits)
        raw_rank_by_hit = {
            id(hit): raw_rank for hit, raw_rank in zip(selected, selected_ranks, strict=True)
        }
        selected = self._prioritize_context(question, selected)
        retrieval_diagnostics = self._retrieval_diagnostics(
            hits, selected, raw_rank_by_hit, discarded
        )
        citations = [
            Citation(
                reference=index,
                source_id=hit.chunk.source_id,
                file_name=hit.chunk.file_name,
                original_uri=hit.chunk.original_uri,
                relative_path=hit.chunk.relative_path,
                locator=hit.chunk.locator,
                section=hit.chunk.section,
                snippet=hit.chunk.text[:600],
                score=round(hit.score, 6),
            )
            for index, hit in enumerate(selected, start=1)
        ]
        if not selected:
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
                retrieval_diagnostics=retrieval_diagnostics,
            )

        context_parts: list[str] = []
        for citation, hit in zip(citations, selected, strict=True):
            location = ", ".join(f"{key}: {value}" for key, value in citation.locator.items())
            context_parts.append(
                f"[{citation.reference}] Archivo: {citation.relative_path}"
                f"{f' | Sección: {citation.section}' if citation.section else ''}"
                f"{f' | {location}' if location else ''}\n{hit.chunk.text}"
            )
        context = "\n\n".join(context_parts)
        technical_hints = self._technical_evidence_hints(question, citations, selected)
        if technical_hints:
            context = f"{technical_hints}\n\nFRAGMENTOS COMPLETOS\n{context}"
        generation_mode: Literal["llm", "extractive_fallback"] = (
            "extractive_fallback"
            if self.generation_strategy == "extractive_fallback"
            else "llm"
        )
        generated = None
        if self.generation_strategy == "llm":
            generated = self._generate_validated(
                question,
                context,
                expected_language,
                {citation.reference for citation in citations},
                {
                    citation.reference: hit.chunk.text
                    for citation, hit in zip(citations, selected, strict=True)
                },
            )
        if generated is None:
            generated = self._extractive_technical_fallback(
                question, citations, selected, expected_language
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
                citations=citations,
                model=self.generator.model_name,
                embedding_model=self.embedder.model_name,
                answer_language=expected_language,
                claims=[],
                generation_mode="none",
                retrieval_diagnostics=retrieval_diagnostics,
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
                citations=citations,
                model=self.generator.model_name,
                embedding_model=self.embedder.model_name,
                answer_language=expected_language,
                claims=claims,
                generation_mode=generation_mode,
                retrieval_diagnostics=retrieval_diagnostics,
            )

        return QueryResult(
            answer_status="grounded",
            answer=answer,
            citations=citations,
            model=self.generator.model_name,
            embedding_model=self.embedder.model_name,
            answer_language=expected_language,
            claims=claims,
            generation_mode=generation_mode,
            retrieval_diagnostics=retrieval_diagnostics,
        )
