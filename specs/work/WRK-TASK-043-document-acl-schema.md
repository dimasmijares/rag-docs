---
id: WRK-TASK-043
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [DOM-RAG-002, FEAT-RAG-003, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-017
    relation: depends-on
  - id: WRK-TASK-036
    relation: depends-on
tags: [tenant, acl, classification, qdrant]
---

# WRK-TASK-043 — Esquema de tenant y ACL

## Objective

Propagar tenant, ACL y clasificación por fuentes, documentos, chunks, PostgreSQL y Qdrant.

## Acceptance Criteria

- [ ] Herencia se normaliza antes de indexar.
- [ ] Todo chunk contiene tenant y política aplicable.
- [ ] Colecciones anteriores se reconstruyen con nuevo fingerprint.
- [ ] Migraciones y tests cubren cambios, bajas y revocaciones.

## Evidence

Pendiente.
