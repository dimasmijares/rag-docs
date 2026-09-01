---
id: WRK-SPEC-008
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-007
    relation: depends-on
  - id: ADR-004
    relation: depends-on
tags: [release, v1.5.0, oidc, acl]
---

# WRK-SPEC-008 — Seguridad preparada v1.5.0

## Proposed Change

Introducir contratos de identidad, Keycloak/OIDC y ACL por documento con autorización fail-closed
antes del retrieval.

## Acceptance Criteria

- [ ] Producción no inicia sin autenticación válida.
- [ ] Casos multiusuario y multitenant prueban aislamiento sin canales laterales.
- [ ] Colecciones previas se reconstruyen con tenant y ACL.
- [ ] Cambiar de IdP sólo requiere configuración estándar OIDC.

## Evidence

Pendiente de `WRK-PLAN-008`.
