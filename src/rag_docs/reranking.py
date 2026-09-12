"""Cross-encoder reranking experiment (``WRK-TASK-038``, ``RFC-001`` gate G2).

Reuses ``sentence-transformers`` (already a dependency for ``embeddings.py``)
instead of adding a new one: ``CrossEncoder`` ships in the same package, so
this stays a configuration change, not a supply-chain addition. The model is
lazy-loaded on first use, mirroring ``SentenceTransformerEmbedder``, so
importing this module never touches the network or the filesystem cache.
"""

from __future__ import annotations

from typing import Protocol

from rag_docs.contracts import SearchHit

RERANK_VERSION = "cross-encoder-v1"


class Reranker(Protocol):
    @property
    def model_name(self) -> str: ...

    def rerank(self, question: str, hits: list[SearchHit], top_n: int) -> list[SearchHit]: ...


class CrossEncoderReranker:
    """Scores each retrieved chunk against the question with a cross-encoder
    and returns the ``top_n`` highest-scoring hits, reordered.

    Fails safe (AC3): if the model cannot be loaded (no network, unknown
    model name) or scoring raises for any reason, ``rerank`` returns the
    original ``hits`` unchanged instead of letting a reranking failure take
    down retrieval — a query must always be answerable from dense/hybrid
    retrieval alone. Once loading has failed once, later calls skip loading
    entirely rather than retrying a doomed download on every query.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None
        self._unavailable = False

    @property
    def model_name(self) -> str:
        return self._model_name

    def _load(self):
        if self._model is None and not self._unavailable:
            try:
                from sentence_transformers import CrossEncoder

                self._model = CrossEncoder(self._model_name, device="cpu")
            except Exception:
                self._unavailable = True
        return self._model

    def rerank(self, question: str, hits: list[SearchHit], top_n: int) -> list[SearchHit]:
        if not hits:
            return hits
        model = self._load()
        if model is None:
            return hits
        try:
            pairs = [(question, hit.chunk.text) for hit in hits]
            scores = model.predict(pairs)
        except Exception:
            return hits
        ranked = sorted(
            zip(hits, scores, strict=True), key=lambda item: float(item[1]), reverse=True
        )
        return [
            SearchHit(chunk=hit.chunk, score=float(score)) for hit, score in ranked[:top_n]
        ]
