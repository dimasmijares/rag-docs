---
id: WRK-TASK-107
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
activates: [ARCH-002, FEAT-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-105
    relation: depends-on
  - id: WRK-TASK-106
    relation: depends-on
tags: [fabric, spark, notebook, indexing]
---

# WRK-TASK-107 — Notebook de indexación Spark

## Objective

Ejecutar `IndexingService` por documento en el Environment de Fabric escribiendo a través del
ledger.

## File Scope

Incluye el notebook en `fabric/` y el código mínimo de arranque en `src/rag_docs/` que reutiliza
`IndexingService`. Excluye orquestación y enriquecimiento.

## Acceptance Criteria

- [ ] El notebook verifica el digest del fingerprint antes de escribir y falla cerrado si no
      coincide.
- [ ] Cada documento se procesa y confirma de forma independiente; un fallo no invalida el resto.
- [ ] El notebook se versiona sin outputs y pasa el gate público.

## Evidence

Pendiente.
