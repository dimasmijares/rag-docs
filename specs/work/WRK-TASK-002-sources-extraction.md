---
id: WRK-TASK-002
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
  - id: WRK-TASK-001
    relation: depends-on
tags: [sources, extraction]
---

# WRK-TASK-002 — Fuentes y extracción

## Objective

Implementar descubrimiento local y extracción estructurada de PDF, DOCX, PPTX, XLSX, TXT y Markdown.

## Scope

Incluye configuración, contratos de fuente, parsers y sus pruebas. Excluye embeddings e índice.

## Acceptance Criteria

- [ ] Descubrimiento recursivo respeta inclusión y exclusión.
- [ ] Cada formato conserva su localizador y los errores son aislados.

## Test Plan

Fixtures mínimas por formato, metadatos y archivo corrupto.

## Evidence

Pruebas de descubrimiento, exclusión, hash, seis formatos y documento corrupto superadas.

## Traceability

Implementado en `src/rag_docs/sources/`, `extractors.py` y `tests/test_extractors.py`.
