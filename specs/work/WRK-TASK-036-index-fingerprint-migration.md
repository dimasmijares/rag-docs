---
id: WRK-TASK-036
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-007
activates: [ARCH-002, DOM-RAG-002, RULE-004]
dependencies:
  - id: WRK-TASK-035
    relation: depends-on
tags: [chunking, tokenizer, fingerprint, qdrant]
---

# WRK-TASK-036 — Fingerprint y migración del índice

## Objective

Chunkear con tokenizer, calcular `IndexFingerprint` y migrar colecciones mediante alias atómico.

## Acceptance Criteria

- [ ] El fingerprint cubre extractor, chunking y embedding efectivo.
- [ ] Escritura o consulta incompatible se rechaza.
- [ ] Una colección nueva se valida antes de mover el alias.
- [ ] Rollback conserva la colección anterior durante la ventana definida.

## Evidence

Pendiente.
