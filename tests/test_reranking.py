from pathlib import Path

from rag_docs.chunking import chunk_document
from rag_docs.models import DocumentCandidate, ExtractedUnit, SearchHit
from rag_docs.reranking import CrossEncoderReranker


def _hit(tmp_path: Path, text: str, score: float, name: str) -> SearchHit:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    candidate = DocumentCandidate("demo", path, name, path.as_uri(), "hash")
    chunk = chunk_document(candidate, [ExtractedUnit(text)])[0]
    return SearchHit(chunk, score)


def test_rerank_returns_original_order_when_the_model_cannot_be_loaded(
    tmp_path: Path,
) -> None:
    hits = [_hit(tmp_path, "uno", 0.5, "a.txt"), _hit(tmp_path, "dos", 0.4, "b.txt")]
    reranker = CrossEncoderReranker("this-model-does-not-exist/definitely-not")

    result = reranker.rerank("pregunta", hits, top_n=2)

    assert result == hits


def test_rerank_returns_original_hits_unchanged_when_scoring_raises(
    tmp_path: Path,
) -> None:
    hits = [_hit(tmp_path, "uno", 0.5, "a.txt")]
    reranker = CrossEncoderReranker("fake-model")

    class ExplodingModel:
        def predict(self, pairs):
            raise RuntimeError("boom")

    reranker._model = ExplodingModel()

    result = reranker.rerank("pregunta", hits, top_n=1)

    assert result == hits


def test_rerank_reorders_by_score_and_truncates_to_top_n(tmp_path: Path) -> None:
    low = _hit(tmp_path, "poco relevante", 0.9, "low.txt")
    high = _hit(tmp_path, "muy relevante", 0.1, "high.txt")
    reranker = CrossEncoderReranker("fake-model")

    class RecordingModel:
        def predict(self, pairs):
            return [0.1 if pair[1] == "poco relevante" else 0.9 for pair in pairs]

    reranker._model = RecordingModel()

    result = reranker.rerank("pregunta", [low, high], top_n=1)

    assert len(result) == 1
    assert result[0].chunk.relative_path == "high.txt"


def test_rerank_of_empty_hits_never_loads_the_model(tmp_path: Path) -> None:
    reranker = CrossEncoderReranker("this-model-does-not-exist/definitely-not")

    result = reranker.rerank("pregunta", [], top_n=5)

    assert result == []
    assert reranker._model is None
    assert reranker._unavailable is False
