---
id: WRK-TASK-057
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-010
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-056
    relation: depends-on
  - id: WRK-TASK-083
    relation: depends-on
tags: [contracts, openapi, errors, idempotency]
---

# WRK-TASK-057 — Contratos HTTP de servicios

## Objective

Exponer sobre transporte HTTP `/v1` los puertos y objetos de valor ya estabilizados en
`WRK-TASK-083`, sin redefinirlos.

## Acceptance Criteria

- [ ] Los esquemas `/v1` derivan de los DTO de `rag_docs.contracts`; ninguna forma de dato se
      redefine en la capa de transporte.
- [ ] Contratos públicos e internos tienen compatibilidad y ownership explícitos.
- [ ] La taxonomía `ErrorKind` se mapea a códigos HTTP de forma única y documentada.
- [ ] IDs de correlación e idempotencia atraviesan llamadas y jobs entre procesos.
- [ ] Contract tests detectan breaking changes.

## Evidence

Pendiente.
