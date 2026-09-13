---
id: WRK-SPEC-013
type: spec
layer: work-spec
scope: ephemeral
status: active
confidence: medium
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-012
    relation: depends-on
  - id: RFC-004
    relation: depends-on
  - id: ADR-RAG-013
    relation: depends-on
tags: [release, v0.4.0, fabric, vector-store, evaluation, power-bi]
---

# WRK-SPEC-013 — Backend neutral y plano de evaluación en Fabric v0.4.0

## Proposed Change

Introducir las costuras de backend vectorial y publicación que el esquema de `v1.0.0` da por
supuestas, y usarlas para un primer perfil Fabric sin runtime asíncrono: el índice construido en
local se publica en SQL database in Fabric, la API y la web locales consultan ese backend con Ollama,
y la evaluación se almacena en Delta y se visualiza en Power BI.

## Rationale

`RFC-004` y `ADR-RAG-013` exigen que ledger y store queden tras puertos antes de modelar PostgreSQL;
hacerlo después obligaría a rehacer el esquema de `WRK-TASK-030`. Validar un segundo backend real
antes de `v1.0.0` demuestra que los puertos no están diseñados sólo para Qdrant.

## Acceptance Criteria

- [ ] El monolito consume un único `VectorStorePort` e `IndexPublicationPort`, y el backend se elige
      por configuración sin cambiar el comportamiento con Qdrant.
- [ ] App y benchmark producen el mismo digest de fingerprint para la misma configuración.
- [ ] Una suite de contrato común pasa contra Qdrant en el gate por defecto y contra Fabric SQL en
      `scripts/verify-fabric.ps1`.
- [ ] El gate público rechaza notebooks con outputs, cadenas de conexión con credenciales e IDs de
      tenant o workspace antes de versionar cualquier artefacto Fabric.
- [ ] La API local responde con citas válidas consultando vectores en Fabric SQL, con el prefiltro de
      ámbito y el fingerprint aplicados.
- [ ] Todo informe declara `vector_backend` y `vector_search_mode`; la latencia no se compara entre
      backends.
- [ ] Gold sets e informes se cargan en Delta por `corpus_version` y un informe Power BI versionado
      en PBIP los muestra por perfil, backend y fingerprint.
- [ ] `scripts/verify.ps1` sigue en verde sin Fabric ni credenciales.

## Evidence

Pendiente de `WRK-PLAN-013`.
