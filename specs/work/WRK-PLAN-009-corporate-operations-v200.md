---
id: WRK-PLAN-009
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-009
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v2.0.0, connectors, observability, resilience]
---

# WRK-PLAN-009 — Operación corporativa v2.0.0

## Task Decomposition

`050 → 018 → 051` desarrolla conectores y `050 → 087` fija sus controles de publicación;
`019 → 052` instrumenta y despliega observabilidad; `053/054` endurecen operación y
`055 → 088 → 056` valida SLO y fallos y decide con evidencia el alcance de `v2.5.0`.

## Gate

Conector simulado en CI, observabilidad privada, restore probado, capacidad documentada y alcance
de extracción de servicios decidido con evidencia.
