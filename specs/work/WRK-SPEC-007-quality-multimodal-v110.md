---
id: WRK-SPEC-007
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-004]
dependencies:
  - id: WRK-SPEC-006
    relation: depends-on
  - id: ADR-002
    relation: depends-on
tags: [release, v1.1.0, retrieval, multimodal]
---

# WRK-SPEC-007 — Calidad y multimodal v1.1.0

## Proposed Change

Versionar el índice por fingerprint, medir dense/hybrid/reranking y añadir OCR, imágenes, tablas y
visión condicional preservando provenance.

## Acceptance Criteria

- [ ] Cambios incompatibles publican una colección nueva mediante alias.
- [ ] Hybrid y reranking sólo se adoptan si superan el baseline.
- [ ] OCR y visión conservan localizador y coordenadas.
- [ ] Streaming sólo se marca grounded tras validación final.

## Evidence

Pendiente de `WRK-PLAN-007`.
