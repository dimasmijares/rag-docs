---
id: WRK-TASK-012
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-09-02
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

- [x] Se registran rank, score, selección y motivo de descarte sin publicar contenido privado.
- [x] Variantes documentales equivalentes y chunks repetidos no ocupan contexto redundante.
- [x] Se miden Recall@1/3/5/8, MRR, Precision@k y latencia por caso y agregada.
- [x] Casos sin evidencia no se contabilizan como falsos fallos de recuperación.
- [x] El informe permite atribuir cada fallo a recuperación, selección de contexto o generación.

## Evidence

- `QueryResult.retrieval_diagnostics` conserva el ranking del vector store, score, identificadores
  opacos, localizador, selección, orden de contexto y descarte; no incluye texto, snippets ni URI.
- La selección descarta chunks repetidos y variantes con la misma huella normalizada antes de
  aplicar el límite de contexto, con motivos `duplicate_chunk`, `equivalent_document` y
  `context_limit` cubiertos por pruebas sintéticas.
- El evaluador calcula Recall@1/3/5/8, reciprocal rank (MRR al agregar), Precision@1/3/5/8 y
  latencia por caso/agregada usando documentos, secciones y localizadores del gold set.
- Los casos negativos quedan marcados como no elegibles en las métricas de retrieval y los fallos
  se atribuyen a `retrieval`, `context_selection`, `generation` o `api`.
- Gates locales superados: KDD validó `125` specs y `863` relaciones sin huérfanos; lifecycle,
  Ruff, `47` tests, gate de publicación sobre `201` candidatos y `git diff --check` quedaron verdes.
