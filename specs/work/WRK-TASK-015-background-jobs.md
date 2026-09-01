---
id: WRK-TASK-015
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-030
    relation: depends-on
tags: [jobs, scheduler, indexing, operations]
---

# WRK-TASK-015 — API persistente de jobs

## Objective

Exponer recursos persistentes para crear, consultar, cancelar y reintentar jobs de indexación.

## Acceptance Criteria

- [ ] Crear, consultar, cancelar y reintentar jobs idempotentes.
- [ ] `POST /api/index` devuelve `202` y un `JobResource` persistido.
- [ ] Listado y detalle exponen progreso, timestamps y errores estructurados.
- [ ] La API no ejecuta extracción ni embeddings dentro de la petición.

## Evidence

Pendiente.
