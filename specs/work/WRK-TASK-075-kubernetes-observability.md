---
id: WRK-TASK-075
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
activates: [ARCH-002, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-071
    relation: depends-on
  - id: WRK-TASK-052
    relation: depends-on
tags: [kubernetes, telemetry, dashboards, optional]
---

# WRK-TASK-075 — Observabilidad Kubernetes

## Objective

Desplegar telemetría y dashboards opcionales dentro de Kubernetes con presupuestos explícitos.

## Acceptance Criteria

- [ ] Core/security funcionan sin instalar observabilidad.
- [ ] Dashboards cubren API, jobs, servicios y dependencias.
- [ ] Retención y redacción se aplican dentro del clúster.
- [ ] Exportación a backends externos se configura por values.

## Evidence

Pendiente.
