---
id: WRK-TASK-112
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-014
activates: [DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-102
    relation: depends-on
  - id: WRK-TASK-110
    relation: depends-on
tags: [evaluation, llm-as-judge, delta]
---

# WRK-TASK-112 — LLM-as-judge en evaluación

## Objective

Puntuar en batch las respuestas del benchmark con el LLM local como complemento de las métricas
deterministas.

## File Scope

Incluye prompts y rúbrica versionados, la integración con la cola y las tablas Delta de resultados.
Excluye sustituir métricas deterministas.

## Acceptance Criteria

- [ ] Las puntuaciones se guardan en Delta junto a las métricas deterministas del mismo informe.
- [ ] El acuerdo entre juez y métricas deterministas queda medido y documentado.
- [ ] La rúbrica y el modelo juez forman parte de la clave de comparabilidad del informe.

## Evidence

Pendiente.
