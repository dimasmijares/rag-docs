---
id: WRK-SPEC-010
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-009
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ADR-003
    relation: depends-on
  - id: ADR-004
    relation: depends-on
  - id: ADR-006
    relation: depends-on
tags: [release, v2.5.0, microservices, contracts]
---

# WRK-SPEC-010 — Ocho servicios v2.5.0

## Proposed Change

Extraer ocho servicios con contratos `/v1`, imágenes, health checks, seguridad servicio a servicio
y trazas distribuidas.

## Acceptance Criteria

- [ ] Cada servicio tiene contrato, imagen, liveness, readiness y pruebas.
- [ ] Sólo los servicios autorizadores reciben el token de usuario cuando es necesario.
- [ ] El resto usa OAuth2 client credentials y valida tokens.
- [ ] Fallos parciales producen errores explícitos y retries acotados.

## Evidence

Pendiente de `WRK-PLAN-010`.
