---
id: WRK-TASK-031
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-015
    relation: depends-on
tags: [celery, redis, worker, outbox]
---

# WRK-TASK-031 — Dispatcher y worker Celery

## Objective

Publicar eventos outbox y ejecutar jobs mediante un worker que recibe únicamente `job_id`, dejando
en `WRK-TASK-084` la definición verificable del contrato de idempotencia y reconciliación.

## Acceptance Criteria

- [ ] El dispatcher tolera publicación repetida sin perder jobs.
- [ ] El mensaje Celery no incluye configuración ni texto documental.
- [ ] El worker recupera estado desde PostgreSQL y actualiza progreso.
- [ ] Reentregas no duplican chunks ni efectos finales.
- [ ] La composición del proceso worker es distinta de la de la API: la API no carga el modelo de
      embeddings y el worker no monta recursos estáticos.

## Evidence

Pendiente.
