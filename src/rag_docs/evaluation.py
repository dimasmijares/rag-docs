from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import httpx
import yaml

from rag_docs.language import normalized_contains, text_matches_language


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
    }


def evaluate(base_url: str, gold_path: Path) -> dict[str, Any]:
    gold = yaml.safe_load(gold_path.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    with httpx.Client(base_url=base_url, timeout=240) as client:
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
                        "latency_ms": round((perf_counter() - started) * 1000, 2),
                    }
                )
    passed = sum(item["passed"] for item in results)
    latencies = [float(item["latency_ms"]) for item in results]
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "gold_set": str(gold_path),
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
        "cases": results,
    }


def run() -> None:
    parser = argparse.ArgumentParser(description="Evalúa rag-docs contra el gold set")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--gold", type=Path, default=Path("evaluation/gold-set.yaml"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.base_url, args.gold)
    output = args.output or Path("logs") / f"evaluation-{datetime.now():%Y%m%d-%H%M%S}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    raise SystemExit(0 if report["passed"] == report["total"] else 1)


if __name__ == "__main__":
    run()
