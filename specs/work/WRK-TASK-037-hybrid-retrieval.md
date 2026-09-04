---
id: WRK-TASK-037
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, RULE-004]
dependencies:
  - id: WRK-TASK-036
    relation: depends-on
  - id: WRK-TASK-012
    relation: depends-on
  - id: WRK-TASK-090
    relation: depends-on
tags: [retrieval, lexical, hybrid, evaluation]
---

# WRK-TASK-037 — Retrieval léxico e híbrido

## Objective

Implementar un índice léxico y comparar dense frente a hybrid sobre la baseline.

## Acceptance Criteria

- [ ] Scores y fusión son explicables y versionados.
- [ ] Se comparan identificadores exactos y preguntas semánticas.
- [ ] Calidad, latencia y memoria se registran por estrategia.
- [ ] Hybrid sólo se adopta si supera el criterio previo.
- [ ] La comparación se declara sobre una baseline con el mismo `corpus_version` e
      `index_fingerprint`; si el índice léxico cambia el fingerprint, se publica el re-baseline.

## Evidence

Pendiente.
