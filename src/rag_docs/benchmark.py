from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

import httpx
import psutil
import yaml

from rag_docs.config import SourceDefinition, load_sources
from rag_docs.container import VECTOR_SEARCH_MODES
from rag_docs.contracts import IndexFingerprint
from rag_docs.embeddings import Embedder, SentenceTransformerEmbedder
from rag_docs.evaluation import (
    DEFAULT_CORPUS_COMPATIBILITY,
    REPORT_SCHEMA_VERSION,
    _percentile,
    aggregate_retrieval_metrics,
    evaluate_case,
    load_corpus_compatibility,
    report_vector_backend,
    verify_fingerprint_compatibility,
    verify_gold_corpus_version,
)
from rag_docs.generation import (
    GeneratedResponse,
    Generator,
    GeneratorCapabilities,
    GeneratorHealth,
    InvalidGeneratedResponse,
    OllamaGenerator,
)
from rag_docs.indexing import IndexingService
from rag_docs.lexical import FUSION_VERSION, LEXICAL_VERSION
from rag_docs.query import QueryService
from rag_docs.reranking import RERANK_VERSION, CrossEncoderReranker
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore, VectorStore

#: Schema of config/benchmark.yaml and the decision lock. Reports use
#: ``REPORT_SCHEMA_VERSION`` (1.1 since WRK-TASK-098).
SCHEMA_VERSION = "1.0"
#: Default backend of a profile: an in-memory Qdrant collection with its default HNSW index
#: configuration. A profile may declare ``vector_backend: fabric_sql`` (WRK-TASK-102); its
#: search mode is then the backend's (``container.VECTOR_SEARCH_MODES``).
BENCHMARK_VECTOR_BACKEND = "qdrant"
DEFAULT_CONFIG = Path("config/benchmark.yaml")
DEFAULT_DEV_REPORT = Path("evaluation/benchmarks/wrk-task-027/dev-results.json")
DEFAULT_DECISION = Path("evaluation/benchmarks/wrk-task-027/decision-lock.json")
DEFAULT_VALIDATION_REPORT = Path(
    "evaluation/benchmarks/wrk-task-027/validation-results.json"
)


class RebaselineRequired(RuntimeError):
    """Raised by ``compare_reports`` when two reports do not share the same
    comparability key (``corpus_version``, ``IndexFingerprint`` digest,
    ``vector_backend``, ``vector_search_mode``) and no explicit re-baseline was
    declared (``ADR-RAG-011``, ``ADR-RAG-013``)."""


def _fingerprint_payload(fingerprint: IndexFingerprint) -> dict[str, Any]:
    return {**asdict(fingerprint), "digest": fingerprint.digest()}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_manifest(path: Path) -> None:
    root = path.parent
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        expected, relative = line.split("  ", maxsplit=1)
        candidate = (root / relative).resolve()
        if candidate.parent != root and root not in candidate.parents:
            raise ValueError("El manifiesto contiene una ruta fuera del corpus")
        if not candidate.is_file() or _sha256(candidate) != expected:
            raise RuntimeError(f"El corpus no coincide con el manifiesto: {relative}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _revision() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
    ).strip()


def _repo_root() -> Path:
    value = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True, encoding="utf-8"
    ).strip()
    return Path(value).resolve()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def load_benchmark_config(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    required = {
        "schema_version",
        "benchmark_id",
        "seed",
        "embedding_batch_size",
        "chunk_tokens",
        "chunk_overlap",
        "ollama_timeout",
        "ollama_temperature",
        "source_file",
        "development_gold",
        "validation_gold",
        "corpus_manifest",
        "selection",
        "profiles",
    }
    missing = required.difference(raw)
    if missing:
        raise ValueError(f"Faltan campos de configuración: {', '.join(sorted(missing))}")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version no soportada: {raw['schema_version']}")
    profiles = list(raw["profiles"])
    ids = [str(item["id"]) for item in profiles]
    if len(ids) != len(set(ids)) or not profiles:
        raise ValueError("profiles debe contener IDs únicos")
    modes = {str(item["generator_mode"]) for item in profiles}
    if not modes.issubset({"ollama", "forced_fallback"}):
        raise ValueError(f"generator_mode no soportado: {sorted(modes)}")
    if not any(bool(item.get("baseline_eligible")) for item in profiles):
        raise ValueError("Debe existir al menos un perfil elegible como baseline")
    backends = {_profile_backend(item) for item in profiles}
    if not backends.issubset(VECTOR_SEARCH_MODES):
        raise ValueError(f"vector_backend no soportado: {sorted(backends)}")
    return raw


def _profile_backend(profile: dict[str, Any]) -> str:
    return str(profile.get("vector_backend", BENCHMARK_VECTOR_BACKEND))


def _benchmark_store(profile: dict[str, Any]) -> Any:
    """Empty store for one profile. Fabric SQL profiles use a logical index of their own that is
    dropped before indexing, so a rerun never measures leftovers (WRK-TASK-102)."""
    logical_name = f"benchmark_{profile['id']}".replace("-", "_")
    if _profile_backend(profile) == "qdrant":
        return QdrantVectorStore(":memory:", logical_name)
    from rag_docs.config import Settings
    from rag_docs.fabric_sql_store import build_fabric_sql_store

    store = build_fabric_sql_store(Settings(), logical_name)
    store.drop_logical_index()
    return store


@dataclass(slots=True)
class StageRecorder:
    embedding_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    generation_ms: float = 0.0
    generation_calls: int = 0


class TimedEmbedder:
    def __init__(self, wrapped: Embedder, recorder: StageRecorder) -> None:
        self.wrapped = wrapped
        self.recorder = recorder

    @property
    def dimension(self) -> int:
        return self.wrapped.dimension

    @property
    def model_name(self) -> str:
        return self.wrapped.model_name

    @property
    def revision(self) -> str | None:
        return self.wrapped.revision

    @property
    def query_prefix(self) -> str:
        return self.wrapped.query_prefix

    @property
    def passage_prefix(self) -> str:
        return self.wrapped.passage_prefix

    @property
    def normalize(self) -> bool:
        return self.wrapped.normalize

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.wrapped.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        started = perf_counter()
        try:
            return self.wrapped.embed_query(text)
        finally:
            self.recorder.embedding_ms += (perf_counter() - started) * 1000


class TimedStore:
    def __init__(self, wrapped: VectorStore, recorder: StageRecorder) -> None:
        self.wrapped = wrapped
        self.recorder = recorder

    def ensure_collection(self, vector_size: int, fingerprint=None) -> None:
        self.wrapped.ensure_collection(vector_size, fingerprint)

    def list_documents(self, source_ids: set[str]):
        return self.wrapped.list_documents(source_ids)

    def delete_document(self, document_id: str) -> None:
        self.wrapped.delete_document(document_id)

    def prune_document(self, document_id: str, keep_chunk_ids: set[str]) -> None:
        self.wrapped.prune_document(document_id, keep_chunk_ids)

    def upsert(self, chunks, vectors) -> None:
        self.wrapped.upsert(chunks, vectors)

    def search(self, vector: list[float], limit: int, score_threshold: float | None, scope):
        started = perf_counter()
        try:
            return self.wrapped.search(vector, limit, score_threshold, scope)
        finally:
            self.recorder.retrieval_ms += (perf_counter() - started) * 1000

    def scan_chunks(self, scope):
        started = perf_counter()
        try:
            return self.wrapped.scan_chunks(scope)
        finally:
            self.recorder.retrieval_ms += (perf_counter() - started) * 1000


class TimedReranker:
    def __init__(self, wrapped, recorder: StageRecorder) -> None:
        self.wrapped = wrapped
        self.recorder = recorder

    @property
    def model_name(self) -> str:
        return self.wrapped.model_name

    def rerank(self, question, hits, top_n):
        started = perf_counter()
        try:
            return self.wrapped.rerank(question, hits, top_n)
        finally:
            self.recorder.rerank_ms += (perf_counter() - started) * 1000


class TimedGenerator:
    def __init__(self, wrapped: Generator, recorder: StageRecorder) -> None:
        self.wrapped = wrapped
        self.recorder = recorder

    @property
    def model_name(self) -> str:
        return self.wrapped.model_name

    @property
    def capabilities(self) -> GeneratorCapabilities:
        return self.wrapped.capabilities

    def health(self) -> GeneratorHealth:
        return self.wrapped.health()

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> GeneratedResponse:
        started = perf_counter()
        self.recorder.generation_calls += 1
        try:
            return self.wrapped.generate(
                question, context, validation_feedback=validation_feedback
            )
        finally:
            self.recorder.generation_ms += (perf_counter() - started) * 1000


class ForcedFallbackGenerator:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(True, False, False)

    def health(self) -> GeneratorHealth:
        return GeneratorHealth(True, "local-control", self.model_name, (self.model_name,))

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> GeneratedResponse:
        raise InvalidGeneratedResponse("fallback forzado por el benchmark")


class MemorySampler:
    def __init__(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.process_peak = self.process.memory_info().rss
        self.host_peak = psutil.virtual_memory().used
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, daemon=True)

    def _sample(self) -> None:
        while not self._stop.wait(0.02):
            self.process_peak = max(self.process_peak, self.process.memory_info().rss)
            self.host_peak = max(self.host_peak, psutil.virtual_memory().used)

    def __enter__(self) -> MemorySampler:
        self._thread.start()
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop.set()
        self._thread.join()
        self._sample_once()

    def _sample_once(self) -> None:
        self.process_peak = max(self.process_peak, self.process.memory_info().rss)
        self.host_peak = max(self.host_peak, psutil.virtual_memory().used)


def _hardware_summary() -> dict[str, Any]:
    memory_gib = psutil.virtual_memory().total / (1024**3)
    return {
        "os_family": platform.system(),
        "architecture": platform.machine(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "memory_gib_bucket": int(memory_gib // 4 * 4),
        "embedding_device": "cpu",
    }


def _ollama_metadata(base_url: str, model_name: str) -> dict[str, Any]:
    response = httpx.get(f"{base_url}/api/tags", timeout=10)
    response.raise_for_status()
    model = next(
        (item for item in response.json().get("models", []) if item.get("name") == model_name),
        None,
    )
    if model is None:
        raise RuntimeError(f"El modelo requerido no está instalado: {model_name}")
    details = model.get("details") or {}
    return {
        "name": model_name,
        "digest": model.get("digest"),
        "parameter_size": details.get("parameter_size"),
        "quantization": details.get("quantization_level"),
    }


def _unload_ollama(base_url: str, model_name: str) -> None:
    response = httpx.post(
        f"{base_url}/api/generate",
        json={"model": model_name, "prompt": "", "keep_alive": 0, "stream": False},
        timeout=30,
    )
    response.raise_for_status()


def _model_memory(base_url: str, model_name: str) -> dict[str, Any]:
    try:
        response = httpx.get(f"{base_url}/api/ps", timeout=10)
        response.raise_for_status()
        model = next(
            (
                item
                for item in response.json().get("models", [])
                if item.get("name") == model_name
            ),
            None,
        )
        if model is None:
            return {"resident_mb": None, "vram_mb": None}
        return {
            "resident_mb": round(float(model.get("size", 0)) / (1024**2), 2),
            "vram_mb": round(float(model.get("size_vram", 0)) / (1024**2), 2),
        }
    except (httpx.HTTPError, TypeError, ValueError):
        return {"resident_mb": None, "vram_mb": None}


def _public_case(result: dict[str, Any], stages: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": result["id"],
        "run_state": stages.pop("run_state"),
        "passed": result["passed"],
        "status_ok": result["status_ok"],
        "retrieval_ok": result["retrieval_ok"],
        "facts_ok": result["facts_ok"],
        "language_ok": result["language_ok"],
        "citations_ok": result["citations_ok"],
        "generation_mode": result["generation_mode"],
        "failure_stage": result["failure_stage"],
        "retrieval_metrics": result["retrieval_metrics"],
        "stages": stages,
        "error": result.get("api_error"),
    }


def _stage_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    names = (
        "embedding_ms",
        "retrieval_ms",
        "rerank_ms",
        "grounding_ms",
        "generation_ms",
        "total_ms",
    )
    summary: dict[str, Any] = {}
    for name in names:
        values = [float(item["stages"][name]) for item in cases]
        summary[name.removesuffix("_ms")] = {
            "p50_ms": round(_percentile(values, 0.5), 2),
            "p95_ms": round(_percentile(values, 0.95), 2),
            "min_ms": round(min(values), 2) if values else 0.0,
            "max_ms": round(max(values), 2) if values else 0.0,
        }
    return summary


def _aggregate_profile(profile: dict[str, Any], cases: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(bool(item["passed"]) for item in cases)
    retrieval_input = [
        {"retrieval_metrics": item["retrieval_metrics"]} for item in cases
    ]
    retrieval_strategy = profile.get("retrieval_strategy", "dense")
    reranker_model = profile.get("reranker_model")
    return {
        "profile_id": profile["id"],
        "vector_backend": _profile_backend(profile),
        "vector_search_mode": VECTOR_SEARCH_MODES[_profile_backend(profile)],
        "baseline_eligible": bool(profile.get("baseline_eligible")),
        "retrieval_strategy": retrieval_strategy,
        "retrieval_strategy_version": (
            f"{LEXICAL_VERSION}+{FUSION_VERSION}" if retrieval_strategy == "hybrid" else "dense"
        ),
        "reranker_model": reranker_model,
        "reranker_version": RERANK_VERSION if reranker_model else None,
        "rerank_top_n": profile.get("rerank_top_n") if reranker_model else None,
        "effective_config": {
            key: profile[key]
            for key in (
                "generator_mode",
                "generator_model",
                "generator_digest",
                "embedding_model",
                "embedding_revision",
                "retrieval_top_k",
                "context_chunks",
                "min_score",
            )
        },
        "passed": passed,
        "total": len(cases),
        "score": passed / len(cases) if cases else 0.0,
        "retrieval": aggregate_retrieval_metrics(retrieval_input),
        "performance": _stage_summary(cases),
        "performance_by_state": {
            state: _stage_summary([item for item in cases if item["run_state"] == state])
            for state in ("cold", "warm")
        },
        "errors": {
            code: sum(item["error"] == code for item in cases)
            for code in sorted({item["error"] for item in cases if item["error"]})
        },
        "cases": cases,
    }


def profile_embedder(
    profile: dict[str, Any], config: dict[str, Any]
) -> SentenceTransformerEmbedder:
    """The embedder a benchmark profile indexes and queries with. Its revision
    is always the pinned one, like the app's ``Settings.embedding_revision``,
    so both build the same fingerprint digest (WRK-TASK-095)."""
    return SentenceTransformerEmbedder(
        str(profile["embedding_model"]),
        int(config["embedding_batch_size"]),
        str(profile["embedding_revision"]),
    )


def _build_services(
    profile: dict[str, Any],
    config: dict[str, Any],
    source_definitions: list[SourceDefinition],
    ollama_url: str,
) -> tuple[QueryService, StageRecorder, float, IndexFingerprint]:
    index_embedder = profile_embedder(profile, config)
    store = _benchmark_store(profile)
    sources = [LocalFolderSource(item) for item in source_definitions]
    started = perf_counter()
    indexing_service = IndexingService(
        sources,
        index_embedder,
        store,
        int(config["chunk_tokens"]),
        int(config["chunk_overlap"]),
    )
    index_report = indexing_service.index()
    fingerprint = indexing_service.fingerprint
    indexing_ms = (perf_counter() - started) * 1000
    if index_report.errors:
        raise RuntimeError(f"La indexación falló en {len(index_report.errors)} documento(s)")
    recorder = StageRecorder()
    query_embedder = TimedEmbedder(profile_embedder(profile, config), recorder)
    if profile["generator_mode"] == "forced_fallback":
        raw_generator: Generator = ForcedFallbackGenerator(str(profile["generator_model"]))
    else:
        raw_generator = OllamaGenerator(
            ollama_url,
            str(profile["generator_model"]),
            timeout=float(config["ollama_timeout"]),
            temperature=float(config["ollama_temperature"]),
            seed=int(config["seed"]),
        )
    service = QueryService(
        query_embedder,
        TimedStore(store, recorder),
        TimedGenerator(raw_generator, recorder),
        int(profile["retrieval_top_k"]),
        int(profile["context_chunks"]),
        float(profile["min_score"]),
        "extractive_fallback"
        if profile["generator_mode"] == "forced_fallback"
        else "llm",
        retrieval_strategy=profile.get("retrieval_strategy", "dense"),
        reranker=TimedReranker(CrossEncoderReranker(str(profile["reranker_model"])), recorder)
        if profile.get("reranker_model")
        else None,
        rerank_top_n=profile.get("rerank_top_n"),
    )
    return service, recorder, indexing_ms, fingerprint


def _run_profile(
    profile: dict[str, Any],
    config: dict[str, Any],
    gold: dict[str, Any],
    source_definitions: list[SourceDefinition],
    _root: Path,
    ollama_url: str,
    compatibility: dict[str, Any],
) -> dict[str, Any]:
    if profile["generator_mode"] == "ollama":
        _unload_ollama(ollama_url, str(profile["generator_model"]))
    service, recorder, indexing_ms, fingerprint = _build_services(
        profile, config, source_definitions, ollama_url
    )
    verify_fingerprint_compatibility(compatibility, fingerprint.digest())
    cases: list[dict[str, Any]] = []
    for index, case in enumerate(gold["cases"]):
        recorder.embedding_ms = 0.0
        recorder.retrieval_ms = 0.0
        recorder.rerank_ms = 0.0
        recorder.generation_ms = 0.0
        recorder.generation_calls = 0
        started = perf_counter()
        with MemorySampler() as memory:
            try:
                payload = service.query(str(case["question"])).model_dump()
                evaluated = evaluate_case(case, payload)
            except Exception as exc:
                evaluated = {
                    "id": case["id"],
                    "passed": False,
                    "status_ok": False,
                    "retrieval_ok": False,
                    "facts_ok": False,
                    "language_ok": False,
                    "citations_ok": False,
                    "generation_mode": None,
                    "failure_stage": "runtime",
                    "retrieval_metrics": {
                        "eligible": False,
                        **dict.fromkeys(
                            [
                                f"{metric}_at_{cutoff}"
                                for metric in ("recall", "precision")
                                for cutoff in (1, 3, 5, 8)
                            ]
                            + ["reciprocal_rank"]
                        ),
                    },
                    "api_error": f"runtime:{type(exc).__name__}",
                }
        total_ms = (perf_counter() - started) * 1000
        measured_ms = (
            recorder.embedding_ms
            + recorder.retrieval_ms
            + recorder.rerank_ms
            + recorder.generation_ms
        )
        stages = {
            "run_state": "cold" if index == 0 else "warm",
            "embedding_ms": round(recorder.embedding_ms, 2),
            "retrieval_ms": round(recorder.retrieval_ms, 2),
            "rerank_ms": round(recorder.rerank_ms, 2),
            "grounding_ms": round(max(total_ms - measured_ms, 0.0), 2),
            "generation_ms": round(recorder.generation_ms, 2),
            "generation_calls": recorder.generation_calls,
            "total_ms": round(total_ms, 2),
            "process_peak_rss_mb": round(memory.process_peak / (1024**2), 2),
            "host_peak_used_mb": round(memory.host_peak / (1024**2), 2),
        }
        cases.append(_public_case(evaluated, stages))
    aggregated = _aggregate_profile(profile, cases)
    aggregated["indexing_ms"] = round(indexing_ms, 2)
    aggregated["index_fingerprint"] = _fingerprint_payload(fingerprint)
    aggregated["model_memory"] = (
        _model_memory(ollama_url, str(profile["generator_model"]))
        if profile["generator_mode"] == "ollama"
        else {"resident_mb": 0.0, "vram_mb": 0.0}
    )
    # A live backend keeps state: drop the profile's logical index once measured.
    cleanup = getattr(getattr(service.store, "wrapped", None), "drop_logical_index", None)
    if callable(cleanup):
        cleanup()
    return aggregated


def execute_phase(
    config_path: Path,
    phase: str,
    output: Path,
    *,
    selected_profile: str | None = None,
    decision_sha256: str | None = None,
    ollama_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    root = _repo_root()
    parsed_ollama = urlparse(ollama_url)
    if parsed_ollama.scheme != "http" or parsed_ollama.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError("WRK-TASK-027 sólo permite Ollama sobre loopback local")
    config_path = (root / config_path).resolve()
    config = load_benchmark_config(config_path)
    gold_key = "development_gold" if phase == "development" else "validation_gold"
    gold_path = (root / str(config[gold_key])).resolve()
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    expected_split = "dev" if phase == "development" else "validation"
    if gold.get("split") != expected_split:
        raise ValueError(f"El gold set no declara split={expected_split}")
    profiles = list(config["profiles"])
    if selected_profile is not None:
        profiles = [item for item in profiles if item["id"] == selected_profile]
        if len(profiles) != 1:
            raise ValueError(f"Perfil bloqueado desconocido: {selected_profile}")
    required_models = {
        str(item["generator_model"])
        for item in profiles
        if item["generator_mode"] == "ollama"
    }
    model_metadata = [
        _ollama_metadata(ollama_url, model) for model in sorted(required_models)
    ]
    expected_digests = {
        str(item["generator_model"]): str(item["generator_digest"])
        for item in profiles
        if item["generator_mode"] == "ollama"
    }
    for metadata in model_metadata:
        if metadata["digest"] != expected_digests[metadata["name"]]:
            raise RuntimeError(f"Digest Ollama inesperado para {metadata['name']}")
        if "3" not in str(metadata["parameter_size"]):
            raise RuntimeError("WRK-TASK-027 sólo admite el generador local 3B")
    source_path = (root / str(config["source_file"])).resolve()
    source_definitions = load_sources(source_path)
    expected_demo_root = (root / "examples/corpus/demo").resolve()
    if len(source_definitions) != 1 or source_definitions[0].id != "demo":
        raise ValueError("El benchmark público sólo permite la fuente sintética demo")
    if source_definitions[0].root != expected_demo_root:
        raise ValueError("La fuente demo debe resolver a examples/corpus/demo")
    manifest_path = (root / str(config["corpus_manifest"])).resolve()
    _verify_manifest(manifest_path)
    compatibility_path = (root / DEFAULT_CORPUS_COMPATIBILITY).resolve()
    compatibility = load_corpus_compatibility(compatibility_path)
    verify_gold_corpus_version(gold, compatibility)
    started = _utc_now()
    results = [
        _run_profile(item, config, gold, source_definitions, root, ollama_url, compatibility)
        for item in profiles
    ]
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "benchmark_id": config["benchmark_id"],
        "phase": phase,
        "started_at": started,
        "completed_at": _utc_now(),
        "revision": _revision(),
        "config_path": _relative(config_path, root),
        "config_sha256": _sha256(config_path),
        "gold_set": _relative(gold_path, root),
        "gold_sha256": _sha256(gold_path),
        "source_sha256": _sha256(source_path),
        "corpus_manifest_sha256": _sha256(manifest_path),
        "corpus_version": compatibility["corpus_version"],
        "corpus_compatibility_sha256": _sha256(compatibility_path),
        "seed": int(config["seed"]),
        "shared_config": {
            key: config[key]
            for key in (
                "embedding_batch_size",
                "chunk_tokens",
                "chunk_overlap",
                "ollama_timeout",
                "ollama_temperature",
            )
        },
        "run_definition": {
            "cold": "primer caso tras desalojar Ollama y recrear el embedder",
            "warm": "casos restantes del mismo perfil y proceso",
            "grounding": "selección, construcción y validación fuera de embed/retrieval/generate",
            "memory": "pico RSS Python, uso host y residencia Ollama durante cada consulta",
        },
        "hardware": _hardware_summary(),
        "models": model_metadata,
        "decision_sha256": decision_sha256,
        "profiles": results,
    }
    _write_json(output, report)
    return report


def select_baseline(config_path: Path, dev_report_path: Path, output: Path) -> dict[str, Any]:
    root = _repo_root()
    config_path = (root / config_path).resolve()
    dev_report_path = (root / dev_report_path).resolve()
    config = load_benchmark_config(config_path)
    report = _load_json(dev_report_path)
    if report.get("phase") != "development":
        raise ValueError("La decisión sólo puede derivarse de un informe development")
    if report.get("config_sha256") != _sha256(config_path):
        raise ValueError("La configuración cambió después del benchmark development")
    candidates = [item for item in report["profiles"] if item["baseline_eligible"]]
    if not candidates:
        raise ValueError("El informe no contiene candidatos elegibles")

    def rank(item: dict[str, Any]) -> tuple[float, float, float]:
        recall = item["retrieval"].get("recall_at_8")
        p95 = item["performance"]["total"]["p95_ms"]
        return float(item["score"]), float(recall or 0.0), -float(p95)

    selected = max(candidates, key=rank)
    validation_path = root / str(config["validation_gold"])
    decision = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": config["benchmark_id"],
        "locked_at": _utc_now(),
        "revision": report["revision"],
        "selected_profile": selected["profile_id"],
        "selection_policy": config["selection"],
        "selection_values": {
            "score": selected["score"],
            "retrieval_recall_at_8": selected["retrieval"].get("recall_at_8"),
            "latency_p95_ms": selected["performance"]["total"]["p95_ms"],
        },
        "config_sha256": report["config_sha256"],
        "development_gold_sha256": report["gold_sha256"],
        "validation_gold_sha256": _sha256(validation_path),
        "corpus_manifest_sha256": report["corpus_manifest_sha256"],
        "corpus_version": report.get("corpus_version"),
        "corpus_compatibility_sha256": report.get("corpus_compatibility_sha256"),
        "source_sha256": report["source_sha256"],
        "development_report_sha256": _sha256(dev_report_path),
        "validation_executions_allowed": 1,
    }
    _write_json(output, decision)
    return decision


def execute_validation(
    config_path: Path,
    decision_path: Path,
    output: Path,
    *,
    ollama_url: str = "http://127.0.0.1:11434",
) -> dict[str, Any]:
    root = _repo_root()
    output = (root / output).resolve()
    if output.exists():
        raise FileExistsError("La validación ya fue ejecutada; no se permite sobrescribirla")
    config_path = (root / config_path).resolve()
    decision_path = (root / decision_path).resolve()
    decision = _load_json(decision_path)
    config = load_benchmark_config(config_path)
    checks = {
        "revision": _revision() == decision["revision"],
        "config": _sha256(config_path) == decision["config_sha256"],
        "development_gold": _sha256(root / str(config["development_gold"]))
        == decision["development_gold_sha256"],
        "validation_gold": _sha256(root / str(config["validation_gold"]))
        == decision["validation_gold_sha256"],
        "corpus_manifest": _sha256(root / str(config["corpus_manifest"]))
        == decision["corpus_manifest_sha256"],
        "corpus_compatibility": _sha256((root / DEFAULT_CORPUS_COMPATIBILITY).resolve())
        == decision.get("corpus_compatibility_sha256"),
        "source": _sha256(root / str(config["source_file"]))
        == decision["source_sha256"],
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"El lock de decisión no coincide: {', '.join(failed)}")
    return execute_phase(
        config_path,
        "validation",
        output,
        selected_profile=str(decision["selected_profile"]),
        decision_sha256=_sha256(decision_path),
        ollama_url=ollama_url,
    )


def verify_artifacts(
    config_path: Path, dev_path: Path, decision_path: Path, validation_path: Path
) -> dict[str, bool]:
    root = _repo_root()
    config_path = (root / config_path).resolve()
    dev_path = (root / dev_path).resolve()
    decision_path = (root / decision_path).resolve()
    validation_path = (root / validation_path).resolve()
    config = load_benchmark_config(config_path)
    dev = _load_json(dev_path)
    decision = _load_json(decision_path)
    validation = _load_json(validation_path)
    checks = {
        "development_phase": dev.get("phase") == "development",
        "validation_phase": validation.get("phase") == "validation",
        "single_validation_profile": len(validation.get("profiles", [])) == 1,
        "selected_profile": validation["profiles"][0]["profile_id"]
        == decision["selected_profile"],
        "config_hash": _sha256(config_path) == decision["config_sha256"],
        "development_hash": _sha256(dev_path)
        == decision["development_report_sha256"],
        "validation_gold_hash": _sha256(root / str(config["validation_gold"]))
        == decision["validation_gold_sha256"],
        "source_hash": _sha256(root / str(config["source_file"]))
        == decision["source_sha256"],
        "decision_hash": validation.get("decision_sha256") == _sha256(decision_path),
        "corpus_version_match": dev.get("corpus_version") == validation.get("corpus_version")
        == decision.get("corpus_version"),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"Artefactos de benchmark inválidos: {', '.join(failed)}")
    return checks


def compare_reports(
    previous_path: Path,
    current_path: Path,
    *,
    profile_id: str,
    rebaseline: bool = False,
) -> dict[str, Any]:
    """Compares one profile across two benchmark reports (``ADR-RAG-011``,
    ``WRK-TASK-086``, ``WRK-TASK-098``). The comparability key is
    ``corpus_version``, ``IndexFingerprint`` digest, ``vector_backend`` and
    ``vector_search_mode``; if any differs the runs are not directly
    comparable and the delta cannot be presented as a regression or an
    improvement without an explicit ``rebaseline=True`` declaration.

    Recall stays comparable across backends or modes when corpus and
    fingerprint match (that is what a backend comparison measures); latency is
    comparable only under the full key, never across backends."""

    def _profile(report: dict[str, Any], path: Path) -> dict[str, Any]:
        match = next(
            (item for item in report.get("profiles", []) if item["profile_id"] == profile_id),
            None,
        )
        if match is None:
            raise ValueError(f"{path} no contiene el perfil {profile_id!r}")
        return match

    def _key(report: dict[str, Any], profile: dict[str, Any]) -> tuple[Any, ...]:
        return (
            report.get("corpus_version"),
            profile.get("index_fingerprint", {}).get("digest"),
            *report_vector_backend(report, profile),
        )

    def _summary(key: tuple[Any, ...], profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "corpus_version": key[0],
            "index_fingerprint": key[1],
            "vector_backend": key[2],
            "vector_search_mode": key[3],
            "score": profile["score"],
            "recall_at_8": profile.get("retrieval", {}).get("recall_at_8"),
            "latency_p95_ms": profile.get("performance", {}).get("total", {}).get("p95_ms"),
        }

    def _delta(name: str, allowed: bool) -> float | None:
        before, after = previous_summary[name], current_summary[name]
        if not allowed or before is None or after is None:
            return None
        return after - before

    previous = _load_json(previous_path)
    current = _load_json(current_path)
    previous_profile = _profile(previous, previous_path)
    current_profile = _profile(current, current_path)
    previous_key = _key(previous, previous_profile)
    current_key = _key(current, current_profile)
    comparable = previous_key == current_key
    if not comparable and not rebaseline:
        raise RebaselineRequired(
            "corpus_version/index_fingerprint/vector_backend/vector_search_mode difieren "
            f"entre informes para {profile_id!r}: {previous_key} -> {current_key}. El delta "
            "no puede presentarse como regresión ni como mejora sin una declaración "
            "explícita de re-baseline (--rebaseline)."
        )
    previous_summary = _summary(previous_key, previous_profile)
    current_summary = _summary(current_key, current_profile)
    recall_comparable = previous_key[:2] == current_key[:2]
    return {
        "profile_id": profile_id,
        "comparable": comparable,
        "rebaseline_declared": rebaseline,
        "recall_comparable": recall_comparable,
        "latency_comparable": comparable,
        "latency_note": None
        if comparable
        else (
            "latencia no comparable entre backends distintos"
            if previous_key[2] != current_key[2]
            else "latencia no comparable fuera de la misma clave de comparabilidad"
        ),
        "previous": previous_summary,
        "current": current_summary,
        "score_delta": _delta("score", comparable),
        "recall_at_8_delta": _delta("recall_at_8", recall_comparable),
        "latency_p95_delta_ms": _delta("latency_p95_ms", comparable),
    }


PARITY_METRICS = (
    "recall_at_1",
    "recall_at_3",
    "recall_at_5",
    "recall_at_8",
    "reciprocal_rank",
)


def backend_parity(report_path: Path, *, tolerance: float = 1e-9) -> dict[str, Any]:
    """Recall parity between profiles of one report that are identical except for
    ``vector_backend`` (``WRK-TASK-102``, ``ADR-RAG-013``). Same corpus and fingerprint make
    recall comparable across backends; latency never is, so it is reported per backend only."""
    report = _load_json(report_path)

    def pairing_key(profile: dict[str, Any]) -> str:
        return json.dumps(
            {
                "retrieval_strategy": profile.get("retrieval_strategy"),
                "reranker_model": profile.get("reranker_model"),
                "rerank_top_n": profile.get("rerank_top_n"),
                "effective_config": profile.get("effective_config"),
                "fingerprint": profile.get("index_fingerprint", {}).get("digest"),
            },
            sort_keys=True,
        )

    groups: dict[str, list[dict[str, Any]]] = {}
    for profile in report.get("profiles", []):
        groups.setdefault(pairing_key(profile), []).append(profile)
    pairs = []
    for members in groups.values():
        by_backend = {report_vector_backend(report, item)[0]: item for item in members}
        if len(by_backend) < 2 or "qdrant" not in by_backend:
            continue
        reference = by_backend["qdrant"]
        reference_cases = {case["id"]: case["retrieval_metrics"] for case in reference["cases"]}
        for backend, candidate in sorted(by_backend.items()):
            if backend == "qdrant":
                continue
            deltas = {
                name: (
                    None
                    if reference["retrieval"].get(name) is None
                    or candidate["retrieval"].get(name) is None
                    else round(candidate["retrieval"][name] - reference["retrieval"][name], 6)
                )
                for name in PARITY_METRICS
            }
            differing_cases = sorted(
                case["id"]
                for case in candidate["cases"]
                if case["retrieval_metrics"] != reference_cases.get(case["id"])
            )
            pairs.append(
                {
                    "reference_profile": reference["profile_id"],
                    "candidate_profile": candidate["profile_id"],
                    "reference_backend": "qdrant",
                    "reference_search_mode": report_vector_backend(report, reference)[1],
                    "candidate_backend": backend,
                    "candidate_search_mode": report_vector_backend(report, candidate)[1],
                    "index_fingerprint": reference["index_fingerprint"]["digest"],
                    "recall_reference": {n: reference["retrieval"].get(n) for n in PARITY_METRICS},
                    "recall_candidate": {n: candidate["retrieval"].get(n) for n in PARITY_METRICS},
                    "recall_delta": deltas,
                    "cases_with_different_retrieval": differing_cases,
                    "recall_parity": not differing_cases
                    and all(delta is None or abs(delta) <= tolerance for delta in deltas.values()),
                    "latency_comparable": False,
                    "latency_p95_ms_by_backend": {
                        "qdrant": reference["performance"]["retrieval"]["p95_ms"],
                        backend: candidate["performance"]["retrieval"]["p95_ms"],
                    },
                }
            )
    return {
        "benchmark_id": report.get("benchmark_id"),
        "phase": report.get("phase"),
        "corpus_version": report.get("corpus_version"),
        "pairs": pairs,
        "recall_parity": bool(pairs) and all(pair["recall_parity"] for pair in pairs),
    }


def run() -> None:
    parser = argparse.ArgumentParser(description="Benchmark local reproducible de rag-docs")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    subparsers = parser.add_subparsers(dest="command", required=True)
    dev = subparsers.add_parser("development")
    dev.add_argument("--output", type=Path, default=DEFAULT_DEV_REPORT)
    lock = subparsers.add_parser("lock")
    lock.add_argument("--development", type=Path, default=DEFAULT_DEV_REPORT)
    lock.add_argument("--output", type=Path, default=DEFAULT_DECISION)
    validation = subparsers.add_parser("validation")
    validation.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    validation.add_argument("--output", type=Path, default=DEFAULT_VALIDATION_REPORT)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--development", type=Path, default=DEFAULT_DEV_REPORT)
    verify.add_argument("--decision", type=Path, default=DEFAULT_DECISION)
    verify.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION_REPORT)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--previous", type=Path, required=True)
    compare.add_argument("--current", type=Path, required=True)
    compare.add_argument("--profile-id", required=True)
    compare.add_argument("--rebaseline", action="store_true")
    parity = subparsers.add_parser("parity")
    parity.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "parity":
        result = backend_parity(args.report)
    elif args.command == "development":
        result = execute_phase(args.config, "development", args.output)
    elif args.command == "lock":
        result = select_baseline(args.config, args.development, args.output)
    elif args.command == "validation":
        result = execute_validation(args.config, args.decision, args.output)
    elif args.command == "compare":
        result = compare_reports(
            args.previous,
            args.current,
            profile_id=args.profile_id,
            rebaseline=args.rebaseline,
        )
    else:
        result = verify_artifacts(
            args.config, args.development, args.decision, args.validation
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run()
