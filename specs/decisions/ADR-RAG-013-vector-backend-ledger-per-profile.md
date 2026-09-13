---
id: ADR-RAG-013
type: adr
layer: adr
scope: persistent
status: accepted
confidence: medium
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RFC-004
    relation: constrained-by
  - id: ADR-RAG-008
    relation: extends
  - id: ADR-RAG-010
    relation: extends
  - id: ADR-RAG-011
    relation: extends
  - id: ARCH-002
    relation: implements
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [architecture-decision, vector-store, ledger, fabric, fingerprint, comparability]
---

# ADR-RAG-013 — Backend vectorial y ledger por perfil de despliegue

## Context

`RFC-004` introduce un perfil Fabric en el que los vectores viven en SQL database in Fabric. El
código actual no tiene las costuras necesarias:

- Conviven dos protocolos de store divergentes: `vector_store.VectorStore` (con `prune_document` y
  `scan_chunks`) y `contracts.VectorStorePort`.
- `ApplicationContainer` fija Qdrant y `migrate_and_publish` comprueba `isinstance(QdrantVectorStore)`.
- No existe una suite de contrato reutilizable entre backends.
- La app construye el fingerprint con `embedding_revision=None` y el benchmark con revisión fijada:
  sus digests difieren, lo que impediría verificar que Spark y local escriben el mismo índice.
- `ADR-RAG-008` hace de PostgreSQL el único recurso transaccional y de Qdrant un modelo derivado. Si
  un notebook Spark escribe vectores en Fabric sin ledger, Fabric pasa a ser una segunda fuente de
  verdad.
- `ADR-RAG-011` compara informes por `corpus_version + fingerprint.digest`, que no distingue backend;
  búsqueda exacta (`VECTOR_DISTANCE`) frente a índices aproximados (HNSW, DiskANN) cambia recall y
  latencia.

## Options Considered

1. **Qdrant como único backend y Fabric sólo para evaluación**: no hay plano de datos en Fabric.
2. **Fabric SQL como backend vectorial con el ledger en PostgreSQL local**: reintroduce una
   transacción entre dos recursos y deja la ventana de `ADR-RAG-008` fuera de control.
3. **Puertos unificados y un único recurso transaccional por perfil**: cada perfil agrupa ledger y
   vectores derivados donde puede confirmarlos juntos.

## Decision

**Opción 3.**

- **Puertos.** `rag_docs.contracts` define un `VectorStorePort` unificado (incluye `prune_document`
  y `scan_chunks`), un `IndexPublicationPort` (alias lógico, fingerprint vigente, publicación y
  rollback) y un `DocumentLedgerPort`. El monolito sólo consume puertos; la factoría del contenedor
  elige la implementación con `Settings.vector_backend`.
- **Un recurso transaccional por perfil.** Local: PostgreSQL (ledger, jobs, outbox) con Qdrant como
  modelo derivado, tal como decide `ADR-RAG-008`. Fabric: una SQL database que contiene el ledger y
  las tablas vectoriales derivadas; ledger y chunks de un documento se confirman en la misma
  transacción, lo que elimina la ventana `ack`/commit en ese perfil.
- **Esquema portable del ledger.** Las tablas de ledger usan SQL portable (sin construcciones
  exclusivas de PostgreSQL) para que ambas implementaciones compartan una suite de contrato. Jobs,
  outbox y leases de `v1.0.0` pueden ser específicos de PostgreSQL.
- **Fingerprint físico.** Una tabla física por fingerprint y una tabla de alias, equivalente a la
  colección física y el alias de Qdrant (`RULE-004`). El digest es idéntico entre backends; se fija
  `embedding_revision` en configuración para que app y benchmark coincidan.
- **Semántica de búsqueda.** `score = 1 − distancia coseno`. El prefiltro de ámbito (`RULE-003`,
  `ADR-RAG-009`) se aplica antes de `TOP k`; los subjects ACL viven en una tabla hija y un cambio de
  ACL no toca vectores.
- **Comparabilidad.** Todo informe declara `vector_backend` y `vector_search_mode` (`exact`,
  `hnsw`, `diskann`), que forman parte de la clave de comparación. La latencia nunca es comparable
  entre backends.

## Consequences

- `vector_store.py`, `container.py`, `migration` y `benchmark.py` cambian contrato antes de
  `v1.0.0` (`WRK-TASK-094`, `095`, `098`); el comportamiento con Qdrant debe ser idéntico.
- `WRK-TASK-030` modela el ledger tras `DocumentLedgerPort` y con SQL portable.
- La suite de contrato (`WRK-TASK-096`) corre contra Qdrant `:memory:` en el gate por defecto y
  contra Fabric sólo en `scripts/verify-fabric.ps1`.
- Hybrid/BM25 hace `scan_chunks` por consulta: aceptable sólo sobre el corpus demo en SQL.
- DiskANN está en preview; se mide como experimento del gate G2 y no es el modo por defecto.

## Work Impact

Crear en `WRK-PLAN-013`: `WRK-TASK-094`, `095`, `096`, `098`, `100`, `101` y `102`. Crear en
`WRK-PLAN-014`: `WRK-TASK-106`. Ampliar `WRK-TASK-030` con dependencia de `WRK-TASK-094` y el
criterio de ledger portable. `RULE-003`, `RULE-004` y `DOC-RAG-001` se actualizan en las tareas que
implementan el enforcement en el nuevo backend.
