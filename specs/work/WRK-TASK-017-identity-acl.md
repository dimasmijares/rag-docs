---
id: WRK-TASK-017
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, RULE-001, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-042
    relation: depends-on
tags: [identity, authorization, acl, security]
---

# WRK-TASK-017 — Contratos de identidad

## Objective

Definir `Principal`, `AuthProvider` y modos explícitos `development`/`oidc` sin implementar aún
la política documental completa.

## Acceptance Criteria

- [ ] `Principal` normaliza usuario, tenant, grupos, roles y claims.
- [ ] `AuthProvider` desacopla FastAPI del IdP.
- [ ] Producción rechaza el modo development.
- [ ] Tests cubren principal válido, ausente y mal configurado.

## Evidence

Pendiente.
