"""Backward-compatible re-export shim.

These DTOs now live in ``rag_docs.contracts`` (``ADR-RAG-010``, ``WRK-TASK-083``):
that is the package with no I/O dependency that both the monolith and the
future v2.5.0 services import. Import from ``rag_docs.contracts`` in new code;
this module stays so existing call sites do not all need to change in the same
diff.
"""

from __future__ import annotations

from rag_docs.contracts.dtos import (
    DocumentCandidate,
    DocumentChunk,
    ExtractedUnit,
    IndexedDocument,
    Locator,
    SearchHit,
    chunk_from_payload,
)

__all__ = [
    "DocumentCandidate",
    "DocumentChunk",
    "ExtractedUnit",
    "IndexedDocument",
    "Locator",
    "SearchHit",
    "chunk_from_payload",
]
