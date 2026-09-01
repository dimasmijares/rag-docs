---
id: WRK-PLAN-010
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-010
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v2.5.0, microservices, contracts]
---

# WRK-PLAN-010 — Ocho servicios v2.5.0

## Task Decomposition

`057` fija contratos; `058–060` separan capacidades base; `061–065` extraen retrieval,
grounding y fachadas; `066` endurece comunicaciones y `067` consolida Compose distribuido.

## Gate

Contract tests, autenticación entre servicios, trazas y comportamiento explícito ante fallos.
