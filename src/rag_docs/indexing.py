from __future__ import annotations

from collections.abc import Callable

from rag_docs.chunking import CHUNKER_VERSION, chunk_document
from rag_docs.contracts import AppError, ErrorKind, IndexError, IndexFingerprint, IndexReport
from rag_docs.embeddings import Embedder
from rag_docs.extractors import EXTRACTOR_VERSION, extract_document
from rag_docs.models import DocumentCandidate
from rag_docs.sources.base import DocumentSource
from rag_docs.vector_store import QdrantVectorStore, VectorStore

__all__ = [
    "IndexError",
    "IndexReport",
    "IndexingService",
    "build_fingerprint",
    "migrate_and_publish",
]


def build_fingerprint(
    embedder: Embedder, chunk_tokens: int, chunk_overlap: int
) -> IndexFingerprint:
    """Everything RULE-004 requires to tell two collections apart, gathered
    from the components that actually vary: none of it stays opaque inside an
    adapter (``ADR-RAG-010``)."""
    return IndexFingerprint(
        extractor=EXTRACTOR_VERSION,
        chunker=CHUNKER_VERSION,
        chunk_tokens=chunk_tokens,
        chunk_overlap=chunk_overlap,
        embedding_model=embedder.model_name,
        embedding_revision=embedder.revision,
        dimension=embedder.dimension,
        normalize=embedder.normalize,
        query_prefix=embedder.query_prefix,
        passage_prefix=embedder.passage_prefix,
    )


class IndexingService:
    def __init__(
        self,
        sources: list[DocumentSource],
        embedder: Embedder,
        store: VectorStore,
        chunk_tokens: int = 500,
        chunk_overlap: int = 75,
    ) -> None:
        self.sources = {source.source_id: source for source in sources}
        self.embedder = embedder
        self.store = store
        self.chunk_tokens = chunk_tokens
        self.chunk_overlap = chunk_overlap
        self._fingerprint: IndexFingerprint | None = None

    @property
    def fingerprint(self) -> IndexFingerprint:
        if self._fingerprint is None:
            self._fingerprint = build_fingerprint(
                self.embedder, self.chunk_tokens, self.chunk_overlap
            )
        return self._fingerprint

    def index(self, requested_source_ids: list[str] | None = None) -> IndexReport:
        selected_ids = set(requested_source_ids or self.sources)
        unknown = selected_ids.difference(self.sources)
        if unknown:
            raise ValueError(f"Fuentes desconocidas: {', '.join(sorted(unknown))}")

        self.store.ensure_collection(self.embedder.dimension, self.fingerprint)
        existing = self.store.list_documents(selected_ids)
        report = IndexReport()
        candidates: dict[str, DocumentCandidate] = {}
        discovered_sources: set[str] = set()

        for source_id in sorted(selected_ids):
            try:
                discovered = self.sources[source_id].discover()
                discovered_sources.add(source_id)
                candidates.update({candidate.document_id: candidate for candidate in discovered})
            except Exception as exc:
                report.errors.append(IndexError(source_id, "", str(exc)))

        for document_id, candidate in candidates.items():
            previous = existing.get(document_id)
            if previous and previous.content_hash == candidate.content_hash:
                report.unchanged += 1
                continue
            try:
                units = extract_document(candidate)
                chunks = chunk_document(
                    candidate, units, self.chunk_tokens, self.chunk_overlap, self.fingerprint
                )
                vectors = self.embedder.embed_documents([chunk.text for chunk in chunks])
                self.store.upsert(chunks, vectors)
                if previous:
                    # Content differs at the same position produces a new chunk_id
                    # (chunk_document folds content_hash into identity), so the
                    # rewrite above never needed a delete first; only points that
                    # became stale are pruned now.
                    self.store.prune_document(
                        document_id, {chunk.chunk_id for chunk in chunks}
                    )
                report.chunks_written += len(chunks)
                if previous:
                    report.updated += 1
                else:
                    report.added += 1
                if not chunks:
                    report.skipped += 1
            except Exception as exc:
                report.skipped += 1
                report.errors.append(
                    IndexError(candidate.source_id, candidate.relative_path, str(exc))
                )

        current_ids = set(candidates)
        for document_id, previous in existing.items():
            if previous.source_id in discovered_sources and document_id not in current_ids:
                self.store.delete_document(document_id)
                report.deleted += 1
        return report


def migrate_and_publish(
    live: IndexingService,
    validate: Callable[[IndexReport, VectorStore], bool],
) -> str:
    """Build the collection for ``live``'s active fingerprint out of band,
    validate it, and only then move the alias.

    Nothing under ``live.store``'s logical name is touched until ``validate``
    returns ``True``: the candidate is populated through a store bound
    directly to its own physical collection, invisible through the alias
    (``QdrantVectorStore.for_physical_collection``). If ``validate`` -
    typically a gold set run against the candidate - rejects it, the alias is
    never moved and the candidate collection is left behind for inspection.
    The previously published physical collection is never deleted here, so
    ``QdrantVectorStore.rollback_alias`` can restore it during the window the
    operator chooses to keep it.
    """
    if not isinstance(live.store, QdrantVectorStore):
        raise AppError(
            ErrorKind.VALIDATION,
            "migrate_and_publish requiere un QdrantVectorStore.",
        )
    fingerprint = live.fingerprint
    physical_name = live.store.physical_name_for(fingerprint)
    candidate_store = QdrantVectorStore.for_physical_collection(
        live.store.client, physical_name
    )
    candidate_indexing = IndexingService(
        list(live.sources.values()),
        live.embedder,
        candidate_store,
        live.chunk_tokens,
        live.chunk_overlap,
    )
    report = candidate_indexing.index()
    if report.errors:
        raise AppError(
            ErrorKind.DEPENDENCY_UNAVAILABLE,
            f"La migración no pobló el índice candidato: {len(report.errors)} error(es).",
        )
    if not validate(report, candidate_store):
        raise AppError(
            ErrorKind.VALIDATION,
            f"El índice candidato '{physical_name}' no superó la validación; "
            "el alias no se movió.",
        )
    live.store.publish_alias(physical_name)
    return physical_name
