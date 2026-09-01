---
id: ADR-002
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
  - id: ARCH-002
    relation: implements
tags: [architecture-decision, monorepo, microservices]
---

# ADR-002 — Monorepo y límites de servicios

## Context

El proyecto necesita demostrar evolución a microservicios sin multiplicar repositorios ni
duplicar contratos durante la fase de aprendizaje.

## Decision

Mantener un monorepo Python 3.11. Extraer ocho servicios desplegables desde módulos y contratos
compartidos sólo en `v2.5.0`; antes se separan procesos por necesidad operativa.

## Consequences

Las refactorizaciones conservan trazabilidad y cambios atómicos. El monorepo requiere límites de
dependencias, ownership y contract tests para evitar un monolito distribuido.
