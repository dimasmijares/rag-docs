---
id: WRK-TASK-109
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
activates: [FEAT-RAG-002, DOM-RAG-002]
dependencies:
  - id: WRK-TASK-015
    relation: depends-on
  - id: WRK-TASK-108
    relation: depends-on
tags: [fabric, api, jobs, rest]
---

# WRK-TASK-109 — Gateway `JobResource` ↔ job Fabric

## Objective

Exponer la indexación de Fabric con el mismo contrato de jobs de `v1.0.0`.

## File Scope

Incluye un adaptador de lanzamiento de pipeline por REST, la selección por perfil en
`src/rag_docs/api.py` y tests con dobles. Excluye cambios en el contrato `JobResource`.

## Acceptance Criteria

- [ ] En perfil Fabric, `POST /api/index` lanza el pipeline y devuelve `202 JobResource` con el
      estado mapeado.
- [ ] El `200 IndexReport` síncrono se conserva según el Human Checkpoint de `ADR-RAG-008`.
- [ ] Errores de autenticación o capacidad se mapean a estados de job explícitos.

## Evidence

Pendiente.
