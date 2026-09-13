---
id: WRK-TASK-102
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

- [x] Gold sets, manifiesto e informes se cargan en Delta de forma append-only por `corpus_version`.
- [x] El benchmark `dense` y `dense-reranked` se ejecuta en Qdrant y Fabric SQL y la paridad de
      recall queda medida.
- [x] DiskANN se evalúa como experimento del gate G2 y no se adopta sin mejora medida.
- [x] Ningún informe incluye contenido documental fuera del corpus sintético.

## Evidence

- **Carga en Delta, append-only por `corpus_version`:**
  - `fabric/ragdocs_eval_loader.Notebook`: notebook `.ipynb` sin outputs y sin lakehouse ni IDs en
    la definición; resuelve el Lakehouse por nombre.
  - `fabric/load_evaluation.ps1`: valida en local, aterriza con `fab cp` en
    `Files/landing/0.2.0/`, importa y ejecuta el notebook con `fab job run`.
  - Seis tablas con esquema explícito (`load_log`, `corpus_manifest`, `gold_cases`,
    `evaluation_runs`, `evaluation_profiles`, `evaluation_cases`), documentadas en `DOC-RAG-003`.
  - Escritura solo con `mode("append")`; cada fichero se registra por sha256 en `load_log` y uno ya
    cargado se omite.
  - Ejecución live (2026-09-13, workspace `rag-docs`): 13 ficheros aterrizados (compatibilidad,
    manifiesto, 3 gold sets y 8 informes de `wrk-task-037/038/091/102`). Recuentos por el SQL
    endpoint: `load_log 12`, `corpus_manifest 12`, `gold_cases 28`, `evaluation_runs 8`,
    `evaluation_profiles 22` (`qdrant/hnsw` 18, `fabric_sql/exact` 4), `evaluation_cases 264`.
  - Se cargó tres veces, la última con la versión final del notebook, y los recuentos no cambiaron:
    la carga es idempotente y nunca duplica.
  - Los informes de `wrk-task-027` se excluyen explícitamente: son anteriores a `corpus_version`.
- **Benchmark por backend:**
  - `config/benchmark-102-backends.yaml`: `dense` y `dense-reranked` × `qdrant` / `fabric_sql`,
    con generador extractivo forzado como en `WRK-TASK-038`.
  - `benchmark.py`: `vector_backend` por perfil (validado en la config); los perfiles Fabric usan
    un índice lógico propio que se crea vacío y se elimina tras medir. `vector_search_mode` sale de
    `container.VECTOR_SEARCH_MODES`.
  - Nuevo `backend_parity` y subcomando `rag-docs-benchmark parity`: empareja perfiles idénticos
    salvo backend y marca la latencia como no comparable.
  - Informes `evaluation/benchmarks/wrk-task-102/{dev,validation}-backend-report.json`
    (schema 1.1) y `{dev,validation}-backend-parity.json`. Mismo fingerprint `724f6786a9170f8b` en
    los 4 perfiles.
  - **Paridad de recall exacta** en dev (16 casos) y validation (8 casos), para `dense` y
    `dense-reranked`: recall@1/3/5/8 y MRR idénticos (dev `dense` MRR 0.7286,
    `dense-reranked` 0.7976; validation 0.9167 y 1.0) y ningún caso con métricas de retrieval
    distintas.
  - Latencia de retrieval p95 solo por backend: qdrant :memory: ~2 ms, Fabric SQL por red
    ~127–162 ms.
  - Qdrant `:memory:` declara `hnsw` pero busca de forma exhaustiva (matiz de `WRK-TASK-098`); por
    eso la paridad frente a la búsqueda exacta de SQL es total.
- **Experimento DiskANN (G2)**, `scripts/diskann_experiment.py` →
  `evaluation/benchmarks/wrk-task-102/diskann-experiment.json`:
  - Tabla temporal con los 22 chunks reales y 308 casi-duplicados (ruido 0.05) de otro tenant, e
    índice `CREATE VECTOR INDEX ... TYPE = 'diskann'`. La tabla se elimina al final.
  - Restricciones encontradas al medir:
    - el índice exige al menos 100 vectores, así que no puede indexar el corpus sintético tal cual;
    - `CREATE VECTOR INDEX` no admite transacción de usuario;
    - la versión actual del índice rechaza `TOP_N` y exige `SELECT TOP (k) WITH APPROXIMATE ...
      ORDER BY distance` sin más columnas.
  - Resultado sobre los 21 casos grounded (dev + validation): el filtrado iterativo respeta el
    ámbito (8/8 resultados en ámbito, 0 casos con menos de k), solapamiento 8/8 con la búsqueda
    exacta y recall de documento 1.0 igual que exacta. Latencia p50 en el mismo backend:
    exacta 18.7 ms, DiskANN 17.9 ms.
  - **No adoptado:** no mejora el recall, está en preview y no aplica por debajo de 100 vectores.
    La búsqueda exacta sigue como modo por defecto. La búsqueda exacta del experimento coincide con
    `FabricSqlVectorStore.search` en todos los casos.
- **Sin contenido documental:** el benchmark solo admite la fuente sintética `demo` y
  `_public_case` no publica respuestas. La carga rechaza informes con `answer`, `snippet`, `text` o
  `claims` y los que no referencian el manifiesto del corpus sintético. Los JSON de
  `wrk-task-102` no contienen ninguna de esas claves; el experimento solo publica ids de caso y
  métricas.
- **Limpieza verificada:** en la SQL database solo queda el índice publicado
  `rag_docs__724f6786a9170f8b`, sin tablas `benchmark_*`, `diskann*` ni `contract_*`.
- **Tests del gate por defecto:** backend y modo por perfil, rechazo de backend desconocido en la
  config, y `backend_parity` con paridad y ruptura. `scripts/verify.ps1` en verde (152 tests), y el
  gate público y sus tests superados con el notebook incluido.
- **Fuera del File Scope literal:** `src/rag_docs/benchmark.py` (necesario para configurar el
  benchmark por backend) y `scripts/diskann_experiment.py` (experimento G2 exigido por el criterio).
