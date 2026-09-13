---
id: WRK-TASK-094
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
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

- [x] `VectorStorePort` es el único protocolo de store e incluye `prune_document` y `scan_chunks`;
      `vector_store.VectorStore` desaparece o es un alias del puerto.
- [x] `IndexPublicationPort` expone alias lógico, fingerprint vigente, publicación y rollback.
- [x] `Settings.vector_backend` (por defecto `qdrant`) selecciona la implementación en una factoría
      del contenedor.
- [x] `migrate_and_publish` y `rollback_alias` operan sobre los puertos, sin
      `isinstance(QdrantVectorStore)`.
- [x] La suite existente pasa sin cambios de comportamiento y `scripts/verify.ps1` sigue en verde.

## Evidence

- `src/rag_docs/contracts/ports.py`: `VectorStorePort` es el único protocolo de store e incorpora
  `prune_document`, `scan_chunks` y `bind_fingerprint`. `vector_store.VectorStore` queda como alias
  (`VectorStore = VectorStorePort`) para los consumidores fuera de scope (`query.py`, `benchmark.py`).
- `IndexPublicationPort` (`runtime_checkable`) expone `logical_name`, `physical_name_for`,
  `published_physical_name` (índice físico del fingerprint vigente, o `None`), `candidate_store`,
  `publish_alias` y `rollback_alias`. `QdrantVectorStore` lo implementa añadiendo `logical_name`,
  `published_physical_name` y `candidate_store`, delegando en la lógica de alias existente.
- `Settings.vector_backend: Literal["qdrant"] = "qdrant"`; `container.build_vector_store` resuelve
  la implementación en `VECTOR_STORE_FACTORIES` y falla con `AppError(VALIDATION)` si un backend no
  tiene factoría. `ApplicationContainer` sólo ve `VectorStorePort`.
- `indexing.migrate_and_publish` trabaja sobre `IndexPublicationPort`: ya no importa
  `rag_docs.vector_store` ni usa `isinstance(QdrantVectorStore)`; el candidato sale de
  `candidate_store(fingerprint)`. Un store sin el puerto se rechaza con `AppError(VALIDATION)`.
  `rollback_alias` es parte del puerto.
- Sin cambios de payload, fingerprint ni API HTTP.
- Tests nuevos: `tests/test_container.py` (backend por defecto, factoría Qdrant, backend inválido
  rechazado por `Settings` y por la factoría), `test_vector_store_port_is_the_single_store_protocol`,
  `test_qdrant_adapter_implements_the_publication_port`,
  `test_migrate_and_publish_rejects_a_store_without_publication_port` y
  `test_indexing_module_does_not_depend_on_the_qdrant_adapter`. `FakeVectorStore` añade
  `bind_fingerprint`.
- Comportamiento Qdrant intacto: los tests existentes pasan sin modificación (115 en total) y
  `scripts/migration_drill.py` sigue terminando en `rolled-back` con el alias en la colección original.
  `scripts/verify.ps1` en verde.
