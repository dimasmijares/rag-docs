---
id: WRK-TASK-061
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-010
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-003, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-088
    relation: depends-on
  - id: WRK-TASK-058
    relation: depends-on
  - id: WRK-TASK-060
    relation: depends-on
tags: [service, retrieval, qdrant, authorization]
---

# WRK-TASK-061 — Retrieval service

## Objective

Extraer `POST /v1/retrieve`, consultar autorización y Qdrant y devolver sólo hits permitidos.

**Estado condicional (ADR-RAG-007, decisión D).** Es una llamada síncrona 1:1 en la ruta de petición con ciclo de vida compartido con `query-api` y `context-grounding-service`; por defecto permanece en el mismo desplegable salvo que `WRK-TASK-088` mida escalado divergente sobre la evidencia de `WRK-TASK-055`.

## Acceptance Criteria

- [ ] Top-k y filtros del cliente se limitan por política del servidor.
- [ ] Autorización precede a embedding y búsqueda documental.
- [ ] Hits conservan scores, provenance y fingerprint.
- [ ] Fallos de authz o Qdrant producen errores explícitos sin fallback inseguro.

## Evidence

Pendiente.
