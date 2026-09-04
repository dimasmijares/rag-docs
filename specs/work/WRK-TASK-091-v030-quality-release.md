---
id: WRK-TASK-091
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-082
    relation: depends-on
  - id: WRK-TASK-086
    relation: depends-on
  - id: WRK-TASK-038
    relation: depends-on
  - id: WRK-TASK-092
    relation: depends-on
tags: [release, v0.3.0, integration, consolidation]
---

# WRK-TASK-091 — Release de invariantes y calidad v0.3.0

## Objective

Validar de extremo a extremo los invariantes introducidos, consolidar `WRK-SPEC-012` y publicar
`v0.3.0` como baseline sobre la que se decide la industrialización.

## Acceptance Criteria

- [ ] Una migración de colección completa se ejecuta y se revierte con el corpus sintético.
- [ ] El informe de calidad compara dense, hybrid y reranking sobre una baseline declarada
      comparable, con decisión de adopción registrada.
- [ ] El README y `DOC-RAG-001` describen el fingerprint, el ámbito obligatorio y la política de
      comparabilidad.
- [ ] `WRK-SPEC-012` se consolida y sus tareas se archivan conservando Evidence antes del tag.
- [ ] `scripts/verify.ps1` queda verde sin requerir infraestructura adicional a la de `v0.2.0`.

## Evidence

Pendiente.
