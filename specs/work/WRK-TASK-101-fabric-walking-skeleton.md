---
id: WRK-TASK-101
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
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-003, RULE-001, RULE-004]
dependencies:
  - id: WRK-TASK-095
    relation: depends-on
  - id: WRK-TASK-100
    relation: depends-on
tags: [fabric, walking-skeleton, migration, end-to-end]
---

# WRK-TASK-101 — Walking skeleton local → Fabric SQL

## Objective

Demostrar el recorrido completo: índice construido en local, publicado en Fabric SQL y consultado
desde la API y la web locales con Ollama.

## File Scope

Incluye scripts de publicación del índice local al backend Fabric, la adaptación de
`scripts/migration_drill.py` para el backend SQL, tests live en `scripts/verify-fabric.ps1` y
documentación en `DOC-RAG-003`. Excluye indexación en Fabric y evaluación en Delta.

## Acceptance Criteria

- [ ] El digest del fingerprint publicado en Fabric coincide con el del índice local.
- [ ] Una consulta sobre el corpus sintético devuelve respuesta grounded con citas válidas usando el
      backend Fabric.
- [ ] El drill de migración y rollback se ejecuta en SQL y una vinculación obsoleta rechaza la
      consulta.

## Evidence

Pendiente.
