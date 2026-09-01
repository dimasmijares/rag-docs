---
id: WRK-TASK-005
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-25
owner: rag-docs-team
parent: WRK-PLAN-001
activates: [FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-004
    relation: depends-on
tags: [api, web]
---

# WRK-TASK-005 — API y web

## Objective

Exponer los contratos HTTP y una interfaz estática accesible para la PoC.

## Scope

Incluye esquemas API, composición de dependencias, endpoints y recursos web. Excluye autenticación.

## Acceptance Criteria

- [ ] Los tres endpoints devuelven esquemas estables y errores accionables.
- [ ] La web consulta, indexa y muestra citas y localizadores.

## Test Plan

Tests de contrato con dependencias sustituidas y smoke test de `/`.

## Evidence

Contratos de fuentes, indexación, consulta y carga de la web superados mediante TestClient.

## Traceability

Implementado en `api.py`, `container.py` y `static/`.
