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
tags: [corpus, evaluation, synthetic, gold-set]
---

# WRK-TASK-026 — Corpus y gold sets sintéticos

## Objective

Ampliar un corpus multiformato completamente sintético y separar preguntas de desarrollo y
validación para evitar ajuste al test.

## Acceptance Criteria

- [ ] Corpus y respuestas se regeneran de forma determinista.
- [ ] Los splits no comparten preguntas equivalentes ni referencias privadas.
- [ ] Hay casos positivos, compuestos, multilingües y de evidencia insuficiente.
- [ ] Los formatos y metadatos soportados quedan representados.

## Evidence

Pendiente.
