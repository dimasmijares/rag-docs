from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from enum import StrEnum

# Value objects shared across every internal port. They carry no behaviour beyond
# derivation of their own identity and never import an I/O client (see
# ``tests/test_contracts.py``). Compatibility policy for every DTO and value object
# in this package: fields are additive only, never renamed and never given a new
# meaning in place. A breaking change is a new name, not an edit.


@dataclass(frozen=True, slots=True)
class IndexFingerprint:
    """Everything that makes two collections incomparable if it differs.

    ``RULE-004`` requires this to be observable from outside any adapter: the e5
    ``passage:`` / ``query:`` prefixes and the chunker parameters are inputs here,
    not hidden constants inside ``SentenceTransformerEmbedder`` or ``Settings``.
    """

    extractor: str
    chunker: str
    chunk_tokens: int
    chunk_overlap: int
    embedding_model: str
    embedding_revision: str | None
    dimension: int
    normalize: bool
    query_prefix: str
    passage_prefix: str

    def digest(self) -> str:
        parts = (
            self.extractor,
            self.chunker,
            str(self.chunk_tokens),
            str(self.chunk_overlap),
            self.embedding_model,
            self.embedding_revision or "",
            str(self.dimension),
            "1" if self.normalize else "0",
            self.query_prefix,
            self.passage_prefix,
        )
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class Scope:
    """Authorization envelope resolved before retrieval (``ADR-RAG-009``).

    In v0.3.0 the resolver returns a single-tenant scope; the shape is frozen now
    so v1.5.0 can swap the implementation without touching a single caller.
    """

    tenant: str
    subjects: frozenset[str] = frozenset()
    classifications: frozenset[str] = frozenset()
    version: int = 1


SINGLE_TENANT = "default"
SINGLE_TENANT_SCOPE = Scope(tenant=SINGLE_TENANT)


class ErrorKind(StrEnum):
    """Closed taxonomy that maps to transport codes at the edge, never leaking
    an exception string to the client the way ``api.py`` does today."""

    VALIDATION = "validation"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"
    TIMEOUT = "timeout"
    INVALID_MODEL_OUTPUT = "invalid_model_output"


@dataclass(frozen=True, slots=True)
class CorrelationId:
    value: str

    @staticmethod
    def new() -> CorrelationId:
        return CorrelationId(uuid.uuid4().hex)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    value: str

    @staticmethod
    def for_payload(*parts: str) -> IdempotencyKey:
        digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()
        return IdempotencyKey(digest)

    def __str__(self) -> str:
        return self.value
