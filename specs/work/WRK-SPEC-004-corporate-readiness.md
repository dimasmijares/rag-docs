---
id: WRK-SPEC-004
type: spec
layer: work-spec
scope: ephemeral
status: active
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-001, ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-001, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: WRK-SPEC-003
    relation: depends-on
tags: [corporate, security, deployment, operations]
---

# WRK-SPEC-004 — Preparación corporativa

## Problem Statement

La PoC es monousuario y local; no dispone todavía de ejecución persistente, identidad, permisos documentales, conectores corporativos, auditoría ni recuperación operativa.

## Proposed Change

Industrializar la solución mediante releases verificables: primero procesos asíncronos y
seguridad, después operación corporativa, extracción de ocho servicios y despliegue en Kubernetes.

## Entry Criteria

- Contratos de calidad y proveedor estabilizados por `WRK-SPEC-003`.
- Usuarios, concurrencia, repositorios, SLO y clasificación de datos definidos.
- Responsables corporativos de identidad, red, seguridad y operación identificados.

## Acceptance Criteria

- [x] Las releases `v0.2.0` a `v3.0.0` tienen work spec, plan, dependencias y gate explícitos.
- [ ] Despliegue reproducible y persistente con separación de secretos.
- [ ] Autenticación y ACL impiden recuperar contenido no autorizado.
- [ ] Conectores preservan identidad, versión, permisos y sincronización incremental.
- [ ] Métricas, auditoría, backups, restauración y CI/CD están probados.

## Evidence

- Roadmap aprobado en `RFC-002`; ejecución pendiente de `WRK-PLAN-004`.
- `WRK-TASK-023` validó los work specs, planes, dependencias y gates de `v0.2.0` a `v3.0.0`.
