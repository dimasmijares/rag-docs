---
id: WRK-SPEC-003
type: spec
layer: work-spec
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-001, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, RULE-001]
dependencies:
  - id: RFC-001
    relation: depends-on
  - id: WRK-SPEC-002
    relation: depends-on
tags: [answer-quality, evaluation, retrieval, models, multimodal]
---

# WRK-SPEC-003 — Calidad de respuesta y portabilidad de modelos

## Problem Statement

El sistema debe distinguir entre evidencia recuperada y respuesta realmente completa, bien citada y escrita en el idioma solicitado. También debe permitir comparar generadores locales o remotos sin alterar embeddings, Qdrant, API ni corpus.

## Proposed Change

Construir una evaluación v2 y endurecer el contrato de generación antes de experimentar con modelos, retrieval avanzado o visión documental.

## Constraints

- Se conserva el pipeline local y el índice actual durante la caracterización.
- No se reindexará al cambiar únicamente el generador.
- Las pruebas remotas usarán corpus sintético salvo autorización explícita.
- Cada técnica avanzada tendrá baseline, métricas y criterio de rollback.

## Acceptance Criteria

- [x] El caso de regresión exige los tres identificadores, español y citas vinculadas.
- [x] Las preguntas compuestas se evalúan por hechos atómicos.
- [x] El generador es sustituible por configuración y se compara con el mismo gold set.
- [x] La evaluación separa retrieval, generación y validación de respuesta.
- [x] La selección de proveedor y modelo no obliga a reindexar.

## Evidence

- `WRK-TASK-009` a `011` completadas: evaluación v2, contrato verificable y portabilidad
  local/remota.
- `WRK-TASK-021` y `022` completaron selección de endpoint y modelo autorizados.
- Retrieval avanzado, visión y benchmarks ampliados se trasladaron a `WRK-SPEC-005` y `007` para
  exigir corpus público, métricas y fingerprint de índice antes de su adopción.
