---
id: WRK-TASK-098
type: spec
layer: work-task
scope: ephemeral
status: archived
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

- [x] Los informes declaran `vector_backend` y `vector_search_mode` con `schema_version` 1.1; los
      informes 1.0 se leen como `qdrant`/`hnsw`.
- [x] `compare_reports` rechaza comparar backends o modos distintos sin `--rebaseline` explícito.
- [x] La latencia se marca como no comparable entre backends distintos aunque se permita comparar
      recall.

## Evidence

- `src/rag_docs/evaluation.py`: `REPORT_SCHEMA_VERSION = "1.1"` y `report_vector_backend(report,
  profile)`. Lee `vector_backend`/`vector_search_mode` del perfil o del informe. Un informe `1.0` o
  sin `schema_version` se lee como `qdrant`/`hnsw`, y uno `1.1` sin esos campos es inválido
  (`ValueError`). `evaluate()` emite `schema_version: "1.1"`, `vector_backend` y
  `vector_search_mode`, tomados de `GET /api/sources` si la API los declara y, si no, `qdrant`/`hnsw`
  (la API solo sirve Qdrant hasta `WRK-TASK-100`/`101`). `live_index_fingerprint` pasa a
  `live_index_descriptor` para leer ambos con una sola petición.
- `src/rag_docs/benchmark.py`:
  - Los informes de fase usan `schema_version` `1.1` y cada perfil declara `vector_backend: qdrant` y
    `vector_search_mode: hnsw` (`_aggregate_profile`).
  - `SCHEMA_VERSION` `1.0` se mantiene para `config/benchmark.yaml` y el lock de decisión, que no
    son informes; no se regeneran benchmarks históricos.
  - `compare_reports` usa la clave `corpus_version` + digest + `vector_backend` +
    `vector_search_mode` y lanza `RebaselineRequired` si difiere sin `--rebaseline`.
  - Devuelve `recall_comparable` (mismo corpus y fingerprint, aunque cambie backend o modo) con
    `recall_at_8_delta`, y `latency_comparable` solo bajo la clave completa, con
    `latency_p95_delta_ms` y `latency_note` ("latencia no comparable entre backends distintos").
    `score_delta` conserva su semántica previa.
- Tests en `tests/test_benchmark.py`:
  - `test_report_schema_is_1_1_and_legacy_reports_read_as_qdrant_hnsw`;
  - `test_compare_reports_treats_a_legacy_report_as_qdrant_hnsw`;
  - `test_compare_reports_requires_rebaseline_across_backends_or_modes` (parametrizado por backend y
    por modo: exige re-baseline; con él, recall comparable y latencia no);
  - `test_compare_reports_reports_latency_delta_under_the_full_key`;
  - `_aggregate_profile` declara backend y modo.

  En `tests/test_evaluation.py`: esquema `1.1` con valores por defecto y
  `test_evaluate_records_the_backend_the_api_declares`. Los tests previos de `compare_reports`
  pasan sin cambios de expectativa.
- Matiz registrado: el benchmark indexa en Qdrant `:memory:`, que en local busca de forma exhaustiva
  aunque la colección declare la configuración HNSW por defecto. Se declara `hnsw` por coherencia
  con la lectura obligatoria de los informes `1.0`, producidos igual; declarar `exact` rompería la
  comparabilidad con toda la serie histórica. La paridad de recall entre backends (`WRK-TASK-101`)
  debe tener en cuenta este matiz.
- La sección de comparabilidad del `README.md` sigue describiendo la tripleta; su actualización
  queda para la consolidación `WRK-TASK-104` (fuera del File Scope). `scripts/verify.ps1` en verde.
