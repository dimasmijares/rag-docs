---
id: WRK-TASK-063
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-010
activates: [ARCH-002, FEAT-RAG-001, FEAT-RAG-003, RULE-001, RULE-003]
dependencies:
  - id: WRK-TASK-088
    relation: depends-on
  - id: WRK-TASK-062
    relation: depends-on
tags: [service, api, facade, orchestration]
---

# WRK-TASK-063 — Query API

## Objective

Extraer la fachada pública que autentica, valida y orquesta retrieval y grounding.

**Estado condicional (ADR-RAG-007, decisión D).** `query-api` vive con `retrieval-service` y `context-grounding-service` como un único desplegable por defecto; sólo se separa si `WRK-TASK-088` encuentra evidencia de escalado o de despliegue divergente.

## Acceptance Criteria

- [ ] Conserva compatibilidad de `POST /api/query`.
- [ ] Propaga identidad sólo a servicios que la necesitan.
- [ ] No accede directamente a Qdrant ni a modelos.
- [ ] Health checks distinguen liveness y readiness.

## Evidence

Pendiente.
