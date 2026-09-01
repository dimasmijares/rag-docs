---
id: WRK-TASK-054
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-030
    relation: depends-on
  - id: WRK-TASK-052
    relation: depends-on
tags: [backup, restore, postgres, qdrant]
---

# WRK-TASK-054 — Backup y restauración

## Objective

Respaldar y restaurar PostgreSQL y Qdrant con versiones y orden consistentes.

## Acceptance Criteria

- [ ] Restore reconstruye jobs, configuración, cursores e índice consultable.
- [ ] Fingerprint y alias se verifican tras restaurar.
- [ ] RPO/RTO observados se registran.
- [ ] El ensayo usa corpus sintético y almacenamiento aislado.

## Evidence

Pendiente.
