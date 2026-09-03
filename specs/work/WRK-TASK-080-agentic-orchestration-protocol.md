---
id: WRK-TASK-080
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [DOC-RAG-002, RFC-003]
dependencies:
  - id: WRK-TASK-079
    relation: depends-on
  - id: WRK-TASK-028
    relation: depends-on
tags: [agents, orchestration, concurrency, kdd]
---

# WRK-TASK-080 — Protocolo de orquestación agentic KDD

## Objective

Hacer persistente un protocolo eficiente para que agentes ejecuten una o varias iteraciones KDD,
usen subagentes y paralelicen únicamente tareas independientes sin romper el DAG ni los gates.

## File Scope

Incluye `AGENTS.md`, `RFC-003`, `DOC-RAG-002`, scripts de lifecycle, `WRK-PLAN-005` y el
refinamiento de Definition-of-Ready de `WRK-TASK-026`. Excluye corpus, gold sets, `src/**`, tests
funcionales y contratos runtime.

## Acceptance Criteria

- [x] `AGENTS.md` remite a KDD como fuente canónica y define semántica para solicitudes singulares,
  continuación serial y paralelismo autorizado.
- [x] Subagentes pueden resolver workstreams internos independientes, con integración propiedad
  del agente principal y sin ediciones concurrentes conflictivas.
- [x] Tareas independientes pueden ejecutarse en paralelo con máximo inicial de dos, worktrees,
  ramas y PR separadas; tareas dependientes esperan al merge terminal de sus predecesoras.
- [x] Cada checkout mantiene como máximo una WRK-TASK activa y las PR concurrentes se integran una
  a una, resincronizando y repitiendo gates.
- [x] `DOC-RAG-002`, lifecycle y `AGENTS.md` no contienen reglas contradictorias.
- [x] `RFC-003` conserva la decisión transversal, sus límites, consecuencias y alternativas.
- [x] `WRK-TASK-026` define esquema, matriz de cobertura, contaminación entre splits,
  localizadores, manifiesto y regeneración determinista suficientes para una sesión nueva.
- [x] KDD validate, orphans, context, lifecycle, gate público y `git diff --check` pasan sin
  modificar comportamiento runtime.

## Evidence

- `AGENTS.md` conserva instrucciones ejecutables concisas y remite a `DOC-RAG-002` como protocolo
  canónico; distingue petición singular, continuación serial y paralelismo autorizado.
- `RFC-003` registra la decisión transversal, máximo inicial de dos tareas, aislamiento por
  worktree/rama/PR, integración una a una y serialización ante incertidumbre.
- `DOC-RAG-002` diferencia iteración y sesión coordinadora; el lifecycle precisa que el máximo de
  una tarea activa se aplica al checkout inspeccionado.
- `WRK-TASK-026` quedó en versión `0.2.0`, confidence medium y con contrato de dataset, matriz por
  split, localizadores compatibles con los extractores actuales, aislamiento de hechos y
  regeneración byte a byte verificable.
- KDD validó 125 specs y 863 edges sin errores ni huérfanos; los contextos de `080` y `026` fueron
  coherentes y lifecycle quedó limpio.
- Ruff y 35 tests pasaron; gate público revisó 190 candidatos, los fixtures negativos fueron
  rechazados y `git diff --check` quedó limpio. No se modificaron `src/**`, corpus, gold sets ni
  contratos runtime.
- La PR `#4` superó `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan`
  en el run `33537545536`.
