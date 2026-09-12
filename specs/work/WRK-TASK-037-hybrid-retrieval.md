---
id: WRK-TASK-037
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.3.0
created: 2026-09-01
updated: 2026-09-12
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

- [x] Scores y fusión son explicables y versionados.
- [x] Se comparan identificadores exactos y preguntas semánticas.
- [x] Calidad, latencia y memoria se registran por estrategia.
- [x] Hybrid sólo se adopta si supera el criterio previo.
- [x] La comparación se declara sobre una baseline con el mismo `corpus_version` e
      `index_fingerprint`; si el índice léxico cambia el fingerprint, se publica el re-baseline.

## Evidence

- **`src/rag_docs/lexical.py` (nuevo):** `BM25Index` implementa BM25 (Robertson/Sparck-Jones,
  constantes `BM25_K1=1.5`, `BM25_B=0.75`) en Python puro sobre los chunks que recibe —
  sin dependencia nueva (evita el gate de `dependency-review` y el riesgo de cadena de suministro
  para un algoritmo de una página), y sin estado persistido ni fingerprint propio: se reconstruye
  por consulta a partir de `VectorStore.scan_chunks(scope)` (nuevo), que reutiliza el mismo filtro
  de `Scope` que `search()` (`ADR-RAG-009`) — un hit léxico nunca es un chunk que el prefiltro de
  autorización habría rechazado. `reciprocal_rank_fusion` combina dense y léxico por **rango**, no
  por score bruto (similitud coseno y BM25 viven en escalas incomparables), con la constante
  estándar `RRF_K=60` (Cormack, Clarke & Buettcher, 2009). `LEXICAL_VERSION="bm25-v1"` y
  `FUSION_VERSION="rrf-v1"` versionan explícitamente ambas piezas (AC1); el tokenizador conserva el
  guion bajo (`ETL_CLIENTES_DIARIA` no se parte en `etl`/`clientes`) precisamente para que la
  comparación entre identificadores técnicos exactos y preguntas semánticas (AC2) tenga sentido.
- **Integración:** `QueryService` gana `retrieval_strategy: Literal["dense","hybrid"] = "dense"`.
  En modo `hybrid`, la fase densa se ejecuta sin `min_score` (el umbral está calibrado para
  similitud coseno, no para un score RRF) y se fusiona con `BM25Index` sobre
  `store.scan_chunks(scope)`; el resto del pipeline (`ContextBuilder`, validación, fallback) no
  cambia. El valor por defecto sigue siendo `"dense"`: no se cambia el comportamiento observable de
  la aplicación por defecto, sólo se ofrece la estrategia como opción medible (AC4, ver más abajo).
  `VectorStorePort`/`VectorStore` ganan `scan_chunks` en su firma; `TimedStore` (benchmark) y
  `FakeVectorStore` (tests) se actualizan a la vez.
- **Comparación por estrategia, con datos reales:** `config/benchmark-037-hybrid.yaml` (nuevo,
  independiente de `config/benchmark.yaml` para no invalidar el `config_sha256` que
  `decision-lock.json` de `v0.2.0` ya tiene congelado — la misma lección de `WRK-TASK-086`) declara
  dos perfiles idénticos salvo `retrieval_strategy` (`dense-baseline` / `hybrid-rrf`), con
  `generator_mode: forced_fallback` para medir exclusivamente retrieval (calidad, latencia, memoria)
  sin depender de Ollama. `_aggregate_profile` añade `retrieval_strategy` y
  `retrieval_strategy_version` a cada perfil del informe (AC1/AC3). Ejecutado en vivo (Qdrant en
  memoria, mismo corpus `demo` v0.2.0) sobre **ambos** gold sets y guardado como evidencia
  reproducible en `evaluation/benchmarks/wrk-task-037/{dev,validation}-comparison.json`:
  - **`gold-set.dev.yaml` (16 casos, 14 elegibles):** hybrid mejora `recall_at_1` (0.571 → 0.714),
    `precision_at_1` (0.571 → 0.714) y `reciprocal_rank`/MRR (0.729 → 0.836); `recall_at_3/5/8`
    quedan iguales (0.929/1.0/1.0).
  - **`gold-set.validation.yaml` (8 casos, 6 elegibles):** recall@1, precision@1 y MRR quedan
    idénticos (0.75/0.833/0.917); pero `recall_at_8` **empeora** (1.0 → 0.917) y `precision_at_8`
    también (0.167 → 0.146) — al menos un documento relevante queda desplazado fuera del corte que
    `QueryService` usa por defecto (`top_k=8`).
  - Latencia y memoria por estrategia (recorder de benchmark, ver los JSON): la fase de retrieval
    híbrida cuesta ~1 ms más de mediana (BM25 + fusión sobre un corpus de demo) frente a los
    cientos de ms de generación real; memoria sin diferencia atribuible a la estrategia.
- **Decisión (AC4), documentada, no ambigüedad sin resolver:** el resultado es mixto — mejora clara
  en desarrollo, mejora nula y una regresión en `recall_at_8`/`precision_at_8` en validación, que es
  exactamente el corte de retrieval que la aplicación usa hoy. `RFC-001` (gate G2) exige "mejora
  medible" para adoptar híbrido, y `AC4` exige que "supere" el criterio previo, no que empate con una
  regresión en el conjunto de confirmación. **No se cambia el valor por defecto de
  `retrieval_strategy`**: sigue siendo `"dense"` en `QueryService` y en el `container.py` de
  producción. La capacidad híbrida queda implementada, probada y medida — lista para adoptarse si
  una iteración futura del índice léxico (p. ej. down-weighting de campos ruidosos, o fusión
  ponderada en vez de RRF puro) cierra la regresión de `recall_at_8` sin sacrificar la mejora de
  `recall_at_1`/MRR. Esto es justo lo que `RFC-001` anticipaba en su alternativa 2: "añadir hybrid
  retrieval de inmediato... queda sujeto a resultados del gold set."
- **Fingerprint (AC5):** el índice léxico no persiste nada y no forma parte de `IndexFingerprint`
  (se reconstruye desde `scan_chunks`, que ya respeta el fingerprint vinculado a la colección vía
  `_check_bound()`), así que no hay cambio de fingerprint que reequilibrar ni re-baseline que
  publicar — ambos perfiles de la comparación comparten el mismo `index_fingerprint` (verificado en
  los JSON guardados), que es además el mismo `corpus_version` (`0.2.0`) que
  `evaluation/corpus-compatibility.yaml` ya declara compatible.
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (102 tests, 8 nuevos: 6 en `tests/test_lexical.py`, 1 en `tests/test_query.py`, 1 en
  `tests/test_vector_store.py`, y las actualizaciones de las firmas existentes); `./scripts/kdd.ps1
  validate`; `./scripts/check-public-safety.ps1` sobre los nuevos JSON de comparación (sólo
  contienen IDs sintéticos, métricas y hardware saneado, igual que los de `wrk-task-027`);
  `uv run --no-sync rag-docs-benchmark verify` y `./scripts/demo.ps1` sobre los artefactos
  canónicos de `v0.2.0` (sin regenerarlos, sin tocar `config/benchmark.yaml`) siguen en verde.
