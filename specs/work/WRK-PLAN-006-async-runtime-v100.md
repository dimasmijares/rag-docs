---
id: WRK-PLAN-006
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-006
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-001, RULE-002, RULE-004]
dependencies: []
tags: [release-plan, v1.0.0, jobs, compose]
---

# WRK-PLAN-006 — Runtime asíncrono v1.0.0

## Task Decomposition

`030 → 015 → 031 → 084 → 032`, con `033` tras `030`; `016` integra `031/033`, `034` depende de
`015`, `014` valida `016/034` y `035` consolida `014/032`.

`030` entra sólo con `v0.3.0` cerrada: depende de `WRK-TASK-091` y del modelo de tenant de
`WRK-TASK-082`, de modo que el esquema nace multi-tenant. `084` fija el contrato de idempotencia
que `031` implementa y del que `032` depende para reconciliar.

## Gate

Jobs durables, mensajes sin documentos, efectos convergentes ante interrupción y Compose completo
sin Python en el host.
