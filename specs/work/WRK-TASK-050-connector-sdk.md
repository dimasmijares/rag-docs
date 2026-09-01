---
id: WRK-TASK-050
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-004, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-049
    relation: depends-on
tags: [connectors, sdk, cursor, acl]
---

# WRK-TASK-050 — SDK de conectores

## Objective

Definir un contrato para identidad, versión, cursor, hash, ACL, paginación y descarga.

## Acceptance Criteria

- [ ] `local_folder` se adapta sin perder comportamiento.
- [ ] Cursor y versión soportan altas, cambios, bajas y movimientos.
- [ ] ACL y tenant son obligatorios en fuentes corporativas.
- [ ] Contract tests permiten certificar nuevos adaptadores.

## Evidence

Pendiente.
