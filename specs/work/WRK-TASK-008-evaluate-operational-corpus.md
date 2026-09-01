---
id: WRK-TASK-008
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-08-30
owner: rag-docs-team
parent: WRK-PLAN-002
activates: [DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-007
    relation: depends-on
tags: [evaluation, gold-set, grounding]
---

# WRK-TASK-008 — Evaluar corpus operativo

## Objective

Derivar preguntas verificables de varios documentos y ejecutar un gold set local contra la API.

## Scope

Incluye inspección local, selección de hechos, evaluación y recomendaciones. Excluye versionar contenido o rutas corporativas.

## Acceptance Criteria

- [x] Las preguntas cubren varios procesos y formatos.
- [x] Cada caso positivo identifica al menos un documento esperado.
- [x] Existe un caso sin evidencia para comprobar la negativa segura.

## Test Plan

Ejecutar el runner de evaluación, revisar fallos y conservar el informe local.

## Evidence

- Gold set local con casos positivos y una negativa sobre varios formatos.
- La ejecución reveló equivalencias documentales y una expectativa textual frágil; se corrigió la
  evaluación sin alterar retrieval ni generación.
- La ejecución final, preguntas, respuestas, rutas y métricas permanecen en artefactos ignorados.
- Suite, lint, validación KDD y control de huérfanos fueron superados localmente.
