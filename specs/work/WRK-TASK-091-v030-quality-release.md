---
id: WRK-TASK-091
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: high
version: 1.0.0
created: 2026-09-04
updated: 2026-09-12
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-082
    relation: depends-on
  - id: WRK-TASK-086
    relation: depends-on
  - id: WRK-TASK-038
    relation: depends-on
  - id: WRK-TASK-092
    relation: depends-on
tags: [release, v0.3.0, integration, consolidation]
---

# WRK-TASK-091 — Release de invariantes y calidad v0.3.0

## Objective

Validar de extremo a extremo los invariantes introducidos, consolidar `WRK-SPEC-012` y publicar
`v0.3.0` como baseline sobre la que se decide la industrialización.

## Acceptance Criteria

- [x] Una migración de colección completa se ejecuta y se revierte con el corpus sintético.
- [x] El informe de calidad compara dense, hybrid y reranking sobre una baseline declarada
      comparable, con decisión de adopción registrada.
- [x] El README y `DOC-RAG-001` describen el fingerprint, el ámbito obligatorio y la política de
      comparabilidad.
- [x] `WRK-SPEC-012` se consolida y sus tareas se archivan conservando Evidence antes del tag.
- [x] `scripts/verify.ps1` queda verde sin requerir infraestructura adicional a la de `v0.2.0`.

## Evidence

- **Migración con corpus sintético (AC1):** `scripts/migration_drill.py` (nuevo) ejecuta en vivo,
  contra `:memory:` Qdrant y el corpus `demo`, el ciclo completo de `WRK-TASK-036`: indexa con un
  fingerprint, construye una colección candidata con `chunk_tokens`/`chunk_overlap` distintos
  (`migrate_and_publish`), valida el candidato con una búsqueda real antes de mover el alias, y
  **confirma que una vinculación de fingerprint desactualizada rechaza la consulta**
  (`RULE-004` — el proceso que sigue apuntando al fingerprint anterior obtiene `AppError`, no un
  resultado plausible) hasta que se rebinda explícitamente. Después ejecuta `rollback_alias` y
  verifica que la colección anterior sigue sirviendo resultados correctos y que la colección
  migrada permanece disponible para inspección forense. Ejecución real:
  `uv run --no-sync python scripts/migration_drill.py` — sin Docker, mismo requisito que `v0.2.0`.
- **Informe de calidad de los tres perfiles (AC2):** `config/benchmark-091-quality-report.yaml`
  (independiente de `config/benchmark.yaml`, misma razón que `WRK-TASK-037/038/086`) declara
  `dense-baseline`, `hybrid-rrf` y `dense-reranked` con configuración idéntica salvo la estrategia,
  garantizando que las tres comparten `index_fingerprint` (verificado en los JSON:
  `724f6786a9170f8b` en los tres perfiles, en ambos gold sets — la "baseline declarada comparable").
  Ejecutado en vivo sobre `gold-set.dev.yaml` y `gold-set.validation.yaml`; evidencia reproducible en
  `evaluation/benchmarks/wrk-task-091/{dev,validation}-quality-report.json`. Resultado en
  validación (el conjunto que decide): `dense-baseline` recall@1 0.75/MRR 0.917; `hybrid-rrf` igual
  en recall@1/MRR pero **retrocede** en recall@8/precision@8 (1.0→0.917, 0.167→0.146); `dense-reranked`
  mejora en todos los cortes sin ninguna regresión (recall@1 0.917, MRR 1.0, precision@8 0.267).
  **Decisión de adopción registrada** (ya tomada con evidencia propia y ahora confirmada en un
  informe conjunto sobre el mismo fingerprint): `dense` sigue siendo la estrategia de retrieval por
  defecto (`WRK-TASK-037` Evidence — hybrid no supera el criterio de `RFC-001` gate G2 en
  validación); reranking por cross-encoder se adopta como **capacidad opt-in**, no como valor por
  defecto (`ADR-RAG-012` — mejora limpia pero cambiar el comportamiento de despliegues existentes
  sin que el operador lo pida no es aceptable).
- **README y `DOC-RAG-001` (AC3):** nueva sección "Índice: fingerprint, ámbito y comparabilidad" en
  `README.md` documenta `IndexFingerprint`/alias/`migrate_and_publish`/`rollback_alias`
  (`RULE-004`), `Scope` obligatorio sin valor por defecto en `VectorStorePort` (`RULE-003`,
  `ADR-RAG-009`) y la política de comparabilidad `corpus_version`/`index_fingerprint`/
  `compare_reports --rebaseline` (`ADR-RAG-011`), enlazando los resultados de `WRK-TASK-037`/`038`.
  `DOC-RAG-001` (`specs/documentation/`) sube a `v1.4.0` con un AC y una entrada de Evidence nuevos
  que referencian esa sección.
- **Consolidación de `WRK-SPEC-012` (AC4):** `WRK-SPEC-012` pasa a `archived` (`v1.0.0`) con sus
  siete Acceptance Criteria marcados y Evidence consolidada citando cada `WRK-TASK` que los
  implementa. `WRK-PLAN-012` pasa a `archived` (`v1.0.0`) con una tabla de estado final (mismo
  patrón que `WRK-PLAN-005` al cerrar `v0.2.0`) y su propia sección `Evidence`. Las ocho tareas que
  decompone (`092`, `083`, `036`, `090`, `086`, `082`, `037`, `038`) pasan de `completed` a
  `archived`, **sin tocar su contenido ni su Evidence** — sólo el campo `status` y `updated`.
  `./scripts/check-kdd-lifecycle.ps1` verificó que cada artefacto `archived` tiene Evidence no vacía
  y que ningún hijo archivado cuelga de un padre no archivado. `WRK-TASK-093` (trabajo descubierto
  durante `086`, en curso en paralelo) queda explícitamente fuera de esta consolidación — depende
  sólo de `086` y `WRK-PLAN-012` ya declaraba que no bloquea el cierre de `091`.
- **`scripts/verify.ps1` (AC5):** verde sin infraestructura adicional a la de `v0.2.0` — todos los
  comandos usados en esta tarea (`migration_drill.py`, el benchmark de tres perfiles) corren contra
  `:memory:` Qdrant y `generator_mode: forced_fallback`, sin Docker ni Ollama.
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (109 tests, sin cambios de código en `src/rag_docs/**` más allá de `scripts/`, que no tiene
  tests propios por ser un script operativo, no una librería); `./scripts/kdd.ps1 validate`/
  `orphans`; `./scripts/check-kdd-lifecycle.ps1`; `./scripts/check-public-safety.ps1` sobre los
  nuevos JSON (mismo saneamiento que `wrk-task-027`); `uv run --no-sync rag-docs-benchmark verify`
  sigue en verde sobre los artefactos canónicos de `v0.2.0` (sin regenerarlos, sin tocar
  `config/benchmark.yaml`).
