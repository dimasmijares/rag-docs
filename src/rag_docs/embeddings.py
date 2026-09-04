from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    @property
    def revision(self) -> str | None: ...

    @property
    def query_prefix(self) -> str: ...

    @property
    def passage_prefix(self) -> str: ...

    @property
    def normalize(self) -> bool: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    #: e5-family convention. Previously hard-coded inline in ``embed_documents``
    #: / ``embed_query`` where ``IndexFingerprint`` could not observe it
    #: (``ADR-RAG-010``); now exposed so the fingerprint covers it.
    passage_prefix = "passage: "
    query_prefix = "query: "
    normalize = True

    def __init__(
        self, model_name: str, batch_size: int = 16, revision: str | None = None
    ) -> None:
        self._model_name = model_name
        self.batch_size = batch_size
        self.revision = revision
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self._model_name, device="cpu", revision=self.revision
            )
        return self._model

    @property
    def dimension(self) -> int:
        dimension = self._load().get_sentence_embedding_dimension()
        if dimension is None:
            raise RuntimeError("El modelo de embeddings no publica su dimensión")
        return int(dimension)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        prefixed = [f"{self.passage_prefix}{text}" for text in texts]
        vectors = self._load().encode(
            prefixed,
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._load().encode(
            f"{self.query_prefix}{text}",
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
        )
        return vector.tolist()
