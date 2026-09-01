---
id: WRK-TASK-074
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
activates: [ARCH-002, FEAT-RAG-002, DOC-RAG-002, RULE-003]
dependencies:
  - id: WRK-TASK-071
    relation: depends-on
  - id: WRK-TASK-073
    relation: depends-on
tags: [hpa, scaling, load, workers]
---

# WRK-TASK-074 — Escalado Kubernetes

## Objective

Configurar HPA donde proceda y validar cinco usuarios concurrentes y dos workers.

## Acceptance Criteria

- [ ] Señales de escalado y límites evitan thrashing.
- [ ] API y workers pueden escalar de forma independiente.
- [ ] La prueba local documenta saturación y limitaciones físicas.
- [ ] Dependencias stateful no se presentan como HA por ejecutarse en kind.

## Evidence

Pendiente.
