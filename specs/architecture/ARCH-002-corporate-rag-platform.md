---
id: ARCH-002
type: spec
layer: architecture
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-13
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
Celery transportan identificadores; un vector store derivado (Qdrant por defecto) almacena chunks,
vectores y metadatos ACL; Keycloak provee OIDC local. Gateway API es el contrato de entrada y Envoy
Gateway la implementación local.

Cada límite debe existir primero como contrato interno. Compose sigue siendo el camino sencillo;
Helm sobre `kind` valida la topología distribuida. Modelos y dependencias de datos admiten
endpoints externos configurables.

## Plataforma de datos externa (opcional)

`RFC-004` define Microsoft Fabric como perfil opcional; el núcleo y el camino Compose no dependen de
él. En ese perfil las fronteras se mapean así:

- `retrieval-service`: adaptador de `VectorStorePort` sobre SQL database in Fabric, con ledger y
  vectores derivados en la misma base de datos (`ADR-RAG-013`).
- `index-worker` y `embedding-service`: notebooks Spark en un Environment con el wheel del proyecto,
  orquestados por eventos y calendario.
- `evaluation-runner`: gold sets e informes en Delta, visualizados en Power BI.
- `model-gateway`: sólo cargas batch (enriquecimiento, juez, candidatos de gold set) mediante la cola
  pull hacia el LLM local (`ADR-RAG-014`); el servicio interactivo sigue siendo local.

## Invariants

- Ningún mensaje del broker contiene texto documental.
- Ningún retrieval se ejecuta sin un ámbito de autorización válido.
- Un índice no mezcla fingerprints de embeddings, chunking o extracción.
- Métricas y logs no incluyen contenido documental por defecto.
