---
id: WRK-SPEC-007
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-13
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-004]
dependencies:
  - id: WRK-SPEC-006
    relation: depends-on
  - id: WRK-SPEC-014
    relation: depends-on
  - id: ADR-002
    relation: depends-on
tags: [release, v1.2.0, retrieval, multimodal]
---

# WRK-SPEC-007 — Calidad y multimodal v1.2.0

Renumerada de `v1.1.0` a `v1.2.0` por `RFC-004`: el plano de indexación en Fabric
(`WRK-SPEC-014`) ocupa `v1.1.0`. El nombre de fichero conserva el sufijo histórico.

## Proposed Change

Añadir OCR, imágenes, tablas y visión condicional preservando provenance, sobre el fingerprint y la
baseline de calidad ya establecidos en `v0.3.0`.

## Acceptance Criteria

- [ ] El corpus multimodal se publica como versión aditiva y conserva la anterior.
- [ ] OCR y visión conservan localizador y coordenadas.
- [ ] Streaming sólo se marca grounded tras validación final.
- [ ] Los extractores nuevos funcionan también en el Environment de Fabric del perfil opcional
      (`WRK-SPEC-014`).

## Evidence

Pendiente de `WRK-PLAN-007`.
