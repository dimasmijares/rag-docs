---
id: WRK-TASK-079
type: spec
layer: work-task
scope: ephemeral
status: active
confidence: low
version: 0.1.0
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

- [ ] Los work artifacts de WRK-SPEC-001 a 003 están consolidados y archivados sin criterios pendientes.
- [ ] RULE-003 y RULE-004 distinguen la baseline actual de sus gates de enforcement futuro.
- [ ] Las tareas restantes de `v0.2.0` tienen dependencias, scope y criterios de salida inequívocos.
- [ ] El protocolo de una tarea por rama/PR y la creación controlada de trabajo nuevo quedan documentados.
- [ ] Un gate local detecta incoherencias de lifecycle antes de ejecutar pruebas funcionales.
- [ ] KDD, Ruff, tests, gate público y `git diff --check` superan la validación final.

## Evidence

Pendiente.
