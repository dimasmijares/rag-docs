---
id: WRK-TASK-032
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002]
dependencies:
  - id: WRK-TASK-084
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
- [ ] Jobs abandonados se recuperan por expiración de lease o fallan de forma auditable.
- [ ] Cancelación y retry respetan la máquina de estados y se evalúan en las fronteras entre
      documentos, no dentro del procesamiento de uno.
- [ ] El reconciliador compara el ledger documental contra el vector store, nunca al revés.

## Evidence

Pendiente.
