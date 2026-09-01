---
id: WRK-TASK-006
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-25
owner: rag-docs-team
parent: WRK-PLAN-001
activates: [DOC-RAG-001, DOM-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-005
    relation: depends-on
tags: [evaluation, operations, documentation]
---

# WRK-TASK-006 — Evaluación y operación

## Objective

Entregar corpus didáctico, gold set, evaluación, Compose y guía reproducible.

## Scope

Incluye ejemplos, evaluación, contenedores, logs y documentación. Excluye infraestructura corporativa.

## Acceptance Criteria

- [x] El gold set mide recuperación de documento y estado de respuesta.
- [x] La guía cubre instalación, ejecución, privacidad y problemas comunes.

## Test Plan

Suite completa, validación KDD y smoke tests condicionados a servicios disponibles.

## Evidence

- Corpus de seis formatos y gold set de cuatro casos creados.
- 17 pruebas, lint, grafo KDD y validación de Compose superados.
- Gold set didáctico ejecutado 4/4 con Qdrant y Ollama locales.
- Validación complementaria con corpus operativo ejecutada 6/6 en `WRK-SPEC-002`.

## Traceability

Implementado en `evaluation/`, `examples/corpus/demo/`, `compose.yaml` y `README.md`.
