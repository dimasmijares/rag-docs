from rag_docs.evaluation import _percentile, evaluate_case


def citation(reference: int, path: str) -> dict:
    return {"reference": reference, "relative_path": path}


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
