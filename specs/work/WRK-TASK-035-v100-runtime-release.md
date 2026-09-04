---
id: WRK-TASK-035
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-014
    relation: depends-on
  - id: WRK-TASK-032
    relation: depends-on
tags: [release, v1.0.0, integration, recovery]
---

# WRK-TASK-035 — Release de runtime v1.0.0

## Objective

Validar reinicios, reconciliación, integración completa y consolidar `v1.0.0`.

## Acceptance Criteria

- [ ] E2E reinicia API, Redis y worker sin perder el job ni duplicar efectos.
- [ ] Una prueba de interrupción entre el `ack` del vector store y el commit del ledger demuestra
      convergencia tras el siguiente intento.
- [ ] Compose funciona desde un host sin Python.
- [ ] Rendimiento y errores se comparan con la baseline pública.
- [ ] `WRK-SPEC-006` se consolida antes de la release.

## Evidence

Pendiente.
