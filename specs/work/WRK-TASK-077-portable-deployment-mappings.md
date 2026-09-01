---
id: WRK-TASK-077
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
  - id: WRK-TASK-069
    relation: depends-on
  - id: WRK-TASK-073
    relation: depends-on
tags: [cloud-neutral, azure, aws, server, values]
---

# WRK-TASK-077 — Mappings de despliegue portable

## Objective

Mapear values y dependencias a servidor corporativo, Azure y AWS sin acoplar el núcleo.

## Acceptance Criteria

- [ ] Tabla mapea identidad, datos, secretos, gateway, telemetría y modelos.
- [ ] El chart acepta endpoints gestionados sin templates específicos de proveedor.
- [ ] Privacidad y residencia de datos se presentan como decisiones de despliegue.
- [ ] No se afirma que los mappings sean despliegues certificados.

## Evidence

Pendiente.
