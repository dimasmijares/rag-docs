from __future__ import annotations

from collections.abc import Callable

from rag_docs.config import Settings, SourceDefinition, load_sources
from rag_docs.contracts import AppError, ErrorKind, VectorStorePort
from rag_docs.embeddings import SentenceTransformerEmbedder
from rag_docs.generator_profiles import GeneratorProfile, GeneratorProfileRegistry
from rag_docs.indexing import IndexingService
from rag_docs.query import QueryService
from rag_docs.reranking import CrossEncoderReranker
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore


def build_embedder(settings: Settings) -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(
        settings.embedding_model,
        settings.embedding_batch_size,
        settings.embedding_revision,
    )


def _qdrant_store(settings: Settings) -> VectorStorePort:
    return QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection)


def _fabric_sql_store(settings: Settings) -> VectorStorePort:
    # Imported lazily: the Fabric backend is optional (WRK-TASK-100).
    from rag_docs.fabric_sql_store import build_fabric_sql_store

    return build_fabric_sql_store(settings)


#: One factory per ``Settings.vector_backend`` value (ADR-RAG-013). The rest of
#: the container only sees ``VectorStorePort``.
VECTOR_STORE_FACTORIES: dict[str, Callable[[Settings], VectorStorePort]] = {
    "qdrant": _qdrant_store,
    "fabric_sql": _fabric_sql_store,
}


def build_vector_store(settings: Settings) -> VectorStorePort:
    factory = VECTOR_STORE_FACTORIES.get(settings.vector_backend)
    if factory is None:
        raise AppError(
            ErrorKind.VALIDATION,
            f"Backend vectorial no soportado: '{settings.vector_backend}'.",
        )
    return factory(settings)


class ApplicationContainer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.source_definitions: list[SourceDefinition] = load_sources(
            self.settings.sources_file
        )
        self.sources = [LocalFolderSource(definition) for definition in self.source_definitions]
        self.embedder = build_embedder(self.settings)
        self.store = build_vector_store(self.settings)
        profiles = [
            GeneratorProfile(
                id="local",
                label="Local (este portátil)",
                endpoint=self.settings.ollama_local_url or self.settings.ollama_url,
                model=self.settings.ollama_local_model or self.settings.ollama_model,
            )
        ]
        if self.settings.ollama_remote_url:
            profiles.append(
                GeneratorProfile(
                    id="remote",
                    label="Remoto (PC personal)",
                    endpoint=self.settings.ollama_remote_url,
                    model=self.settings.ollama_remote_model or self.settings.ollama_model,
                )
            )
        self.generator_registry = GeneratorProfileRegistry(
            profiles,
            self.settings.ollama_active_profile,
            timeout=self.settings.ollama_timeout,
            temperature=self.settings.ollama_temperature,
            seed=self.settings.ollama_seed,
        )
        self.generator = self.generator_registry.active_generator
        self.indexing = IndexingService(
            self.sources,
            self.embedder,
            self.store,
            self.settings.chunk_tokens,
            self.settings.chunk_overlap,
        )
        # Bind the fingerprint eagerly, not only when indexing runs: a
        # query-only process must reject a mismatched index just as
        # explicitly as a write would (RULE-004).
        self.store.bind_fingerprint(self.indexing.fingerprint)
        self.query = QueryService(
            self.embedder,
            self.store,
            self.generator,
            self.settings.retrieval_top_k,
            self.settings.context_chunks,
            self.settings.min_score,
            reranker=CrossEncoderReranker(self.settings.reranker_model)
            if self.settings.reranker_model
            else None,
            rerank_top_n=self.settings.rerank_top_n,
        )

    def generator_profiles_state(self) -> dict:
        return self.generator_registry.state()

    def check_generator_profile(self, profile_id: str) -> dict:
        return self.generator_registry.check(profile_id)

    def activate_generator_profile(
        self,
        profile_id: str,
        model_name: str | None = None,
    ) -> dict:
        result = self.generator_registry.activate(profile_id, model_name)
        self.generator = self.generator_registry.active_generator
        self.query.generator = self.generator
        return result
