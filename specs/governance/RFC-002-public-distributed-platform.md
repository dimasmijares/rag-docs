---
id: RFC-002
type: rfc
layer: rfc
status: accepted
confidence: medium
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: extends
  - id: RFC-001
    relation: depends-on
  - id: DOM-RAG-001
    relation: extends
  - id: FEAT-RAG-001
    relation: extends
  - id: RULE-001
    relation: constrained-by
tags: [roadmap, public, distributed, kubernetes, corporate]
---

# RFC-002 — Evolución a plataforma pública y distribuida

## Problem Statement

La PoC local demuestra el flujo RAG, pero no cubre ejecución asíncrona durable, aislamiento por
identidad, conectores corporativos, operación observable ni despliegue portable. Además, el
proyecto debe poder publicarse sin exponer documentación o derivados privados.

## Decision

Evolucionar mediante siete releases compatibles: `v0.2.0`, `v1.0.0`, `v1.1.0`, `v1.5.0`,
`v2.0.0`, `v2.5.0` y `v3.0.0`. El destino es un monorepo Apache-2.0 con ocho servicios,
PostgreSQL, Redis/Celery, Qdrant, Keycloak, OpenTelemetry y despliegue Compose o Helm sobre
`kind`. El núcleo será neutral respecto de cloud y el LLM podrá permanecer externo.

## Compatibility Strategy

- Mantener `POST /api/query` y añadir recursos de jobs sin romper clientes deliberadamente.
- Extraer servicios desde contratos del monolito modular, no reescribir el dominio.
- Aceptar dependencias internas o endpoints externos mediante configuración.
- Aplicar gates de calidad, privacidad y seguridad antes de cada release.

## Consequences

El recorrido añade infraestructura de forma progresiva y verificable. La separación física de
servicios se pospone hasta que contratos, persistencia, seguridad y observabilidad estén probados.
