---
id: WRK-PLAN-010
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-SPEC-010
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v2.5.0, microservices, contracts, conditional-extraction]
---

# WRK-PLAN-010 — Extracción condicional por frontera v2.5.0

## Task Decomposition

`057` fija el transporte HTTP sobre los puertos ya estabilizados en `WRK-TASK-083`. `058`, `059` y
`065` (embedding-service, model-gateway, index-worker) proceden sin depender de `088`: su motor ya
es demostrable hoy por `ADR-RAG-007`. `060` a `064` (authz-service, retrieval-service,
context-grounding-service, query-api, index-api) dependen de `088`, el gate de decisión que revisa
la evidencia de `WRK-TASK-055` frontera a frontera antes de autorizar su extracción; por defecto
permanecen en un único desplegable. `066` endurece comunicaciones entre lo efectivamente extraído y
`067` consolida el Compose distribuido resultante, que puede ser de tres a ocho servicios según lo
que confirme `088`.

## Gate

Contract tests, autenticación entre servicios, trazas y comportamiento explícito ante fallos —
únicamente sobre las fronteras efectivamente extraídas, sea el mínimo de tres o el conjunto que
`WRK-TASK-088` amplíe con evidencia.
