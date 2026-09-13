---
id: WRK-TASK-093
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-12
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [DOM-RAG-001, DOC-RAG-002, RULE-004]
dependencies:
  - id: WRK-TASK-086
    relation: depends-on
tags: [fingerprint, evaluation, api, contract-change, discovered-work]
---

# WRK-TASK-093 — Exponer el `IndexFingerprint` vigente en la API para `rag-docs-eval`

## Objective

Permitir que `evaluate()` (el evaluador de humo contra la API en marcha, usado por
`uv run rag-docs-eval`) registre el `IndexFingerprint` real del servicio y lo verifique con
`verify_fingerprint_compatibility`, con la misma garantía de fallo explícito que `WRK-TASK-086` ya
dio a `benchmark.py`. Hoy `evaluate()` sólo ve `embedding_model`/`model` por caso vía HTTP y no
puede reconstruir el fingerprint completo, así que registra un `config_snapshot` best-effort en
lugar del fingerprint real y nunca puede fallar explícito ante una incompatibilidad de corpus.

## File Scope

Incluye `src/rag_docs/api.py` (exponer el fingerprint vigente, previsiblemente en
`GET /api/sources` o en la respuesta de `POST /api/query`), `src/rag_docs/container.py` si hace
falta para exponer `IndexingService.fingerprint` al endpoint elegido, `src/rag_docs/evaluation.py`
(consumir el campo nuevo, sustituir o complementar `config_snapshot` con `index_fingerprint` real,
y llamar a `verify_fingerprint_compatibility` igual que `benchmark.py`), y sus tests
(`tests/test_api.py`, `tests/test_evaluation.py`). Excluye cualquier cambio a
`IndexFingerprint`/`IndexingService`/`benchmark.py` en sí (ya cerrados por `WRK-TASK-036` y
`WRK-TASK-086`), y excluye `evaluation/corpus-compatibility.yaml` salvo que la verificación
descubra que necesita un digest adicional ya cubierto por la política aditiva existente.

## Acceptance Criteria

- [ ] El servicio expone su `IndexFingerprint` vigente (los diez campos de valor, no sólo
      `embedding_model`) a través de un endpoint HTTP existente o nuevo, documentado como cambio de
      contrato de API (versión de API o nota de compatibilidad, según convención del proyecto).
- [ ] `evaluate()` consume ese campo y registra `index_fingerprint` (objeto completo + `digest()`)
      en el informe de evaluación, en el mismo formato que `_fingerprint_payload` usa en
      `benchmark.py`, en vez de (o junto a) `config_snapshot`.
- [ ] `evaluate()` llama a `verify_fingerprint_compatibility` contra
      `evaluation/corpus-compatibility.yaml` antes de puntuar los casos; una API cuyo fingerprint
      vigente no esté en `compatible_fingerprint_digests` falla de forma explícita, no produce
      métricas bajas.
- [ ] Un cliente HTTP existente que no pida el campo nuevo (compatibilidad hacia atrás del
      contrato) sigue recibiendo la misma respuesta que antes más el campo añadido; ningún campo
      existente cambia de nombre ni de significado.
- [ ] Tests cubren: el endpoint devuelve el fingerprint vigente y coincide con
      `IndexingService.fingerprint`; `evaluate()` contra una API con fingerprint incompatible falla
      explícito; `evaluate()` contra una API compatible registra `index_fingerprint` y su `digest()`
      coincide con el declarado.

## Evidence

(pendiente de ejecución)
