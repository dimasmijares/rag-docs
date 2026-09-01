from pathlib import Path

from rag_docs.chunking import chunk_document
from rag_docs.generation import GeneratedClaim, GeneratedResponse
from rag_docs.models import DocumentCandidate, ExtractedUnit, SearchHit
from rag_docs.query import QueryService
from tests.fakes import FakeEmbedder, FakeGenerator, FakeVectorStore


def make_hit(
    tmp_path: Path,
    score: float = 0.9,
    text: str = "ETL_CLIENTES_DIARIA carga clientes.",
) -> SearchHit:
    path = tmp_path / "doc.md"
    path.write_text("ETL_CLIENTES_DIARIA", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "etl/doc.md", path.as_uri(), "hash")
    chunk = chunk_document(
        candidate,
        [ExtractedUnit(text, {"page": 1})],
    )[0]
    return SearchHit(chunk, score)


def test_query_returns_grounded_answer_with_citations(tmp_path: Path) -> None:
    store = FakeVectorStore()
    store.hits = [make_hit(tmp_path)]
    generator = FakeGenerator("La carga corresponde a ETL_CLIENTES_DIARIA [1].")
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query("¿Qué carga clientes?")

    assert result.answer_status == "grounded"
    assert result.citations[0].relative_path == "etl/doc.md"
    assert "[1]" in result.answer
    assert "ETL_CLIENTES_DIARIA" in generator.context


def test_query_without_hits_does_not_call_generator() -> None:
    store = FakeVectorStore()
    generator = FakeGenerator()
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query("Pregunta sin respuesta")

    assert result.answer_status == "insufficient_evidence"
    assert result.citations == []
    assert generator.context == ""


def test_generator_can_reject_related_but_insufficient_context(tmp_path: Path) -> None:
    store = FakeVectorStore()
    store.hits = [make_hit(tmp_path)]
    service = QueryService(
        FakeEmbedder(), store, FakeGenerator("INSUFFICIENT_EVIDENCE")
    )
    result = service.query("Pregunta ambigua")
    assert result.answer_status == "insufficient_evidence"
    assert result.citations


def test_compound_question_retries_language_and_coverage(tmp_path: Path) -> None:
    store = FakeVectorStore()
    store.hits = [
        make_hit(
            tmp_path,
            text=(
                "La tabla final es CI.DQ.TABLA_FINAL y el perímetro es "
                "CI.DQ.TABLA_PERIMETRO."
            ),
        )
    ]
    invalid = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[GeneratedClaim(text="A resposta é a tabela final.", citations=[1])],
        unanswered_parts=[],
    )
    corrected = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[
            GeneratedClaim(text="La tabla final es CI.DQ.TABLA_FINAL.", citations=[1]),
            GeneratedClaim(text="El perímetro es CI.DQ.TABLA_PERIMETRO.", citations=[1]),
        ],
        unanswered_parts=[],
    )
    generator = FakeGenerator([invalid, corrected])
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query("¿Cuál es la tabla final y cuál es el perímetro?")

    assert result.answer_status == "grounded"
    assert result.answer_language == "es"
    assert len(result.claims) == 2
    assert "CI.DQ.TABLA_FINAL" in result.answer
    assert "CI.DQ.TABLA_PERIMETRO" in result.answer
    assert generator.feedback[0] is None
    assert "mezcla idiomas" in str(generator.feedback[1])
    assert "al menos 2 afirmaciones" in str(generator.feedback[1])


def test_invalid_citations_are_not_reported_as_grounded(tmp_path: Path) -> None:
    store = FakeVectorStore()
    store.hits = [make_hit(tmp_path)]
    invalid = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[GeneratedClaim(text="La tabla es TABLA_X.", citations=[99])],
        unanswered_parts=[],
    )
    service = QueryService(FakeEmbedder(), store, FakeGenerator([invalid, invalid]))

    result = service.query("¿Qué tabla se utiliza?")

    assert result.answer_status == "insufficient_evidence"
    assert result.claims == []


def test_technical_questions_prioritize_chunks_with_identifiers(tmp_path: Path) -> None:
    generic = make_hit(tmp_path, score=0.95, text="La documentación describe la tabla final.")
    technical = make_hit(
        tmp_path,
        score=0.80,
        text="La tabla final es CI.DQ.TABLA_FINAL.",
    )
    store = FakeVectorStore()
    store.hits = [generic, technical]
    generator = FakeGenerator(
        GeneratedResponse(
            status="grounded",
            language="es",
            claims=[
                GeneratedClaim(
                    text="La tabla final es CI.DQ.TABLA_FINAL.", citations=[1]
                )
            ],
            unanswered_parts=[],
        )
    )
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query("¿Qué tabla final se utiliza?")

    assert result.answer_status == "grounded"
    assert result.citations[0].snippet.startswith("La tabla final es CI.DQ.TABLA_FINAL")
    assert "EVIDENCIA TÉCNICA LITERAL" in generator.context
    assert "[1] La tabla final es CI.DQ.TABLA_FINAL." in generator.context


def test_procedural_question_does_not_require_an_etl_identifier(tmp_path: Path) -> None:
    store = FakeVectorStore()
    store.hits = [
        make_hit(
            tmp_path,
            text="Antes de lanzar la ETL hay que evitar eliminar datos válidos.",
        )
    ]
    generator = FakeGenerator(
        GeneratedResponse(
            status="grounded",
            language="es",
            claims=[
                GeneratedClaim(
                    text="La precaución es no eliminar datos válidos.", citations=[1]
                )
            ],
            unanswered_parts=[],
        )
    )
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query(
        "¿Qué precaución debe revisarse antes de lanzar la ETL respecto a los datos?"
    )

    assert result.answer_status == "grounded"


def test_only_explicit_second_questions_require_multiple_claims() -> None:
    assert QueryService._minimum_claims(
        "¿Qué variable se usa para ORION y LYRA?"
    ) == 1
    assert QueryService._minimum_claims(
        "¿Qué acción actualiza SQL_BD y muestra el resultado?"
    ) == 1
    assert QueryService._minimum_claims(
        "¿En qué tabla se consolida y cuáles son las tablas finales?"
    ) == 2
    assert QueryService._minimum_claims(
        "¿Qué tabla se consulta y por qué campo se filtra?"
    ) == 2


def test_technical_question_rechecks_insufficient_answer_when_candidates_exist(
    tmp_path: Path,
) -> None:
    store = FakeVectorStore()
    store.hits = [
        make_hit(
            tmp_path,
            text=(
                "Proyecto carga_origenes_demo para ORION y LYRA.\n"
                "Inicio STEP_PEDIR_FECHA informa Job::FechaProceso."
            ),
        )
    ]
    insufficient = GeneratedResponse(
        status="insufficient_evidence",
        language="es",
        claims=[],
        unanswered_parts=["No se encontró una variable."],
    )
    corrected = GeneratedResponse(
        status="grounded",
        language="es",
        claims=[
            GeneratedClaim(
                text="La variable es Job::FechaProceso.", citations=[1]
            )
        ],
        unanswered_parts=[],
    )
    generator = FakeGenerator([insufficient, corrected])
    service = QueryService(FakeEmbedder(), store, generator)

    result = service.query("¿Qué variable contiene la fecha de proceso?")

    assert result.answer_status == "grounded"
    assert "Job::FechaProceso" in result.answer
    assert "EVIDENCIA TÉCNICA LITERAL" in str(generator.feedback[1])


def test_technical_question_uses_cited_extractive_fallback_after_two_rejections(
    tmp_path: Path,
) -> None:
    store = FakeVectorStore()
    store.hits = [
        make_hit(
            tmp_path,
            text=(
                "Proyecto carga_origenes_demo para ORION y LYRA.\n"
                "Inicio STEP_PEDIR_FECHA informa Job::FechaProceso."
            ),
        )
    ]
    insufficient = GeneratedResponse(
        status="insufficient_evidence",
        language="es",
        claims=[],
        unanswered_parts=["No se encontró una variable."],
    )
    service = QueryService(
        FakeEmbedder(), store, FakeGenerator([insufficient, insufficient])
    )

    result = service.query("¿Qué variable contiene la fecha de proceso?")

    assert result.answer_status == "grounded"
    assert result.generation_mode == "extractive_fallback"
    assert "Job::FechaProceso" in result.answer
    assert "[1]" in result.answer
