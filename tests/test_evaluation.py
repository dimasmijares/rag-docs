import pytest

from rag_docs.evaluation import (
    _percentile,
    aggregate_retrieval_metrics,
    evaluate_case,
)


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
