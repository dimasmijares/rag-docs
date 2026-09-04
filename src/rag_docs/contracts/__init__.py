"""Internal port and value-object package (``ADR-RAG-010``).

``rag_docs.contracts`` has no dependency on any I/O client (``qdrant_client``,
``sentence_transformers``, ``httpx``, ``fastapi``); ``tests/test_contracts.py``
verifies it. Both today's monolith and tomorrow's v2.5.0 services depend on it,
so the extraction becomes implementing an adapter per port, not a rewrite.

Compatibility policy for every value object and DTO here: fields are additive
only, never renamed, never given new semantics in place.
"""

from __future__ import annotations

from rag_docs.contracts.dtos import (
    AnswerClaim,
    Citation,
    DocumentCandidate,
    DocumentChunk,
    ExtractedUnit,
    IndexedDocument,
    IndexError,
    IndexReport,
    Locator,
    QueryResult,
    RetrievalDiagnostic,
    SearchHit,
    chunk_from_payload,
)
from rag_docs.contracts.errors import AppError, http_status_for
from rag_docs.contracts.ports import (
    AuthorizationPort,
    DocumentSourcePort,
    EmbeddingPort,
    GenerationDelta,
    GenerationMetrics,
    GenerationPort,
    GroundingPort,
    GroundingVerdict,
    RetrievalPort,
    VectorStorePort,
)
from rag_docs.contracts.value_objects import (
    SINGLE_TENANT,
    SINGLE_TENANT_SCOPE,
    CorrelationId,
    ErrorKind,
    IdempotencyKey,
    IndexFingerprint,
    Scope,
)

__all__ = [
    "AnswerClaim",
    "AppError",
    "AuthorizationPort",
    "Citation",
    "CorrelationId",
    "DocumentCandidate",
    "DocumentChunk",
    "DocumentSourcePort",
    "EmbeddingPort",
    "ErrorKind",
    "ExtractedUnit",
    "GenerationDelta",
    "GenerationMetrics",
    "GenerationPort",
    "GroundingPort",
    "GroundingVerdict",
    "IdempotencyKey",
    "IndexError",
    "IndexFingerprint",
    "IndexReport",
    "IndexedDocument",
    "Locator",
    "QueryResult",
    "RetrievalDiagnostic",
    "RetrievalPort",
    "Scope",
    "SINGLE_TENANT",
    "SINGLE_TENANT_SCOPE",
    "SearchHit",
    "VectorStorePort",
    "chunk_from_payload",
    "http_status_for",
]
