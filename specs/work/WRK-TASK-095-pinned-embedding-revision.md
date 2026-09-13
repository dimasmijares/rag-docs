---
id: WRK-TASK-095
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
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

- [x] `Settings.embedding_revision` existe y se propaga al embedder y al `IndexFingerprint` de la
      aplicación.
- [x] Para la misma configuración, el digest de la aplicación coincide con el del benchmark (test).
- [x] `evaluation/corpus-compatibility.yaml` declara el digest resultante con la política aditiva
      existente.
- [x] La nota de migración documenta que un índice previo sin revisión fijada exige migración según
      `RULE-004`.

## Evidence

- `Settings.embedding_revision` (`RAG_DOCS_EMBEDDING_REVISION`) fija por defecto
  `614241f622f53c4eeff9890bdc4f31cfecc418b3`, la misma revisión que todos los perfiles de
  `config/benchmark.yaml`; el modelo por defecto no cambia. `container.build_embedder(settings)` la
  propaga a `SentenceTransformerEmbedder` y, por `build_fingerprint`, al `IndexFingerprint` de la
  aplicación. `embeddings.py` ya aceptaba `revision` y no necesitó cambios.
- `benchmark.profile_embedder(profile, config)` centraliza el embedder de indexado y de consulta del
  benchmark (antes duplicado), para que el test compare exactamente la misma construcción.
- `tests/test_container.py`: `test_embedding_revision_setting_propagates_to_the_app_embedder` y
  `test_app_and_benchmark_build_the_same_fingerprint_digest`. Este último no carga el modelo
  (dimensión fijada a 384) y comprueba que, con la configuración por defecto, el digest de la
  aplicación es igual al de cada perfil del benchmark con el mismo modelo, y que está declarado en
  `evaluation/corpus-compatibility.yaml`.
- Digest resultante: `724f6786a9170f8b`, ya declarado en `compatible_fingerprint_digests`. Siguiendo
  la política aditiva no se añade ni se sustituye ningún digest; un comentario en el manifiesto
  registra que desde esta tarea también es el digest de la aplicación. Antes, la aplicación sin
  revisión fijada producía `8270a45e87e30cc7`, no declarado (hallazgo de `WRK-TASK-093`), así que
  `rag-docs-eval` contra la API vuelve a ser verificable.
- Nota de migración: sección "Índice: fingerprint, ámbito y comparabilidad" de `README.md`, donde
  `DOC-RAG-001` documenta el modelo de índice. Se añadió ahí, fuera del File Scope literal, porque el
  criterio lo exige y es el documento operativo que ya explica `RULE-004`. `.env.example` declara
  `RAG_DOCS_EMBEDDING_REVISION`. La revisión ya estaba en la caché local de Hugging Face, así que no
  hay descarga nueva.
- `scripts/verify.ps1` en verde.
