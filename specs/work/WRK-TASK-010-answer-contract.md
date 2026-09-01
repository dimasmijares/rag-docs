---
id: WRK-TASK-010
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
created: 2026-08-30
updated: 2026-08-31
owner: rag-docs-team
parent: WRK-PLAN-003
activates: [DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-009
    relation: depends-on
tags: [generation, structured-output, grounding, language]
---

# WRK-TASK-010 — Contrato verificable de respuesta

## Objective

Garantizar idioma, cobertura de preguntas compuestas, conservación literal de identificadores y citas por afirmación.

## File Scope

Incluye `src/rag_docs/generation.py`, `src/rag_docs/query.py`, contratos API relacionados y sus tests. Excluye cambiar embeddings o Qdrant.

## Technical Direction

Salida interna estructurada con estado, idioma, lista de afirmaciones y referencias. Validación determinista antes de renderizar; un único reintento correctivo sólo si falla esquema, idioma o cobertura verificable.

## Acceptance Criteria

- [x] La regresión responde en español con todos los identificadores requeridos.
- [x] Cada afirmación factual tiene una cita válida próxima.
- [x] Las partes sin evidencia se declaran explícitamente.
- [x] Una salida inválida no se etiqueta automáticamente como `grounded`.

## Evidence

- Contrato Pydantic de salida estructurada con estado, idioma, afirmaciones, citas y
  partes sin respuesta en `src/rag_docs/generation.py`.
- Validación determinista previa al renderizado en `src/rag_docs/query.py`: idioma,
  cobertura de preguntas compuestas, referencias existentes e identificadores técnicos
  literales presentes en su evidencia.
- Un único reintento correctivo; después, una respuesta inválida se degrada de forma
  segura. Para preguntas técnicas existe un fallback extractivo explícito y auditable
  que sólo reutiliza líneas citadas de los fragmentos seleccionados.
- La API expone `claims`, `answer_language` y `generation_mode` para distinguir respuestas
  del LLM, fallback extractivo y ausencia de generación sin romper los campos anteriores.
- La regresión de desarrollo local comprobó cobertura completa, identificadores literales e
  idioma; sus hechos y el informe se excluyen del repositorio público.
- La validación reservada superó sus criterios mediante LLM y fallback extractivo; recuentos,
  preguntas, respuestas y métricas detalladas permanecen locales.
- `scripts/verify.ps1`: KDD válido, cero huérfanos, Ruff correcto y 27 pruebas aprobadas
  el 2026-08-31.
