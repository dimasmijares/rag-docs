---
id: WRK-TASK-019
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-049
    relation: depends-on
tags: [observability, audit, secrets, backups]
---

# WRK-TASK-019 — Instrumentación OpenTelemetry

## Objective

Instrumentar API, jobs, retrieval, embeddings y modelos con trazas y métricas correlacionadas.

## Acceptance Criteria

- [ ] Trazas y métricas cubren retrieval, modelos, jobs y conectores.
- [ ] Propagación de contexto enlaza petición, job y llamadas internas.
- [ ] Preguntas, chunks y respuestas no se incluyen por defecto.
- [ ] La instrumentación funciona sin exigir un backend concreto.

## Evidence

Pendiente.
