---
id: WRK-TASK-033
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-030
    relation: depends-on
tags: [configuration, models, stateless-api]
---

# WRK-TASK-033 — Configuración persistente

## Objective

Persistir fuentes y perfiles de modelos para que la API no dependa de estado mutable local.

## Acceptance Criteria

- [ ] Configuración versionada se valida antes de activarse.
- [ ] Secretos se referencian, nunca se almacenan en claro.
- [ ] Varias réplicas observan una configuración efectiva coherente.
- [ ] El flujo local sencillo conserva valores por defecto explícitos.

## Evidence

Pendiente.
