---
id: WRK-PLAN-012
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-SPEC-012
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v0.3.0, fingerprint, contracts, retrieval, quality]
---

# WRK-PLAN-012 — Invariantes de índice y calidad v0.3.0

## Task Decomposition

`092` es independiente y puede ejecutarse desde el primer momento. `083` fija los contratos y
desbloquea el resto: `083 → 036` y `083 → 090` son ramas paralelas; `036 → 082` y `036 → 086`
vuelven a abrirse en paralelo; `037` requiere `036` y `090`, y `038` sigue a `037`. `091` consolida
la release sobre `082`, `086`, `038` y `092`.

## Critical Ordering

- El fingerprint (`036`) precede a cualquier cambio de payload, porque un cambio de payload sin
  fingerprint aplicado corrompe la colección en silencio.
- Los contratos (`083`) preceden a la división de `QueryService` (`090`) y al modelo de tenant
  (`082`), que se escriben contra los puertos y no al revés.
- La calidad medida (`037`, `038`) precede a la decisión de industrializar de `WRK-SPEC-006`.

## Gate

Ningún invariante declarado en `RULE-003` o `RULE-004` queda sin enforcement verificable; ninguna
técnica de retrieval se adopta sin mejora medida sobre un baseline comparable.
