---
id: WRK-TASK-039
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
activates: [DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, RULE-002]
dependencies:
  - id: WRK-TASK-013
    relation: depends-on
tags: [images, tables, diagrams, provenance]
---

# WRK-TASK-039 — Extracción visual con provenance

## Objective

Extraer imágenes, tablas y diagramas preservando documento, página/slide, índice y coordenadas.

## Acceptance Criteria

- [ ] Cada activo visual tiene identidad y hash estables.
- [ ] Tablas mantienen celdas y localización cuando el formato lo permita.
- [ ] Derivados privados respetan `RULE-002` y no entran en Git.
- [ ] Tests cubren PDF, DOCX y PPTX sintéticos.

## Evidence

Pendiente.
