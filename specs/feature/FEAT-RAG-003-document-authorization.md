---
id: FEAT-RAG-003
type: spec
layer: feature
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: FEAT-RAG-001
    relation: extends
  - id: ARCH-002
    relation: implements
  - id: DOM-RAG-002
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
tags: [feature, oidc, acl, authorization]
---

# FEAT-RAG-003 — Identidad y autorización documental

## Intent

Autenticar personas y servicios y filtrar toda evidencia por tenant y ACL antes del retrieval.

## Definition

El modo `development` proporciona una identidad explícita sólo en entornos permitidos. El modo
`oidc` valida firma, issuer, audience, expiración, roles y grupos mediante JWT/JWKS. El motor de
autorización produce un ámbito de búsqueda sin revelar información documental.

## Acceptance Criteria

- Producción no inicia con autenticación deshabilitada.
- Un usuario no autorizado no recibe hit, título, cita, texto ni confirmación de existencia.
- Los servicios validan tokens y no confían en cabeceras de identidad inventadas.
- Keycloak demuestra el flujo local sin acoplar el código a un IdP concreto.
