---
id: WRK-TASK-088
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [ARCH-002, DOC-RAG-002]
dependencies:
  - id: WRK-TASK-055
    relation: depends-on
  - id: ADR-RAG-007
    relation: depends-on
tags: [decision-gate, microservices, evidence, scaling]
---

# WRK-TASK-088 — Gate de decisión de extracción de servicios

## Objective

Convertir la extracción a microservicios de `v2.5.0` en una decisión con evidencia, frontera a
frontera, en lugar de un objetivo asumido de antemano.

## File Scope

Incluye el informe de decisión, los criterios por frontera y la actualización de `WRK-SPEC-010` y
`WRK-PLAN-010` con el alcance resultante. Excluye cualquier implementación de servicio.

## Acceptance Criteria

- [ ] Se declaran los criterios que justifican extraer una frontera: perfil de escalado divergente
      medido, aislamiento de fallo requerido, ciclo de despliegue independiente o frontera de
      seguridad.
- [ ] Cada una de las ocho fronteras de `ARCH-002` se evalúa contra esos criterios usando los datos
      de carga y SLO de `WRK-TASK-055`.
- [ ] El informe distingue de forma explícita las fronteras justificadas por evidencia técnica de
      las justificadas por el objetivo de portfolio de `RFC-002`.
- [ ] El alcance resultante de `WRK-SPEC-010` queda fijado antes de abrir su primera tarea.
- [ ] Las fronteras no extraídas conservan su contrato en proceso y la decisión queda documentada
      como reversible.

## Evidence

Pendiente.
