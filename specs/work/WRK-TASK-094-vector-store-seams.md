---
id: WRK-TASK-094
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [ARCH-002, FEAT-RAG-001, DOC-RAG-002, RULE-003, RULE-004]
dependencies:
  - id: ADR-RAG-013
    relation: depends-on
tags: [vector-store, contracts, ports, refactor, fabric]
---

# WRK-TASK-094 — Costuras de store y factoría por backend

## Objective

Unificar los dos protocolos de store en `rag_docs.contracts` y quitar el acoplamiento a Qdrant del
contenedor y de la migración, sin cambiar el comportamiento observable con Qdrant.

## File Scope

Incluye `src/rag_docs/contracts/**`, `src/rag_docs/vector_store.py`, `src/rag_docs/container.py`,
`src/rag_docs/config.py`, el módulo de migración/publicación y sus tests. Excluye cualquier backend
nuevo, cambios de payload o de fingerprint y la API HTTP.

## Acceptance Criteria

- [ ] `VectorStorePort` es el único protocolo de store e incluye `prune_document` y `scan_chunks`;
      `vector_store.VectorStore` desaparece o es un alias del puerto.
- [ ] `IndexPublicationPort` expone alias lógico, fingerprint vigente, publicación y rollback.
- [ ] `Settings.vector_backend` (por defecto `qdrant`) selecciona la implementación en una factoría
      del contenedor.
- [ ] `migrate_and_publish` y `rollback_alias` operan sobre los puertos, sin
      `isinstance(QdrantVectorStore)`.
- [ ] La suite existente pasa sin cambios de comportamiento y `scripts/verify.ps1` sigue en verde.

## Evidence

Pendiente.
