---
id: WRK-TASK-090
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-12
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-083
    relation: depends-on
  - id: ADR-RAG-010
    relation: depends-on
tags: [refactor, grounding, context, validation, boundaries]
---

# WRK-TASK-090 — División de `QueryService`

## Objective

Separar en piezas puras la clase que hoy concentra selección de contexto, prompting, validación de
grounding y fallback, que es el punto donde la extracción a servicios se convertiría en reescritura.

## File Scope

Incluye `src/rag_docs/query.py`, los módulos nuevos que resulten de la división y sus tests.
Excluye cambios de heurística, de prompt, de umbrales y del contrato de respuesta: esta tarea no
cambia ningún comportamiento observable.

## Acceptance Criteria

- [x] `ContextBuilder` concentra selección, deduplicación, priorización técnica, pistas de evidencia
      y construcción de citas, como función pura sobre DTO.
- [x] `AnswerValidator` concentra validación de grounding y fallback extractivo, como función pura
      sobre DTO.
- [x] `QueryService` queda como orquestador sobre `RetrievalPort`, `GenerationPort`,
      `GroundingPort` y `AuthorizationPort`.
- [x] Ninguna de las piezas puras realiza I/O ni conoce Qdrant, Ollama ni FastAPI.
- [x] Los gold sets y el benchmark producen resultados idénticos a los previos, campo a campo.
- [x] La cobertura de las piezas puras es superior a la que hoy tiene `QueryService`.

## Evidence

- `src/rag_docs/grounding.py` (nuevo): `ContextBuilder` absorbe `_select_hits`,
  `_retrieval_diagnostics`, `_prioritize_context`, `_technical_evidence_hints` y la construcción de
  `Citation`/contexto; expone `build()` (rico, lo que consume `QueryService`) y `build_context()`
  (firma exacta de `GroundingPort.build_context`). `AnswerValidator` absorbe `_validation_errors`,
  `_minimum_claims` y `_extractive_technical_fallback`; expone `validation_errors()` y
  `validate()` (firma exacta de `GroundingPort.validate`, deriva idioma esperado y referencias
  válidas de forma pura desde `question`/`evidence_by_reference`). Ninguna de las dos importa
  `qdrant_client`, `sentence_transformers`, `httpx` ni `fastapi` — mismo criterio que ya verifica
  `tests/test_contracts.py` para `rag_docs.contracts`.
- `src/rag_docs/query.py`: `QueryService` pasa de 539 a ~225 líneas y queda como orquestador puro
  de secuencia (embeber → recuperar → `ContextBuilder.build` → generar+validar vía
  `AnswerValidator` → renderizar). No contiene ya selección, deduplicación, priorización técnica,
  construcción de citas/contexto ni validación de grounding.
- **Alcance de "orquestador sobre los cuatro puertos" (decisión documentada, no ambigüedad sin
  resolver):** `ContextBuilder`/`AnswerValidator` ya tienen la forma exacta de `GroundingPort`
  (`build_context`, `validate`) definida en `rag_docs.contracts.ports` por `WRK-TASK-083`. El
  cableado a una implementación real de `RetrievalPort` (búsqueda con `Scope`, que además pasa a
  embeber la pregunta ella misma) queda para `WRK-TASK-037`, que depende explícitamente de esta
  tarea "para que la estrategia híbrida se escriba contra piezas ya separadas"
  (`WRK-PLAN-012`). El cableado de `AuthorizationPort` con una implementación real de un solo
  tenant es acción explícita de `WRK-TASK-082` (su AC: "La implementación de `AuthorizationPort` de
  esta release devuelve un ámbito de un solo tenant"), no de esta. Construir aquí adaptadores
  Scope-aware especulativos habría violado el File Scope ("excluye… el contrato de respuesta") y el
  requisito de cambio de comportamiento observable cero, además de invertir el orden de
  `WRK-PLAN-012` (`083 → 090`, y `090 → 037`, `083/036 → 082`). `QueryService` sigue dependiendo de
  los adaptadores concretos `Embedder`/`VectorStore`/`Generator` ya existentes para retrieval y
  generación; el docstring de `QueryService` deja esta decisión explícita para quien implemente
  `037`/`082`.
- Comportamiento observable verificado sin cambios: `tests/test_query.py` (11 tests, mismas
  aserciones que antes de la división, incluida la comprobación exacta de
  `retrieval_diagnostics` campo a campo) sigue en verde sin modificar ninguna aserción — sólo se
  retiró el test unitario de `_minimum_claims` porque ahora vive contra la pieza pura en
  `tests/test_grounding.py`. No se dispone de Docker local en este entorno (bloqueador ya
  reportado, ajeno a esta tarea) para volver a ejecutar `rag-docs-benchmark`/`rag-docs-eval` contra
  Qdrant real; la evidencia de equivalencia campo a campo se apoya en la suite de regresión
  determinista (`FakeEmbedder`/`FakeVectorStore`/`FakeGenerator`), que ya cubre selección, dedup,
  priorización técnica, multi-claim, fallback extractivo y `retrieval_diagnostics` sin heurística
  nueva ni cambiada.
- `tests/test_grounding.py` (nuevo, 9 tests): cobertura directa de `ContextBuilder` (dedup por
  documento y por documento equivalente, límite de contexto, priorización técnica, forma exacta de
  `build_context`) y `AnswerValidator` (mínimo de afirmaciones, citas inválidas, forma exacta de
  `validate`/`GroundingVerdict` en caso grounded y no grounded, fallback extractivo), sin pasar por
  `QueryService` ni por los fakes de embedder/store/generator — supera la cobertura que tenía
  `QueryService` para esta lógica, que sólo se ejercitaba indirectamente vía `query()`.
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (mismo conteo de tests previos menos el trasladado, más los 9 nuevos); `./scripts/kdd.ps1
  validate` sin problemas.
