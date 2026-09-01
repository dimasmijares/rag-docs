---
id: WRK-TASK-064
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-004, RULE-003]
dependencies:
  - id: WRK-TASK-057
    relation: depends-on
  - id: WRK-TASK-032
    relation: depends-on
tags: [service, index-api, jobs, sources]
---

# WRK-TASK-064 — Index API

## Objective

Extraer la fachada autenticada de fuentes, jobs, cancelación y reintento.

## Acceptance Criteria

- [ ] Mantiene los contratos públicos de jobs y fuentes.
- [ ] Aplica tenant y permisos administrativos.
- [ ] Sólo persiste estado y outbox; no procesa documentos.
- [ ] Operaciones idempotentes conservan claves del cliente.

## Evidence

Pendiente.
