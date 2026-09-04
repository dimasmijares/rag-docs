from __future__ import annotations

from rag_docs.chunking import chunk_document
from rag_docs.contracts import IndexError, IndexReport
from rag_docs.embeddings import Embedder
from rag_docs.extractors import extract_document
from rag_docs.models import DocumentCandidate
from rag_docs.sources.base import DocumentSource
from rag_docs.vector_store import VectorStore

__all__ = ["IndexError", "IndexReport", "IndexingService"]


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

    def index(self, requested_source_ids: list[str] | None = None) -> IndexReport:
        selected_ids = set(requested_source_ids or self.sources)
        unknown = selected_ids.difference(self.sources)
        if unknown:
            raise ValueError(f"Fuentes desconocidas: {', '.join(sorted(unknown))}")

        self.store.ensure_collection(self.embedder.dimension)
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
                    candidate, units, self.chunk_tokens, self.chunk_overlap
                )
                vectors = self.embedder.embed_documents([chunk.text for chunk in chunks])
                if previous:
                    self.store.delete_document(document_id)
                self.store.upsert(chunks, vectors)
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
