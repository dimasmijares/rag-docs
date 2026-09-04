---
id: WRK-TASK-086
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [DOM-RAG-001, DOC-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-036
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [corpus, gold-sets, manifest, evaluation, comparability]
---

# WRK-TASK-086 — Manifiesto de compatibilidad de corpus y evaluación

## Objective

Impedir que un cambio de pipeline se presente como una regresión de calidad, versionando de forma
conjunta corpus, gold sets y fingerprint, y haciendo explícita la comparabilidad entre informes.

## File Scope

Incluye el manifiesto de corpus y gold sets, su verificación en `benchmark.py` y `evaluation.py`, el
registro de versiones en los informes y sus tests. Excluye la generación de contenido nuevo de
corpus y cualquier cambio de extracción o chunking.

## Acceptance Criteria

- [ ] El manifiesto cubre corpus, gold sets y el rango de `IndexFingerprint` con el que son
      compatibles, extendiendo la verificación que ya existe en `benchmark.py`.
- [ ] Todo informe de evaluación y de benchmark registra `corpus_version`, `index_fingerprint` y el
      snapshot de configuración efectiva.
- [ ] Comparar informes con tripletas distintas exige una declaración explícita de re-baseline y no
      puede presentarse como regresión ni como mejora.
- [ ] Un gold set incompatible con el fingerprint vigente falla de forma explícita en lugar de
      producir métricas bajas.
- [ ] La política de corpus aditivo queda escrita: una versión nueva no muta la anterior, que se
      conserva como serie de regresión.

## Evidence

Pendiente.
