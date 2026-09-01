---
id: WRK-TASK-051
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [FEAT-RAG-004, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-018
    relation: depends-on
tags: [sharepoint, downloads, rate-limit, retries]
---

# WRK-TASK-051 — Transferencia segura de SharePoint

## Objective

Endurecer descargas temporales, rate limits, retries, borrado y prueba live opt-in.

## Acceptance Criteria

- [ ] Temporales usan permisos restrictivos y borrado garantizado.
- [ ] Retries respetan `Retry-After`, presupuesto y cancelación.
- [ ] Errores se aíslan por documento sin perder cursor válido.
- [ ] El test live no corre en CI ni persiste credenciales o contenido.

## Evidence

Pendiente.
