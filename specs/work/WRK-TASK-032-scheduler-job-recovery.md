---
id: WRK-TASK-032
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002]
dependencies:
  - id: WRK-TASK-031
    relation: depends-on
tags: [scheduler, cursor, retry, recovery]
---

# WRK-TASK-032 — Scheduler y recuperación de jobs

## Objective

Añadir programaciones, cursores, reintentos acotados, cancelación cooperativa y reconciliación de
jobs huérfanos.

## Acceptance Criteria

- [ ] Programaciones incompatibles no se solapan.
- [ ] Un cursor sólo avanza tras finalizar correctamente.
- [ ] Jobs abandonados se recuperan o fallan de forma auditable.
- [ ] Cancelación y retry respetan la máquina de estados.

## Evidence

Pendiente.
