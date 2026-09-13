---
id: WRK-SPEC-014
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-006
    relation: depends-on
  - id: WRK-SPEC-013
    relation: depends-on
  - id: ADR-RAG-013
    relation: depends-on
  - id: ADR-RAG-014
    relation: depends-on
tags: [release, v1.1.0, fabric, indexing, spark, inference-queue]
---

# WRK-SPEC-014 — Plano de indexación en Fabric v1.1.0

## Proposed Change

Llevar la indexación al perfil Fabric sobre el runtime durable de `v1.0.0`: documentos en OneLake,
ledger y chunks en Fabric SQL confirmados en una transacción, indexación en notebooks Spark
orquestada por eventos y calendario, y cargas batch de LLM local mediante la cola pull de
`ADR-RAG-014`.

## Rationale

`v0.4.0` valida el backend y la evaluación con un índice construido en local. El plano de
indexación sólo tiene sentido cuando existen jobs, ledger e idempotencia (`WRK-SPEC-006`,
`ADR-RAG-008`); hacerlo antes duplicaría esas garantías en Spark sin contrato común.

## Acceptance Criteria

- [ ] Un documento sintético subido a OneLake se indexa sin intervención y conserva `relative_path`
      idéntico al local.
- [ ] Ledger y chunks de cada documento se confirman en una transacción; la suite de contrato de
      ledger pasa contra Fabric SQL y PostgreSQL.
- [ ] Spark verifica el digest de fingerprint antes de escribir y falla cerrado si no coincide.
- [ ] Eventos duplicados no duplican efectos y el borrado de huérfanos sólo ocurre con snapshot
      completo.
- [ ] `POST /api/index` en perfil Fabric devuelve `202 JobResource` mapeado al pipeline, y el
      `200 IndexReport` síncrono sigue disponible.
- [ ] La cola de inferencia no abre puertos entrantes, es idempotente y tiene dead-letter.
- [ ] Enriquecimiento, LLM-as-judge y candidatos de gold set tienen evidencia medida y revisión
      humana donde `ADR-RAG-014` la exige.
- [ ] Power BI muestra runs de indexación, cola, consumo de CU, salud del ledger y juez.

## Evidence

Pendiente de `WRK-PLAN-014`.
