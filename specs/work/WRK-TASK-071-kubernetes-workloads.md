---
id: WRK-TASK-071
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
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-069
    relation: depends-on
tags: [kubernetes, deployments, services, probes, pvc]
---

# WRK-TASK-071 — Workloads Kubernetes

## Objective

Crear Deployments, Services, Jobs, probes, recursos y PVC para servicios y evaluation runner.

## Acceptance Criteria

- [ ] Cada servicio tiene requests/limits, liveness y readiness.
- [ ] Workers y Jobs terminan de forma cooperativa.
- [ ] ConfigMaps y Secrets se montan con mínimo alcance.
- [ ] LLM externo es el valor recomendado en el perfil local.

## Evidence

Pendiente.
