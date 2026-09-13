---
id: WRK-TASK-110
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-014
activates: [ARCH-002, DOC-RAG-003, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-100
    relation: depends-on
  - id: ADR-RAG-014
    relation: depends-on
tags: [fabric, queue, worker, ollama, security]
---

# WRK-TASK-110 — Cola de inferencia pull y worker local

## Objective

Permitir que Fabric use el LLM local sin puertos entrantes mediante una cola con leases.

## File Scope

Incluye el DDL de la cola en Fabric SQL, el worker local en `src/rag_docs/`, una suite de contrato
de cola sin infraestructura y la operación en `DOC-RAG-003`. Excluye los usos concretos
(`WRK-TASK-111` a `113`).

## Acceptance Criteria

- [ ] El worker reclama con lease (`UPDLOCK, READPAST`), renueva visibilidad y aplica reintentos con
      backoff y dead-letter.
- [ ] Reprocesar una petición con la misma effect-key produce un único resultado.
- [ ] El worker sólo abre conexiones salientes y se autentica como service principal sin secretos
      versionados.
- [ ] Logs y métricas no contienen prompts, respuestas ni contenido documental.

## Evidence

Pendiente.
