from __future__ import annotations

from typing import Protocol


class Embedder(Protocol):
    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, batch_size: int = 16) -> None:
        self._model_name = model_name
        self.batch_size = batch_size
        self._model = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name, device="cpu")
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
        prefixed = [f"passage: {text}" for text in texts]
        vectors = self._load().encode(
            prefixed,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_query(self, text: str) -> list[float]:
        vector = self._load().encode(
            f"query: {text}", normalize_embeddings=True, show_progress_bar=False
        )
        return vector.tolist()
