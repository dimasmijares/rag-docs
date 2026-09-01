---
id: ADR-004
type: adr
layer: adr
scope: persistent
status: accepted
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-003
    relation: implements
  - id: DOM-RAG-002
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
tags: [architecture-decision, oidc, keycloak, acl]
---

# ADR-004 — OIDC local con Keycloak y ACL documental

## Context

El portfolio debe demostrar autenticación real e independencia del proveedor corporativo.

## Decision

Usar OIDC estándar, Keycloak como IdP local reproducible y ACL por documento normalizadas a
tenant, usuarios, grupos, clasificación e herencia. El modo development queda limitado a
entornos no productivos.

## Consequences

La aplicación puede cambiar a otro IdP mediante issuer, audience y JWKS. Las colecciones previas
deben reconstruirse al introducir ACL.
