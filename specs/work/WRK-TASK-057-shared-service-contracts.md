---
id: WRK-TASK-057
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-010
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-056
    relation: depends-on
tags: [contracts, openapi, errors, idempotency]
---

# WRK-TASK-057 — Contratos compartidos de servicios

## Objective

Versionar esquemas, errores, correlación, autenticación e idempotencia para las interfaces `/v1`.

## Acceptance Criteria

- [ ] Contratos públicos e internos tienen compatibilidad y ownership explícitos.
- [ ] Errores distinguen validación, autorización, dependencia y disponibilidad.
- [ ] IDs de correlación e idempotencia atraviesan llamadas y jobs.
- [ ] Contract tests detectan breaking changes.

## Evidence

Pendiente.
