---
id: WRK-TASK-026
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [DOM-RAG-001, FEAT-RAG-001, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-024
    relation: depends-on
  - id: WRK-TASK-079
    relation: depends-on
tags: [corpus, evaluation, synthetic, gold-set]
---

# WRK-TASK-026 — Corpus y gold sets sintéticos

## Objective

Ampliar un corpus multiformato completamente sintético y separar preguntas de desarrollo y
validación para evitar ajuste al test.

## File Scope

Incluye `examples/corpus/demo/**`, `evaluation/**`, el generador de corpus, sus tests y la
documentación estrictamente necesaria. Excluye retrieval, generación, modelos reales y datos
locales ignorados.

## Acceptance Criteria

- [ ] `gold-set.dev.yaml` contiene al menos 16 casos y `gold-set.validation.yaml` al menos 8.
- [ ] Los splits no comparten preguntas equivalentes, hechos objetivo ni referencias privadas.
- [ ] Hay casos positivos, compuestos, multilingües, negativos y al menos dos pares documentales equivalentes.
- [ ] PDF, DOCX, PPTX, XLSX, TXT y Markdown, junto con sus localizadores, quedan representados.
- [ ] Un manifiesto SHA-256 y dos regeneraciones consecutivas producen exactamente los mismos archivos.
- [ ] `gold-set.yaml` permanece como smoke set compatible hasta la consolidación de `v0.2.0`.

## Evidence

Pendiente.
