---
id: WRK-TASK-058
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
activates: [ARCH-002, DOM-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-057
    relation: depends-on
tags: [service, embeddings, fingerprint, batching]
---

# WRK-TASK-058 — Embedding service

## Objective

Extraer `POST /v1/embeddings` con lote, `input_type=query|passage`, límites y fingerprint.

## Acceptance Criteria

- [ ] Respuesta incluye modelo/revisión, dimensión y normalización efectivos.
- [ ] Batching y límites evitan agotamiento de memoria.
- [ ] Fingerprint incompatible se rechaza explícitamente.
- [ ] Imagen, health checks y contract tests son independientes.

## Evidence

Pendiente.
