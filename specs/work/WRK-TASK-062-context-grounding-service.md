---
id: WRK-TASK-062
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
activates: [ARCH-002, DOM-RAG-001, RULE-001, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-059
    relation: depends-on
  - id: WRK-TASK-061
    relation: depends-on
tags: [service, context, grounding, fallback]
---

# WRK-TASK-062 — Context-grounding service

## Objective

Extraer `POST /v1/answer`, construir contexto autorizado, invocar el modelo y validar citas,
idioma y completitud.

## Acceptance Criteria

- [ ] Sólo acepta fragmentos autorizados y trazables.
- [ ] Devuelve respuesta estructurada grounded o evidencia insuficiente.
- [ ] Fallback es extractivo, explícito y auditable.
- [ ] Identificadores técnicos deben aparecer literalmente en evidencia citada.

## Evidence

Pendiente.
