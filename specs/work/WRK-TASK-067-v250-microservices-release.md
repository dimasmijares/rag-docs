---
id: WRK-TASK-067
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-066
    relation: depends-on
tags: [release, v2.5.0, compose, contracts, chaos]
---

# WRK-TASK-067 — Release de microservicios v2.5.0

## Objective

Validar Compose distribuido, contract tests y chaos tests y consolidar ocho servicios.

## Acceptance Criteria

- [ ] Cada imagen y contrato `/v1` supera health y contract tests.
- [ ] Fallos parciales no causan filtraciones ni reintentos infinitos.
- [ ] El E2E conserva API pública y calidad de respuesta.
- [ ] `WRK-SPEC-010` se consolida antes de la release.

## Evidence

Pendiente.
