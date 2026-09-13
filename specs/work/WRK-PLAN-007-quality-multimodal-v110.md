---
id: WRK-PLAN-007
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-SPEC-007
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-004]
dependencies: []
tags: [release-plan, v1.2.0, retrieval, multimodal]
---

# WRK-PLAN-007 — Calidad y multimodal v1.2.0

Renumerado de `v1.1.0` a `v1.2.0` por `RFC-004`; sigue a `WRK-PLAN-014` (`v1.1.0`).

## Task Decomposition

`013 → 039 → 040` tras `035`. `041` depende del baseline de rendimiento y `042` consolida los
experimentos que forman el gate de la release.

`036`, `037` y `038` se trasladaron a `WRK-PLAN-012` (`v0.3.0`) por `ADR-RAG-007`: el fingerprint
es prerrequisito del ledger de `v1.0.0` y del payload ACL de `v1.5.0`, y la evidencia de calidad
debe preceder a la decisión de industrializar, no seguirla.

`WRK-TASK-081` conserva como línea independiente y no bloqueante la comparación 3B/14B en el PC
personal. Sólo queda preparada después de cerrar `v0.2.0` y no publica resultados hasta disponer
del equipo remoto autorizado.

## Gate

Toda evidencia visual conserva provenance y el corpus multimodal se publica como versión aditiva,
conservando la anterior como serie de regresión.
