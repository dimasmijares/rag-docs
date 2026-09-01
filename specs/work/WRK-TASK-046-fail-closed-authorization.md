---
id: WRK-TASK-046
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
activates: [DOM-RAG-002, FEAT-RAG-003, RULE-003]
dependencies:
  - id: WRK-TASK-043
    relation: depends-on
  - id: WRK-TASK-045
    relation: depends-on
tags: [authorization, fail-closed, retrieval, qdrant]
---

# WRK-TASK-046 — Autorización previa al retrieval

## Objective

Calcular un ámbito fail-closed y aplicarlo obligatoriamente en la consulta a Qdrant.

## Acceptance Criteria

- [ ] Sin principal o política válida no se consulta el índice.
- [ ] Tenant y ACL forman parte del filtro del vector store.
- [ ] Errores no revelan existencia documental.
- [ ] Ningún caller puede omitir el filtro autorizado.

## Evidence

Pendiente.
