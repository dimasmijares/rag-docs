---
id: WRK-TASK-009
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-08-30
owner: rag-docs-team
parent: WRK-PLAN-003
activates: [DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-PLAN-003
    relation: implements
tags: [evaluation, regression, language, completeness]
---

# WRK-TASK-009 — Evaluación v2 y caso de regresión

## Objective

Evitar que una respuesta parcial o en un idioma incorrecto apruebe el gold set.

## File Scope

Incluye `src/rag_docs/evaluation.py`, `src/rag_docs/language.py`, `evaluation/`, `tests/test_evaluation.py` y evidencia KDD. Excluye generación y retrieval productivos.

## Acceptance Criteria

- [x] Un caso admite `required_facts` múltiples, documentos alternativos y `expected_language`.
- [x] Se separan métricas de retrieval, cobertura, idioma, citas y estado.
- [x] La respuesta defectuosa reproducida falla por cobertura e idioma.
- [x] Existen conjuntos separados de desarrollo y validación para reducir sobreajuste.

## Test Strategy

Tests unitarios del evaluador y ejecución baseline con el generador actual.

## Evidence

- Evaluador v2 retrocompatible implementado con métricas separadas de estado, retrieval, hechos, idioma y citas.
- Pruebas unitarias superadas, incluida una regresión sintética equivalente a la salida defectuosa.
- La baseline local confirmó retrieval, estado y citas correctos, pero cobertura e idioma
  incorrectos; el informe detallado está ignorado.
- Gold sets privados separados en desarrollo y validación, ambos excluidos del repositorio.
