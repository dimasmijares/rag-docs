---
id: WRK-TASK-013
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-007
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, RULE-001, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-035
    relation: depends-on
tags: [ocr, pdf, images, provenance]
---

# WRK-TASK-013 — OCR condicional

## Objective

Recuperar texto de PDF e imágenes sin contenido textual útil mediante OCR condicional y trazable.

## File Scope

Incluye detección de ausencia de texto, OCR, metadatos de página/imagen/coordenadas y tests.
Excluye interpretación visual de tablas y diagramas, que corresponde a `039/040`.

## Acceptance Criteria

- [ ] OCR se aplica a contenido sin texto útil y produce chunks trazables.
- [ ] Página, imagen y coordenadas se conservan cuando estén disponibles.
- [ ] Se registran precisión, tiempo y almacenamiento adicional frente al extractor textual.

## Evidence

Pendiente.
