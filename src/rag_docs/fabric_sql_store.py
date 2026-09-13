"""``VectorStorePort`` + ``IndexPublicationPort`` over SQL database in Fabric
(``ADR-RAG-013``, ``WRK-TASK-100``).

Layout, the SQL equivalent of Qdrant's physical collection + alias (``RULE-004``):

- ``dbo.rag_index_alias``: logical name -> physical index currently published.
- ``dbo.rag_index_physical``: catalog of physical indexes (one per fingerprint).
- ``dbo.[<physical>__chunks]``: one row per chunk with its payload, the scope columns the
  prefilter reads (``tenant_id``, ``classification``) and a ``VECTOR(n)`` embedding.
- ``dbo.[<physical>__acl]``: ACL subjects as a child table, so an ACL change never rewrites a
  vector (``ADR-RAG-009``).

Search is exact (``VECTOR_DISTANCE``): the scope prefilter is part of the ``WHERE`` clause, so it
runs before ``TOP k`` (``RULE-003``), and ``score = 1 - cosine distance``. The SQL driver
(``mssql-python``) and ``azure-identity`` are the optional ``[fabric]`` extra and are imported
lazily; authentication is always a Microsoft Entra token, never a stored secret.
"""

from __future__ import annotations

import json
import re
import struct
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from rag_docs.contracts import (
    AclFields,
    AppError,
    DocumentChunk,
    ErrorKind,
    IndexedDocument,
    IndexFingerprint,
    Scope,
    SearchHit,
    chunk_from_payload,
)

ALIAS_TABLE = "dbo.rag_index_alias"
PHYSICAL_TABLE = "dbo.rag_index_physical"
SQL_SCOPE = "https://database.windows.net/.default"
#: ``SQL_COPT_SS_ACCESS_TOKEN``: pre-connect attribute that carries the Entra token.
ACCESS_TOKEN_ATTRIBUTE = 1256
_NAME = re.compile(r"^[A-Za-z0-9_]{1,80}$")

ConnectionFactory = Callable[[], Any]


def _json(values: object) -> str:
    return json.dumps(sorted(values) if isinstance(values, set | frozenset) else values)


def _vector(values: list[float]) -> str:
    return json.dumps([float(value) for value in values])


class FabricSqlVectorStore:
    """Fabric SQL adapter with the same fingerprint, scope and ACL guarantees as
    ``QdrantVectorStore``. ``logical_name`` is always resolved through the alias table,
    except for a candidate store bound directly to one physical index."""

    def __init__(
        self,
        connection_factory: ConnectionFactory,
        logical_name: str,
        *,
        _physical_name: str | None = None,
    ) -> None:
        if not _NAME.match(logical_name):
            raise AppError(
                ErrorKind.VALIDATION,
                "El nombre lógico del índice sólo admite letras, dígitos y '_' (máx. 80).",
            )
        self._connect = connection_factory
        self._connection: Any = None
        self.collection_name = logical_name
        self._direct_physical = _physical_name
        self._bound_fingerprint: IndexFingerprint | None = None
        self._schema_ready = False

    # -- connection and error mapping -------------------------------------------------

    @contextmanager
    def _cursor(self) -> Iterator[Any]:
        try:
            if self._connection is None:
                self._connection = self._connect()
            cursor = self._connection.cursor()
            try:
                yield cursor
                # Reads also end their transaction, so no lock outlives the call.
                self._connection.commit()
            except BaseException:
                self._rollback_quietly()
                raise
            finally:
                cursor.close()
        except AppError:
            raise
        except Exception as exc:
            self._discard_connection()
            raise _map_error(exc) from exc

    def _rollback_quietly(self) -> None:
        try:
            if self._connection is not None:
                self._connection.rollback()
        except Exception:
            self._discard_connection()

    def _discard_connection(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def close(self) -> None:
        self._discard_connection()

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self._cursor() as cursor:
            cursor.execute(
                f"IF OBJECT_ID(N'{ALIAS_TABLE}', N'U') IS NULL "
                f"CREATE TABLE {ALIAS_TABLE} ("
                "logical_name NVARCHAR(128) NOT NULL PRIMARY KEY, "
                "physical_name NVARCHAR(128) NOT NULL, "
                "updated_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
            )
            cursor.execute(
                f"IF OBJECT_ID(N'{PHYSICAL_TABLE}', N'U') IS NULL "
                f"CREATE TABLE {PHYSICAL_TABLE} ("
                "physical_name NVARCHAR(128) NOT NULL PRIMARY KEY, "
                "logical_name NVARCHAR(128) NOT NULL, "
                "dimension INT NOT NULL, "
                "created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME())"
            )
        self._schema_ready = True

    # -- IndexPublicationPort ---------------------------------------------------------

    @property
    def logical_name(self) -> str:
        return self.collection_name

    def physical_name_for(self, fingerprint: IndexFingerprint) -> str:
        if self._direct_physical is not None:
            return self._direct_physical
        return f"{self.collection_name}__{fingerprint.digest()}"

    def published_physical_name(self) -> str | None:
        return self._resolve_alias()

    def candidate_store(self, fingerprint: IndexFingerprint) -> FabricSqlVectorStore:
        return FabricSqlVectorStore(
            self._connect,
            self.collection_name,
            _physical_name=f"{self.collection_name}__{fingerprint.digest()}",
        )

    def _resolve_alias(self) -> str | None:
        self._ensure_schema()
        if self._direct_physical is not None:
            return self._direct_physical if self._physical_exists(self._direct_physical) else None
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT physical_name FROM {ALIAS_TABLE} WHERE logical_name = ?",
                (self.collection_name,),
            )
            row = cursor.fetchone()
        return str(row[0]) if row else None

    def _physical_exists(self, physical_name: str) -> bool:
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT 1 FROM {PHYSICAL_TABLE} WHERE physical_name = ?", (physical_name,)
            )
            return cursor.fetchone() is not None

    def _dimension(self, physical_name: str) -> int:
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT dimension FROM {PHYSICAL_TABLE} WHERE physical_name = ?",
                (physical_name,),
            )
            row = cursor.fetchone()
        if row is None:
            raise AppError(ErrorKind.NOT_FOUND, f"No existe el índice físico '{physical_name}'.")
        return int(row[0])

    def publish_alias(self, physical_name: str) -> None:
        """Repoint the alias in a single transactional ``MERGE``: readers see either the
        previous or the new physical index, never none."""
        self._ensure_schema()
        with self._cursor() as cursor:
            cursor.execute(
                f"MERGE {ALIAS_TABLE} WITH (HOLDLOCK) AS target "
                "USING (SELECT ? AS logical_name, ? AS physical_name) AS source "
                "ON target.logical_name = source.logical_name "
                "WHEN MATCHED THEN UPDATE SET physical_name = source.physical_name, "
                "updated_at = SYSUTCDATETIME() "
                "WHEN NOT MATCHED THEN INSERT (logical_name, physical_name) "
                "VALUES (source.logical_name, source.physical_name);",
                (self.collection_name, physical_name),
            )

    def rollback_alias(self, previous_physical_name: str) -> None:
        self._ensure_schema()
        if not self._physical_exists(previous_physical_name):
            raise AppError(
                ErrorKind.NOT_FOUND,
                f"El índice anterior '{previous_physical_name}' ya no existe: "
                "fuera de la ventana de rollback.",
            )
        self.publish_alias(previous_physical_name)

    def delete_physical(self, physical_name: str) -> None:
        """End the rollback window explicitly; refuses to drop the alias target."""
        if self._resolve_alias() == physical_name:
            raise AppError(
                ErrorKind.VALIDATION,
                f"'{physical_name}' es el objetivo actual del alias; no se elimina.",
            )
        self._drop_physical(physical_name)

    def _drop_physical(self, physical_name: str) -> None:
        chunks, acl = _tables(physical_name)
        with self._cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {acl}")
            cursor.execute(f"DROP TABLE IF EXISTS {chunks}")
            cursor.execute(
                f"DELETE FROM {PHYSICAL_TABLE} WHERE physical_name = ?", (physical_name,)
            )

    def drop_logical_index(self) -> None:
        """Remove every physical index and the alias of this logical name. Used to clean up
        live contract runs; never called by the application."""
        self._ensure_schema()
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT physical_name FROM {PHYSICAL_TABLE} WHERE logical_name = ?",
                (self.collection_name,),
            )
            physical_names = [str(row[0]) for row in cursor.fetchall()]
        for physical_name in physical_names:
            self._drop_physical(physical_name)
        with self._cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {ALIAS_TABLE} WHERE logical_name = ?", (self.collection_name,)
            )
        self.close()

    # -- fingerprint binding (RULE-004) -----------------------------------------------

    def bind_fingerprint(self, fingerprint: IndexFingerprint) -> None:
        self._bound_fingerprint = fingerprint

    def verify_fingerprint(self, fingerprint: IndexFingerprint) -> str:
        physical = self.physical_name_for(fingerprint)
        current = self._resolve_alias()
        if current is None:
            raise AppError(ErrorKind.NOT_FOUND, f"No existe el índice '{self.collection_name}'.")
        if current != physical:
            raise AppError(
                ErrorKind.VALIDATION,
                f"El índice '{self.collection_name}' no coincide con el fingerprint activo; "
                "ejecute la migración antes de escribir o consultar.",
            )
        return physical

    def _check_bound(self) -> str:
        if self._bound_fingerprint is None:
            raise AppError(
                ErrorKind.VALIDATION,
                "Ningún fingerprint vinculado: llame a ensure_collection o bind_fingerprint "
                "antes de usar el índice.",
            )
        return self.verify_fingerprint(self._bound_fingerprint)

    def ensure_collection(
        self, vector_size: int, fingerprint: IndexFingerprint | None = None
    ) -> None:
        if fingerprint is None:
            raise AppError(
                ErrorKind.VALIDATION, "ensure_collection requiere el fingerprint activo (RULE-004)."
            )
        physical = self.physical_name_for(fingerprint)
        current = self._resolve_alias()
        if current is None:
            self._create_physical(physical, vector_size)
            if self._direct_physical is None:
                self.publish_alias(physical)
        elif current != physical:
            raise AppError(
                ErrorKind.VALIDATION,
                f"El índice '{self.collection_name}' ya existe con otro fingerprint "
                f"('{current}' != '{physical}'); reutilizarlo sin migrar está prohibido "
                "(RULE-004). Ejecute la migración explícita antes de escribir.",
            )
        self.bind_fingerprint(fingerprint)

    def _create_physical(self, physical_name: str, vector_size: int) -> None:
        if self._physical_exists(physical_name):
            return
        dimension = int(vector_size)
        chunks, acl = _tables(physical_name)
        index = physical_name
        with self._cursor() as cursor:
            cursor.execute(
                f"CREATE TABLE {chunks} ("
                "chunk_id VARCHAR(64) NOT NULL PRIMARY KEY, "
                "document_id VARCHAR(64) NOT NULL, "
                "source_id NVARCHAR(128) NOT NULL, "
                "content_hash NVARCHAR(128) NOT NULL, "
                "tenant_id NVARCHAR(128) NOT NULL, "
                "classification NVARCHAR(64) NOT NULL, "
                "payload NVARCHAR(MAX) NOT NULL, "
                f"embedding VECTOR({dimension}) NOT NULL)"
            )
            cursor.execute(
                f"CREATE INDEX [IX_{index}__scope] ON {chunks} (tenant_id, classification)"
            )
            cursor.execute(f"CREATE INDEX [IX_{index}__document] ON {chunks} (document_id)")
            cursor.execute(f"CREATE INDEX [IX_{index}__source] ON {chunks} (source_id)")
            cursor.execute(
                f"CREATE TABLE {acl} ("
                "chunk_id VARCHAR(64) NOT NULL, "
                "subject NVARCHAR(256) NOT NULL, "
                f"CONSTRAINT [PK_{index}__acl] PRIMARY KEY (chunk_id, subject))"
            )
            cursor.execute(f"CREATE INDEX [IX_{index}__subject] ON {acl} (subject, chunk_id)")
            cursor.execute(
                f"INSERT INTO {PHYSICAL_TABLE} (physical_name, logical_name, dimension) "
                "VALUES (?, ?, ?)",
                (physical_name, self.collection_name, dimension),
            )

    # -- VectorStorePort --------------------------------------------------------------

    def list_documents(self, source_ids: set[str]) -> dict[str, IndexedDocument]:
        physical = self._resolve_alias()
        if physical is None or not source_ids:
            return {}
        chunks, _ = _tables(physical)
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT DISTINCT document_id, source_id, content_hash FROM {chunks} "
                "WHERE source_id IN (SELECT value FROM OPENJSON(?))",
                (_json(source_ids),),
            )
            rows = cursor.fetchall()
        return {
            str(row[0]): IndexedDocument(
                document_id=str(row[0]), source_id=str(row[1]), content_hash=str(row[2])
            )
            for row in rows
        }

    def delete_document(self, document_id: str) -> None:
        physical = self._resolve_alias()
        if physical is None:
            return
        chunks, acl = _tables(physical)
        with self._cursor() as cursor:
            cursor.execute(
                f"DELETE a FROM {acl} a JOIN {chunks} c ON a.chunk_id = c.chunk_id "
                "WHERE c.document_id = ?",
                (document_id,),
            )
            cursor.execute(f"DELETE FROM {chunks} WHERE document_id = ?", (document_id,))

    def prune_document(self, document_id: str, keep_chunk_ids: set[str]) -> None:
        if not keep_chunk_ids:
            self.delete_document(document_id)
            return
        physical = self._resolve_alias()
        if physical is None:
            return
        chunks, acl = _tables(physical)
        stale = (
            "c.document_id = ? AND c.chunk_id NOT IN (SELECT value FROM OPENJSON(?))"
        )
        parameters = (document_id, _json(keep_chunk_ids))
        with self._cursor() as cursor:
            cursor.execute(
                f"DELETE a FROM {acl} a JOIN {chunks} c ON a.chunk_id = c.chunk_id WHERE {stale}",
                parameters,
            )
            cursor.execute(f"DELETE c FROM {chunks} c WHERE {stale}", parameters)

    def upsert(self, chunks: list[DocumentChunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Cada chunk debe tener exactamente un vector")
        physical = self._check_bound()
        if not chunks:
            return
        dimension = self._dimension(physical)
        chunk_table, acl_table = _tables(physical)
        chunk_ids = _json([chunk.chunk_id for chunk in chunks])
        with self._cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {acl_table} WHERE chunk_id IN (SELECT value FROM OPENJSON(?))",
                (chunk_ids,),
            )
            cursor.execute(
                f"DELETE FROM {chunk_table} WHERE chunk_id IN (SELECT value FROM OPENJSON(?))",
                (chunk_ids,),
            )
            cursor.executemany(
                f"INSERT INTO {chunk_table} (chunk_id, document_id, source_id, content_hash, "
                "tenant_id, classification, payload, embedding) "
                f"VALUES (?, ?, ?, ?, ?, ?, ?, CAST(? AS VECTOR({dimension})))",
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.source_id,
                        chunk.content_hash,
                        chunk.tenant_id,
                        chunk.classification,
                        json.dumps(chunk.payload(), ensure_ascii=False),
                        _vector(vector),
                    )
                    for chunk, vector in zip(chunks, vectors, strict=True)
                ],
            )
            acl_rows = [
                (chunk.chunk_id, subject)
                for chunk in chunks
                for subject in dict.fromkeys(chunk.acl_subjects)
            ]
            if acl_rows:
                cursor.executemany(
                    f"INSERT INTO {acl_table} (chunk_id, subject) VALUES (?, ?)", acl_rows
                )

    def search(
        self, vector: list[float], limit: int, score_threshold: float | None, scope: Scope
    ) -> list[SearchHit]:
        physical = self._check_bound()
        if not scope.subjects or not scope.classifications:
            # Fail closed (RULE-003): an empty subject or classification set matches nothing.
            return []
        dimension = self._dimension(physical)
        chunks, acl = _tables(physical)
        threshold = "" if score_threshold is None else "AND 1.0 - distance >= ? "
        parameters: list[object] = [
            _vector(vector),
            int(limit),
            scope.tenant,
            _json(scope.classifications),
            _json(scope.subjects),
        ]
        if score_threshold is not None:
            parameters.append(float(score_threshold))
        with self._cursor() as cursor:
            cursor.execute(
                f"DECLARE @query VECTOR({dimension}) = CAST(? AS VECTOR({dimension})); "
                "SELECT TOP (?) payload, 1.0 - distance AS score FROM ("
                "SELECT c.chunk_id, c.payload, "
                "VECTOR_DISTANCE('cosine', c.embedding, @query) AS distance "
                f"FROM {chunks} c "
                "WHERE c.tenant_id = ? "
                "AND c.classification IN (SELECT value FROM OPENJSON(?)) "
                f"AND EXISTS (SELECT 1 FROM {acl} a WHERE a.chunk_id = c.chunk_id "
                "AND a.subject IN (SELECT value FROM OPENJSON(?)))"
                f") AS scoped WHERE 1 = 1 {threshold}"
                "ORDER BY distance ASC, chunk_id ASC",
                tuple(parameters),
            )
            rows = cursor.fetchall()
        return [
            SearchHit(chunk=chunk_from_payload(json.loads(row[0])), score=float(row[1]))
            for row in rows
        ]

    def scan_chunks(self, scope: Scope) -> list[DocumentChunk]:
        physical = self._check_bound()
        if not scope.subjects or not scope.classifications:
            return []
        chunks, acl = _tables(physical)
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT c.payload FROM {chunks} c "
                "WHERE c.tenant_id = ? "
                "AND c.classification IN (SELECT value FROM OPENJSON(?)) "
                f"AND EXISTS (SELECT 1 FROM {acl} a WHERE a.chunk_id = c.chunk_id "
                "AND a.subject IN (SELECT value FROM OPENJSON(?))) "
                "ORDER BY c.chunk_id",
                (scope.tenant, _json(scope.classifications), _json(scope.subjects)),
            )
            rows = cursor.fetchall()
        return [chunk_from_payload(json.loads(row[0])) for row in rows]

    def update_acl(self, document_id: str, acl: AclFields) -> None:
        """Rewrite scope columns, payload ACL fields and ACL rows of ``document_id``; the
        ``embedding`` column is never touched (``ADR-RAG-009``)."""
        physical = self._check_bound()
        chunks, acl_table = _tables(physical)
        with self._cursor() as cursor:
            cursor.execute(
                f"SELECT chunk_id, payload FROM {chunks} WHERE document_id = ?", (document_id,)
            )
            rows = cursor.fetchall()
            updates = []
            for chunk_id, payload in rows:
                data = json.loads(payload)
                data.update(
                    tenant_id=acl.tenant_id,
                    acl_subjects=list(acl.acl_subjects),
                    classification=acl.classification,
                    acl_policy_id=acl.acl_policy_id,
                    acl_version=acl.acl_version,
                )
                updates.append(
                    (acl.tenant_id, acl.classification, json.dumps(data, ensure_ascii=False),
                     str(chunk_id))
                )
            if not updates:
                return
            cursor.executemany(
                f"UPDATE {chunks} SET tenant_id = ?, classification = ?, payload = ? "
                "WHERE chunk_id = ?",
                updates,
            )
            cursor.execute(
                f"DELETE a FROM {acl_table} a JOIN {chunks} c ON a.chunk_id = c.chunk_id "
                "WHERE c.document_id = ?",
                (document_id,),
            )
            cursor.executemany(
                f"INSERT INTO {acl_table} (chunk_id, subject) VALUES (?, ?)",
                [
                    (chunk_id, subject)
                    for *_, chunk_id in updates
                    for subject in dict.fromkeys(acl.acl_subjects)
                ],
            )


def _tables(physical_name: str) -> tuple[str, str]:
    if not re.match(r"^[A-Za-z0-9_]{1,120}$", physical_name):
        raise AppError(ErrorKind.VALIDATION, "Nombre de índice físico no válido.")
    return f"dbo.[{physical_name}__chunks]", f"dbo.[{physical_name}__acl]"


def _map_error(exc: Exception) -> AppError:
    """Map driver and identity failures to ``ErrorKind`` without leaking server, database or
    token details to callers (``ADR-RAG-010``)."""
    name = type(exc).__name__
    text = str(exc).casefold()
    if name in {"ClientAuthenticationError", "CredentialUnavailableError"} or (
        "login failed" in text or "authentication" in text or "permission" in text
        or "denied" in text
    ):
        return AppError(ErrorKind.AUTHORIZATION, "Fabric SQL rechazó la identidad o el permiso.")
    if "timeout" in text or "timed out" in text:
        return AppError(ErrorKind.TIMEOUT, "Fabric SQL no respondió a tiempo.")
    return AppError(ErrorKind.DEPENDENCY_UNAVAILABLE, "Fabric SQL no está disponible.")


def entra_connection_factory(
    server: str, database: str, credential_provider: Callable[[], Any]
) -> ConnectionFactory:
    """Connection factory authenticated with a Microsoft Entra access token. The credential
    and the driver are created on first connect, so building a store needs neither."""
    credentials: list[Any] = []

    def connect() -> Any:
        import mssql_python

        if not credentials:
            credentials.append(credential_provider())
        token = credentials[0].get_token(SQL_SCOPE).token.encode("utf-16-le")
        return mssql_python.connect(
            f"Server={server};Database={database};Encrypt=yes;TrustServerCertificate=no;",
            attrs_before={
                ACCESS_TOKEN_ATTRIBUTE: struct.pack(f"<I{len(token)}s", len(token), token)
            },
        )

    return connect


def _missing_certificate_settings(settings: Any) -> list[str]:
    if settings.fabric_sql_credential != "certificate":
        return []
    return [
        name
        for name in ("fabric_tenant_id", "fabric_client_id", "fabric_client_cert_path")
        if not getattr(settings, name)
    ]


def credential_from_settings(settings: Any) -> Any:
    from azure.identity import AzureCliCredential, CertificateCredential, DefaultAzureCredential

    kind = settings.fabric_sql_credential
    if kind == "certificate":
        return CertificateCredential(
            tenant_id=settings.fabric_tenant_id,
            client_id=settings.fabric_client_id,
            certificate_path=str(settings.fabric_client_cert_path),
        )
    if kind == "azure_cli":
        return AzureCliCredential()
    return DefaultAzureCredential()


def build_fabric_sql_store(settings: Any, logical_name: str | None = None) -> FabricSqlVectorStore:
    if not settings.fabric_sql_server or not settings.fabric_sql_database:
        raise AppError(
            ErrorKind.VALIDATION,
            "vector_backend=fabric_sql requiere RAG_DOCS_FABRIC_SQL_SERVER y "
            "RAG_DOCS_FABRIC_SQL_DATABASE.",
        )
    missing = _missing_certificate_settings(settings)
    if missing:
        raise AppError(
            ErrorKind.VALIDATION, f"Faltan ajustes para el certificado: {', '.join(missing)}."
        )
    factory = entra_connection_factory(
        settings.fabric_sql_server,
        settings.fabric_sql_database,
        lambda: credential_from_settings(settings),
    )
    return FabricSqlVectorStore(factory, logical_name or settings.fabric_sql_index)


def contract_store(logical_name: str) -> FabricSqlVectorStore:
    """Live hook for the contract suite (``RAG_DOCS_CONTRACT_LIVE_FACTORY``)."""
    from rag_docs.config import Settings

    return build_fabric_sql_store(Settings(), logical_name)
