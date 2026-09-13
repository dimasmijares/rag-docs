---
id: WRK-TASK-093
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.2.0
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

- [x] El servicio expone su `IndexFingerprint` vigente (los diez campos de valor, no sólo
      `embedding_model`) a través de un endpoint HTTP existente o nuevo, documentado como cambio de
      contrato de API (versión de API o nota de compatibilidad, según convención del proyecto).
- [x] `evaluate()` consume ese campo y registra `index_fingerprint` (objeto completo + `digest()`)
      en el informe de evaluación, en el mismo formato que `_fingerprint_payload` usa en
      `benchmark.py`, en vez de (o junto a) `config_snapshot`.
- [x] `evaluate()` llama a `verify_fingerprint_compatibility` contra
      `evaluation/corpus-compatibility.yaml` antes de puntuar los casos; una API cuyo fingerprint
      vigente no esté en `compatible_fingerprint_digests` falla de forma explícita, no produce
      métricas bajas.
- [x] Un cliente HTTP existente que no pida el campo nuevo (compatibilidad hacia atrás del
      contrato) sigue recibiendo la misma respuesta que antes más el campo añadido; ningún campo
      existente cambia de nombre ni de significado.
- [x] Tests cubren: el endpoint devuelve el fingerprint vigente y coincide con
      `IndexingService.fingerprint`; `evaluate()` contra una API con fingerprint incompatible falla
      explícito; `evaluate()` contra una API compatible registra `index_fingerprint` y su `digest()`
      coincide con el declarado.

## Evidence

- Endpoint elegido: `GET /api/sources` (`src/rag_docs/api.py`) añade `index_fingerprint` con los
  campos de `IndexingService.fingerprint` y su `digest()`, en el mismo formato que
  `benchmark._fingerprint_payload`. Cambio aditivo documentado en la descripción OpenAPI del endpoint
  (la convención del proyecto versiona el contrato con `__version__` en OpenAPI): `sources` y sus
  campos no cambian; `POST /api/query` no cambia.
- `src/rag_docs/evaluation.py`: `live_index_fingerprint(client)` lee el campo, reconstruye
  `IndexFingerprint` y recalcula el digest (un payload sin el campo, con campos inválidos o con un
  digest que no casa con sus campos falla con `RuntimeError`). `evaluate()` lo llama y ejecuta
  `verify_fingerprint_compatibility` contra `corpus-compatibility.yaml` **antes** de enviar ningún
  caso, y registra `index_fingerprint` en el informe junto a `config_snapshot`, que se conserva.
  `evaluate()` acepta `transport` opcional (`httpx`) para pruebas; la CLI no cambia.
- Tests: `test_sources_expose_the_live_index_fingerprint_additively` (coincide con
  `IndexingService.fingerprint` y el contrato previo de `sources` queda intacto);
  `test_evaluate_records_the_live_index_fingerprint_when_compatible` (digest registrado igual al
  declarado); `test_evaluate_fails_explicitly_before_scoring_against_an_incompatible_index` (no se
  envía ninguna consulta); `test_evaluate_rejects_an_api_without_fingerprint_or_with_a_forged_digest`.
- Hallazgo operativo, sin cambiar el manifiesto: la app construye hoy el fingerprint con
  `embedding_revision=None` (digest `8270a45e87e30cc7`), que no está en
  `compatible_fingerprint_digests` (el benchmark fija la revisión: `724f6786a9170f8b`). Por tanto
  `rag-docs-eval` contra la API real falla ahora de forma explícita, que es lo que exige esta tarea.
  No se añade el digest sin revisión fijada porque no es reproducible; `WRK-TASK-095` fija la revisión
  en configuración para que app y benchmark coincidan.
- `scripts/verify.ps1` en verde.
