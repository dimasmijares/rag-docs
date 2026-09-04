from __future__ import annotations

import uuid
from collections.abc import Iterable
from typing import Protocol

from rag_docs.contracts import (
    AppError,
    DocumentChunk,
    ErrorKind,
    IndexedDocument,
    IndexFingerprint,
    SearchHit,
    chunk_from_payload,
)


class VectorStore(Protocol):
    def ensure_collection(
        self, vector_size: int, fingerprint: IndexFingerprint | None = None
    ) -> None: ...

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]: ...

    def delete_document(self, document_id: str) -> None: ...

    def prune_document(self, document_id: str, keep_chunk_ids: set[str]) -> None: ...

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None: ...

    def search(
        self, vector: list[float], limit: int, score_threshold: float | None
    ) -> list[SearchHit]: ...


class QdrantVectorStore:
    """Qdrant adapter. ``collection_name`` is the logical name configured by the
    operator; it is never a physical collection itself. It is always a Qdrant
    *alias*, and the physical collection it points to is named after the
    active ``IndexFingerprint`` (``RULE-004``). This is what lets a
    configuration change (a different embedding model, a different chunker) be
    rejected explicitly instead of silently writing incompatible vectors into
    whatever collection happens to already exist.
    """

    def __init__(self, url: str, collection_name: str, *, _direct_mode: bool = False) -> None:
        from qdrant_client import QdrantClient

        if url == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(url=url, timeout=30, check_compatibility=False)
        self.collection_name = collection_name
        self._bound_fingerprint: IndexFingerprint | None = None
        self._direct_mode = _direct_mode

    @classmethod
    def for_physical_collection(
        cls, client: object, physical_name: str
    ) -> QdrantVectorStore:
        """A store bound directly to a physical collection, bypassing alias
        resolution. Used to populate a migration candidate before it is ever
        reachable through the logical alias (``migrate_and_publish``)."""
        store = cls.__new__(cls)
        store.client = client
        store.collection_name = physical_name
        store._bound_fingerprint = None
        store._direct_mode = True
        return store

    def physical_name_for(self, fingerprint: IndexFingerprint) -> str:
        """The physical collection name the alias would point to for
        ``fingerprint``. Public because migration orchestration needs it
        before the alias exists to point at it."""
        return self._physical_name(fingerprint)

    def _physical_name(self, fingerprint: IndexFingerprint) -> str:
        if self._direct_mode:
            return self.collection_name
        return f"{self.collection_name}__{fingerprint.digest()}"

    def _resolve_alias(self) -> str | None:
        if self._direct_mode:
            exists = self.client.collection_exists(self.collection_name)
            return self.collection_name if exists else None
        for alias in self.client.get_aliases().aliases:
            if alias.alias_name == self.collection_name:
                return alias.collection_name
        return None

    def delete_physical(self, physical_name: str) -> None:
        """End the rollback window explicitly: delete a physical collection
        that is no longer the alias target. Refuses to delete whatever the
        alias currently points to."""
        if self._resolve_alias() == physical_name:
            raise AppError(
                ErrorKind.VALIDATION,
                f"'{physical_name}' es el objetivo actual del alias; no se elimina.",
            )
        if self.client.collection_exists(physical_name):
            self.client.delete_collection(physical_name)

    def bind_fingerprint(self, fingerprint: IndexFingerprint) -> None:
        """Record the fingerprint every subsequent read/write is checked
        against, without touching Qdrant. ``ensure_collection`` calls this too;
        a query-only process binds it directly so a search still fails
        explicitly against a mismatched index (``RULE-004``)."""
        self._bound_fingerprint = fingerprint

    def verify_fingerprint(self, fingerprint: IndexFingerprint) -> None:
        physical = self._physical_name(fingerprint)
        current = self._resolve_alias()
        if current is None:
            raise AppError(
                ErrorKind.NOT_FOUND,
                f"No existe el índice '{self.collection_name}'.",
            )
        if current != physical:
            raise AppError(
                ErrorKind.VALIDATION,
                f"El índice '{self.collection_name}' no coincide con el fingerprint "
                "activo; ejecute la migración antes de escribir o consultar.",
            )

    def _check_bound(self) -> IndexFingerprint:
        if self._bound_fingerprint is None:
            raise AppError(
                ErrorKind.VALIDATION,
                "Ningún fingerprint vinculado: llame a ensure_collection o "
                "bind_fingerprint antes de usar el índice.",
            )
        self.verify_fingerprint(self._bound_fingerprint)
        return self._bound_fingerprint

    def _create_physical(self, name: str, vector_size: int) -> None:
        from qdrant_client.models import Distance, VectorParams

        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def publish_alias(self, physical_name: str) -> None:
        """Atomically repoint the logical alias at ``physical_name``. Both the
        delete of the old mapping and the creation of the new one are sent as
        a single Qdrant operation, so the alias is never briefly absent."""
        from qdrant_client.models import (
            CreateAlias,
            CreateAliasOperation,
            DeleteAlias,
            DeleteAliasOperation,
        )

        current = self._resolve_alias()
        operations: list[CreateAliasOperation | DeleteAliasOperation] = []
        if current is not None:
            operations.append(
                DeleteAliasOperation(delete_alias=DeleteAlias(alias_name=self.collection_name))
            )
        operations.append(
            CreateAliasOperation(
                create_alias=CreateAlias(
                    collection_name=physical_name, alias_name=self.collection_name
                )
            )
        )
        self.client.update_collection_aliases(change_aliases_operations=operations)

    def rollback_alias(self, previous_physical_name: str) -> None:
        """Repoint the alias back at a prior physical collection. The prior
        collection is never deleted by ``publish_alias``, so it stays
        available for this during the rollback window (``RULE-004``)."""
        if not self.client.collection_exists(previous_physical_name):
            raise AppError(
                ErrorKind.NOT_FOUND,
                f"La colección anterior '{previous_physical_name}' ya no existe: "
                "fuera de la ventana de rollback.",
            )
        self.publish_alias(previous_physical_name)

    def ensure_collection(
        self, vector_size: int, fingerprint: IndexFingerprint | None = None
    ) -> None:
        if fingerprint is None:
            raise AppError(
                ErrorKind.VALIDATION,
                "ensure_collection requiere el fingerprint activo (RULE-004).",
            )
        physical = self._physical_name(fingerprint)
        current = self._resolve_alias()
        if current is None:
            self._create_physical(physical, vector_size)
            if not self._direct_mode:
                self.publish_alias(physical)
        elif current != physical:
            raise AppError(
                ErrorKind.VALIDATION,
                f"El índice '{self.collection_name}' ya existe con otro fingerprint "
                f"('{current}' != '{physical}'); reutilizarlo sin migrar está prohibido "
                "(RULE-004). Ejecute la migración explícita antes de escribir.",
            )
        self.bind_fingerprint(fingerprint)

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

    def prune_document(self, document_id: str, keep_chunk_ids: set[str]) -> None:
        """Delete every point of ``document_id`` whose ``chunk_id`` is not in
        ``keep_chunk_ids``. Since a chunk's identity now folds in its content
        hash (``chunking.chunk_document``), a rewrite's new points already
        exist after ``upsert``; this only removes what became stale, instead
        of a blanket delete before the upsert that leaves the document
        momentarily empty if the process is interrupted in between."""
        if not keep_chunk_ids:
            self.delete_document(document_id)
            return
        from qdrant_client.models import (
            FieldCondition,
            Filter,
            FilterSelector,
            MatchExcept,
            MatchValue,
        )

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key="document_id", match=MatchValue(value=document_id)),
                        FieldCondition(
                            key="chunk_id", match=MatchExcept(**{"except": list(keep_chunk_ids)})
                        ),
                    ]
                )
            ),
            wait=True,
        )

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        from qdrant_client.models import PointStruct

        if len(chunks) != len(vectors):
            raise ValueError("Cada chunk debe tener exactamente un vector")
        self._check_bound()
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
        self._check_bound()
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
