---
id: WRK-TASK-062
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
activates: [ARCH-002, DOM-RAG-001, RULE-001, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-088
    relation: depends-on
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

**Estado condicional (ADR-RAG-007, decisión D).** Mismo criterio que `WRK-TASK-061`: frontera síncrona 1:1 sin perfil de escalado propio conocido; extracción supeditada a la evidencia que revise `WRK-TASK-088`.

## Acceptance Criteria

- [ ] Sólo acepta fragmentos autorizados y trazables.
- [ ] Devuelve respuesta estructurada grounded o evidencia insuficiente.
- [ ] Fallback es extractivo, explícito y auditable.
- [ ] Identificadores técnicos deben aparecer literalmente en evidencia citada.

## Evidence

Pendiente.
