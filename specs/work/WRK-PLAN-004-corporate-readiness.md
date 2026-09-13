---
id: WRK-PLAN-004
type: spec
layer: work-plan
scope: ephemeral
status: active
confidence: low
version: 0.3.0
created: 2026-08-30
updated: 2026-09-13
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
| 3 | WRK-PLAN-013 | v0.4.0 | Backend neutral y plano de evaluación en Fabric |
| 4 | WRK-PLAN-006 | v1.0.0 | API y worker asíncrono durable |
| 5 | WRK-PLAN-014 | v1.1.0 | Plano de indexación en Fabric |
| 6 | WRK-PLAN-007 | v1.2.0 | Documentos visuales y streaming |
| 7 | WRK-PLAN-008 | v1.5.0 | OIDC y ACL funcionales |
| 8 | WRK-PLAN-009 | v2.0.0 | Operación corporativa observable |
| 9 | WRK-PLAN-010 | v2.5.0 | Servicios extraídos según el gate de `WRK-TASK-088` |
| 10 | WRK-PLAN-011 | v3.0.0 | Plataforma Helm sobre `kind` |

## Critical Ordering

- Cada plan sólo comienza cuando el gate de la release anterior está consolidado.
- Las costuras de backend y el ledger portable (`v0.4.0`) preceden al esquema PostgreSQL de
  `v1.0.0`; el perfil Fabric es opcional y ningún gate obligatorio depende de él.
- Los invariantes preceden a la infraestructura que los da por supuestos: fingerprint antes del
  ledger documental, modelo de tenant antes del esquema PostgreSQL, contratos antes de la
  extracción de servicios.
- La evidencia de calidad precede a la decisión de industrializar.
- Seguridad precede a conectores corporativos; contratos preceden a microservicios.
- Instrumentación precede a capacidad; restore precede a disaster recovery.
- La extracción de una frontera exige evidencia de escalado, aislamiento, ciclo de despliegue o
  seguridad; sin ella, la frontera permanece como contrato en proceso.

## Evidence

La descomposición y sus dependencias están registradas en los planes 005 a 014.

La reordenación de la secuencia y sus motivos están registrados en `ADR-RAG-007`; los invariantes
que la justifican, en `ADR-RAG-008` a `ADR-RAG-011`. La incorporación del perfil opcional de
Microsoft Fabric (`v0.4.0`, `v1.1.0`) y la renumeración de multimodal a `v1.2.0` están registradas
en `RFC-004`, con el backend vectorial y ledger por perfil en `ADR-RAG-013` y la inferencia local
por modelo pull en `ADR-RAG-014`.
