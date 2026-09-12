---
id: WRK-TASK-038
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
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001]
dependencies:
  - id: WRK-TASK-037
    relation: depends-on
tags: [reranking, experiment, adr, evaluation]
---

# WRK-TASK-038 — Experimento de reranking

## Objective

Medir un reranker configurable y registrar mediante ADR su adopción o rechazo.

## Acceptance Criteria

- [x] Baseline, modelo, top-n, latencia y memoria son reproducibles.
- [x] La mejora se calcula sobre validación no usada para ajuste.
- [x] Fallos mantienen una estrategia explícita y segura.
- [x] Un ADR documenta decisión y consecuencias.

## Evidence

- **`src/rag_docs/reranking.py` (nuevo):** `CrossEncoderReranker` reutiliza
  `sentence-transformers` (dependencia ya presente en `embeddings.py`) — sin dependencia nueva,
  mismo criterio de `WRK-TASK-037` para no disparar `dependency-review`. Carga el modelo de forma
  perezosa (patrón de `SentenceTransformerEmbedder`) y **falla en modo seguro** (AC3): si la carga
  o `predict()` lanzan cualquier excepción (sin red, nombre de modelo inválido, lo que sea),
  `rerank()` devuelve los hits originales sin reordenar en lugar de romper la consulta; una vez que
  la carga falla una vez, no se reintenta en cada consulta (`_unavailable`). `RERANK_VERSION =
  "cross-encoder-v1"` versiona explícitamente la pieza (AC1).
- **Integración:** `QueryService` gana `reranker: Reranker | None = None` y `rerank_top_n` (por
  defecto, `context_chunks`). Se aplica al final de `_retrieve`, después de dense o hybrid, y
  reordena/trunca la lista antes de que `ContextBuilder` seleccione — sin tocar deduplicación ni
  citación. Por defecto no cambia nada (mismo principio de `retrieval_strategy` en `WRK-TASK-037`).
  `Settings` gana `reranker_model`/`rerank_top_n` (`None` por defecto) y `ApplicationContainer` los
  conecta sólo si el operador los declara — ninguna instalación existente cambia de comportamiento
  al actualizar.
- **Medición con datos reales, dos gold sets (AC1/AC2):** `config/benchmark-038-reranking.yaml`
  (independiente de `config/benchmark.yaml`, misma razón que `WRK-TASK-037`/`086`: no invalidar el
  `config_sha256` que `decision-lock.json` de `v0.2.0` tiene congelado) compara `dense-baseline`
  (perfil de producción tras `WRK-TASK-037`) contra `dense-reranked`
  (`cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, elegido multilingüe para ser coherente con
  `intfloat/multilingual-e5-small` — un cross-encoder entrenado sólo en inglés como
  `ms-marco-MiniLM-L-6-v2` no encajaría con el corpus en español). Ejecutado en vivo (Qdrant en
  memoria, mismo corpus `demo` v0.2.0, `retrieval_top_k=8`, `rerank_top_n=5`) sobre ambos gold sets;
  guardado como evidencia reproducible en
  `evaluation/benchmarks/wrk-task-038/{dev,validation}-comparison.json`:
  - **`gold-set.validation.yaml` (8 casos, 6 elegibles — el conjunto que decide, nunca usado para
    ajustar `rerank_top_n` o el modelo, AC2):** `recall_at_1` 0.75 → 0.917, `precision_at_1` 0.833 →
    1.0, `recall_at_3`/`recall_at_5` 0.917 → 1.0, `reciprocal_rank`/MRR 0.917 → 1.0, `precision_at_8`
    0.167 → 0.267. **Ninguna métrica retrocede en ningún corte.**
  - **`gold-set.dev.yaml` (16 casos, 14 elegibles):** mismo patrón — `recall_at_1` 0.571 → 0.643,
    MRR 0.729 → 0.798, sin regresiones.
  - **Latencia (AC1):** medida en un bucket propio (`rerank_ms` en `StageRecorder`/`TimedReranker`,
    separado de `embedding_ms`/`retrieval_ms`/`generation_ms`, no mezclado en `grounding_ms` como
    hubiera quedado sin instrumentar). En estado `warm` el reranking añade ~112–171 ms de mediana
    (cross-encoder de 12 capas en CPU sobre `top_k=8` pares); el total pasa de ~30 ms a ~140–215 ms
    de mediana. El coste depende de `top_k`, no del tamaño del corpus. El `p95` bruto de la primera
    ejecución incluye la descarga/carga única del modelo (~11–30 s) — separado en
    `performance_by_state.cold` frente a `warm` precisamente para no confundir ese coste de arranque
    con latencia de consulta.
  - **Memoria:** sin diferencia atribuible más allá de la carga del modelo cross-encoder.
- **Decisión (AC4):** `ADR-RAG-012` documenta la adopción — a diferencia del resultado mixto de
  `WRK-TASK-037`, éste es un caso limpio de "mejora medible" sin regresión en ningún corte sobre el
  conjunto de validación. Se adopta la **capacidad**, no el valor por defecto: `reranker_model`
  permanece `None` salvo que el operador lo declare explícitamente, para no forzar una descarga de
  modelo ni un cambio de latencia no solicitado en ningún despliegue existente al actualizar
  (mismo principio de `RULE-004` aplicado a un cambio de comportamiento en tiempo de consulta, no
  en el índice). El ADR recomienda activarlo cuando la latencia adicional sea aceptable.
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (109 tests, 7 nuevos: 4 en `tests/test_reranking.py`, 1 en `tests/test_query.py`, y
  actualización de `tests/test_benchmark.py` para el nuevo bucket `rerank_ms`); `./scripts/kdd.ps1
  validate`; `./scripts/check-public-safety.ps1` sobre los nuevos JSON de comparación (mismo
  contenido saneado que `wrk-task-027`/`037`); `uv run --no-sync rag-docs-benchmark verify` sigue en
  verde sobre los artefactos canónicos de `v0.2.0` (sin regenerarlos, sin tocar
  `config/benchmark.yaml`).
