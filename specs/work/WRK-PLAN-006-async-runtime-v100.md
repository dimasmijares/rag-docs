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

`030 → 015 → 031 → 032`, con `033` tras `030`; `016` integra `031/033`, `034` depende de
`015`, `014` valida `016/034` y `035` consolida `014/032`.

## Gate

Jobs durables, mensajes sin documentos y Compose completo sin Python en el host.
