---
id: WRK-TASK-043
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [DOM-RAG-002, FEAT-RAG-003, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-017
    relation: depends-on
  - id: WRK-TASK-082
    relation: depends-on
tags: [tenant, acl, classification, qdrant]
---

# WRK-TASK-043 — Propagación y ciclo de vida de la ACL

## Objective

Propagar tenant, ACL y clasificación reales por fuentes, documentos, chunks, PostgreSQL y Qdrant
sobre el modelo de datos ya establecido en `WRK-TASK-082`, y cubrir su ciclo de vida completo.

## Acceptance Criteria

- [ ] La herencia entre fuente, carpeta y documento se normaliza y se expande a sujetos antes de
      indexar.
- [ ] Todo chunk contiene tenant y política aplicable; un documento cuya ACL no se puede normalizar
      falla ese documento y no el job.
- [ ] Colecciones anteriores se reconstruyen con nuevo fingerprint mediante alias atómico.
- [ ] Una revocación o un cambio de pertenencia a grupo se aplica por actualización de payload, sin
      recalcular embeddings, y con latencia de propagación acotada y medida.
- [ ] Migraciones y tests cubren altas, cambios, bajas y revocaciones, incluida la reconciliación de
      documentos indexados con una versión de política ya obsoleta.

## Evidence

Pendiente.
