---
id: WRK-TASK-090
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
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

- [ ] `ContextBuilder` concentra selección, deduplicación, priorización técnica, pistas de evidencia
      y construcción de citas, como función pura sobre DTO.
- [ ] `AnswerValidator` concentra validación de grounding y fallback extractivo, como función pura
      sobre DTO.
- [ ] `QueryService` queda como orquestador sobre `RetrievalPort`, `GenerationPort`,
      `GroundingPort` y `AuthorizationPort`.
- [ ] Ninguna de las piezas puras realiza I/O ni conoce Qdrant, Ollama ni FastAPI.
- [ ] Los gold sets y el benchmark producen resultados idénticos a los previos, campo a campo.
- [ ] La cobertura de las piezas puras es superior a la que hoy tiene `QueryService`.

## Evidence

Pendiente.
