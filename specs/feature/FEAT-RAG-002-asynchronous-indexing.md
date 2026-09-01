---
id: FEAT-RAG-002
type: spec
layer: feature
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: FEAT-RAG-001
    relation: extends
  - id: ARCH-002
    relation: implements
  - id: DOM-RAG-002
    relation: constrained-by
tags: [feature, indexing, jobs, asynchronous]
---

# FEAT-RAG-002 — Indexación asíncrona

## Intent

Permitir crear, consultar, cancelar, reintentar y recuperar jobs de indexación sin bloquear la
API ni perder estado ante reinicios.

## Definition

`POST /api/index` devuelve `202 JobResource`. La API confirma el job y un evento outbox en una
misma transacción. El dispatcher publica sólo `job_id`; un worker idempotente recupera la
configuración desde PostgreSQL, procesa la fuente y actualiza progreso y cursores.

## Acceptance Criteria

- Reiniciar API, broker o worker no pierde el job.
- Cancelación y reintento tienen estados y errores explícitos.
- El scheduler evita solapamientos y recupera jobs huérfanos.
- El contenido documental nunca circula por Redis.
