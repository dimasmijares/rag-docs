---
id: WRK-TASK-106
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
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, RULE-004]
dependencies:
  - id: WRK-TASK-030
    relation: depends-on
  - id: WRK-TASK-100
    relation: depends-on
  - id: ADR-RAG-013
    relation: depends-on
tags: [fabric, ledger, transactions, contract]
---

# WRK-TASK-106 — Ledger documental en Fabric SQL

## Objective

Implementar `DocumentLedgerPort` en Fabric SQL confirmando ledger y chunks de un documento en una
única transacción.

## File Scope

Incluye el adaptador de ledger Fabric SQL, su DDL portable y la suite de contrato de ledger
compartida con la implementación PostgreSQL de `WRK-TASK-030`. Excluye jobs, outbox y leases.

## Acceptance Criteria

- [ ] Ledger y chunks de un documento se confirman en la misma transacción; un fallo no deja ninguno
      de los dos.
- [ ] La clave de efecto `(document_id, content_hash, index_fingerprint)` hace idempotente la
      reescritura.
- [ ] La suite de contrato de ledger pasa contra PostgreSQL y contra Fabric SQL (esta última en
      `scripts/verify-fabric.ps1`).

## Evidence

Pendiente.
