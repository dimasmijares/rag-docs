---
id: WRK-TASK-044
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
activates: [ARCH-002, FEAT-RAG-003, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-017
    relation: depends-on
tags: [keycloak, oidc, realm, compose]
---

# WRK-TASK-044 — IdP Keycloak local

## Objective

Crear realm, clientes, usuarios, grupos y roles reproducibles sin secretos publicados.

## Acceptance Criteria

- [ ] Importar el realm produce el mismo entorno local.
- [ ] Existen clientes separados para web y servicios.
- [ ] Fixtures multiusuario cubren grupos y tenants sintéticos.
- [ ] Credenciales de desarrollo están claramente aisladas de producción.

## Evidence

Pendiente.
