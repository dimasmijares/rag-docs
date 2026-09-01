---
id: WRK-TASK-066
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-058
    relation: depends-on
  - id: WRK-TASK-059
    relation: depends-on
  - id: WRK-TASK-060
    relation: depends-on
  - id: WRK-TASK-061
    relation: depends-on
  - id: WRK-TASK-062
    relation: depends-on
  - id: WRK-TASK-063
    relation: depends-on
  - id: WRK-TASK-064
    relation: depends-on
  - id: WRK-TASK-065
    relation: depends-on
tags: [oauth2, timeouts, retries, tracing]
---

# WRK-TASK-066 — Seguridad y resiliencia entre servicios

## Objective

Aplicar client credentials, validación de tokens, timeouts, retries limitados y trazas distribuidas.

## Acceptance Criteria

- [ ] Cada servicio valida audience y permisos de su token.
- [ ] Token de usuario sólo se propaga donde se autoriza contenido.
- [ ] Retries tienen presupuesto y no forman bucles.
- [ ] Caídas parciales producen errores correlacionados y explícitos.

## Evidence

Pendiente.
