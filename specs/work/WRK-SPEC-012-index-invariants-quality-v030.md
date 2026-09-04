---
id: WRK-SPEC-012
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-005
    relation: depends-on
  - id: ADR-RAG-007
    relation: depends-on
  - id: ADR-RAG-010
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [release, v0.3.0, fingerprint, contracts, retrieval, quality]
---

# WRK-SPEC-012 — Invariantes de índice y calidad v0.3.0

## Proposed Change

Aplicar dentro del monolito, y antes de introducir infraestructura nueva, los invariantes que las
releases posteriores dan por supuestos: enforcement del fingerprint del índice, puertos y objetos de
valor compartidos, modelo de datos de tenant y ACL, y la mejora medida del retrieval.

## Rationale

`RULE-004` es `active` con enforcement previsto dos releases más tarde; el esquema PostgreSQL de
`v1.0.0` se diseñaría sin tenant; y la evidencia de calidad que justifica industrializar llegaría
después de haber industrializado. Esta release corrige las tres cosas sin añadir ninguna dependencia
de infraestructura: todo el trabajo ocurre en `src/rag_docs/**`, `evaluation/**` y `specs/**`.

## Acceptance Criteria

- [ ] Escribir o consultar con un fingerprint distinto al de la colección falla de forma explícita.
- [ ] Los puertos y objetos de valor compartidos existen en `rag_docs.contracts` sin dependencias de
      I/O y son los que consume el monolito.
- [ ] El puerto de búsqueda exige un ámbito de autorización sin valor por defecto.
- [ ] Un cambio de ACL no requiere recalcular embeddings.
- [ ] Toda evaluación declara `corpus_version`, `index_fingerprint` y configuración efectiva.
- [ ] Hybrid y reranking sólo se adoptan si superan el baseline con evidencia reproducible.
- [ ] El gate de publicación deja de contener en claro los identificadores que protege.

## Evidence

Pendiente de `WRK-PLAN-012`.
