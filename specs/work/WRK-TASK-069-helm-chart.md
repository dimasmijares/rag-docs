---
id: WRK-TASK-069
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
activates: [ARCH-002, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-068
    relation: depends-on
tags: [helm, chart, values, namespaces]
---

# WRK-TASK-069 — Helm chart

## Objective

Definir chart, values, namespaces, labels y helpers para todos los componentes.

## Acceptance Criteria

- [ ] `helm lint` y renderizado determinista superan CI.
- [ ] Values separan core, security y observabilidad opcional.
- [ ] Imágenes, recursos y endpoints son parametrizables.
- [ ] Ningún secreto tiene valor real en el chart.

## Evidence

Pendiente.
