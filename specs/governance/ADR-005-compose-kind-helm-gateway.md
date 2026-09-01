---
id: ADR-005
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
  - id: DOC-RAG-002
    relation: implements
tags: [architecture-decision, compose, kind, helm, gateway-api]
---

# ADR-005 — Compose, kind, Helm y Gateway API

## Context

Se necesita un camino local simple y otro que simule una plataforma corporativa portable.

## Decision

Conservar Docker Compose como quickstart. Usar `kind` para desarrollo y CI Kubernetes, un Helm
chart parametrizable, Gateway API como interfaz y Envoy Gateway como implementación local.

## Consequences

Una misma aplicación cubre aprendizaje y despliegue portable. La V3 local valida topología y
operación, pero no afirma alta disponibilidad física en un único portátil.
