---
id: WRK-TASK-070
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-011
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-069
    relation: depends-on
tags: [kubernetes, postgres, redis, qdrant, keycloak]
---

# WRK-TASK-070 — Dependencias de datos en Kubernetes

## Objective

Permitir PostgreSQL, Redis, Qdrant y Keycloak internos o endpoints externos mediante values.

## Acceptance Criteria

- [ ] Cada dependencia tiene modo internal/external mutuamente exclusivo.
- [ ] Readiness evita iniciar consumidores sin dependencias disponibles.
- [ ] PVC, credenciales y endpoints se configuran sin hardcode.
- [ ] El perfil local usa recursos compatibles con 16 GB.

## Evidence

Pendiente.
