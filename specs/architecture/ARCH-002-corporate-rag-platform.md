---
id: ARCH-002
type: spec
layer: architecture
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: extends
  - id: RULE-002
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [architecture, microservices, security, kubernetes]
---

# ARCH-002 — Plataforma RAG corporativa objetivo

## Intent

Definir límites estables para escalar desde la PoC sin acoplar dominio, IA, infraestructura ni
proveedor cloud.

## Definition

La arquitectura objetivo comprende `query-api`, `authz-service`, `retrieval-service`,
`context-grounding-service`, `index-api`, `index-worker`, `embedding-service` y
`model-gateway`. `evaluation-runner` será un Job. PostgreSQL conserva estado crítico; Redis y
Celery transportan identificadores; Qdrant almacena chunks, vectores y metadatos ACL; Keycloak
provee OIDC local. Gateway API es el contrato de entrada y Envoy Gateway la implementación local.

Cada límite debe existir primero como contrato interno. Compose sigue siendo el camino sencillo;
Helm sobre `kind` valida la topología distribuida. Modelos y dependencias de datos admiten
endpoints externos configurables.

## Invariants

- Ningún mensaje del broker contiene texto documental.
- Ningún retrieval se ejecuta sin un ámbito de autorización válido.
- Un índice no mezcla fingerprints de embeddings, chunking o extracción.
- Métricas y logs no incluyen contenido documental por defecto.
