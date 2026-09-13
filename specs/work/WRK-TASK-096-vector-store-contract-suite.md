---
id: WRK-TASK-096
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
activates: [FEAT-RAG-001, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-094
    relation: depends-on
tags: [tests, contract, vector-store]
---

# WRK-TASK-096 — Suite de contrato de VectorStore

## Objective

Disponer de una suite de contrato parametrizada que cualquier backend de `VectorStorePort` e
`IndexPublicationPort` deba superar.

## File Scope

Incluye `tests/contract/**` (o equivalente), fixtures compartidas en `tests/conftest.py` y la
documentación del enganche live. Excluye implementaciones de backend nuevas.

## Acceptance Criteria

- [x] La suite cubre round-trip de chunks, fingerprint vinculado y rechazo sin vínculo,
      `prune_document`, prefiltro de ámbito, `update_acl` sin tocar vectores, `scan_chunks`,
      publicación y rollback.
- [x] Corre contra Qdrant `:memory:` dentro del gate por defecto, sin infraestructura.
- [x] Existe un enganche opcional para ejecutarla contra un backend live, excluido de
      `scripts/verify.ps1`.

## Evidence

- `tests/contract/test_vector_store_contract.py`: 11 casos que usan solo métodos de
  `VectorStorePort` e `IndexPublicationPort`:
  - implementación del puerto de publicación;
  - round-trip `upsert` → `list_documents` → `search` (chunk idéntico, score ≈ 1) → `delete_document`;
  - rechazo sin fingerprint vinculado (`search` y `upsert`);
  - rechazo de reutilizar un índice con otro fingerprint;
  - fallo explícito con un fingerprint vinculado obsoleto tras mover el alias;
  - `prune_document`, incluido el conjunto vacío;
  - prefiltro de ámbito por tenant, subject y classification;
  - `update_acl` cambia la visibilidad con score idéntico (vector intacto);
  - `scan_chunks` con ámbito;
  - publicación de un candidato invisible hasta publicar, y rollback;
  - rollback a un índice inexistente con `NOT_FOUND`.
- `tests/conftest.py`: fixture `contract_store` parametrizada (nombre lógico único por test) y
  `make_fingerprint`. El parámetro `qdrant-memory` siempre existe. El parámetro `live` (marcador
  `live`) solo se genera si `RAG_DOCS_CONTRACT_LIVE_FACTORY=modulo:factoria` está definido, así que
  `scripts/verify.ps1` y CI nunca lo ejecutan.
- Documentación del enganche live: `tests/contract/README.md`.
- Verificado: sin la variable, la recolección da 11 tests (`qdrant-memory`). Con
  `RAG_DOCS_CONTRACT_LIVE_FACTORY=tests.conftest:_qdrant_memory` y `-m live`, pasan los 11 casos
  `[live]` (11 deseleccionados), lo que prueba el mecanismo de carga de la factoría sin
  infraestructura. `scripts/verify.ps1` en verde.
