---
id: WRK-TASK-016
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, FEAT-RAG-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-031
    relation: depends-on
  - id: WRK-TASK-033
    relation: depends-on
tags: [docker, deployment, configuration]
---

# WRK-TASK-016 — Empaquetado y despliegue reproducible

## Objective

Crear imágenes no-root y Compose con API, worker, PostgreSQL, Redis y Qdrant, manteniendo el
generador como endpoint configurable.

## Acceptance Criteria

- [ ] Imágenes reproducibles, no root y con health checks.
- [ ] Fuentes montadas en solo lectura y persistencia explícita.
- [ ] Secretos fuera de imágenes y Compose.
- [ ] Ollama local, remoto o gateway se selecciona por configuración.

## Evidence

Pendiente.
