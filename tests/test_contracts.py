from __future__ import annotations

import ast
from pathlib import Path

import pytest

from rag_docs import contracts
from rag_docs.contracts import (
    AnswerClaim,
    AppError,
    AuthorizationPort,
    Citation,
    CorrelationId,
    DocumentCandidate,
    DocumentChunk,
    DocumentSourcePort,
    EmbeddingPort,
    ErrorKind,
    GenerationPort,
    GroundingPort,
    IdempotencyKey,
    IndexError,
    IndexFingerprint,
    IndexReport,
    QueryResult,
    RetrievalDiagnostic,
    RetrievalPort,
    Scope,
    SearchHit,
    VectorStorePort,
    http_status_for,
)

FORBIDDEN_IMPORTS = {"qdrant_client", "sentence_transformers", "httpx", "fastapi"}
CONTRACTS_DIR = Path(contracts.__file__).parent


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def test_contracts_package_has_no_io_dependency() -> None:
    for path in CONTRACTS_DIR.glob("*.py"):
        modules = _imported_modules(path.read_text(encoding="utf-8"))
        offending = modules.intersection(FORBIDDEN_IMPORTS)
        assert not offending, f"{path.name} importa un cliente de I/O: {offending}"


def test_ports_exist_as_protocols() -> None:
    for port in (
        EmbeddingPort,
        GenerationPort,
        RetrievalPort,
        AuthorizationPort,
        GroundingPort,
        DocumentSourcePort,
        VectorStorePort,
    ):
        assert getattr(port, "_is_protocol", False)


def test_value_objects_are_frozen() -> None:
    fingerprint = IndexFingerprint(
        extractor="pdf-v1",
        chunker="tokens-v1",
        chunk_tokens=500,
        chunk_overlap=75,
        embedding_model="intfloat/multilingual-e5-small",
        embedding_revision=None,
        dimension=384,
        normalize=True,
        query_prefix="query: ",
        passage_prefix="passage: ",
    )
    with pytest.raises(AttributeError):
        fingerprint.dimension = 128  # type: ignore[misc]
    assert len(fingerprint.digest()) == 16

    scope = Scope(tenant="acme")
    with pytest.raises(AttributeError):
        scope.tenant = "other"  # type: ignore[misc]

    assert str(CorrelationId.new()) != ""
    assert IdempotencyKey.for_payload("a", "b") == IdempotencyKey.for_payload("a", "b")


def test_error_kind_maps_to_a_distinct_http_status_without_leaking_text() -> None:
    seen_statuses: set[int] = set()
    for kind in ErrorKind:
        status = http_status_for(kind)
        assert 400 <= status < 600
        seen_statuses.add(status)
    assert len(seen_statuses) == len(list(ErrorKind))

    error = AppError(ErrorKind.NOT_FOUND, "recurso no encontrado")
    assert error.kind is ErrorKind.NOT_FOUND
    assert http_status_for(error.kind) == 404


def test_domain_dtos_are_hosted_in_contracts() -> None:
    # The DTOs ADR-RAG-010 names as crossing a boundary live in this package;
    # rag_docs.models/query/indexing re-export them for existing call sites.
    assert DocumentChunk.__module__.startswith("rag_docs.contracts")
    assert SearchHit.__module__.startswith("rag_docs.contracts")
    assert Citation.__module__.startswith("rag_docs.contracts")
    assert AnswerClaim.__module__.startswith("rag_docs.contracts")
    assert RetrievalDiagnostic.__module__.startswith("rag_docs.contracts")
    assert QueryResult.__module__.startswith("rag_docs.contracts")
    assert IndexReport.__module__.startswith("rag_docs.contracts")
    assert IndexError.__module__.startswith("rag_docs.contracts")
    assert DocumentCandidate.__module__.startswith("rag_docs.contracts")
