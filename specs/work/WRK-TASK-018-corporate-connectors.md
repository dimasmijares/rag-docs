---
id: WRK-TASK-018
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-050
    relation: depends-on
tags: [sharepoint, connectors, incremental-sync, permissions]
---

# WRK-TASK-018 — Conector SharePoint/Microsoft Graph

## Objective

Implementar sobre el SDK un adaptador opcional de SharePoint/Microsoft Graph probado con dobles.

## Acceptance Criteria

- [ ] Identidad estable, URI, versión, fecha, hash y ACL preservados.
- [ ] Sincronización incremental, bajas y movimientos comprobados.
- [ ] CI usa un servidor simulado y no requiere credenciales reales.
- [ ] La prueba live es opt-in y consume secretos exclusivamente locales.

## Evidence

Pendiente.
