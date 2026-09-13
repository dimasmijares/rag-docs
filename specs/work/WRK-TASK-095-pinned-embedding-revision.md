---
id: WRK-TASK-095
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
activates: [FEAT-RAG-001, DOC-RAG-001, RULE-004]
dependencies:
  - id: WRK-TASK-094
    relation: depends-on
tags: [fingerprint, embeddings, reproducibility]
---

# WRK-TASK-095 — Revisión de embeddings fijada

## Objective

Propagar una revisión de embeddings fijada desde configuración para que la aplicación y el benchmark
construyan el mismo digest de fingerprint.

## File Scope

Incluye `src/rag_docs/config.py`, `src/rag_docs/container.py`, `src/rag_docs/embeddings.py`,
`src/rag_docs/benchmark.py` en la construcción del fingerprint,
`evaluation/corpus-compatibility.yaml` y tests. Excluye cambiar el modelo de embeddings por defecto.

## Acceptance Criteria

- [ ] `Settings.embedding_revision` existe y se propaga al embedder y al `IndexFingerprint` de la
      aplicación.
- [ ] Para la misma configuración, el digest de la aplicación coincide con el del benchmark (test).
- [ ] `evaluation/corpus-compatibility.yaml` declara el digest resultante con la política aditiva
      existente.
- [ ] La nota de migración documenta que un índice previo sin revisión fijada exige migración según
      `RULE-004`.

## Evidence

Pendiente.
