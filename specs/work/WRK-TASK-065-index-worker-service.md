---
id: WRK-TASK-065
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-004, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-058
    relation: depends-on
  - id: WRK-TASK-064
    relation: depends-on
tags: [service, worker, celery, indexing]
---

# WRK-TASK-065 — Index worker

## Objective

Aislar el consumidor Celery que descubre, extrae, chunkifica, embebe y actualiza Qdrant.

## Acceptance Criteria

- [ ] Consume sólo `job_id` y recupera configuración autorizada.
- [ ] Usa embedding-service y verifica fingerprint.
- [ ] Cancelación y reintentos son idempotentes.
- [ ] Montajes de fuentes son read-only cuando el conector lo permite.

## Evidence

Pendiente.
