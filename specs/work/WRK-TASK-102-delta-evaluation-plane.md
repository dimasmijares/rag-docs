---
id: WRK-TASK-102
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
activates: [DOM-RAG-001, FEAT-RAG-001, DOC-RAG-003, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-093
    relation: depends-on
  - id: WRK-TASK-098
    relation: depends-on
  - id: WRK-TASK-101
    relation: depends-on
tags: [fabric, evaluation, delta, benchmark]
---

# WRK-TASK-102 — Plano de evaluación en Delta

## Objective

Almacenar gold sets, manifiesto de corpus e informes de evaluación en Delta y medir la paridad de
recall entre backends.

## File Scope

Incluye un notebook cargador en `fabric/`, el esquema de tablas Delta, configuración de benchmark
por backend y evidencia en `evaluation/benchmarks/`. Excluye Power BI y LLM-as-judge.

## Acceptance Criteria

- [ ] Gold sets, manifiesto e informes se cargan en Delta de forma append-only por `corpus_version`.
- [ ] El benchmark `dense` y `dense-reranked` se ejecuta en Qdrant y Fabric SQL y la paridad de
      recall queda medida.
- [ ] DiskANN se evalúa como experimento del gate G2 y no se adopta sin mejora medida.
- [ ] Ningún informe incluye contenido documental fuera del corpus sintético.

## Evidence

Pendiente.
