---
id: WRK-TASK-079
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-025
    relation: depends-on
tags: [kdd, governance, lifecycle, roadmap]
---

# WRK-TASK-079 — Limpieza y protocolo operativo KDD

## Objective

Normalizar el ciclo de vida histórico, hacer verificable la coherencia entre estados y evidencia,
y dejar un protocolo inequívoco para ejecutar una sola tarea por iteración según el DAG.

## File Scope

Incluye `specs/**`, README y scripts de validación KDD. Excluye `src/**`, tests funcionales,
corpus, gold sets, configuración runtime y contratos de API.

## Acceptance Criteria

- [x] Los work artifacts de WRK-SPEC-001 a 003 están consolidados y archivados sin criterios pendientes.
- [x] RULE-003 y RULE-004 distinguen la baseline actual de sus gates de enforcement futuro.
- [x] Las tareas restantes de `v0.2.0` tienen dependencias, scope y criterios de salida inequívocos.
- [x] El protocolo de una tarea por rama/PR y la creación controlada de trabajo nuevo quedan documentados.
- [x] Un gate local detecta incoherencias de lifecycle antes de ejecutar pruebas funcionales.
- [x] KDD, Ruff, tests, gate público y `git diff --check` superan la validación final.

## Evidence

- Se archivaron `WRK-SPEC/PLAN-001` a `003` y `WRK-TASK-001` a `011`, `021` y `022`;
  sus criterios, versiones terminales y Evidence quedaron reconciliados sin eliminar historia.
- RULE-003 y RULE-004 subieron a `0.2.0` con aplicabilidad transitoria explícita y gates de
  enforcement en `WRK-TASK-046` y `WRK-TASK-036` respectivamente.
- `DOC-RAG-002` registra una tarea por rama/PR, selección por DAG/riesgo, creación controlada de
  tareas nuevas y consolidación/archivo al cerrar cada release.
- `WRK-TASK-026`, `012`, `027`, `028` y `029` quedaron refinadas. `079` bloqueó la entrada a
  `026`, `012` y `028`; `012` depende además del corpus estable de `026`.
- `scripts/check-kdd-lifecycle.ps1` valida una única tarea activa, dependencias terminales,
  jerarquía activa, scope y cierre de criterios/Evidence, y forma parte de `scripts/verify.ps1`.
- Validación final: `123` artefactos, `855` relaciones, cero huérfanos; contextos de `079`,
  `028`, `026` y `012` coherentes; Ruff limpio; `35` tests; gate público sobre `186` archivos
  candidatos y `git diff --check` sin errores.
- No se modificaron `src/**`, tests funcionales, corpus, gold sets, configuración runtime ni API.
