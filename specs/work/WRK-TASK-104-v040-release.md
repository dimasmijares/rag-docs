---
id: WRK-TASK-104
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

- [ ] README y `DOC-RAG-001`/`DOC-RAG-003` documentan el perfil Fabric opcional y que el quickstart
      no lo necesita.
- [ ] Criterios y Evidence de `WRK-SPEC-013` están completos.
- [ ] Spec, plan y tareas quedan archivados conservando Evidence.
- [ ] La versión del proyecto pasa a `0.4.0` y `scripts/verify.ps1` cierra en verde.

## Evidence

Pendiente.
