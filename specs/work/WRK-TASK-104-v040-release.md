---
id: WRK-TASK-104
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: high
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-093
    relation: depends-on
  - id: WRK-TASK-094
    relation: depends-on
  - id: WRK-TASK-095
    relation: depends-on
  - id: WRK-TASK-096
    relation: depends-on
  - id: WRK-TASK-097
    relation: depends-on
  - id: WRK-TASK-098
    relation: depends-on
  - id: WRK-TASK-099
    relation: depends-on
  - id: WRK-TASK-100
    relation: depends-on
  - id: WRK-TASK-101
    relation: depends-on
  - id: WRK-TASK-102
    relation: depends-on
  - id: WRK-TASK-103
    relation: depends-on
tags: [release, v0.4.0, consolidation]
---

# WRK-TASK-104 — Consolidación de la release v0.4.0

## Objective

Consolidar conocimiento, documentación y Evidence de `v0.4.0` y cerrar `WRK-SPEC-013`.

## File Scope

Incluye `README.md`, `specs/documentation/DOC-RAG-001-*`, `DOC-RAG-003-*`, `WRK-SPEC-013`,
`WRK-PLAN-013` y sus tareas, y el bump de versión del proyecto. Excluye funcionalidad nueva.

## Acceptance Criteria

- [x] README y `DOC-RAG-001`/`DOC-RAG-003` documentan el perfil Fabric opcional y que el quickstart
      no lo necesita.
- [x] Criterios y Evidence de `WRK-SPEC-013` están completos.
- [x] Spec, plan y tareas quedan archivados conservando Evidence.
- [x] La versión del proyecto pasa a `0.4.0` y `scripts/verify.ps1` cierra en verde.

## Evidence

- **`README.md`:**
  - release `v0.4.0`;
  - campos aditivos de `GET /api/sources`;
  - clave de comparabilidad con backend y modo, y verificación de fingerprint en `rag-docs-eval`;
  - backends vectoriales tras puertos con suite de contrato;
  - nueva sección "Perfil opcional Microsoft Fabric" con sus cuatro puntos de entrada, resultados
    medidos y la advertencia de que el quickstart, la demo y `scripts/verify.ps1` no lo necesitan.
- **`DOC-RAG-001` 1.5.0:** definición ampliada, nuevo criterio sobre el perfil opcional y Evidence
  de esta tarea.
- **`DOC-RAG-003` 1.0.0 (`active`):** declaración explícita de perfil opcional sin impacto en
  quickstart, demo, verify ni CI, cobertura de `v0.4.0` y lo que queda para `v1.1.0` (worker de
  inferencia y monitorización de capacidad, `WRK-PLAN-014`).
- **Cierre KDD:**
  - `WRK-SPEC-013` con los 8 criterios marcados y Evidence por criterio con enlaces a PRs, y
    `WRK-PLAN-013` con tabla de estado final y Evidence del gate; ambos `archived`.
  - `WRK-TASK-093` a `WRK-TASK-103` pasan de `completed` a `archived` sin tocar su Evidence.
    `WRK-TASK-104` queda `completed`, igual que `WRK-TASK-091` en `v0.3.0`.
  - `scripts/check-kdd-lifecycle.ps1` válido.
- **Versión `0.4.0`:** `pyproject.toml`, `rag_docs.__version__`, OpenAPI (test
  `test_openapi_declares_release_version`) y `uv.lock` regenerado con `uv lock`.
- `scripts/verify.ps1` en verde y gate público superado.
