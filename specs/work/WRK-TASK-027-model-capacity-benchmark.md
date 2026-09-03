---
id: WRK-TASK-027
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-01
updated: 2026-09-03
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [ARCH-001, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-012
    relation: depends-on
  - id: WRK-TASK-026
    relation: depends-on
tags: [benchmark, llm, embeddings, latency, memory]
---

# WRK-TASK-027 — Baseline local reproducible

## Objective

Establecer en el portátil una baseline reproducible comparando el generador local 3B, embeddings
compatibles con sus recursos y fallback mediante métricas de calidad, p50/p95, memoria y
configuración efectiva.

## File Scope

Incluye runner, configuración, bloqueo de decisión y resultados sintéticos de benchmark
reproducibles en este portátil desde un clon limpio. Excluye modelos 14B, ejecuciones dependientes
del PC personal o de un endpoint remoto, modificar el split de validación, publicar resultados
locales privados o adoptar hybrid/reranking.

## Acceptance Criteria

- [x] Separar latencia de embedding, retrieval, grounding y generación.
- [x] Comparar sobre desarrollo sólo configuraciones ejecutables íntegramente en el portátil:
  generador 3B, embeddings compatibles y fallback explícito.
- [x] Seleccionar modelos y parámetros exclusivamente sobre desarrollo y bloquear la decisión
  antes de consultar validación.
- [x] Ejecutar validación una sola vez como confirmación, sin modificarla ni repetir la selección
  tras conocer resultados.
- [x] Registrar runs cold/warm, hardware, revisión, parámetros, semillas, memoria y errores de
  forma reproducible y publicable.
- [x] Recomendar la baseline local, documentar sus límites y verificar el procedimiento desde un
  clon limpio sin depender del PC personal.

## Evidence

- `src/rag_docs/benchmark.py` añade el runner `rag-docs-benchmark` con fases ordenadas
  `development` → `lock` → `validation` → `verify`. `config/benchmark.yaml` declara los tres
  perfiles ejecutables en el portátil: `qwen-3b-balanced` y `qwen-3b-compact` (ambos
  `intfloat/multilingual-e5-small` + `qwen2.5:3b` con distinto `retrieval_top_k`/`context_chunks`)
  y `extractive-fallback-control` (mismo retrieval, generación forzada al fallback extractivo). El
  runner rechaza endpoints no loopback, fuentes distintas de `demo`, digest de modelo inesperado,
  generadores que no sean 3B y corpus que no cuadre con `examples/corpus/demo/manifest.sha256`.
- Adaptadores `TimedEmbedder`/`TimedStore`/`TimedGenerator` separan `embedding` (`embed_query`),
  `retrieval` (búsqueda vectorial) y `generation` (llamadas al modelo); `grounding` es el residuo
  local de selección de contexto, validación de afirmaciones, render y fallback. `MemorySampler`
  registra pico RSS del proceso y pico de RAM del host; `/api/ps` aporta residencia del modelo en
  Ollama. El primer caso de cada perfil es `cold` tras desalojar el modelo (`keep_alive: 0`); el
  resto `warm`.
- Fase `development` (16 casos, `evaluation/gold-set.dev.yaml`), resultados en
  `evaluation/benchmarks/wrk-task-027/dev-results.json`: `qwen-3b-balanced` y `qwen-3b-compact`
  empatan a 13/16 (`score` 0.8125) con Recall@8 = 1.0 en todos los casos —los tres fallos son de
  `generation`, nunca de recuperación—; el control de fallback saca 3/16, lo que justifica el LLM.
  Latencias `qwen-3b-balanced`: `embedding` p50 53 ms / p95 2040 ms (primer cold), `retrieval` p50
  3 ms, `grounding` p50 5 ms, `generation` p50 34,6 s / p95 68,6 s; RSS de proceso ≤ ~0,95 GiB;
  residencia del modelo en Ollama ≈ 2064 MB.
- Fase `lock` (`decision-lock.json`): la regla `score → recall_at_8 → -p95` selecciona
  `qwen-3b-balanced` (mejor p95 total con score y Recall@8 empatados). El lock fija los SHA-256 de
  configuración, ambos gold sets, corpus, fuentes y del informe `development`, y `revision` del
  commit; `validation` sólo se ejecuta si todos coinciden.
- Fase `validation` (8 casos, ejecutada **una sola vez**, `validation-results.json`): sólo el
  perfil bloqueado, `score` 0.5 (4/8), Recall@8 = 1.0, MRR 0.92; los 4 fallos vuelven a ser de
  `generation`. `execute_validation` aborta si el fichero ya existe y `verify` confirma fase,
  perfil único, coincidencia con el lock y hashes (`rag-docs-benchmark verify` → 9/9 checks).
- Recomendación de baseline y límites documentados en el bloque «Benchmark local reproducible» de
  `README.md`: la baseline local es `qwen-3b-balanced`; el cuello de botella es la generación 3B
  (calidad y p95), no el retrieval; los p50/p95 son descriptivos y dependen de carga/energía; la
  comparación con un 14B se difiere a `WRK-TASK-081`. El procedimiento desde un clon limpio
  (`uv sync` → `ollama pull qwen2.5:3b` → `generate_demo_corpus.py --check` → `rag-docs-benchmark
  verify`) no depende del PC personal.
- Los JSON publicados sólo contienen IDs sintéticos, métricas, `generation_mode`, `failure_stage`,
  configuración efectiva y hardware saneado (familia de SO, arquitectura, recuento de CPU, bucket
  de RAM); sin preguntas, respuestas, prompts, fragmentos, rutas, hostname, usuario ni PID.
- Gates locales verdes: `ruff`, `pytest` (54), `kdd validate` (126 specs, 873 edges, 0 huérfanos),
  lifecycle KDD y gate de publicación sobre los artefactos nuevos.

## Deferred Work

La comparación con un 14B ejecutado en el PC personal queda fuera del gate de `v0.2.0` y se
realizará, cuando ese equipo esté disponible, mediante `WRK-TASK-081`. No se publicarán resultados
14B simulados ni se presentará esa configuración como verificada antes de ejecutarla.
