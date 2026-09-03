---
id: WRK-SPEC-005
type: spec
layer: work-spec
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-01
updated: 2026-09-03
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

- [x] El roadmap corporativo está representado por un grafo KDD válido.
- [x] El repositorio público sólo contiene corpus, resultados y configuración sintéticos.
- [x] CI valida KDD, estilo, pruebas, secretos y dependencias.
- [x] El benchmark y la demo pública son reproducibles sin infraestructura corporativa.
- [x] La release `v0.2.0` queda documentada y etiquetada.

## Evidence

Las diez WRK-TASK de `WRK-PLAN-005` (023, 024, 025, 079, 028, 080, 026, 012, 027, 029) están
terminales y archivadas conservando sus criterios y Evidence.

- `WRK-TASK-023` dejó el roadmap corporativo `WRK-SPEC-004` + planes 005–011 como grafo KDD válido.
- `WRK-TASK-024`/`025` sanearon el repositorio, publicaron `main` bajo Apache-2.0 y dejaron el
  historial Git publicable; `examples/corporate/**` y los derivados privados quedan fuera de Git.
- `WRK-TASK-079`/`080` normalizaron lifecycle, Definition of Ready y el protocolo de orquestación
  agentic (`AGENTS.md`, `DOC-RAG-002`).
- `WRK-TASK-028` dejó obligatorios en CI los gates `kdd`, `python-quality`, `public-safety`,
  `dependency-review` y `secret-scan`.
- `WRK-TASK-026` publicó el corpus sintético `0.2.0` (doce fixtures multiformato, manifiesto
  SHA-256) y los gold sets `dev` (16) / `validation` (8) aislados entre sí.
- `WRK-TASK-012` añadió diagnóstico privacy-safe, deduplicación y métricas de retrieval por cortes.
- `WRK-TASK-027` estableció la baseline local reproducible `qwen-3b-balanced` (runner
  `rag-docs-benchmark`, artefactos en `evaluation/benchmarks/wrk-task-027/`).
- `WRK-TASK-029` publicó README, diagramas, privacidad, `scripts/demo.ps1`, versión `0.2.0` en
  paquete y API, y consolidó/archivó el release antes de etiquetar `v0.2.0`.
- El gate `public-safety` (local y CI) confirma que el repositorio sólo contiene corpus, gold sets,
  configuración y resultados sintéticos.
