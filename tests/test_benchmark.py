from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_docs.benchmark import (
    RebaselineRequired,
    StageRecorder,
    TimedEmbedder,
    TimedGenerator,
    TimedStore,
    _aggregate_profile,
    compare_reports,
    execute_validation,
    load_benchmark_config,
    select_baseline,
)
from rag_docs.contracts import SINGLE_TENANT_SCOPE
from rag_docs.evaluation import REPORT_SCHEMA_VERSION, report_vector_backend
from tests.fakes import FakeEmbedder, FakeGenerator, FakeVectorStore


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_timed_adapters_keep_stages_separate() -> None:
    recorder = StageRecorder()
    embedder = TimedEmbedder(FakeEmbedder(), recorder)
    store = TimedStore(FakeVectorStore(), recorder)
    generator = TimedGenerator(FakeGenerator("respuesta [1]"), recorder)

    assert embedder.embed_query("pregunta")
    assert store.search([1.0, 0.0, 0.0], 8, None, SINGLE_TENANT_SCOPE) == []
    generator.generate("pregunta", "contexto")

    assert recorder.embedding_ms >= 0
    assert recorder.retrieval_ms >= 0
    assert recorder.generation_ms >= 0
    assert recorder.generation_calls == 1


def test_aggregate_profile_reports_stage_percentiles() -> None:
    retrieval = {
        "eligible": True,
        "recall_at_1": 1.0,
        "recall_at_3": 1.0,
        "recall_at_5": 1.0,
        "recall_at_8": 1.0,
        "reciprocal_rank": 1.0,
        "precision_at_1": 1.0,
        "precision_at_3": 1.0,
        "precision_at_5": 1.0,
        "precision_at_8": 1.0,
    }
    profile = {
        "id": "candidate",
        "baseline_eligible": True,
        "generator_mode": "ollama",
        "generator_model": "qwen2.5:3b",
        "generator_digest": "digest",
        "embedding_model": "embedding",
        "embedding_revision": "revision",
        "retrieval_top_k": 8,
        "context_chunks": 5,
        "min_score": 0.45,
    }
    cases = [
        {
            "passed": True,
            "run_state": "cold" if value == 1.0 else "warm",
            "error": None,
            "retrieval_metrics": retrieval,
            "stages": {
                "embedding_ms": value,
                "retrieval_ms": value,
                "rerank_ms": value,
                "grounding_ms": value,
                "generation_ms": value,
                "total_ms": value * 5,
            },
        }
        for value in (1.0, 3.0)
    ]

    result = _aggregate_profile(profile, cases)

    assert result["score"] == 1.0
    assert (result["vector_backend"], result["vector_search_mode"]) == ("qdrant", "hnsw")
    assert result["performance"]["embedding"]["p50_ms"] == 2.0
    assert result["performance"]["total"]["p95_ms"] == 14.5


def test_lock_uses_only_eligible_development_profiles(tmp_path: Path) -> None:
    config = Path("config/benchmark.yaml").resolve()
    payload = {
        "phase": "development",
        "revision": "abc123",
        "config_sha256": sha256(config),
        "gold_sha256": sha256(Path("evaluation/gold-set.dev.yaml")),
        "corpus_manifest_sha256": sha256(Path("examples/corpus/demo/manifest.sha256")),
        "source_sha256": sha256(Path("config/sources.yaml")),
        "profiles": [
            {
                "profile_id": "qwen-3b-balanced",
                "baseline_eligible": True,
                "score": 0.8,
                "retrieval": {"recall_at_8": 1.0},
                "performance": {"total": {"p95_ms": 100.0}},
            },
            {
                "profile_id": "extractive-fallback-control",
                "baseline_eligible": False,
                "score": 1.0,
                "retrieval": {"recall_at_8": 1.0},
                "performance": {"total": {"p95_ms": 1.0}},
            },
        ],
    }
    report = tmp_path / "dev.json"
    report.write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "lock.json"

    decision = select_baseline(config, report, output)

    assert decision["selected_profile"] == "qwen-3b-balanced"
    assert decision["validation_executions_allowed"] == 1


def test_validation_rejects_tampered_lock_before_loading_split(tmp_path: Path) -> None:
    config = Path("config/benchmark.yaml").resolve()
    decision = {
        "revision": "not-current",
        "selected_profile": "qwen-3b-balanced",
        "config_sha256": "tampered",
        "development_gold_sha256": "tampered",
        "validation_gold_sha256": "tampered",
        "corpus_manifest_sha256": "tampered",
        "source_sha256": "tampered",
    }
    decision_path = tmp_path / "decision.json"
    decision_path.write_text(json.dumps(decision), encoding="utf-8")

    with pytest.raises(RuntimeError, match="lock de decisión no coincide"):
        execute_validation(config, decision_path, tmp_path / "validation.json")


def test_validation_never_overwrites_canonical_result(tmp_path: Path) -> None:
    output = tmp_path / "validation.json"
    output.write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError, match="ya fue ejecutada"):
        execute_validation(
            Path("config/benchmark.yaml"), tmp_path / "missing.json", output
        )


def test_benchmark_config_contains_only_local_3b_profiles() -> None:
    config = load_benchmark_config(Path("config/benchmark.yaml"))

    assert {item["generator_mode"] for item in config["profiles"]} == {
        "ollama",
        "forced_fallback",
    }
    assert {item["generator_model"] for item in config["profiles"]} == {"qwen2.5:3b"}
    assert all(item["embedding_revision"] for item in config["profiles"])


def test_default_corpus_compatibility_manifest_exists() -> None:
    assert Path("evaluation/corpus-compatibility.yaml").is_file()


def _report(
    *,
    corpus_version: str,
    digest: str,
    score: float,
    backend: tuple[str, str] | None = None,
    recall: float | None = None,
    p95_ms: float | None = None,
) -> dict:
    profile: dict = {
        "profile_id": "qwen-3b-balanced",
        "score": score,
        "index_fingerprint": {"digest": digest},
        "retrieval": {"recall_at_8": recall},
        "performance": {"total": {"p95_ms": p95_ms}},
    }
    report: dict = {"corpus_version": corpus_version, "profiles": [profile]}
    if backend is not None:
        report["schema_version"] = REPORT_SCHEMA_VERSION
        profile["vector_backend"], profile["vector_search_mode"] = backend
    return report


def _write(path: Path, report: dict) -> Path:
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def test_compare_reports_computes_delta_for_matching_triplet(tmp_path: Path) -> None:
    previous = tmp_path / "previous.json"
    current = tmp_path / "current.json"
    previous.write_text(
        json.dumps(_report(corpus_version="0.2.0", digest="abc", score=0.5)),
        encoding="utf-8",
    )
    current.write_text(
        json.dumps(_report(corpus_version="0.2.0", digest="abc", score=0.8)),
        encoding="utf-8",
    )

    result = compare_reports(previous, current, profile_id="qwen-3b-balanced")

    assert result["comparable"] is True
    assert result["score_delta"] == pytest.approx(0.3)


def test_compare_reports_requires_explicit_rebaseline_on_fingerprint_change(
    tmp_path: Path,
) -> None:
    previous = tmp_path / "previous.json"
    current = tmp_path / "current.json"
    previous.write_text(
        json.dumps(_report(corpus_version="0.2.0", digest="abc", score=0.5)),
        encoding="utf-8",
    )
    current.write_text(
        json.dumps(_report(corpus_version="0.2.0", digest="xyz", score=0.9)),
        encoding="utf-8",
    )

    with pytest.raises(RebaselineRequired, match="re-baseline"):
        compare_reports(previous, current, profile_id="qwen-3b-balanced")

    result = compare_reports(
        previous, current, profile_id="qwen-3b-balanced", rebaseline=True
    )
    assert result["comparable"] is False
    assert result["score_delta"] is None
    assert result["rebaseline_declared"] is True


def test_report_schema_is_1_1_and_legacy_reports_read_as_qdrant_hnsw() -> None:
    assert REPORT_SCHEMA_VERSION == "1.1"
    assert report_vector_backend({}) == ("qdrant", "hnsw")
    assert report_vector_backend({"schema_version": "1.0"}) == ("qdrant", "hnsw")
    assert report_vector_backend(
        {"schema_version": "1.1"}, {"vector_backend": "fabric_sql", "vector_search_mode": "exact"}
    ) == ("fabric_sql", "exact")
    with pytest.raises(ValueError, match="no declara vector_backend"):
        report_vector_backend({"schema_version": "1.1"}, {})


def test_compare_reports_treats_a_legacy_report_as_qdrant_hnsw(tmp_path: Path) -> None:
    previous = _write(
        tmp_path / "previous.json", _report(corpus_version="0.2.0", digest="abc", score=0.5)
    )
    current = _write(
        tmp_path / "current.json",
        _report(corpus_version="0.2.0", digest="abc", score=0.6, backend=("qdrant", "hnsw")),
    )

    result = compare_reports(previous, current, profile_id="qwen-3b-balanced")

    assert result["comparable"] is True
    assert result["latency_comparable"] is True
    assert result["previous"]["vector_backend"] == "qdrant"


@pytest.mark.parametrize(
    "current_backend", [("fabric_sql", "exact"), ("qdrant", "exact")], ids=["backend", "mode"]
)
def test_compare_reports_requires_rebaseline_across_backends_or_modes(
    tmp_path: Path, current_backend: tuple[str, str]
) -> None:
    previous = _write(
        tmp_path / "previous.json",
        _report(
            corpus_version="0.2.0", digest="abc", score=0.5, backend=("qdrant", "hnsw"),
            recall=0.8, p95_ms=100.0,
        ),
    )
    current = _write(
        tmp_path / "current.json",
        _report(
            corpus_version="0.2.0", digest="abc", score=0.5, backend=current_backend,
            recall=0.9, p95_ms=400.0,
        ),
    )

    with pytest.raises(RebaselineRequired, match="vector_backend/vector_search_mode"):
        compare_reports(previous, current, profile_id="qwen-3b-balanced")

    result = compare_reports(previous, current, profile_id="qwen-3b-balanced", rebaseline=True)

    assert result["comparable"] is False
    assert result["score_delta"] is None
    # Same corpus and fingerprint: recall is what a backend/mode comparison measures.
    assert result["recall_comparable"] is True
    assert result["recall_at_8_delta"] == pytest.approx(0.1)
    # Latency is never comparable outside the full key, and never across backends.
    assert result["latency_comparable"] is False
    assert result["latency_p95_delta_ms"] is None
    if current_backend[0] != "qdrant":
        assert result["latency_note"] == "latencia no comparable entre backends distintos"


def test_compare_reports_reports_latency_delta_under_the_full_key(tmp_path: Path) -> None:
    previous = _write(
        tmp_path / "previous.json",
        _report(
            corpus_version="0.2.0", digest="abc", score=0.5, backend=("qdrant", "hnsw"),
            recall=0.8, p95_ms=100.0,
        ),
    )
    current = _write(
        tmp_path / "current.json",
        _report(
            corpus_version="0.2.0", digest="abc", score=0.5, backend=("qdrant", "hnsw"),
            recall=0.8, p95_ms=120.0,
        ),
    )

    result = compare_reports(previous, current, profile_id="qwen-3b-balanced")

    assert result["latency_p95_delta_ms"] == pytest.approx(20.0)
    assert result["latency_note"] is None
