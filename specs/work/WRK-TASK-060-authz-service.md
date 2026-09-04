---
id: WRK-TASK-060
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, RULE-003]
dependencies:
  - id: WRK-TASK-088
    relation: depends-on
  - id: WRK-TASK-057
    relation: depends-on
  - id: WRK-TASK-045
    relation: depends-on
tags: [service, authorization, policy, search-scope]
---

# WRK-TASK-060 — Authz service

## Objective

Extraer `POST /v1/search-scope` como punto de decisión de políticas sin devolver información
documental.

**Estado condicional (ADR-RAG-007, decisión D).** Se promueve a servicio si y sólo si `WRK-TASK-088` concluye que la política de autorización deja de ser evaluable en proceso. Por defecto permanece como contrato interno (`AuthorizationPort` de `ADR-RAG-010`) dentro del mismo desplegable.

## Acceptance Criteria

- [ ] Valida el token de usuario y produce filtros mínimos.
- [ ] Denegación o indisponibilidad se comportan fail-closed.
- [ ] Respuesta no contiene títulos, IDs ni existencia documental.
- [ ] Auditoría registra decisión y política sin claims innecesarios.

## Evidence

Pendiente.
