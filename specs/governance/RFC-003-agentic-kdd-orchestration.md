---
id: RFC-003
type: rfc
layer: rfc
status: accepted
confidence: medium
version: 1.0.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: extends
tags: [agents, orchestration, concurrency, kdd]
---

# RFC-003 — Orquestación agentic de iteraciones KDD

## Problem Statement

El protocolo original equiparaba una iteración, una sesión y una única tarea global. Esa regla
evitaba conflictos durante el bootstrap, pero impedía aprovechar subagentes, encadenar varias
iteraciones autorizadas o ejecutar en paralelo tareas realmente independientes.

## Decision

Mantener una WRK-TASK por checkout, rama y PR, pero permitir que una sesión coordinadora ejecute
varias iteraciones en serie y, cuando el usuario autorice trabajo múltiple, hasta dos tareas
DAG-ready independientes en paralelo.

El paralelismo interno mediante subagentes se usa para workstreams acotados sin ediciones
conflictivas. El agente principal conserva síntesis, archivos compartidos, integración, gates y
resultado final.

## Concurrency Contract

- Una petición singular completa una única tarea lista.
- Continuar el release permite iteraciones seriales, recalculando el DAG tras cada merge.
- Dos tareas sólo pueden coexistir si sus dependencias están terminales en `main`, no existe
  dependencia directa o transitiva entre ellas y sus scopes de implementación no se solapan.
- Cada tarea concurrente usa worktree, rama y PR propios; el coordinador mantiene los archivos KDD
  compartidos.
- Las PR se integran una a una. Cada rama restante se actualiza desde `main` y repite gates antes
  de fusionarse.
- Cualquier duda sobre scope, dependencia u orden convierte el trabajo en serial.

## Consequences

Los prompts recurrentes pueden ser breves porque `AGENTS.md` aplica el protocolo persistente. La
latencia baja cuando existen workstreams independientes, mientras el DAG, la trazabilidad y la
protección de `main` siguen siendo obligatorios. La coordinación añade coste y no se usa cuando
una tarea es pequeña, dependiente o modifica archivos centrales compartidos.

## Alternatives Considered

1. **Una sola tarea global hasta completar cada sesión**: simple, pero desperdicia paralelismo y
   obliga a reiniciar contexto entre iteraciones seriales.
2. **Paralelismo sin límites**: aumenta conflictos, consumo y drift de integración; se descarta a
   favor de un máximo inicial de dos tareas.
3. **Codificar todo en prompts**: no es persistente ni revisable; se conserva KDD como fuente
   canónica y `AGENTS.md` como instrucción ejecutable concisa.
