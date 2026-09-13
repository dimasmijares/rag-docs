---
id: WRK-TASK-096
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

- [ ] La suite cubre round-trip de chunks, fingerprint vinculado y rechazo sin vínculo,
      `prune_document`, prefiltro de ámbito, `update_acl` sin tocar vectores, `scan_chunks`,
      publicación y rollback.
- [ ] Corre contra Qdrant `:memory:` dentro del gate por defecto, sin infraestructura.
- [ ] Existe un enganche opcional para ejecutarla contra un backend live, excluido de
      `scripts/verify.ps1`.

## Evidence

Pendiente.
