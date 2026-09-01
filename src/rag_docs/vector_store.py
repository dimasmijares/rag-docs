from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Protocol

from rag_docs.models import (
    DocumentChunk,
    IndexedDocument,
    SearchHit,
    chunk_from_payload,
)


class VectorStore(Protocol):
    def ensure_collection(self, vector_size: int) -> None: ...

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]: ...

    def delete_document(self, document_id: str) -> None: ...

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None: ...

    def search(
        self, vector: list[float], limit: int, score_threshold: float | None
    ) -> list[SearchHit]: ...


class QdrantVectorStore:
    def __init__(self, url: str, collection_name: str) -> None:
        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=url, timeout=30, check_compatibility=False)
        self.collection_name = collection_name

    def ensure_collection(self, vector_size: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        if self.client.collection_exists(self.collection_name):
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]:
        documents: dict[str, IndexedDocument] = {}
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=256,
                offset=offset,
                with_payload=["document_id", "source_id", "content_hash"],
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                source_id = str(payload.get("source_id", ""))
                if source_id not in source_ids:
                    continue
                document_id = str(payload["document_id"])
                documents[document_id] = IndexedDocument(
                    document_id=document_id,
                    source_id=source_id,
                    content_hash=str(payload["content_hash"]),
                )
            if offset is None:
                break
        return documents

    def delete_document(self, document_id: str) -> None:
        from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                )
            ),
            wait=True,
        )

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        from qdrant_client.models import PointStruct

        if len(chunks) != len(vectors):
            raise ValueError("Cada chunk debe tener exactamente un vector")
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=vector,
                payload=chunk.payload(),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            self.client.upsert(
                collection_name=self.collection_name, points=points, wait=True
            )

    def search(
        self, vector: list[float], limit: int, score_threshold: float | None
    ) -> list[SearchHit]:
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        )
        return [
            SearchHit(chunk=chunk_from_payload(point.payload or {}), score=float(point.score))
            for point in response.points
        ]


def batch(items: list[DocumentChunk], size: int) -> Iterable[list[DocumentChunk]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
