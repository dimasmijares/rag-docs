---
id: WRK-SPEC-009
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-008
    relation: depends-on
  - id: ADR-003
    relation: depends-on
  - id: ADR-004
    relation: depends-on
  - id: ADR-006
    relation: depends-on
tags: [release, v2.0.0, connectors, observability, resilience]
---

# WRK-SPEC-009 — Operación corporativa v2.0.0

## Proposed Change

Añadir SDK de conectores y SharePoint opcional, trazas y stack observable, secretos/TLS,
backup/restore y pruebas de capacidad y fallos.

## Acceptance Criteria

- [ ] SharePoint se prueba con mock en CI y live sólo localmente.
- [ ] Telemetría no registra contenido documental por defecto.
- [ ] Restore de PostgreSQL y Qdrant está ensayado.
- [ ] El perfil observable puede apagarse para operar con 16 GB.

## Evidence

Pendiente de `WRK-PLAN-009`.
