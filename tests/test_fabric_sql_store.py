"""Default-gate tests of ``FabricSqlVectorStore`` that need no Fabric capacity, driver or
credential. Its behavioural contract runs live in ``scripts/verify-fabric.ps1``."""

import pytest

from rag_docs.config import Settings
from rag_docs.container import build_vector_store
from rag_docs.contracts import AppError, ErrorKind, IndexPublicationPort, Scope
from rag_docs.fabric_sql_store import FabricSqlVectorStore, _map_error, build_fabric_sql_store


def _never_connect():
    raise AssertionError("no debe abrirse ninguna conexión")


def test_factory_selects_fabric_sql_without_connecting() -> None:
    settings = Settings(
        _env_file=None,
        vector_backend="fabric_sql",
        fabric_sql_server="sql-endpoint.example.test",
        fabric_sql_database="ragdocs",
    )

    store = build_vector_store(settings)

    assert isinstance(store, FabricSqlVectorStore)
    assert isinstance(store, IndexPublicationPort)
    assert store.logical_name == "rag_docs"


def test_missing_connection_or_certificate_settings_fail_explicitly() -> None:
    with pytest.raises(AppError) as missing_server:
        build_fabric_sql_store(Settings(_env_file=None, vector_backend="fabric_sql"))
    assert missing_server.value.kind is ErrorKind.VALIDATION

    with pytest.raises(AppError, match="fabric_client_cert_path"):
        build_fabric_sql_store(
            Settings(
                _env_file=None,
                fabric_sql_server="sql-endpoint.example.test",
                fabric_sql_database="ragdocs",
                fabric_sql_credential="certificate",
                fabric_tenant_id="tenant",
                fabric_client_id="client",
            )
        )


@pytest.mark.parametrize("name", ["rag-docs", "rag docs", "x]; DROP TABLE t; --", ""])
def test_logical_names_that_are_not_safe_identifiers_are_rejected(name: str) -> None:
    with pytest.raises(AppError) as excinfo:
        FabricSqlVectorStore(_never_connect, name)

    assert excinfo.value.kind is ErrorKind.VALIDATION


@pytest.mark.parametrize(
    "scope",
    [Scope(tenant="default"), Scope(tenant="default", subjects=frozenset({"default"}))],
    ids=["no-subjects", "no-classifications"],
)
def test_search_and_scan_fail_closed_on_an_empty_scope_without_querying(scope: Scope) -> None:
    store = FabricSqlVectorStore(_never_connect, "rag_docs")
    store._check_bound = lambda: "rag_docs__digest"  # type: ignore[method-assign]

    assert store.search([1.0, 0.0, 0.0], limit=5, score_threshold=None, scope=scope) == []
    assert store.scan_chunks(scope) == []


def test_unbound_reads_are_rejected_before_touching_the_database() -> None:
    store = FabricSqlVectorStore(_never_connect, "rag_docs")

    with pytest.raises(AppError) as excinfo:
        store.search([1.0], limit=1, score_threshold=None, scope=Scope(tenant="default"))

    assert excinfo.value.kind is ErrorKind.VALIDATION


def test_driver_failures_map_to_error_kinds_without_leaking_details() -> None:
    class ClientAuthenticationError(Exception):
        pass

    def failing_connect():
        raise RuntimeError("Login failed for user 'secret-user' on internal-host")

    store = FabricSqlVectorStore(failing_connect, "rag_docs")
    with pytest.raises(AppError) as excinfo:
        store.published_physical_name()

    assert excinfo.value.kind is ErrorKind.AUTHORIZATION
    assert "secret" not in excinfo.value.message
    assert "internal-host" not in excinfo.value.message
    assert _map_error(ClientAuthenticationError("token")).kind is ErrorKind.AUTHORIZATION
    assert _map_error(RuntimeError("Query timeout expired")).kind is ErrorKind.TIMEOUT
    assert _map_error(RuntimeError("network down")).kind is ErrorKind.DEPENDENCY_UNAVAILABLE
