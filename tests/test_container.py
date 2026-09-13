import pytest
from pydantic import ValidationError

from rag_docs.config import Settings
from rag_docs.container import build_vector_store
from rag_docs.contracts import AppError, ErrorKind, IndexPublicationPort
from rag_docs.vector_store import QdrantVectorStore


def test_vector_backend_defaults_to_qdrant() -> None:
    assert Settings().vector_backend == "qdrant"


def test_factory_builds_the_qdrant_store_for_the_default_backend() -> None:
    store = build_vector_store(Settings(qdrant_url=":memory:", qdrant_collection="logical"))

    assert isinstance(store, QdrantVectorStore)
    assert isinstance(store, IndexPublicationPort)
    assert store.logical_name == "logical"


def test_settings_reject_an_unknown_vector_backend() -> None:
    with pytest.raises(ValidationError):
        Settings(vector_backend="unknown")  # type: ignore[arg-type]


def test_factory_fails_explicitly_for_a_backend_without_implementation() -> None:
    settings = Settings.model_construct(vector_backend="unknown")

    with pytest.raises(AppError) as excinfo:
        build_vector_store(settings)

    assert excinfo.value.kind is ErrorKind.VALIDATION
