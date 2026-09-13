from dataclasses import asdict
from pathlib import Path

import httpx
import pytest
import yaml

from rag_docs.evaluation import (
    _percentile,
    aggregate_retrieval_metrics,
    evaluate,
    evaluate_case,
    verify_fingerprint_compatibility,
    verify_gold_corpus_version,
)
from rag_docs.indexing import IndexingService
from tests.fakes import FakeEmbedder, FakeVectorStore


def citation(reference: int, path: str) -> dict:
    return {"reference": reference, "relative_path": path}


def diagnostic(
    rank: int,
    path: str,
    *,
    selected: bool,
    context_rank: int | None = None,
    discard_reason: str | None = None,
) -> dict:
    return {
        "rank": rank,
        "score": round(1 - rank / 100, 2),
        "chunk_id": f"chunk-{rank}",
        "document_id": f"document-{rank}",
        "source_id": "demo",
        "relative_path": path,
        "locator": {},
        "section": None,
        "selected": selected,
        "context_rank": context_rank,
        "discard_reason": discard_reason,
    }


def grounded_case() -> dict:
    return {
        "id": "retrieval-case",
        "expected_status": "grounded",
        "expected_documents": ["target.md"],
        "expected_any_documents": [],
        "expected_language": "es",
        "required_facts": ["HECHO_OBJETIVO"],
    }


def test_partial_mixed_language_answer_fails_regression() -> None:
    case = {
        "id": "compound-question",
        "expected_status": "grounded",
        "expected_any_documents": ["guide.md", "guide.docx"],
        "expected_language": "es",
        "required_facts": [
            "DWH.DEMO.FACT_VENTAS_NORTE",
            "DWH.DEMO.FACT_VENTAS_SUR",
            "DWH.DEMO.PERIMETRO_PROMOCIONES",
        ],
    }
    payload = {
        "answer_status": "grounded",
        "answer": (
            "Final Norte e Final Sur son las tablas finales y "
            "DWH.DEMO.PERIMETRO_PROMOCIONES é a tabela de perímetro. [1]"
        ),
        "citations": [citation(1, "guide.md")],
    }

    result = evaluate_case(case, payload)

    assert result["passed"] is False
    assert result["retrieval_ok"] is True
    assert result["facts_ok"] is False
    assert result["language_ok"] is False
    assert result["missing_facts"] == [
        "DWH.DEMO.FACT_VENTAS_NORTE",
        "DWH.DEMO.FACT_VENTAS_SUR",
    ]


def test_complete_answer_with_alternative_document_passes() -> None:
    case = {
        "id": "compound-question",
        "expected_status": "grounded",
        "expected_any_documents": ["guide.md", "guide.docx"],
        "expected_language": "es",
        "required_facts": ["TABLA_HG", "TABLA_AA", "PERIMETRO"],
    }
    payload = {
        "answer_status": "grounded",
        "answer": "Las tablas son TABLA_HG y TABLA_AA [1]. El consolidado es PERIMETRO [1].",
        "citations": [citation(1, "guide.docx")],
    }

    result = evaluate_case(case, payload)

    assert result["passed"] is True
    assert result["facts_ok"] is True
    assert result["language_ok"] is True
    assert result["citations_ok"] is True
    assert result["retrieval_metrics"]["recall_at_1"] == 1.0
    assert result["retrieval_metrics"]["reciprocal_rank"] == 1.0


def test_retrieval_metrics_report_ranks_and_context_selection_failure() -> None:
    diagnostics = [
        diagnostic(1, "noise-1.md", selected=True, context_rank=1),
        diagnostic(2, "target.md", selected=False, discard_reason="context_limit"),
        diagnostic(3, "noise-3.md", selected=False, discard_reason="context_limit"),
        diagnostic(4, "noise-4.md", selected=False, discard_reason="context_limit"),
        diagnostic(5, "noise-5.md", selected=False, discard_reason="context_limit"),
        diagnostic(6, "noise-6.md", selected=False, discard_reason="context_limit"),
        diagnostic(7, "noise-7.md", selected=False, discard_reason="context_limit"),
        diagnostic(8, "noise-8.md", selected=False, discard_reason="context_limit"),
    ]
    payload = {
        "answer_status": "insufficient_evidence",
        "answer": "No hay evidencia suficiente.",
        "citations": [citation(1, "noise-1.md")],
        "retrieval_diagnostics": diagnostics,
    }

    result = evaluate_case(grounded_case(), payload)

    assert result["failure_stage"] == "context_selection"
    assert result["retrieval_metrics"] == {
        "eligible": True,
        "recall_at_1": 0.0,
        "recall_at_3": 1.0,
        "recall_at_5": 1.0,
        "recall_at_8": 1.0,
        "reciprocal_rank": 0.5,
        "precision_at_1": 0.0,
        "precision_at_3": pytest.approx(1 / 3),
        "precision_at_5": 0.2,
        "precision_at_8": 0.125,
    }


def test_failure_stage_distinguishes_retrieval_generation_and_success() -> None:
    retrieval_payload = {
        "answer_status": "insufficient_evidence",
        "answer": "No hay evidencia suficiente.",
        "citations": [],
        "retrieval_diagnostics": [
            diagnostic(1, "noise.md", selected=True, context_rank=1)
        ],
    }
    generation_payload = {
        "answer_status": "grounded",
        "answer": "Respuesta incompleta [1].",
        "citations": [citation(1, "target.md")],
        "retrieval_diagnostics": [
            diagnostic(1, "target.md", selected=True, context_rank=1)
        ],
    }
    success_payload = {
        "answer_status": "grounded",
        "answer": "El resultado es HECHO_OBJETIVO [1].",
        "citations": [citation(1, "target.md")],
        "retrieval_diagnostics": [
            diagnostic(1, "target.md", selected=True, context_rank=1)
        ],
    }

    assert evaluate_case(grounded_case(), retrieval_payload)["failure_stage"] == "retrieval"
    assert evaluate_case(grounded_case(), generation_payload)["failure_stage"] == "generation"
    assert evaluate_case(grounded_case(), success_payload)["failure_stage"] is None


def test_negative_case_is_excluded_from_retrieval_denominators() -> None:
    case = {
        "id": "negative",
        "expected_status": "insufficient_evidence",
        "expected_documents": [],
        "expected_any_documents": [],
        "expected_language": "es",
        "required_facts": [],
    }
    payload = {
        "answer_status": "insufficient_evidence",
        "answer": "No hay evidencia suficiente.",
        "citations": [],
        "retrieval_diagnostics": [
            diagnostic(1, "unrelated.md", selected=True, context_rank=1)
        ],
    }

    result = evaluate_case(case, payload)

    assert result["passed"] is True
    assert result["failure_stage"] is None
    assert result["retrieval_metrics"] == {
        "eligible": False,
        "recall_at_1": None,
        "recall_at_3": None,
        "recall_at_5": None,
        "recall_at_8": None,
        "reciprocal_rank": None,
        "precision_at_1": None,
        "precision_at_3": None,
        "precision_at_5": None,
        "precision_at_8": None,
    }

    invalid_payload = {
        **payload,
        "answer_status": "grounded",
        "answer": "Respuesta no sustentada.",
    }
    assert evaluate_case(case, invalid_payload)["failure_stage"] == "generation"


def test_aggregate_retrieval_metrics_averages_only_eligible_cases() -> None:
    def metrics(value: float) -> dict:
        return {
            "eligible": True,
            "recall_at_1": value,
            "recall_at_3": value,
            "recall_at_5": value,
            "recall_at_8": value,
            "reciprocal_rank": value,
            "precision_at_1": value,
            "precision_at_3": value,
            "precision_at_5": value,
            "precision_at_8": value,
        }

    excluded = {key: None for key in metrics(0.0)}
    excluded["eligible"] = False

    aggregate = aggregate_retrieval_metrics(
        [
            {"retrieval_metrics": metrics(1.0)},
            {"retrieval_metrics": metrics(0.0)},
            {"retrieval_metrics": excluded},
        ]
    )

    assert aggregate["cases"] == 3
    assert aggregate["eligible_cases"] == 2
    for name in (
        "recall_at_1",
        "recall_at_3",
        "recall_at_5",
        "recall_at_8",
        "reciprocal_rank",
        "precision_at_1",
        "precision_at_3",
        "precision_at_5",
        "precision_at_8",
    ):
        assert aggregate[name] == 0.5


def test_legacy_reference_answer_remains_supported() -> None:
    case = {
        "id": "legacy",
        "expected_status": "grounded",
        "expected_documents": ["doc.md"],
        "reference_answer": "ETL_CLIENTES_DIARIA",
    }
    payload = {
        "answer_status": "grounded",
        "answer": "La respuesta es ETL_CLIENTES_DIARIA [1].",
        "citations": [citation(1, "doc.md")],
    }

    assert evaluate_case(case, payload)["passed"] is True


def test_percentile_uses_linear_interpolation() -> None:
    values = [10.0, 20.0, 30.0, 40.0]

    assert _percentile(values, 0.50) == 25.0
    assert _percentile(values, 0.95) == 38.5


def test_verify_gold_corpus_version_rejects_undeclared_version() -> None:
    with pytest.raises(ValueError, match="no declara corpus_version"):
        verify_gold_corpus_version({}, {"corpus_version": "0.2.0"})


def test_verify_gold_corpus_version_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="No son comparables"):
        verify_gold_corpus_version(
            {"corpus_version": "0.1.0"}, {"corpus_version": "0.2.0"}
        )


def test_verify_gold_corpus_version_accepts_declared_match() -> None:
    verify_gold_corpus_version({"corpus_version": "0.2.0"}, {"corpus_version": "0.2.0"})


def test_verify_fingerprint_compatibility_rejects_undeclared_digest() -> None:
    with pytest.raises(RuntimeError, match="no está declarado compatible"):
        verify_fingerprint_compatibility(
            {"corpus_version": "0.2.0", "compatible_fingerprint_digests": ["aaa"]}, "bbb"
        )


def test_verify_fingerprint_compatibility_accepts_declared_digest() -> None:
    verify_fingerprint_compatibility(
        {"compatible_fingerprint_digests": ["aaa", "bbb"]}, "bbb"
    )


LIVE_FINGERPRINT = IndexingService([], FakeEmbedder(), FakeVectorStore()).fingerprint


def _write_evaluation_inputs(tmp_path: Path, compatible_digests: list[str]) -> tuple[Path, Path]:
    gold = tmp_path / "gold.yaml"
    gold.write_text(
        yaml.safe_dump(
            {
                "corpus_version": "0.2.0",
                "cases": [
                    {
                        "id": "negative",
                        "question": "¿Hay algo?",
                        "expected_status": "insufficient_evidence",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    compatibility = tmp_path / "compatibility.yaml"
    compatibility.write_text(
        yaml.safe_dump(
            {"corpus_version": "0.2.0", "compatible_fingerprint_digests": compatible_digests}
        ),
        encoding="utf-8",
    )
    return gold, compatibility


def _live_api(
    fingerprint_payload: dict | None, queried: list[str], **declared: str
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/sources":
            body: dict = {"sources": [], **declared}
            if fingerprint_payload is not None:
                body["index_fingerprint"] = fingerprint_payload
            return httpx.Response(200, json=body)
        queried.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "answer_status": "insufficient_evidence",
                "answer": "No hay evidencia suficiente.",
                "citations": [],
            },
        )

    return httpx.MockTransport(handler)


def _payload(fingerprint=LIVE_FINGERPRINT) -> dict:
    return {**asdict(fingerprint), "digest": fingerprint.digest()}


def test_evaluate_records_the_live_index_fingerprint_when_compatible(tmp_path: Path) -> None:
    gold, compatibility = _write_evaluation_inputs(tmp_path, [LIVE_FINGERPRINT.digest()])
    queried: list[str] = []

    report = evaluate(
        "http://api",
        gold,
        compatibility_path=compatibility,
        transport=_live_api(_payload(), queried),
    )

    assert report["index_fingerprint"] == _payload()
    assert report["schema_version"] == "1.1"
    assert (report["vector_backend"], report["vector_search_mode"]) == ("qdrant", "hnsw")
    assert report["index_fingerprint"]["digest"] == LIVE_FINGERPRINT.digest()
    assert report["passed"] == report["total"] == 1
    assert queried == ["/api/query"]


def test_evaluate_fails_explicitly_before_scoring_against_an_incompatible_index(
    tmp_path: Path,
) -> None:
    gold, compatibility = _write_evaluation_inputs(tmp_path, ["0000000000000000"])
    queried: list[str] = []

    with pytest.raises(RuntimeError, match="no está declarado compatible"):
        evaluate(
            "http://api",
            gold,
            compatibility_path=compatibility,
            transport=_live_api(_payload(), queried),
        )

    assert queried == []


def test_evaluate_rejects_an_api_without_fingerprint_or_with_a_forged_digest(
    tmp_path: Path,
) -> None:
    gold, compatibility = _write_evaluation_inputs(tmp_path, [LIVE_FINGERPRINT.digest()])

    with pytest.raises(RuntimeError, match="no expone index_fingerprint"):
        evaluate(
            "http://api", gold, compatibility_path=compatibility, transport=_live_api(None, [])
        )

    forged = {**_payload(), "chunk_tokens": 999}
    with pytest.raises(RuntimeError, match="no coincide"):
        evaluate(
            "http://api", gold, compatibility_path=compatibility, transport=_live_api(forged, [])
        )


def test_evaluate_records_the_backend_the_api_declares(tmp_path: Path) -> None:
    gold, compatibility = _write_evaluation_inputs(tmp_path, [LIVE_FINGERPRINT.digest()])

    report = evaluate(
        "http://api",
        gold,
        compatibility_path=compatibility,
        transport=_live_api(
            _payload(), [], vector_backend="fabric_sql", vector_search_mode="exact"
        ),
    )

    assert (report["vector_backend"], report["vector_search_mode"]) == ("fabric_sql", "exact")
