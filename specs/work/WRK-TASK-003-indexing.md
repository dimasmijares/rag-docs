---
id: WRK-TASK-003
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-25
owner: rag-docs-team
parent: WRK-PLAN-001
activates: [ARCH-001, DOM-RAG-001]
dependencies:
  - id: WRK-TASK-002
    relation: depends-on
tags: [chunking, embeddings, qdrant]
---

# WRK-TASK-003 — Indexación incremental

## Objective

Crear chunks estructurales, embeddings y sincronización de altas, cambios y bajas en Qdrant.

## Scope

Incluye chunking, adaptador de embeddings, vector store y servicio de indexación. Excluye generación.

## Acceptance Criteria

- [ ] Los IDs son deterministas y una segunda indexación sin cambios no recalcula.
- [ ] Cambios y borrados sustituyen o eliminan todos los chunks del documento.

## Test Plan

Pruebas de chunking e incrementalidad con adaptadores en memoria.

## Evidence

Pruebas de solape, metadatos, alta, no cambio, actualización, baja y fallo temporal superadas; adaptador Qdrant verificado en memoria.

## Traceability

Implementado en `chunking.py`, `embeddings.py`, `vector_store.py` e `indexing.py`.
