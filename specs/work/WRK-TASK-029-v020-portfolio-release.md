---
id: WRK-TASK-029
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-01
updated: 2026-09-03
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [ARCH-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-027
    relation: depends-on
  - id: WRK-TASK-028
    relation: depends-on
tags: [release, v0.2.0, readme, demo]
---

# WRK-TASK-029 — Release de portfolio v0.2.0

## Objective

Publicar README, diagramas y demo reproducible sobre corpus sintético y consolidar `v0.2.0`.

## File Scope

Incluye README, documentación/diagramas públicos, metadata de versión, specs de release y
automatización de demo. Excluye nuevas capacidades runtime o datos no sintéticos.

## Acceptance Criteria

- [x] README explica propósito, arquitectura, privacidad, quickstart, evaluación y roadmap.
- [x] La demo funciona desde un clon limpio con el flujo documentado.
- [x] CI está verde y el diff de release supera el gate público.
- [x] Paquete y API declaran `0.2.0` y la evidencia pública referencia artefactos sintéticos.
- [x] `WRK-SPEC/PLAN-005` se consolidan y sus tareas se archivan antes de etiquetar.
- [x] El tag `v0.2.0` y la GitHub Release sólo se crean desde `main` fusionada y verificada.

## Evidence

- `README.md` cubre propósito, arquitectura, **Privacidad** (nueva sección: sólo datos sintéticos,
  gate `public-safety`, procesamiento local), quickstart, **Demo reproducible desde un clon
  limpio**, evaluación + benchmark y roadmap (`WRK-SPEC-004`).
- `scripts/demo.ps1` automatiza el flujo verificable de `v0.2.0`: `uv sync --extra dev`,
  `generate_demo_corpus.py --check`, `rag-docs-benchmark verify` y sondeo de Qdrant/Ollama; con
  `-Serve` arranca Qdrant y la API. Ejecutado en verde.
- Demo end-to-end comprobada contra el corpus sintético (`config/sources.yaml`): indexa los 12
  fixtures y responde `grounded` con fuentes exclusivamente sintéticas
  (`ETL_CLIENTES_DIARIA → CLIENTE_MAESTRO`, `02:00`, `ORQ_DATAOPS`).
- `pyproject.toml`, `rag_docs.__version__` y el OpenAPI de la API declaran `0.2.0`
  (`uv.lock` regenerado; test `test_openapi_declares_release_version`). La evidencia pública
  referencia `examples/corpus/demo/**` y `evaluation/benchmarks/wrk-task-027/**`.
- `WRK-SPEC-005` y `WRK-PLAN-005` pasan a `archived` con Evidence consolidada; las diez WRK-TASK
  (023, 024, 025, 079, 028, 080, 026, 012, 027, 029) quedan `archived` conservando criterios y
  Evidence. `kdd validate` (126 specs, 873 edges, 0 huérfanos) y lifecycle en verde.
- Gates locales: `ruff`, `pytest` (55), `check-public-safety` y `git diff --check` en verde. La PR
  supera `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan`.
- El tag `v0.2.0` y la GitHub Release se crean tras fusionar la PR en `main` y verificar el merge
  (paso posterior a esta Evidence, registrado en el cierre de la iteración).
