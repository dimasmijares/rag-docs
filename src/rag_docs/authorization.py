from __future__ import annotations

from rag_docs.contracts import SINGLE_TENANT_SCOPE, Scope

__all__ = ["SingleTenantAuthorization"]


class SingleTenantAuthorization:
    """``AuthorizationPort`` implementation for ``v0.3.0`` (``ADR-RAG-009``,
    ``WRK-TASK-082``): always resolves the single-tenant scope regardless of
    ``principal``. ``v1.5.0`` replaces this with real policy resolution
    (``WRK-TASK-046``) without touching any caller, because callers depend on
    the port's shape, not this implementation."""

    def resolve_scope(self, principal: str | None = None) -> Scope:
        return SINGLE_TENANT_SCOPE
