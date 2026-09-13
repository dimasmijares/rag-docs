---
id: WRK-TASK-108
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
activates: [FEAT-RAG-002, DOC-RAG-003, RULE-002]
dependencies:
  - id: WRK-TASK-107
    relation: depends-on
tags: [fabric, activator, pipeline, idempotency]
---

# WRK-TASK-108 — Orquestación por eventos y calendario

## Objective

Indexar automáticamente al crear ficheros y periódicamente, tolerando eventos duplicados.

## File Scope

Incluye la regla de Activator, los pipelines en `fabric/` y su documentación. Excluye el gateway
HTTP de jobs.

## Acceptance Criteria

- [ ] Un evento `FileCreated` lanza el pipeline y los duplicados no duplican efectos (clave de
      efecto).
- [ ] El borrado de huérfanos sólo ocurre en el pipeline de snapshot completo programado.
- [ ] Ni parámetros ni logs del pipeline contienen contenido documental.

## Evidence

Pendiente.
