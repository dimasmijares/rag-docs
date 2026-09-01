---
id: WRK-TASK-076
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-011
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-020
    relation: depends-on
  - id: WRK-TASK-054
    relation: depends-on
tags: [rollback, rolling-update, restore, disaster-recovery]
---

# WRK-TASK-076 — Rollback y disaster drill

## Objective

Ensayar rolling update, rollback, backup/restore y pérdida simulada de componentes.

## Acceptance Criteria

- [ ] Rollback recupera una versión compatible sin pérdida silenciosa.
- [ ] Migraciones declaran compatibilidad durante rolling update.
- [ ] Restore completo cumple los objetivos observados.
- [ ] Runbook registra tiempos, decisiones y limitaciones de kind.

## Evidence

Pendiente.
