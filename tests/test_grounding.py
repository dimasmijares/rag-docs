from pathlib import Path

from rag_docs.chunking import chunk_document
from rag_docs.generation import GeneratedClaim, GeneratedResponse
from rag_docs.grounding import AnswerValidator, ContextBuilder
from rag_docs.models import DocumentCandidate, ExtractedUnit, SearchHit


def make_hit(
    tmp_path: Path,
    score: float = 0.9,
    text: str = "ETL_CLIENTES_DIARIA carga clientes.",
    relative_path: str = "etl/doc.md",
    locator: dict[str, str | int] | None = None,
    section: str | None = None,
) -> SearchHit:
    path = tmp_path / Path(relative_path).name
    path.write_text("ETL_CLIENTES_DIARIA", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, relative_path, path.as_uri(), "hash")
    chunk = chunk_document(
        candidate,
        [ExtractedUnit(text, locator or {"page": 1}, section)],
    )[0]
    return SearchHit(chunk, score)


def test_context_builder_deduplicates_and_caps_context_size(tmp_path: Path) -> None:
    kept = make_hit(tmp_path, score=0.95, text="Contenido único uno.")
    duplicate_same_document = SearchHit(kept.chunk, 0.9)
    equivalent_text = make_hit(
        tmp_path,
        score=0.85,
        text="Contenido unico uno.",
        relative_path="etl/other.md",
    )
    over_limit = make_hit(tmp_path, score=0.5, text="Contenido distinto dos.")
    builder = ContextBuilder(context_chunks=1)

    result = builder.build(
        "pregunta", [kept, duplicate_same_document, equivalent_text, over_limit]
    )

    assert result.selected == [kept]
    assert [citation.reference for citation in result.citations] == [1]
    reasons = {d.rank: d.discard_reason for d in result.retrieval_diagnostics}
    assert reasons[2] == "duplicate_chunk"
    assert reasons[3] == "equivalent_document"
    assert reasons[4] == "context_limit"


def test_context_builder_prioritizes_technical_identifiers_for_technical_questions(
    tmp_path: Path,
) -> None:
    generic = make_hit(tmp_path, score=0.95, text="La documentación describe la tabla final.")
    technical = make_hit(tmp_path, score=0.80, text="La tabla final es CI.DQ.TABLA_FINAL.")
    builder = ContextBuilder(context_chunks=2)

    result = builder.build("¿Qué tabla final se utiliza?", [generic, technical])

    assert result.selected[0] is technical
    assert "EVIDENCIA TÉCNICA LITERAL" in result.context
    assert "CI.DQ.TABLA_FINAL" in result.context


def test_context_builder_build_context_matches_grounding_port_shape(tmp_path: Path) -> None:
    hit = make_hit(tmp_path)
    builder = ContextBuilder()

    context, selected = builder.build_context("¿Qué carga clientes?", [hit])

    assert selected == [hit]
    assert "ETL_CLIENTES_DIARIA" in context


def test_answer_validator_minimum_claims_requires_explicit_second_question() -> None:
    assert AnswerValidator.minimum_claims("¿Qué variable se usa para ORION y LYRA?") == 1
    assert (
        AnswerValidator.minimum_claims(
            "¿En qué tabla se consolida y cuáles son las tablas finales?"
        )
        == 2
    )


def test_answer_validator_rejects_citations_outside_valid_references() -> None:
    validator = AnswerValidator()
    generated = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[GeneratedClaim(text="La tabla es TABLA_X.", citations=[99])],
        unanswered_parts=[],
    )

    errors = validator.validation_errors(
        generated,
        "¿Qué tabla se usa?",
        "es",
        valid_references={1},
        evidence_by_reference={1: "TABLA_X aparece aquí."},
    )

    assert any("citas inexistentes" in error for error in errors)


def test_answer_validator_validate_matches_grounding_port_shape() -> None:
    validator = AnswerValidator()
    generated = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[GeneratedClaim(text="La tabla es TABLA_X.", citations=[1])],
        unanswered_parts=[],
    )

    verdict = validator.validate(
        generated, "¿Qué tabla se usa?", evidence_by_reference={1: "TABLA_X aparece aquí."}
    )

    assert verdict.grounded is True
    assert verdict.errors == ()


def test_answer_validator_validate_reports_ungrounded_verdict() -> None:
    validator = AnswerValidator()
    generated = GeneratedResponse(
        status="grounded",
        language="en",
        claims=[GeneratedClaim(text="The table is TABLA_X.", citations=[1])],
        unanswered_parts=[],
    )

    verdict = validator.validate(
        generated, "¿Qué tabla se usa?", evidence_by_reference={1: "TABLA_X aparece aquí."}
    )

    assert verdict.grounded is False
    assert verdict.errors


def test_answer_validator_extractive_fallback_cites_literal_evidence(tmp_path: Path) -> None:
    hit = make_hit(
        tmp_path,
        text="Inicio STEP_PEDIR_FECHA informa Job::FechaProceso.",
    )
    builder = ContextBuilder()
    built = builder.build("¿Qué variable contiene la fecha de proceso?", [hit])
    validator = AnswerValidator()

    fallback = validator.extractive_technical_fallback(
        "¿Qué variable contiene la fecha de proceso?",
        built.citations,
        built.selected,
        "es",
    )

    assert fallback is not None
    assert fallback.status == "grounded"
    assert "Job::FechaProceso" in fallback.claims[0].text
