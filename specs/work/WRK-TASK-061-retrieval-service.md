---
id: WRK-TASK-061
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
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-003, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-058
    relation: depends-on
  - id: WRK-TASK-060
    relation: depends-on
tags: [service, retrieval, qdrant, authorization]
---

# WRK-TASK-061 — Retrieval service

## Objective

Extraer `POST /v1/retrieve`, consultar autorización y Qdrant y devolver sólo hits permitidos.

## Acceptance Criteria

- [ ] Top-k y filtros del cliente se limitan por política del servidor.
- [ ] Autorización precede a embedding y búsqueda documental.
- [ ] Hits conservan scores, provenance y fingerprint.
- [ ] Fallos de authz o Qdrant producen errores explícitos sin fallback inseguro.

## Evidence

Pendiente.
