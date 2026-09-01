---
id: WRK-TASK-080
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

- [ ] `AGENTS.md` remite a KDD como fuente canónica y define semántica para solicitudes singulares,
  continuación serial y paralelismo autorizado.
- [ ] Subagentes pueden resolver workstreams internos independientes, con integración propiedad
  del agente principal y sin ediciones concurrentes conflictivas.
- [ ] Tareas independientes pueden ejecutarse en paralelo con máximo inicial de dos, worktrees,
  ramas y PR separadas; tareas dependientes esperan al merge terminal de sus predecesoras.
- [ ] Cada checkout mantiene como máximo una WRK-TASK activa y las PR concurrentes se integran una
  a una, resincronizando y repitiendo gates.
- [ ] `DOC-RAG-002`, lifecycle y `AGENTS.md` no contienen reglas contradictorias.
- [ ] `RFC-003` conserva la decisión transversal, sus límites, consecuencias y alternativas.
- [ ] `WRK-TASK-026` define esquema, matriz de cobertura, contaminación entre splits,
  localizadores, manifiesto y regeneración determinista suficientes para una sesión nueva.
- [ ] KDD validate, orphans, context, lifecycle, gate público y `git diff --check` pasan sin
  modificar comportamiento runtime.

## Evidence

Pendiente.
