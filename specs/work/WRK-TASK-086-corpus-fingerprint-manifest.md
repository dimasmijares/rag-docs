---
id: WRK-TASK-086
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-12
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

- [x] El manifiesto cubre corpus, gold sets y el rango de `IndexFingerprint` con el que son
      compatibles, extendiendo la verificación que ya existe en `benchmark.py`.
- [x] Todo informe de evaluación y de benchmark registra `corpus_version`, `index_fingerprint` y el
      snapshot de configuración efectiva.
- [x] Comparar informes con tripletas distintas exige una declaración explícita de re-baseline y no
      puede presentarse como regresión ni como mejora.
- [x] Un gold set incompatible con el fingerprint vigente falla de forma explícita en lugar de
      producir métricas bajas.
- [x] La política de corpus aditivo queda escrita: una versión nueva no muta la anterior, que se
      conserva como serie de regresión.

## Evidence

- **Manifiesto nuevo:** `evaluation/corpus-compatibility.yaml` (no dentro de `examples/corpus/demo/`
  porque ese árbol debe coincidir byte a byte con la salida determinista de
  `scripts/generate_demo_corpus.py`, verificado por
  `tests/test_demo_corpus.py::test_canonical_corpus_matches_fresh_generation`; añadir el fichero ahí
  rompía ese test). Declara `corpus_version`, el `corpus_manifest` al que se refiere, los tres gold
  sets (`smoke`/`dev`/`validation`) y `compatible_fingerprint_digests` — lista aditiva de digests
  `IndexFingerprint.digest()`, no un único valor, para que un futuro perfil de indexación compatible
  con el mismo corpus se añada sin invalidar el anterior. Incluye la política de corpus aditivo en
  el campo `policy` (AC5), que además ya estaba en la narrativa de `ADR-RAG-011`.
- `src/rag_docs/evaluation.py`: `load_corpus_compatibility`, `verify_gold_corpus_version` (falla
  explícito si el gold set no declara `corpus_version` o si no coincide con el del manifiesto activo
  — AC4 a nivel de corpus) y `verify_fingerprint_compatibility` (falla explícito si el
  `IndexFingerprint.digest()` vigente no está en `compatible_fingerprint_digests` — AC4 a nivel de
  fingerprint), compartidas por `benchmark.py`. `evaluate()` ahora carga el manifiesto, verifica el
  gold set y registra `corpus_version` y `config_snapshot` (modelo/embedding observados y si son
  consistentes entre casos) en el informe.
- `evaluation/gold-set.yaml` (smoke set): se le añadieron `schema_version`/`corpus_version`, que ya
  tenían `gold-set.dev.yaml` y `gold-set.validation.yaml` pero le faltaban a este — sin eso
  `verify_gold_corpus_version` no tiene nada que comprobar.
- `src/rag_docs/benchmark.py`: `_build_services`/`IndexingService.fingerprint` exponen ahora el
  `IndexFingerprint` de cada perfil; `_run_profile` lo verifica con `verify_fingerprint_compatibility`
  antes de generar ninguna respuesta (si el fingerprint vigente no es el declarado compatible, el
  benchmark falla ahí, no produce un score bajo) y lo registra en `index_fingerprint` de cada perfil
  del informe (dígito completo del objeto de valor + `digest()`). `execute_phase` carga el
  manifiesto, verifica `verify_gold_corpus_version` una vez para el gold set de la fase, y añade
  `corpus_version`/`corpus_compatibility_sha256` al informe. `select_baseline` propaga ambos al
  `decision-lock`; `execute_validation` añade una comprobación `corpus_compatibility` al lock (con
  `.get()`, retrocompatible con el `decision-lock.json` congelado de `v0.2.0` que no tiene el campo);
  `verify_artifacts` añade `corpus_version_match` entre `dev`/`validation`/`decision` (también con
  `.get()`, así que el artefacto canónico existente —sin el campo— sigue verificando en verde, ver
  más abajo).
- **`compare_reports` (nuevo, con subcomando CLI `rag-docs-benchmark compare`):** compara un mismo
  `profile_id` entre dos informes; si `corpus_version`/`index_fingerprint` difieren, lanza
  `RebaselineRequired` a menos que se pase `rebaseline=True`/`--rebaseline` explícito (AC3). Con
  triplete idéntico calcula `score_delta`; con re-baseline declarado, `score_delta` es `None` en vez
  de presentarse como mejora o regresión.
- **Decisión de diseño explícita:** el manifiesto de compatibilidad se referencia con una ruta por
  defecto fija (`evaluation.DEFAULT_CORPUS_COMPATIBILITY`), no como clave nueva y obligatoria de
  `config/benchmark.yaml`. Se intentó primero como clave de configuración, pero eso cambia el
  `sha256` de `config/benchmark.yaml`, que es exactamente el campo que `decision-lock.json`
  (artefacto congelado de `v0.2.0`, no se debe regenerar) usa para detectar cambios de configuración
  tras el `development` bloqueado — `rag-docs-benchmark verify` y `scripts/demo.ps1` empezaban a
  fallar en un clon limpio. Con la ruta fija por defecto, `config/benchmark.yaml` queda intacto y
  ambos siguen en verde (ver comprobación más abajo) sin sacrificar ninguna de las verificaciones.
- **Alcance de `index_fingerprint` en `evaluate()` (decisión documentada, no ambigüedad sin
  resolver):** `evaluate()` llama a una API en marcha por HTTP y hoy no tiene forma de recuperar el
  `IndexFingerprint` completo del servicio detrás de `/api/query` — sólo `embedding_model`/`model`
  por caso, que sí se registran en `config_snapshot`. Exponerlo exigiría tocar `api.py`, que no está
  en el File Scope de esta tarea (limitado a "el manifiesto... su verificación en `benchmark.py` y
  `evaluation.py`"). Documentado como trabajo separable: **discovered work** — exponer
  `index_fingerprint` en `GET /api/sources` (o en la respuesta de `/api/query`) para que
  `rag-docs-eval` pueda registrarlo y aplicar `verify_fingerprint_compatibility` igual que
  `benchmark.py` — no implementado aquí para no expandir el alcance en silencio (`AGENTS.md`).
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (90 tests, incluidos 8 nuevos en `tests/test_evaluation.py` y `tests/test_benchmark.py`);
  `./scripts/kdd.ps1 validate` sin problemas; `./scripts/check-public-safety.ps1` sin hallazgos.
  **Ejecución real** (no sólo unitaria, con Ollama local disponible y Qdrant en memoria — no
  requiere Docker): `execute_phase(..., selected_profile="extractive-fallback-control")` contra
  `gold-set.dev.yaml` completa sin error, con `corpus_version="0.2.0"`,
  `index_fingerprint.digest()="91e7717e96ab15ea"` (coincide exactamente con el digest declarado en
  `compatibility.yaml`) y `corpus_compatibility_sha256` poblado; forzando un digest inventado en
  `verify_fingerprint_compatibility` contra el manifiesto real confirma el fallo explícito (AC4).
  `uv run --no-sync rag-docs-benchmark verify` y `./scripts/demo.ps1` sobre los artefactos canónicos
  congelados de `v0.2.0` (sin regenerarlos) siguen en verde tras el cambio, con `corpus_version_match:
  true` pese a que esos JSON no declaran el campo (ambos lados `None`, retrocompatible por diseño).
