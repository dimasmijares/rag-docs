---
id: WRK-TASK-028
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-025
    relation: depends-on
tags: [ci, github-actions, secrets, dependencies]
---

# WRK-TASK-028 — Gates de GitHub Actions

## Objective

Automatizar KDD, Ruff, tests, secret scan, auditoría de dependencias y política de datos públicos.

## Acceptance Criteria

- [ ] Pull requests ejecutan todos los checks sin secretos corporativos.
- [ ] Un fixture privado o una ruta/IP prohibida hace fallar el pipeline.
- [ ] Dependencias y acciones están fijadas y auditadas.
- [ ] Los checks son reutilizables por releases posteriores.

## Evidence

Pendiente.
