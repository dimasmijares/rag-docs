---
id: WRK-TASK-103
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
activates: [DOC-RAG-003, RULE-002]
dependencies:
  - id: WRK-TASK-102
    relation: depends-on
tags: [fabric, power-bi, pbip, evaluation]
---

# WRK-TASK-103 — Informe Power BI de calidad

## Objective

Visualizar la calidad del retrieval y de las respuestas por perfil, backend, corpus y fingerprint.

## File Scope

Incluye el informe y modelo semántico PBIP/TMDL en `fabric/` y su documentación. Excluye páginas
operativas de indexación y cola (`WRK-TASK-114`).

## Acceptance Criteria

- [ ] El informe se versiona como PBIP y pasa el gate público.
- [ ] El modelo usa Direct Lake sobre las tablas Delta de `WRK-TASK-102`.
- [ ] Las métricas se filtran por perfil, backend, `corpus_version` y fingerprint, y la latencia se
      muestra segregada por backend.

## Evidence

Pendiente.
