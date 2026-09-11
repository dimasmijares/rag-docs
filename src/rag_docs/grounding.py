"""Pure pieces behind ``GroundingPort`` (``ADR-RAG-010``, ``WRK-TASK-090``).

``ContextBuilder`` and ``AnswerValidator`` are functions over DTO: no I/O, no
knowledge of Qdrant, Ollama or FastAPI. They absorb what used to be private
methods of ``QueryService`` so the split into a future ``context-grounding-
service`` is an extraction of this module, not a rewrite.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from rag_docs.contracts import Citation, GroundingVerdict, RetrievalDiagnostic, SearchHit
from rag_docs.generation import GeneratedClaim, GeneratedResponse
from rag_docs.language import SupportedLanguage, infer_question_language, text_matches_language

TECHNICAL_IDENTIFIER = re.compile(
    r"\b(?:[A-Za-z][\w]*::[\w]+|(?:[A-Za-z][\w]*\.)+[A-Za-z][\w]*|"
    r"[A-Za-z][A-Za-z0-9]*_(?:[A-Za-z0-9]+_?)+)\b"
)
TECHNICAL_QUESTION = re.compile(
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


def _content_fingerprint(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    unaccented = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[a-z0-9]+", unaccented))


def _content_terms(text: str) -> set[str]:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    normalized = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    terms: set[str] = set()
    for token in re.findall(r"[a-z0-9]+", normalized):
        if len(token) < 4 or token in _QUESTION_STOPWORDS:
            continue
        if len(token) > 5 and token.endswith("es"):
            token = token[:-2]
        elif len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        terms.add(token)
    return terms


@dataclass(frozen=True, slots=True)
class BuiltContext:
    """Everything ``QueryService`` needs from context selection: the pure
    ``(context, selected_hits)`` pair required by ``GroundingPort.build_context``,
    plus the citations and diagnostics it renders into the response."""

    selected: list[SearchHit]
    citations: list[Citation]
    context: str
    retrieval_diagnostics: list[RetrievalDiagnostic]


class ContextBuilder:
    """Hits más pregunta produce contexto y citas (``ADR-RAG-010``).

    Absorbs the former ``QueryService._select_hits``, ``_prioritize_context``,
    ``_technical_evidence_hints`` and citation/context assembly.
    """

    def __init__(self, context_chunks: int = 5) -> None:
        self.context_chunks = context_chunks

    def build(self, question: str, hits: list[SearchHit]) -> BuiltContext:
        selected, discarded, selected_ranks = self._select_hits(hits)
        raw_rank_by_hit = {
            id(hit): raw_rank for hit, raw_rank in zip(selected, selected_ranks, strict=True)
        }
        selected = self._prioritize_context(question, selected)
        retrieval_diagnostics = self._retrieval_diagnostics(
            hits, selected, raw_rank_by_hit, discarded
        )
        citations = self._build_citations(selected)
        context = self._assemble_context(citations, selected)
        technical_hints = self._technical_evidence_hints(question, citations, selected)
        if technical_hints:
            context = f"{technical_hints}\n\nFRAGMENTOS COMPLETOS\n{context}"
        return BuiltContext(
            selected=selected,
            citations=citations,
            context=context,
            retrieval_diagnostics=retrieval_diagnostics,
        )

    def build_context(self, question: str, hits: list[SearchHit]) -> tuple[str, list[SearchHit]]:
        """Narrow adapter matching ``GroundingPort.build_context`` exactly."""
        result = self.build(question, hits)
        return result.context, result.selected

    def _select_hits(
        self, hits: list[SearchHit]
    ) -> tuple[list[SearchHit], dict[int, str], list[int]]:
        selected: list[SearchHit] = []
        selected_ranks: list[int] = []
        discarded: dict[int, str] = {}
        seen: dict[str, SearchHit] = {}
        for rank, hit in enumerate(hits, start=1):
            fingerprint = _content_fingerprint(hit.chunk.text)
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

    @staticmethod
    def _prioritize_context(question: str, hits: list[SearchHit]) -> list[SearchHit]:
        if not TECHNICAL_QUESTION.search(question):
            return hits
        return sorted(
            hits,
            key=lambda hit: (
                len(TECHNICAL_IDENTIFIER.findall(hit.chunk.text)),
                hit.score,
            ),
            reverse=True,
        )

    @staticmethod
    def _build_citations(selected: list[SearchHit]) -> list[Citation]:
        return [
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

    @staticmethod
    def _assemble_context(citations: list[Citation], selected: list[SearchHit]) -> str:
        context_parts: list[str] = []
        for citation, hit in zip(citations, selected, strict=True):
            location = ", ".join(f"{key}: {value}" for key, value in citation.locator.items())
            context_parts.append(
                f"[{citation.reference}] Archivo: {citation.relative_path}"
                f"{f' | Sección: {citation.section}' if citation.section else ''}"
                f"{f' | {location}' if location else ''}\n{hit.chunk.text}"
            )
        return "\n\n".join(context_parts)

    @staticmethod
    def _technical_evidence_hints(
        question: str,
        citations: list[Citation],
        hits: list[SearchHit],
    ) -> str:
        if not TECHNICAL_QUESTION.search(question):
            return ""
        lines: list[str] = []
        seen: set[str] = set()
        for citation, hit in zip(citations, hits, strict=True):
            for raw_line in hit.chunk.text.splitlines():
                line = " ".join(raw_line.split())
                if not line or not TECHNICAL_IDENTIFIER.search(line):
                    continue
                normalized = line.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                lines.append(f"[{citation.reference}] {line}")
                if len(lines) == 12:
                    return "EVIDENCIA TÉCNICA LITERAL\n" + "\n".join(lines)
        return "EVIDENCIA TÉCNICA LITERAL\n" + "\n".join(lines) if lines else ""


class AnswerValidator:
    """Respuesta generada más evidencia produce veredicto de grounding
    (``ADR-RAG-010``). Absorbs the former ``QueryService._validation_errors``
    and ``_extractive_technical_fallback``."""

    @staticmethod
    def minimum_claims(question: str) -> int:
        second_question = re.search(
            r"\b(?:y|e|and)\s+(?:(?:en|por)\s+)?"
            r"(?:cómo|cuál|cuáles|cuánto|cuántos|dónde|qué|how|what|where|which)\b",
            question.casefold(),
        )
        return 2 if second_question else 1

    def validation_errors(
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
            claim_identifiers = TECHNICAL_IDENTIFIER.findall(claim.text)
            cited_evidence = "\n".join(
                evidence_by_reference[reference] for reference in claim.citations
            )
            for identifier in claim_identifiers:
                if identifier.casefold() not in cited_evidence.casefold():
                    errors.append(
                        f"La cita no contiene literalmente el identificador {identifier}."
                    )
                    continue
                evidence_identifiers = TECHNICAL_IDENTIFIER.findall(cited_evidence)
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

            if TECHNICAL_QUESTION.search(question) and not claim_identifiers:
                errors.append(
                    "Cada afirmación solicitada sobre tablas, variables, campos, ETL, "
                    "procedimientos o rutas debe incluir su identificador técnico literal."
                )

        if generated.status == "grounded":
            minimum = self.minimum_claims(question)
            if len(generated.claims) < minimum:
                errors.append(
                    f"La pregunta es compuesta y necesita al menos {minimum} afirmaciones."
                )
            if generated.unanswered_parts:
                errors.append("No puede ser grounded si deja partes sin responder.")
        elif TECHNICAL_QUESTION.search(question) and any(
            TECHNICAL_IDENTIFIER.search(evidence)
            for evidence in evidence_by_reference.values()
        ):
            errors.append(
                "Antes de declarar evidencia insuficiente, revisa EVIDENCIA TÉCNICA "
                "LITERAL: los fragmentos recuperados sí contienen identificadores candidatos."
            )
        return errors

    def validate(
        self,
        answer: GeneratedResponse,
        question: str,
        evidence_by_reference: dict[int, str],
    ) -> GroundingVerdict:
        """Matches ``GroundingPort.validate`` exactly: derives expected language
        and valid references purely from ``question``/``evidence_by_reference``,
        so callers behind the future port don't have to recompute state this
        piece can already derive."""
        expected_language = infer_question_language(question)
        errors = self.validation_errors(
            answer,
            question,
            expected_language,
            set(evidence_by_reference),
            evidence_by_reference,
        )
        return GroundingVerdict(grounded=not errors, errors=tuple(errors))

    def extractive_technical_fallback(
        self,
        question: str,
        citations: list[Citation],
        hits: list[SearchHit],
        expected_language: SupportedLanguage,
    ) -> GeneratedResponse | None:
        if not TECHNICAL_QUESTION.search(question):
            return None
        question_terms = _content_terms(question)
        requested_variable = bool(re.search(r"\bvariables?\b", question, re.IGNORECASE))
        candidates: list[tuple[int, int, float, int, str]] = []
        seen: set[str] = set()
        for citation, hit in zip(citations, hits, strict=True):
            for raw_line in hit.chunk.text.splitlines():
                line = " ".join(raw_line.split())
                identifiers = TECHNICAL_IDENTIFIER.findall(line)
                if not line or not identifiers:
                    continue
                normalized = line.casefold()
                if normalized in seen:
                    continue
                seen.add(normalized)
                overlap = len(question_terms.intersection(_content_terms(line)))
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
        errors = self.validation_errors(
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
