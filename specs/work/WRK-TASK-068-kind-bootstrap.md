---
id: WRK-TASK-068
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
activates: [ARCH-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-067
    relation: depends-on
tags: [kind, kubernetes, bootstrap, images]
---

# WRK-TASK-068 — Bootstrap de kind

## Objective

Crear un clúster `kind` reproducible y un flujo de carga de imágenes locales adecuado al portátil.

## Acceptance Criteria

- [ ] Crear y eliminar el clúster es idempotente y documentado.
- [ ] Puertos, nodos y recursos tienen valores conservadores.
- [ ] Las imágenes locales se cargan sin registry externo.
- [ ] Prerrequisitos fallan con diagnóstico claro.

## Evidence

Pendiente.
