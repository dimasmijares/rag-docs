from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from rag_docs.benchmark import profile_embedder
from rag_docs.config import Settings
from rag_docs.container import build_embedder, build_vector_store
from rag_docs.contracts import AppError, ErrorKind, IndexPublicationPort
from rag_docs.embeddings import SentenceTransformerEmbedder
from rag_docs.indexing import build_fingerprint
from rag_docs.vector_store import QdrantVectorStore

ROOT = Path(__file__).resolve().parents[1]


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


def test_embedding_revision_setting_propagates_to_the_app_embedder() -> None:
    embedder = build_embedder(Settings(_env_file=None, embedding_revision="pinned-rev"))

    assert embedder.revision == "pinned-rev"


def test_app_and_benchmark_build_the_same_fingerprint_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Avoid loading the model: only the declared dimension feeds the fingerprint.
    monkeypatch.setattr(SentenceTransformerEmbedder, "dimension", property(lambda self: 384))
    monkeypatch.delenv("RAG_DOCS_EMBEDDING_REVISION", raising=False)
    config = yaml.safe_load((ROOT / "config/benchmark.yaml").read_text(encoding="utf-8"))
    compatibility = yaml.safe_load(
        (ROOT / "evaluation/corpus-compatibility.yaml").read_text(encoding="utf-8")
    )
    settings = Settings(
        _env_file=None,
        chunk_tokens=config["chunk_tokens"],
        chunk_overlap=config["chunk_overlap"],
        embedding_batch_size=config["embedding_batch_size"],
    )
    app_digest = build_fingerprint(
        build_embedder(settings), settings.chunk_tokens, settings.chunk_overlap
    ).digest()

    profiles = [
        profile
        for profile in config["profiles"]
        if profile["embedding_model"] == settings.embedding_model
    ]
    assert profiles
    for profile in profiles:
        benchmark_digest = build_fingerprint(
            profile_embedder(profile, config), config["chunk_tokens"], config["chunk_overlap"]
        ).digest()
        assert benchmark_digest == app_digest
    assert app_digest in compatibility["compatible_fingerprint_digests"]
