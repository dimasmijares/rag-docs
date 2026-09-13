from __future__ import annotations

import importlib
import os
import uuid
from collections.abc import Callable
from typing import Any

import pytest

from rag_docs.contracts import IndexFingerprint

#: Opt-in hook for running the vector store contract suite against a live backend
#: (WRK-TASK-096). Value: ``package.module:factory``, where ``factory(logical_name)``
#: returns a store implementing ``VectorStorePort`` and ``IndexPublicationPort``.
#: Unset in ``scripts/verify.ps1`` and CI, so the default gate needs no infrastructure.
LIVE_FACTORY_ENV = "RAG_DOCS_CONTRACT_LIVE_FACTORY"


def _qdrant_memory(logical_name: str) -> Any:
    from rag_docs.vector_store import QdrantVectorStore

    return QdrantVectorStore(":memory:", logical_name)


def _load_live_factory(spec: str) -> Callable[[str], Any]:
    module_name, _, attribute = spec.partition(":")
    if not module_name or not attribute:
        raise pytest.UsageError(f"{LIVE_FACTORY_ENV} debe tener la forma 'modulo:factoria'.")
    return getattr(importlib.import_module(module_name), attribute)


def _contract_backends() -> list[Any]:
    backends = [pytest.param(_qdrant_memory, id="qdrant-memory")]
    live = os.environ.get(LIVE_FACTORY_ENV)
    if live:
        backends.append(pytest.param(live, id="live", marks=pytest.mark.live))
    return backends


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", f"live: contract run against the backend named by {LIVE_FACTORY_ENV}"
    )


@pytest.fixture(params=_contract_backends())
def contract_store(request: pytest.FixtureRequest) -> Any:
    """A fresh, empty store per test under a unique logical name, so a live
    backend never sees another test's alias or physical indexes."""
    factory = request.param
    if isinstance(factory, str):
        factory = _load_live_factory(factory)
    return factory(f"contract_{uuid.uuid4().hex[:12]}")


@pytest.fixture
def make_fingerprint() -> Callable[..., IndexFingerprint]:
    def build(**overrides: object) -> IndexFingerprint:
        values: dict[str, object] = dict(
            extractor="extractors-v1",
            chunker="whitespace-window-v1",
            chunk_tokens=500,
            chunk_overlap=75,
            embedding_model="intfloat/multilingual-e5-small",
            embedding_revision="contract-revision",
            dimension=3,
            normalize=True,
            query_prefix="query: ",
            passage_prefix="passage: ",
            payload_schema_version=2,
        )
        values.update(overrides)
        return IndexFingerprint(**values)  # type: ignore[arg-type]

    return build
