---
id: WRK-TASK-111
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-014
activates: [DOM-RAG-001, FEAT-RAG-001, RULE-001, RULE-004]
dependencies:
  - id: WRK-TASK-102
    relation: depends-on
  - id: WRK-TASK-107
    relation: depends-on
  - id: WRK-TASK-110
    relation: depends-on
tags: [experiment, enrichment, retrieval, g2]
---

# WRK-TASK-111 — Experimento de enriquecimiento contextual batch

## Objective

Medir si cabeceras contextuales generadas por el LLM local mejoran el retrieval.

## File Scope

Incluye la columna de enriquecimiento, su versión en el fingerprint, la generación vía cola y la
evidencia de benchmark. Excluye adoptar el enriquecimiento sin ADR.

## Acceptance Criteria

- [ ] El enriquecimiento vive en columna separada, sólo alimenta el embedding y nunca se cita.
- [ ] La versión de enriquecimiento forma parte del fingerprint.
- [ ] La mejora se mide con ambos gold sets y la adopción sólo ocurre por gate G2 con ADR.

## Evidence

Pendiente.
