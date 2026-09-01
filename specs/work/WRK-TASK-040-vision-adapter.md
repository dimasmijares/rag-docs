---
id: WRK-TASK-040
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-007
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-039
    relation: depends-on
  - id: WRK-TASK-027
    relation: depends-on
tags: [vision, adapter, cache, conditional]
---

# WRK-TASK-040 — Adaptador de visión configurable

## Objective

Interpretar relaciones visuales sólo cuando OCR/extracción textual sean insuficientes, con caché
por hash y proveedor configurable.

## Acceptance Criteria

- [ ] La política de activación es determinista y auditable.
- [ ] El resultado cita el activo visual y su localizador.
- [ ] Caché se invalida por hash, modelo, prompt y versión.
- [ ] Un proveedor remoto requiere autorización explícita de privacidad.

## Evidence

Pendiente.
