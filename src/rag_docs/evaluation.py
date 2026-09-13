from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import httpx
import yaml

from rag_docs.contracts import IndexFingerprint
from rag_docs.language import normalized_contains, text_matches_language

DEFAULT_CORPUS_COMPATIBILITY = Path("evaluation/corpus-compatibility.yaml")


def load_corpus_compatibility(path: Path) -> dict[str, Any]:
    """Corpus/gold-set/fingerprint compatibility manifest (``ADR-RAG-011``,
    ``WRK-TASK-086``): which ``corpus_version`` a gold set was written against
    and which ``IndexFingerprint`` digests a report built on that corpus is
    comparable with."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def verify_gold_corpus_version(gold: dict[str, Any], compatibility: dict[str, Any]) -> None:
    """A gold set that does not declare the ``corpus_version`` the active
    compatibility manifest expects fails explicitly instead of silently
    producing low retrieval metrics against locators that moved."""
    declared = gold.get("corpus_version")
    expected = compatibility.get("corpus_version")
    if not declared:
        raise ValueError(
            "El gold set no declara corpus_version; no es comparable con el "
            "manifiesto de compatibilidad activo."
        )
    if declared != expected:
        raise ValueError(
            f"El gold set declara corpus_version={declared!r}, pero el manifiesto de "
            f"compatibilidad activo es corpus_version={expected!r}. No son comparables "
            "sin una declaración explícita de re-baseline."
        )


def verify_fingerprint_compatibility(
    compatibility: dict[str, Any], fingerprint_digest: str
) -> None:
    """The ``IndexFingerprint`` actually in effect must be one this
    ``corpus_version`` was declared compatible with, or the run fails
    explicitly (``RULE-004``, ``ADR-RAG-011``) instead of reporting metrics
    that look like a quality regression."""
    compatible = set(compatibility.get("compatible_fingerprint_digests") or [])
    if fingerprint_digest not in compatible:
        raise RuntimeError(
            f"El fingerprint vigente ({fingerprint_digest}) no está declarado compatible "
            f"con corpus_version={compatibility.get('corpus_version')!r} en "
            "compatibility.yaml. Añade el digest si el cambio es intencional, o revisa la "
            "configuración: no se ejecuta el benchmark/evaluación contra una combinación "
            "no verificada."
        )


def live_index_fingerprint(client: httpx.Client) -> dict[str, Any]:
    """The ``IndexFingerprint`` the running API is actually serving
    (``GET /api/sources``, ``WRK-TASK-093``), in the same shape
    ``benchmark._fingerprint_payload`` records. The digest is recomputed from
    the fields, so a payload whose declared digest does not match them fails
    explicitly instead of being trusted."""
    response = client.get("/api/sources")
    response.raise_for_status()
    payload = response.json().get("index_fingerprint")
    if not payload:
        raise RuntimeError(
            "La API no expone index_fingerprint en GET /api/sources; no se puede "
            "verificar la compatibilidad del índice vigente con el corpus."
        )
    fields = {key: value for key, value in payload.items() if key != "digest"}
    try:
        fingerprint = IndexFingerprint(**fields)
    except TypeError as exc:
        raise RuntimeError(f"index_fingerprint de la API no es válido: {exc}") from exc
    if payload.get("digest") != fingerprint.digest():
        raise RuntimeError(
            f"El digest declarado por la API ({payload.get('digest')}) no coincide con "
            f"el calculado a partir de sus campos ({fingerprint.digest()})."
        )
    return {**asdict(fingerprint), "digest": fingerprint.digest()}


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _fact_matches(answer: str, fact: str | dict[str, list[str]]) -> bool:
    if isinstance(fact, str):
        return normalized_contains(answer, fact)
    if "any_of" in fact:
        return any(normalized_contains(answer, option) for option in fact["any_of"])
    if "all_of" in fact:
        return all(normalized_contains(answer, option) for option in fact["all_of"])
    raise ValueError(f"Hecho no soportado: {fact!r}")


def _matches_evidence(candidate: dict[str, Any], expected: dict[str, Any]) -> bool:
    if candidate.get("relative_path") != expected.get("document"):
        return False
    section = expected.get("section")
    if section is not None and candidate.get("section") != section:
        return False
    locator = expected.get("locator") or {}
    candidate_locator = candidate.get("locator") or {}
    return all(candidate_locator.get(key) == value for key, value in locator.items())


def _expected_evidence_groups(case: dict[str, Any]) -> list[list[dict[str, Any]]]:
    locators = list(case.get("expected_locators") or [])
    required = list(case.get("expected_documents") or [])
    alternatives = list(case.get("expected_any_documents") or [])
    groups: list[list[dict[str, Any]]] = []
    for document in required:
        matches = [item for item in locators if item.get("document") == document]
        groups.extend([[item] for item in matches] or [[{"document": document}]])
    if alternatives:
        matches = [item for item in locators if item.get("document") in alternatives]
        groups.append(matches or [{"document": document} for document in alternatives])
    return groups


def _retrieval_metrics(
    case: dict[str, Any], diagnostics: list[dict[str, Any]]
) -> dict[str, Any]:
    groups = _expected_evidence_groups(case)
    eligible = case.get("expected_status") == "grounded" and bool(groups)
    names = [
        "recall_at_1",
        "recall_at_3",
        "recall_at_5",
        "recall_at_8",
        "reciprocal_rank",
        "precision_at_1",
        "precision_at_3",
        "precision_at_5",
        "precision_at_8",
    ]
    if not eligible:
        return {"eligible": False, **dict.fromkeys(names)}

    ranked = sorted(diagnostics, key=lambda item: int(item["rank"]))

    def relevant(candidate: dict[str, Any]) -> bool:
        return any(
            _matches_evidence(candidate, expected)
            for group in groups
            for expected in group
        )

    metrics: dict[str, Any] = {"eligible": True}
    for cutoff in (1, 3, 5, 8):
        candidates = [item for item in ranked if int(item["rank"]) <= cutoff]
        covered = sum(
            any(
                _matches_evidence(candidate, expected)
                for candidate in candidates
                for expected in group
            )
            for group in groups
        )
        metrics[f"recall_at_{cutoff}"] = covered / len(groups)
        metrics[f"precision_at_{cutoff}"] = (
            sum(relevant(candidate) for candidate in candidates) / len(candidates)
            if candidates
            else 0.0
        )
    first_relevant = next(
        (int(candidate["rank"]) for candidate in ranked if relevant(candidate)), None
    )
    metrics["reciprocal_rank"] = 1 / first_relevant if first_relevant else 0.0
    return metrics


def aggregate_retrieval_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    eligible = [
        item["retrieval_metrics"]
        for item in results
        if item["retrieval_metrics"]["eligible"]
    ]
    names = (
        "recall_at_1",
        "recall_at_3",
        "recall_at_5",
        "recall_at_8",
        "reciprocal_rank",
        "precision_at_1",
        "precision_at_3",
        "precision_at_5",
        "precision_at_8",
    )
    return {
        "cases": len(results),
        "eligible_cases": len(eligible),
        **{
            name: round(sum(float(item[name]) for item in eligible) / len(eligible), 6)
            if eligible
            else None
            for name in names
        },
    }


def evaluate_case(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    answer = str(payload["answer"])
    citations = list(payload.get("citations") or [])
    retrieved = {str(item["relative_path"]) for item in citations}

    expected_documents = set(case.get("expected_documents") or [])
    expected_any_documents = set(case.get("expected_any_documents") or [])
    required_documents_ok = expected_documents.issubset(retrieved)
    alternative_document_ok = (
        not expected_any_documents or bool(expected_any_documents.intersection(retrieved))
    )
    retrieval_ok = required_documents_ok and alternative_document_ok

    required_facts = list(case.get("required_facts") or [])
    missing_facts = [fact for fact in required_facts if not _fact_matches(answer, fact)]
    facts_ok = not missing_facts

    reference = case.get("reference_answer")
    reference_ok = reference is None or normalized_contains(answer, str(reference))

    expected_language = case.get("expected_language")
    language_ok = (
        expected_language is None or text_matches_language(answer, expected_language)
    )

    expected_status = case["expected_status"]
    status_ok = payload["answer_status"] == expected_status
    if expected_status == "grounded":
        valid_references = {str(item["reference"]) for item in citations}
        cited_references = set(re.findall(r"\[(\d+)\]", answer))
        citations_ok = bool(citations) and bool(valid_references.intersection(cited_references))
    else:
        citations_ok = True

    passed = all(
        (status_ok, retrieval_ok, facts_ok, reference_ok, language_ok, citations_ok)
    )
    diagnostics = list(payload.get("retrieval_diagnostics") or [])
    if not diagnostics:
        diagnostics = [
            {
                **citation,
                "rank": index,
                "selected": True,
                "section": citation.get("section"),
                "locator": citation.get("locator") or {},
            }
            for index, citation in enumerate(citations, start=1)
        ]
    retrieval_metrics = _retrieval_metrics(case, diagnostics)
    failure_stage: str | None = None
    if not passed:
        groups = _expected_evidence_groups(case)
        if retrieval_metrics["eligible"]:
            candidates = [item for item in diagnostics if int(item["rank"]) <= 8]
            selected = [item for item in diagnostics if item.get("selected")]

            def covers(items: list[dict[str, Any]]) -> bool:
                return all(
                    any(
                        _matches_evidence(candidate, expected)
                        for candidate in items
                        for expected in group
                    )
                    for group in groups
                )

            if not covers(candidates):
                failure_stage = "retrieval"
            elif not covers(selected):
                failure_stage = "context_selection"
            else:
                failure_stage = "generation"
        else:
            failure_stage = "generation"
    return {
        "id": case["id"],
        "passed": passed,
        "status_ok": status_ok,
        "retrieval_ok": retrieval_ok,
        "facts_ok": facts_ok,
        "missing_facts": missing_facts,
        "language_ok": language_ok,
        "citations_ok": citations_ok,
        "answer_contains_reference": reference_ok,
        "retrieved_documents": sorted(retrieved),
        "answer_status": payload["answer_status"],
        "generation_mode": payload.get("generation_mode"),
        "api_error": None,
        "model": payload.get("model"),
        "embedding_model": payload.get("embedding_model"),
        "retrieval_metrics": retrieval_metrics,
        "failure_stage": failure_stage,
    }


def evaluate(
    base_url: str,
    gold_path: Path,
    *,
    compatibility_path: Path = DEFAULT_CORPUS_COMPATIBILITY,
    transport: httpx.BaseTransport | None = None,
) -> dict[str, Any]:
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    compatibility = load_corpus_compatibility(compatibility_path)
    verify_gold_corpus_version(gold, compatibility)
    results: list[dict[str, Any]] = []
    with httpx.Client(base_url=base_url, timeout=240, transport=transport) as client:
        # Before scoring any case: an index incompatible with this corpus fails
        # explicitly instead of producing low metrics (RULE-004, ADR-RAG-011).
        index_fingerprint = live_index_fingerprint(client)
        verify_fingerprint_compatibility(compatibility, index_fingerprint["digest"])
        for case in gold["cases"]:
            started = perf_counter()
            try:
                response = client.post("/api/query", json={"question": case["question"]})
                response.raise_for_status()
                result = evaluate_case(case, response.json())
                result["latency_ms"] = round((perf_counter() - started) * 1000, 2)
                results.append(result)
            except httpx.HTTPError as exc:
                results.append(
                    {
                        "id": case["id"],
                        "passed": False,
                        "status_ok": False,
                        "retrieval_ok": False,
                        "facts_ok": False,
                        "missing_facts": list(case.get("required_facts") or []),
                        "language_ok": False,
                        "citations_ok": False,
                        "answer_contains_reference": False,
                        "retrieved_documents": [],
                        "answer_status": None,
                        "generation_mode": None,
                        "api_error": str(exc),
                        "model": None,
                        "embedding_model": None,
                        "retrieval_metrics": _retrieval_metrics(case, []),
                        "failure_stage": "api",
                        "latency_ms": round((perf_counter() - started) * 1000, 2),
                    }
                )
    passed = sum(item["passed"] for item in results)
    latencies = [float(item["latency_ms"]) for item in results]
    observed_models = {
        (item.get("model"), item.get("embedding_model"))
        for item in results
        if item.get("model") or item.get("embedding_model")
    }
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "gold_set": str(gold_path),
        "corpus_version": gold.get("corpus_version"),
        "index_fingerprint": index_fingerprint,
        "config_snapshot": {
            "model": next(iter(observed_models))[0] if observed_models else None,
            "embedding_model": next(iter(observed_models))[1] if observed_models else None,
            "consistent_across_cases": len(observed_models) <= 1,
        },
        "passed": passed,
        "total": len(results),
        "score": passed / len(results) if results else 0,
        "metrics": {
            "status": sum(item["status_ok"] for item in results),
            "retrieval": sum(item["retrieval_ok"] for item in results),
            "facts": sum(item["facts_ok"] for item in results),
            "language": sum(item["language_ok"] for item in results),
            "citations": sum(item["citations_ok"] for item in results),
        },
        "performance": {
            "samples": len(latencies),
            "total_ms": round(sum(latencies), 2),
            "p50_ms": round(_percentile(latencies, 0.50), 2),
            "p95_ms": round(_percentile(latencies, 0.95), 2),
            "min_ms": round(min(latencies), 2) if latencies else 0.0,
            "max_ms": round(max(latencies), 2) if latencies else 0.0,
        },
        "retrieval": aggregate_retrieval_metrics(results),
        "cases": results,
    }


def run() -> None:
    parser = argparse.ArgumentParser(description="Evalúa rag-docs contra el gold set")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--gold", type=Path, default=Path("evaluation/gold-set.yaml"))
    parser.add_argument(
        "--corpus-compatibility", type=Path, default=DEFAULT_CORPUS_COMPATIBILITY
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(
        args.base_url, args.gold, compatibility_path=args.corpus_compatibility
    )
    output = args.output or Path("logs") / f"evaluation-{datetime.now():%Y%m%d-%H%M%S}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] == report["total"] else 1)


if __name__ == "__main__":
    run()
