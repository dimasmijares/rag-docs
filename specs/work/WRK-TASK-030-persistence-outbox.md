---
id: WRK-TASK-030
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-091
    relation: depends-on
  - id: WRK-TASK-082
    relation: depends-on
  - id: ADR-RAG-008
    relation: depends-on
tags: [postgresql, sqlalchemy, alembic, outbox, ledger]
---

# WRK-TASK-030 — Persistencia y outbox

## Objective

Modelar en PostgreSQL jobs, fuentes, configuración, cursores, auditoría, ledger documental y eventos
outbox mediante SQLAlchemy y Alembic, con el esquema ya preparado para multi-tenant.

## Acceptance Criteria

- [ ] Migraciones crean y revierten el esquema en una base limpia.
- [ ] Job y evento outbox se confirman en una transacción; ninguna transacción abarca PostgreSQL y
      Qdrant o Redis.
- [ ] El esquema nace con `tenant_id` en toda entidad con alcance de tenant, conforme al modelo de
      `WRK-TASK-082`, sin necesidad de una migración transversal posterior.
- [ ] Existe un ledger documental con `document_id`, `content_hash`, `index_fingerprint`, contadores
      y marcas temporales, que sustituye al recorrido de la colección como fuente de qué está
      indexado.
- [ ] Cada job persiste un snapshot de la configuración efectiva con la que se ejecutó.
- [ ] Claves idempotentes y transiciones de estado están restringidas en base de datos.
- [ ] La suite queda separada en unitaria, ejecutable sin infraestructura, e integración con
      PostgreSQL real, y `scripts/verify.ps1` documenta cuál es el gate obligatorio.

## Evidence

Pendiente.
