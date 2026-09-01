---
id: WRK-SPEC-006
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-001, RULE-002, RULE-004]
dependencies:
  - id: WRK-SPEC-005
    relation: depends-on
  - id: ADR-003
    relation: depends-on
tags: [release, v1.0.0, jobs, compose]
---

# WRK-SPEC-006 — Runtime asíncrono v1.0.0

## Proposed Change

Persistir jobs, fuentes y configuración en PostgreSQL; ejecutar indexación con Celery/Redis y
ofrecer API y web de progreso en un Compose que no requiera Python en el host.

## Acceptance Criteria

- [ ] `POST /api/index` devuelve `202 JobResource` y existen consulta, cancelación y reintento.
- [ ] Reinicios de API, Redis o worker no pierden jobs ni duplican efectos.
- [ ] Redis sólo transporta identificadores y PostgreSQL conserva el estado crítico.
- [ ] El Compose completo supera la indexación no bloqueante.

## Evidence

Pendiente de `WRK-PLAN-006`.
