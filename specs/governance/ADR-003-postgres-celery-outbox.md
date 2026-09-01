---
id: ADR-003
type: adr
layer: adr
scope: persistent
status: accepted
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-002
    relation: implements
  - id: DOM-RAG-002
    relation: constrained-by
tags: [architecture-decision, postgres, redis, celery, outbox]
---

# ADR-003 — PostgreSQL, Redis/Celery y patrón outbox

## Context

La indexación puede durar minutos y debe sobrevivir a reinicios sin depender de la memoria de la
API o del broker.

## Decision

PostgreSQL será la fuente de verdad de jobs, fuentes, configuración, cursores y auditoría. Celery
sobre Redis transportará sólo identificadores. La creación de job y evento outbox será
transaccional; un dispatcher publicará de forma reintentable y el worker será idempotente.

## Consequences

Se añade operación de dos dependencias, migraciones y reconciliación, a cambio de durabilidad y
semántica explícita ante fallos.
