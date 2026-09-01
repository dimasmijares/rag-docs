from __future__ import annotations

import re

from rag_docs.generation import (
    GeneratedClaim,
    GeneratedResponse,
    GeneratorCapabilities,
    GeneratorHealth,
)
from rag_docs.models import DocumentChunk, IndexedDocument, SearchHit


class FakeEmbedder:
    dimension = 3
    model_name = "fake-multilingual"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0, 0.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), 1.0, 0.0]


class FakeVectorStore:
    def __init__(self) -> None:
        self.documents: dict[str, IndexedDocument] = {}
        self.chunks: dict[str, list[DocumentChunk]] = {}
        self.hits: list[SearchHit] = []
        self.vector_size: int | None = None

    def ensure_collection(self, vector_size: int) -> None:
        self.vector_size = vector_size

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]:
        return {
            key: value
            for key, value in self.documents.items()
            if value.source_id in source_ids
        }

    def delete_document(self, document_id: str) -> None:
        self.documents.pop(document_id, None)
        self.chunks.pop(document_id, None)

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        assert len(chunks) == len(vectors)
        if not chunks:
            return
        document_id = chunks[0].document_id
        self.chunks[document_id] = list(chunks)
        self.documents[document_id] = IndexedDocument(
            document_id=document_id,
            source_id=chunks[0].source_id,
            content_hash=chunks[0].content_hash,
        )

    def search(
        self, vector: list[float], limit: int, score_threshold: float | None
    ) -> list[SearchHit]:
        return [
            hit
            for hit in self.hits
            if score_threshold is None or hit.score >= score_threshold
        ][:limit]


class FakeGenerator:
    model_name = "fake-generator"

    @property
    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(True, False, False)

    def health(self) -> GeneratorHealth:
        return GeneratorHealth(True, "fake://generator", self.model_name, (self.model_name,))

    def __init__(
        self,
        answer: str | GeneratedResponse | list[GeneratedResponse] = (
            "La respuesta consta en la fuente [1]."
        ),
    ) -> None:
        if isinstance(answer, list):
            self.responses = answer
        elif isinstance(answer, GeneratedResponse):
            self.responses = [answer]
        elif answer == "INSUFFICIENT_EVIDENCE":
            self.responses = [
                GeneratedResponse(
                    status="insufficient_evidence",
                    language="es",
                    claims=[],
                    unanswered_parts=["pregunta completa"],
                )
            ]
        else:
            references = [int(value) for value in re.findall(r"\[(\d+)\]", answer)]
            text = re.sub(r"\s*\[\d+\]", "", answer).strip()
            self.responses = [
                GeneratedResponse(
                    status="grounded",
                    language="es",
                    claims=[GeneratedClaim(text=text, citations=references or [1])],
                    unanswered_parts=[],
                )
            ]
        self.context = ""
        self.feedback: list[str | None] = []

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> GeneratedResponse:
        self.context = context
        self.feedback.append(validation_feedback)
        index = min(len(self.feedback) - 1, len(self.responses) - 1)
        return self.responses[index]
