---
id: WRK-PLAN-004
type: spec
layer: work-plan
scope: ephemeral
status: active
confidence: low
version: 0.2.0
created: 2026-08-30
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-SPEC-004
activates: [ARCH-001, ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-001, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [corporate-plan, security, operations, connectors]
---

# WRK-PLAN-004 — Plan de industrialización corporativa

## Architecture Approach

Aplicar una secuencia orgánica: publicar la baseline, hacer durable el runtime, mejorar calidad,
introducir seguridad, endurecer operación, extraer servicios y finalmente desplegar en Kubernetes.

## Task Decomposition

| Orden | Plan | Release | Resultado |
|---:|---|---|---|
| 1 | WRK-PLAN-005 | v0.2.0 | Portfolio público saneado y evaluable |
| 2 | WRK-PLAN-012 | v0.3.0 | Invariantes de índice, contratos y calidad medida |
| 3 | WRK-PLAN-006 | v1.0.0 | API y worker asíncrono durable |
| 4 | WRK-PLAN-007 | v1.1.0 | Documentos visuales y streaming |
| 5 | WRK-PLAN-008 | v1.5.0 | OIDC y ACL funcionales |
| 6 | WRK-PLAN-009 | v2.0.0 | Operación corporativa observable |
| 7 | WRK-PLAN-010 | v2.5.0 | Servicios extraídos según el gate de `WRK-TASK-088` |
| 8 | WRK-PLAN-011 | v3.0.0 | Plataforma Helm sobre `kind` |

## Critical Ordering

- Cada plan sólo comienza cuando el gate de la release anterior está consolidado.
- Los invariantes preceden a la infraestructura que los da por supuestos: fingerprint antes del
  ledger documental, modelo de tenant antes del esquema PostgreSQL, contratos antes de la
  extracción de servicios.
- La evidencia de calidad precede a la decisión de industrializar.
- Seguridad precede a conectores corporativos; contratos preceden a microservicios.
- Instrumentación precede a capacidad; restore precede a disaster recovery.
- La extracción de una frontera exige evidencia de escalado, aislamiento, ciclo de despliegue o
  seguridad; sin ella, la frontera permanece como contrato en proceso.

## Evidence

La descomposición y sus dependencias están registradas en los planes 005 a 012.

La reordenación de la secuencia y sus motivos están registrados en `ADR-RAG-007`; los invariantes
que la justifican, en `ADR-RAG-008` a `ADR-RAG-011`.
