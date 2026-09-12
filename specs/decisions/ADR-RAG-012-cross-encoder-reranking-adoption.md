---
id: ADR-RAG-012
type: adr
layer: adr
scope: persistent
status: accepted
confidence: medium
version: 0.3.0
created: 2026-09-12
updated: 2026-09-12
owner: rag-docs-team
dependencies:
  - id: RFC-001
    relation: constrained-by
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-001
    relation: implements
  - id: WRK-TASK-038
    relation: implements
tags: [architecture-decision, retrieval, reranking, evaluation, review]
---

# ADR-RAG-012 — Adopción de reranking por cross-encoder

## Context

`RFC-001` (gate G2 Retrieval) exige que un reranker sólo se añada "ante mejora medible", el mismo
criterio ya aplicado en `WRK-TASK-037` para hybrid retrieval. `WRK-TASK-038` mide un cross-encoder
sobre el pipeline `dense` (la estrategia de retrieval que sigue siendo la de producción tras
`WRK-TASK-037`) en dos gold sets independientes: `gold-set.dev.yaml` (16 casos, usado para explorar
la configuración) y `gold-set.validation.yaml` (8 casos, held-out, nunca usado para ajustar
parámetros — es el conjunto que decide, no el que orienta).

## Options Considered

- **(a) No reranking.** Mantiene el pipeline `dense` de `v0.2.0`/`v0.3.0` sin cambios.
- **(b) Reranking siempre activo por defecto.** Cambia el comportamiento observable de cualquier
  despliegue existente sin que el operador lo pida: descarga un modelo nuevo en el primer arranque y
  añade latencia a cada consulta.
- **(c) Reranking implementado y medido, expuesto como capacidad configurable, apagada por
  defecto.** Mismo patrón que `retrieval_strategy` en `WRK-TASK-037`: la capacidad existe, está
  probada y documentada, pero no se activa sola.

## Decision

**Opción (c), adoptado como capacidad opt-in.** `src/rag_docs/reranking.py` implementa
`CrossEncoderReranker` reutilizando `sentence-transformers` (dependencia ya presente para
`embeddings.py` — ningún paquete nuevo, mismo criterio de `WRK-TASK-037` para evitar el gate de
`dependency-review`). El modelo es *lazy-loaded* y **falla en modo seguro** (AC3): si la carga o el
`predict()` lanzan cualquier excepción, `rerank()` devuelve los hits originales sin reordenar en
lugar de interrumpir la consulta — una falta de red o un nombre de modelo incorrecto degradan a
retrieval sin reranking, nunca a un error de usuario. `QueryService` gana `reranker: Reranker | None
= None` y `rerank_top_n`; por defecto no cambia nada (mismo principio que `retrieval_strategy`).
`Settings` gana `reranker_model`/`rerank_top_n` (`None` por defecto) y `ApplicationContainer` los
conecta cuando el operador los declara.

**Resultado medido** (`config/benchmark-038-reranking.yaml`, perfiles `dense-baseline` vs.
`dense-reranked` con `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` — multilingüe, coherente con
`intfloat/multilingual-e5-small`, sobre el mismo corpus/fingerprint que la baseline de `v0.2.0`;
evidencia reproducible en `evaluation/benchmarks/wrk-task-038/{dev,validation}-comparison.json`):

- **Validación (el conjunto que decide, AC2):** `recall_at_1` 0.75 → 0.917, `precision_at_1` 0.833 →
  1.0, `recall_at_3`/`recall_at_5` 0.917 → 1.0, `reciprocal_rank`/MRR 0.917 → 1.0, `precision_at_8`
  0.167 → 0.267. **Ninguna métrica retrocede en ningún corte** — a diferencia del resultado mixto de
  `WRK-TASK-037`, éste es un caso limpio de "mejora medible".
- **Desarrollo:** mismo patrón (`recall_at_1` 0.571 → 0.643, MRR 0.729 → 0.798, sin regresiones).
- **Coste (latencia, estado `warm`, medido por separado del resto vía `rerank_ms`):** el reranking
  añade ~112–171 ms de mediana por consulta (cross-encoder de 12 capas sobre CPU, `top_k=8` pares) —
  el total pasa de ~30 ms a ~140–215 ms de mediana. El coste depende de `top_k`, no del tamaño del
  corpus (el reranker sólo puntúa lo que `dense` ya recuperó), así que no crece con la indexación de
  más documentos. Es una fracción pequeña frente a los "cientos de ms" de generación real ya
  documentados en `WRK-TASK-037`, pero es un incremento relativo grande frente al retrieval solo, y
  no hay hoy un SLA de latencia declarado contra el que contrastarlo.
- **Memoria:** sin diferencia atribuible más allá de la carga del modelo cross-encoder (unas decenas
  de MB, del mismo orden que el embedder).

## Consequences

Se adopta la capacidad, no el valor por defecto. Cualquier despliegue existente de `v0.3.0` sigue
funcionando exactamente igual tras actualizar, sin descargar ningún modelo nuevo ni cambiar
latencia, hasta que un operador declare `RAG_DOCS_RERANKER_MODEL`. Esto es deliberado: activar
reranking por defecto forzaría una descarga de modelo en el primer arranque de cualquier entorno
(incluidos entornos sin acceso a Hugging Face) y un cambio de latencia no solicitado — el mismo tipo
de sorpresa que `RULE-004` existe para evitar en el índice, aplicado aquí a un cambio de
comportamiento en tiempo de consulta.

Se recomienda activar `reranker_model=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` en despliegues
donde la latencia adicional (~150 ms de mediana) sea aceptable frente a la mejora de
`recall_at_1`/MRR observada, especialmente en corpus con muchos documentos similares donde el
primer resultado denso no siempre es el más relevante. `WRK-TASK-091` decide si la release v0.3.0
la activa como valor por defecto en algún entorno de referencia (README/`DOC-RAG-001`) o la deja
documentada como opción.

Riesgo aceptado: la medición se hizo sobre el corpus sintético `demo` (v0.2.0, 10 documentos). Un
corpus de producción con miles de documentos y mayor solapamiento semántico podría mostrar una
mejora distinta (probablemente mayor, dado que el reranking ayuda más cuando el retrieval denso
trae más falsos positivos en el top-k) — no hay evidencia de que empeore, pero tampoco de que la
magnitud exacta se sostenga fuera del PoC.

## Work Impact

Ninguna tarea nueva creada: `WRK-TASK-038` cierra con este ADR como su Acceptance Criterion de
decisión documentada. `WRK-TASK-091` hereda la recomendación de activación como parte de su
consolidación de calidad de `v0.3.0`.
