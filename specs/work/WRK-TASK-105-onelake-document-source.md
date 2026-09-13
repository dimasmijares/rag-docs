---
id: WRK-TASK-105
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-014
activates: [DOM-RAG-001, FEAT-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-101
    relation: depends-on
tags: [fabric, onelake, source]
---

# WRK-TASK-105 — Fuente documental OneLake

## Objective

Descubrir documentos del Lakehouse como `DocumentSourcePort` con identidad y provenance equivalentes
a la fuente local.

## File Scope

Incluye un adaptador de fuente en `src/rag_docs/` sobre el montaje `/lakehouse/default/Files` y sus
tests. Excluye indexación y orquestación.

## Acceptance Criteria

- [ ] `relative_path` y `document_id` coinciden con los que produce la fuente local para el mismo
      árbol.
- [ ] `original_uri` apunta a la ruta OneLake sin identificadores de workspace versionados.
- [ ] `discover()` declara si el snapshot es completo (`ADR-RAG-008`).

## Evidence

Pendiente.
