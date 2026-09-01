---
id: WRK-SPEC-005
type: spec
layer: work-spec
scope: ephemeral
status: active
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-001, ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, RULE-001, RULE-002]
dependencies:
  - id: WRK-SPEC-004
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ADR-006
    relation: depends-on
tags: [release, v0.2.0, portfolio, public]
---

# WRK-SPEC-005 — Portfolio público v0.2.0

## Problem Statement

La PoC funciona localmente, pero todavía no dispone de un historial Git publicable, un gate
automatizado contra datos privados ni una evaluación suficientemente reproducible para servir
como proyecto de portfolio.

## Proposed Change

Convertir la PoC en una baseline pública, saneada y evaluable, manteniendo fuera de Git cualquier
documento o derivado Sareb y documentando con KDD la evolución posterior.

## Acceptance Criteria

- [ ] El roadmap corporativo está representado por un grafo KDD válido.
- [ ] El repositorio público sólo contiene corpus, resultados y configuración sintéticos.
- [ ] CI valida KDD, estilo, pruebas, secretos y dependencias.
- [ ] El benchmark y la demo pública son reproducibles sin infraestructura corporativa.
- [ ] La release `v0.2.0` queda documentada y etiquetada.

## Evidence

Pendiente de `WRK-PLAN-005`.
