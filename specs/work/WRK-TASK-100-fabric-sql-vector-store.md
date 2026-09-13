---
id: WRK-TASK-100
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
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

- [ ] El DDL crea una tabla física por fingerprint, subjects ACL en tabla hija, tabla de alias e
      índices necesarios.
- [ ] La búsqueda aplica el prefiltro de ámbito antes de `TOP k` y devuelve `score = 1 − distancia
      coseno`.
- [ ] La autenticación usa Entra ID sin secretos en el repositorio y los errores se mapean a
      `ErrorKind`.
- [ ] La suite de contrato de `WRK-TASK-096` pasa en `scripts/verify-fabric.ps1`; el gate por
      defecto no la exige.
- [ ] `RULE-003` y `RULE-004` describen el enforcement en ambos backends.

## Evidence

Pendiente.
