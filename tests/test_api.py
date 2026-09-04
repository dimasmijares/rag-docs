from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from rag_docs.api import create_app
from rag_docs.config import SourceDefinition
from rag_docs.generation import GenerationError
from rag_docs.indexing import IndexReport
from rag_docs.query import QueryResult


class FakeIndexing:
    def index(self, source_ids=None):
        return IndexReport(added=1, chunks_written=2)


class FakeQuery:
    def query(self, question: str):
        return QueryResult(
            answer_status="insufficient_evidence",
            answer="No hay evidencia suficiente.",
            citations=[],
            model=None,
            embedding_model="fake",
            answer_language="es",
            claims=[],
            generation_mode="none",
        )


class UnavailableGeneratorQuery:
    def query(self, question: str):
        raise GenerationError("El generador remoto no responde")


class BrokenQuery:
    def query(self, question: str):
        raise RuntimeError("qdrant connection string=secret@internal-host:6333")


class FakeGeneratorControl:
    def __init__(self) -> None:
        self.active = "local"

    def state(self):
        return {
            "active_profile": self.active,
            "profiles": [
                {
                    "id": "local",
                    "label": "Local",
                    "endpoint": "http://local:11434",
                    "model": "model-a",
                    "active": self.active == "local",
                },
                {
                    "id": "remote",
                    "label": "Remoto",
                    "endpoint": "http://remote:11434",
                    "model": "model-b",
                    "active": self.active == "remote",
                },
            ],
        }

    def check(self, profile: str):
        selected = next(item for item in self.state()["profiles"] if item["id"] == profile)
        return {**selected, "ready": True, "available_models": [selected["model"]]}

    def activate(self, profile: str, model: str | None = None):
        checked = self.check(profile)
        if model:
            checked = {**checked, "model": model, "available_models": [model]}
        self.active = profile
        return {**checked, "active": True}


def test_api_contract_and_web_smoke(tmp_path: Path) -> None:
    container = SimpleNamespace(
        source_definitions=[SourceDefinition(id="demo", root=tmp_path)],
        indexing=FakeIndexing(),
        query=FakeQuery(),
    )
    client = TestClient(create_app(container))

    root = client.get("/")
    sources = client.get("/api/sources")
    indexed = client.post("/api/index", json={})
    queried = client.post("/api/query", json={"question": "¿Qué hay?"})

    assert root.status_code == 200
    assert "Pregunta a tu documentación" in root.text
    assert "Configuración del generador" in root.text
    assert sources.json()["sources"][0]["available"] is True
    assert indexed.json()["chunks_written"] == 2
    assert queried.json()["answer_status"] == "insufficient_evidence"


def test_openapi_declares_release_version(tmp_path: Path) -> None:
    from rag_docs import __version__

    container = SimpleNamespace(
        source_definitions=[SourceDefinition(id="demo", root=tmp_path)],
        indexing=FakeIndexing(),
        query=FakeQuery(),
    )
    client = TestClient(create_app(container))

    assert __version__ == "0.2.0"
    assert client.get("/openapi.json").json()["info"]["version"] == "0.2.0"


def test_generator_failure_is_an_explicit_service_error(tmp_path: Path) -> None:
    container = SimpleNamespace(
        source_definitions=[SourceDefinition(id="demo", root=tmp_path)],
        indexing=FakeIndexing(),
        query=UnavailableGeneratorQuery(),
    )
    client = TestClient(create_app(container))

    response = client.post("/api/query", json={"question": "¿Qué hay?"})

    assert response.status_code == 503
    assert response.json()["detail"] == "El generador remoto no responde"


def test_unexpected_error_maps_to_error_kind_without_leaking_exception_text(
    tmp_path: Path,
) -> None:
    container = SimpleNamespace(
        source_definitions=[SourceDefinition(id="demo", root=tmp_path)],
        indexing=FakeIndexing(),
        query=BrokenQuery(),
    )
    client = TestClient(create_app(container))

    response = client.post("/api/query", json={"question": "¿Qué hay?"})

    assert response.status_code == 503
    assert "secret" not in response.json()["detail"]
    assert "qdrant" not in response.json()["detail"].casefold()


def test_generator_profiles_can_be_checked_and_activated(tmp_path: Path) -> None:
    control = FakeGeneratorControl()
    container = SimpleNamespace(
        source_definitions=[SourceDefinition(id="demo", root=tmp_path)],
        indexing=FakeIndexing(),
        query=FakeQuery(),
        generator_profiles_state=control.state,
        check_generator_profile=control.check,
        activate_generator_profile=control.activate,
    )
    client = TestClient(create_app(container))

    initial = client.get("/api/generator")
    checked = client.post("/api/generator/check", json={"profile": "remote"})
    activated = client.post(
        "/api/generator/activate",
        json={"profile": "remote", "model": "model-new"},
    )
    final = client.get("/api/generator")

    assert initial.json()["active_profile"] == "local"
    assert checked.json()["ready"] is True
    assert checked.json()["model"] == "model-b"
    assert activated.json()["active"] is True
    assert activated.json()["model"] == "model-new"
    assert final.json()["active_profile"] == "remote"
