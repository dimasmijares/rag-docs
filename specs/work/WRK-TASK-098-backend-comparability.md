---
id: WRK-TASK-098
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
tags: [evaluation, benchmark, comparability]
---

# WRK-TASK-098 — Comparabilidad por backend

## Objective

Hacer que backend y modo de búsqueda formen parte de la clave de comparabilidad de los informes,
según `ADR-RAG-013`.

## File Scope

Incluye `src/rag_docs/benchmark.py`, `src/rag_docs/evaluation.py`, `compare_reports`, el esquema de
informe y tests. Excluye regenerar benchmarks históricos.

## Acceptance Criteria

- [ ] Los informes declaran `vector_backend` y `vector_search_mode` con `schema_version` 1.1; los
      informes 1.0 se leen como `qdrant`/`hnsw`.
- [ ] `compare_reports` rechaza comparar backends o modos distintos sin `--rebaseline` explícito.
- [ ] La latencia se marca como no comparable entre backends distintos aunque se permita comparar
      recall.

## Evidence

Pendiente.
