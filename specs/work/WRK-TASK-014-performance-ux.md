---
id: WRK-TASK-014
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
activates: [ARCH-002, FEAT-RAG-001, FEAT-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-016
    relation: depends-on
  - id: WRK-TASK-034
    relation: depends-on
tags: [performance, batching, cache, jobs]
---

# WRK-TASK-014 — Rendimiento y experiencia de uso

## Objective

Reducir espera y hacer observable el progreso sin comprometer corrección.

## File Scope

Incluye embeddings por lotes, concurrencia limitada, cachés versionadas, progreso y métricas.
Excluye streaming, feedback y conversación, que se implementan en `WRK-TASK-041`.

## Acceptance Criteria

- [ ] Se establecen baselines de indexación y consulta con p50/p95.
- [ ] La indexación larga expone progreso y no bloquea una petición HTTP.
- [ ] Las cachés se invalidan por versión de índice, modelo y prompt.
- [ ] Toda caché posterior al retrieval se particiona por ámbito de autorización desde su diseño;
      sólo la caché de embeddings de consulta, independiente del principal, se comparte.
- [ ] El benchmark se ejecuta sobre colección dedicada y ledger vacío, y el informe registra si hubo
      reutilización de estado persistente.
- [ ] Una prueba demuestra que la indexación no bloquea las peticiones HTTP.

## Evidence

Pendiente.
