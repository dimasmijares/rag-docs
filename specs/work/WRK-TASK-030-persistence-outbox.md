---
id: WRK-TASK-030
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-029
    relation: depends-on
tags: [postgresql, sqlalchemy, alembic, outbox]
---

# WRK-TASK-030 — Persistencia y outbox

## Objective

Modelar en PostgreSQL jobs, fuentes, configuración, cursores, auditoría y eventos outbox mediante
SQLAlchemy y Alembic.

## Acceptance Criteria

- [ ] Migraciones crean y revierten el esquema en una base limpia.
- [ ] Job y evento outbox se confirman en una transacción.
- [ ] Claves idempotentes y transiciones de estado están restringidas.
- [ ] Tests de repositorio usan PostgreSQL real en integración.

## Evidence

Pendiente.
