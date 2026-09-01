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
activates: [ARCH-001, ARCH-002, DOM-RAG-001, FEAT-RAG-001, RULE-001, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-009
    relation: depends-on
  - id: WRK-TASK-023
    relation: depends-on
  - id: WRK-TASK-026
    relation: depends-on
  - id: WRK-TASK-079
    relation: depends-on
tags: [retrieval, diagnostics, metrics, deduplication]
---

# WRK-TASK-012 — Calidad y diagnóstico del retrieval

## Objective

Medir qué llega al generador y mejorar recuperación sin confundir fallos de retrieval con fallos de generación.

## File Scope

Incluye el contrato diagnóstico de query/evaluación, tests y resultados sintéticos: candidatos,
rank, scores, seleccionados, descartes, Recall@1/3/5/8, MRR, Precision@k, latencia y
deduplicación. Los diagnósticos detallados de corpus local permanecen en rutas ignoradas.
Excluye hybrid retrieval, reranking, query rewriting, multi-query y cambios de embeddings.

## Acceptance Criteria

- [ ] Se registran rank, score, selección y motivo de descarte sin publicar contenido privado.
- [ ] Variantes documentales equivalentes y chunks repetidos no ocupan contexto redundante.
- [ ] Se miden Recall@1/3/5/8, MRR, Precision@k y latencia por caso y agregada.
- [ ] Casos sin evidencia no se contabilizan como falsos fallos de recuperación.
- [ ] El informe permite atribuir cada fallo a recuperación, selección de contexto o generación.

## Evidence

Pendiente.
