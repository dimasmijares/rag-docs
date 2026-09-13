from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from rag_docs.contracts.dtos import (
    DocumentCandidate,
    DocumentChunk,
    IndexedDocument,
    SearchHit,
)
from rag_docs.contracts.value_objects import AclFields, IndexFingerprint, Scope

# Ports are Python Protocols over pure DTOs, with no I/O dependency. Each one is
# the seam a v2.5.0 service adapter implements; freezing the shape now is what
# turns that extraction into an adapter instead of a rewrite (ADR-RAG-010).


class EmbeddingPort(Protocol):
    """Future ``embedding-service``. Stateless, batch-oriented, maps to HTTP unchanged."""

    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    @property
    def fingerprint(self) -> IndexFingerprint: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


@dataclass(frozen=True, slots=True)
class GenerationMetrics:
    """Token and latency accounting declared now so streaming does not force a
    signature change after the extraction (ADR-RAG-010)."""

    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


@dataclass(frozen=True, slots=True)
class GenerationDelta:
    text: str
    done: bool
    metrics: GenerationMetrics | None = None


class GenerationPort(Protocol):
    """Future ``model-gateway``. The streaming variant and the accounting are part
    of the frozen contract even though ``WRK-TASK-041`` implements them."""

    @property
    def model_name(self) -> str: ...

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> object: ...

    def generate_stream(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> Iterator[GenerationDelta]: ...


class RetrievalPort(Protocol):
    """Future ``retrieval-service``. Design decision frozen here, not in v2.5.0:
    retrieval receives the question text and a ``Scope`` and embeds the query
    itself, so no vector crosses the network per query and the embedding model
    detail never leaks to ``query-api``."""

    def search(
        self,
        question: str,
        scope: Scope,
        k: int,
        threshold: float | None,
        fingerprint: IndexFingerprint,
    ) -> list[SearchHit]: ...


class AuthorizationPort(Protocol):
    """Future ``authz-service``. In v0.3.0 the implementation returns a
    single-tenant ``Scope``; v1.5.0 replaces it without touching any caller."""

    def resolve_scope(self, principal: str | None) -> Scope: ...


@dataclass(frozen=True, slots=True)
class GroundingVerdict:
    grounded: bool
    errors: tuple[str, ...]


class GroundingPort(Protocol):
    """Future ``context-grounding-service``. Splitting ``QueryService`` into the
    pure pieces behind this port is ``WRK-TASK-090``."""

    def build_context(
        self, question: str, hits: list[SearchHit]
    ) -> tuple[str, list[SearchHit]]: ...

    def validate(
        self,
        answer: object,
        question: str,
        evidence_by_reference: dict[int, str],
    ) -> GroundingVerdict: ...


class DocumentSourcePort(Protocol):
    """Future connector SDK (``WRK-TASK-050``). ``discover`` returns the complete,
    deterministic snapshot: ``ADR-RAG-008`` needs that signal to delete orphans
    safely."""

    @property
    def source_id(self) -> str: ...

    def discover(self) -> list[DocumentCandidate]: ...


class VectorStorePort(Protocol):
    """Infrastructure seam behind ``RetrievalPort`` and the only store protocol
    the monolith consumes (``ADR-RAG-013``). Its ``search`` signature carries the
    authorization scope (``ADR-RAG-009``) and every read/write is checked
    against the bound fingerprint (``RULE-004``)."""

    def ensure_collection(
        self, vector_size: int, fingerprint: IndexFingerprint | None = None
    ) -> None: ...

    def bind_fingerprint(self, fingerprint: IndexFingerprint) -> None: ...

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]: ...

    def delete_document(self, document_id: str) -> None: ...

    def prune_document(self, document_id: str, keep_chunk_ids: set[str]) -> None: ...

    def upsert(
        self, chunks: list[DocumentChunk], vectors: list[list[float]]
    ) -> None: ...

    def search(
        self,
        vector: list[float],
        limit: int,
        score_threshold: float | None,
        scope: Scope,
    ) -> list[SearchHit]: ...

    def update_acl(self, document_id: str, acl: AclFields) -> None: ...

    def scan_chunks(self, scope: Scope) -> list[DocumentChunk]: ...


@runtime_checkable
class IndexPublicationPort(Protocol):
    """Logical alias over one physical index per fingerprint (``RULE-004``,
    ``ADR-RAG-013``). A backend publishes a candidate by repointing the alias
    and keeps the previous physical index for rollback."""

    @property
    def logical_name(self) -> str: ...

    def physical_name_for(self, fingerprint: IndexFingerprint) -> str: ...

    def published_physical_name(self) -> str | None:
        """The physical index the alias currently resolves to — the one built
        for the fingerprint in force — or ``None`` before the first publish."""
        ...

    def candidate_store(self, fingerprint: IndexFingerprint) -> VectorStorePort:
        """A store bound to ``fingerprint``'s physical index but unreachable
        through the alias, to populate and validate a migration candidate."""
        ...

    def publish_alias(self, physical_name: str) -> None: ...

    def rollback_alias(self, previous_physical_name: str) -> None: ...
