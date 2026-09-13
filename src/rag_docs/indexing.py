from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from rag_docs.chunking import CHUNKER_VERSION, chunk_document
from rag_docs.contracts import (
    SINGLE_TENANT_ACL,
    AclFields,
    AppError,
    ErrorKind,
    IndexError,
    IndexFingerprint,
    IndexPublicationPort,
    IndexReport,
    VectorStorePort,
)
from rag_docs.embeddings import Embedder
from rag_docs.extractors import EXTRACTOR_VERSION, extract_document
from rag_docs.models import DocumentCandidate
from rag_docs.sources.base import DocumentSource

__all__ = [
    "IndexError",
    "IndexReport",
    "IndexingService",
    "PAYLOAD_SCHEMA_VERSION",
    "build_fingerprint",
    "default_acl_resolver",
    "migrate_and_publish",
]

# Bump when the set or meaning of ACL payload fields changes: it is part of
# IndexFingerprint (RULE-004), so a schema change always forces a new physical
# collection instead of silently mixing old and new payload shapes (ADR-RAG-009).
PAYLOAD_SCHEMA_VERSION = 2


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
        payload_schema_version=PAYLOAD_SCHEMA_VERSION,
    )


def default_acl_resolver(candidate: DocumentCandidate) -> AclFields | None:
    """``AuthorizationPort``-shaped ACL resolution for ``v0.3.0``
    (``ADR-RAG-009``): every document belongs to the single tenant, visible to
    every subject in it. Real per-document policy resolution — connector
    identity, group expansion, inheritance — is ``WRK-TASK-043``/``046``; this
    always returns the single-tenant ACL, but a resolver is still consulted
    (and still validated) so an invalid result never silently becomes a chunk
    with an absent tenant or empty subjects."""
    return SINGLE_TENANT_ACL if SINGLE_TENANT_ACL.is_valid() else None


class IndexingService:
    def __init__(
        self,
        sources: list[DocumentSource],
        embedder: Embedder,
        store: VectorStorePort,
        chunk_tokens: int = 500,
        chunk_overlap: int = 75,
        acl_resolver: Callable[[DocumentCandidate], AclFields | None] = default_acl_resolver,
    ) -> None:
        self.sources = {source.source_id: source for source in sources}
        self.embedder = embedder
        self.store = store
        self.chunk_tokens = chunk_tokens
        self.chunk_overlap = chunk_overlap
        self.acl_resolver = acl_resolver
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
            acl = self.acl_resolver(candidate)
            if acl is None:
                report.skipped += 1
                report.errors.append(
                    IndexError(
                        candidate.source_id,
                        candidate.relative_path,
                        "ACL no normalizable: el documento no se indexa (ADR-RAG-009).",
                    )
                )
                continue
            try:
                units = extract_document(candidate)
                chunks = [
                    replace(
                        chunk,
                        tenant_id=acl.tenant_id,
                        acl_subjects=acl.acl_subjects,
                        classification=acl.classification,
                        acl_policy_id=acl.acl_policy_id,
                        acl_version=acl.acl_version,
                    )
                    for chunk in chunk_document(
                        candidate, units, self.chunk_tokens, self.chunk_overlap, self.fingerprint
                    )
                ]
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
    validate: Callable[[IndexReport, VectorStorePort], bool],
) -> str:
    """Build the index for ``live``'s active fingerprint out of band, validate
    it, and only then move the alias.

    Nothing under ``live.store``'s logical name is touched until ``validate``
    returns ``True``: the candidate is populated through a store bound
    directly to its own physical index, invisible through the alias
    (``IndexPublicationPort.candidate_store``). If ``validate`` - typically a
    gold set run against the candidate - rejects it, the alias is never moved
    and the candidate index is left behind for inspection. The previously
    published physical index is never deleted here, so
    ``IndexPublicationPort.rollback_alias`` can restore it during the window
    the operator chooses to keep it.
    """
    publication = live.store
    if not isinstance(publication, IndexPublicationPort):
        raise AppError(
            ErrorKind.VALIDATION,
            "migrate_and_publish requiere un store que implemente IndexPublicationPort.",
        )
    fingerprint = live.fingerprint
    physical_name = publication.physical_name_for(fingerprint)
    candidate_store = publication.candidate_store(fingerprint)
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
    publication.publish_alias(physical_name)
    return physical_name
