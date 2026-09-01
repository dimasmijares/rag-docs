---
id: WRK-TASK-012
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [ARCH-001, ARCH-002, DOM-RAG-001, FEAT-RAG-001, RULE-001, RULE-004]
dependencies:
  - id: WRK-TASK-009
    relation: depends-on
  - id: WRK-TASK-023
    relation: depends-on
tags: [retrieval, diagnostics, metrics, deduplication]
---

# WRK-TASK-012 — Calidad y diagnóstico del retrieval

## Objective

Medir qué llega al generador y mejorar recuperación sin confundir fallos de retrieval con fallos de generación.

## File Scope

Incluye candidatos, scores, seleccionados, descartes, Recall@k, MRR, latencia y deduplicación.
Excluye implementar hybrid retrieval, reranking, query rewriting o multi-query, que se evaluarán
en tareas posteriores contra esta baseline.

## Acceptance Criteria

- [ ] Se registran candidatos, scores, seleccionados y motivo de descarte.
- [ ] Versiones DOCX/Markdown equivalentes no ocupan contexto redundante.
- [ ] Se miden Recall@k, MRR, precisión y latencia.
- [ ] El informe permite atribuir cada fallo a recuperación, selección de contexto o generación.

## Evidence

Pendiente.
