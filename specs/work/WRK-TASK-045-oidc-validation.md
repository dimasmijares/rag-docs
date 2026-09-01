---
id: WRK-TASK-045
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [FEAT-RAG-003, RULE-003]
dependencies:
  - id: WRK-TASK-044
    relation: depends-on
tags: [jwt, jwks, issuer, audience]
---

# WRK-TASK-045 — Validación OIDC

## Objective

Validar JWT/JWKS, issuer, audience, expiración, roles y grupos y producir `Principal`.

## Acceptance Criteria

- [ ] Tokens expirados, firma inválida o audiencia incorrecta se rechazan.
- [ ] Rotación JWKS tiene caché y recuperación controladas.
- [ ] Claims se normalizan sin confiar en cabeceras externas.
- [ ] Tests integran Keycloak real.

## Evidence

Pendiente.
