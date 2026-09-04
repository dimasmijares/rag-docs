from __future__ import annotations

from rag_docs.config import Settings, SourceDefinition, load_sources
from rag_docs.embeddings import SentenceTransformerEmbedder
from rag_docs.generator_profiles import GeneratorProfile, GeneratorProfileRegistry
from rag_docs.indexing import IndexingService
from rag_docs.query import QueryService
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore


class ApplicationContainer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.source_definitions: list[SourceDefinition] = load_sources(
            self.settings.sources_file
        )
        self.sources = [LocalFolderSource(definition) for definition in self.source_definitions]
        self.embedder = SentenceTransformerEmbedder(
            self.settings.embedding_model, self.settings.embedding_batch_size
        )
        self.store = QdrantVectorStore(
            self.settings.qdrant_url, self.settings.qdrant_collection
        )
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
