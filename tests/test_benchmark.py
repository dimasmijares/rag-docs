from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from rag_docs.benchmark import (
    StageRecorder,
    TimedEmbedder,
    TimedGenerator,
    TimedStore,
    _aggregate_profile,
    execute_validation,
    load_benchmark_config,
    select_baseline,
)
from tests.fakes import FakeEmbedder, FakeGenerator, FakeVectorStore


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_timed_adapters_keep_stages_separate() -> None:
    recorder = StageRecorder()
    embedder = TimedEmbedder(FakeEmbedder(), recorder)
    store = TimedStore(FakeVectorStore(), recorder)
    generator = TimedGenerator(FakeGenerator("respuesta [1]"), recorder)

    assert embedder.embed_query("pregunta")
    assert store.search([1.0, 0.0, 0.0], 8, None) == []
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
                "grounding_ms": value,
                "generation_ms": value,
                "total_ms": value * 4,
            },
        }
        for value in (1.0, 3.0)
    ]

    result = _aggregate_profile(profile, cases)

    assert result["score"] == 1.0
    assert result["performance"]["embedding"]["p50_ms"] == 2.0
    assert result["performance"]["total"]["p95_ms"] == 11.6


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
