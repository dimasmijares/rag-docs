---
id: WRK-TASK-100
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [ARCH-002, FEAT-RAG-001, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-094
    relation: depends-on
  - id: WRK-TASK-096
    relation: depends-on
  - id: WRK-TASK-099
    relation: depends-on
  - id: ADR-RAG-013
    relation: depends-on
tags: [fabric, sql, vector-store, fingerprint, acl]
---

# WRK-TASK-100 — `FabricSqlVectorStore`

## Objective

Implementar los puertos de store y publicación sobre SQL database in Fabric con las mismas garantías
de fingerprint, ámbito y ACL que Qdrant.

## File Scope

Incluye un adaptador nuevo en `src/rag_docs/` (store Fabric SQL y DDL), el registro en la factoría,
`scripts/verify-fabric.ps1` y el enganche live de la suite de contrato, y la actualización del
enforcement descrito en `RULE-003` y `RULE-004`. Excluye ledger, jobs e indexación en Spark.

## Acceptance Criteria

- [x] El DDL crea una tabla física por fingerprint, subjects ACL en tabla hija, tabla de alias e
      índices necesarios.
- [x] La búsqueda aplica el prefiltro de ámbito antes de `TOP k` y devuelve `score = 1 − distancia
      coseno`.
- [x] La autenticación usa Entra ID sin secretos en el repositorio y los errores se mapean a
      `ErrorKind`.
- [x] La suite de contrato de `WRK-TASK-096` pasa en `scripts/verify-fabric.ps1`; el gate por
      defecto no la exige.
- [x] `RULE-003` y `RULE-004` describen el enforcement en ambos backends.

## Evidence

- `src/rag_docs/fabric_sql_store.py`: `FabricSqlVectorStore` implementa `VectorStorePort` e
  `IndexPublicationPort`. DDL idempotente:
  - `dbo.rag_index_alias` (alias lógico → índice físico) y `dbo.rag_index_physical` (catálogo con
    dimensión).
  - Por fingerprint, `dbo.[<lógico>__<digest>__chunks]`: ids `VARCHAR(64)`, columnas de ámbito,
    `payload` JSON y `embedding VECTOR(n)`, con índices por ámbito, documento y fuente.
  - `dbo.[<lógico>__<digest>__acl]` como tabla hija con PK `(chunk_id, subject)` e índice por
    subject.
  - Los nombres lógicos y físicos se validan como identificadores seguros antes de interpolarse.
- Búsqueda exacta: `VECTOR_DISTANCE('cosine')`, con tenant, clasificación (`OPENJSON`) y
  `EXISTS` sobre la tabla ACL en el `WHERE`, antes de `TOP (k)`. Devuelve
  `score = 1.0 - distancia`, ordenado por distancia y `chunk_id`, con umbral opcional. Un ámbito sin
  subjects o sin clasificaciones devuelve vacío sin consultar.
- Semántica idéntica a Qdrant:
  - vinculación obligatoria del fingerprint y rechazo de reutilizar un índice con otro fingerprint;
  - fallo `VALIDATION` si el alias se movió;
  - candidato directo invisible hasta publicar;
  - `publish_alias` con un `MERGE ... WITH (HOLDLOCK)` transaccional;
  - `rollback_alias` con `NOT_FOUND` fuera de ventana y `delete_physical` que no borra el objetivo
    del alias;
  - `update_acl` reescribe columnas de ámbito, payload y filas ACL sin tocar `embedding`.
- Autenticación Entra, sin secretos:
  - token de acceso de `azure-identity` pasado a `mssql-python` como atributo previo a la conexión
    (1256);
  - `Settings.fabric_sql_credential` (`default`, `azure_cli` o `certificate`), con servidor, base
    de datos e identidades en el `.env` local;
  - driver y credencial se crean al primer uso, así que construir el store no los importa.
- Errores: fallos de identidad o permiso → `AUTHORIZATION`, timeouts → `TIMEOUT`, resto →
  `DEPENDENCY_UNAVAILABLE`, siempre con mensajes genéricos que no filtran servidor, usuario ni
  texto del driver.
- Factoría: `Settings.vector_backend` admite `fabric_sql` y `container.VECTOR_STORE_FACTORIES` lo
  construye de forma perezosa. Extra `[fabric]`: `azure-identity` + `mssql-python`, con `uv.lock`
  regenerado.
- `scripts/verify-fabric.ps1 -EnvFile <fabric.env>`:
  - resuelve servidor y base de datos por REST (`fabric_api.py sql-connection`, escrito en el
    fichero local sin imprimirlo);
  - autentica como service principal con certificado y ejecuta `pytest tests/contract -m live` con
    `RAG_DOCS_CONTRACT_LIVE_FACTORY=rag_docs.fabric_sql_store:contract_store`;
  - restaura las variables de entorno al terminar.

  La fixture live llama a `drop_logical_index()` tras cada test.
- Resultado live (2026-09-13, SQL database `ragdocs_vectors`, identidad service principal con rol
  Contributor): `11 passed, 11 deselected`. Comprobado después que no quedan tablas `contract_*`
  ni filas en el alias o el catálogo.
- Gate por defecto, sin Fabric: `tests/test_fabric_sql_store.py` cubre la selección en factoría sin
  conectar, los ajustes que faltan, los nombres inseguros, el fail-closed sin consultar, el rechazo
  sin fingerprint vinculado y el mapeo de errores sin fuga. `scripts/verify.ps1` en verde sin el
  extra `[fabric]`.
- `RULE-003` 0.3.0 y `RULE-004` 0.3.0 describen el enforcement en Qdrant y Fabric SQL;
  `tests/contract/README.md` documenta el gate live.
