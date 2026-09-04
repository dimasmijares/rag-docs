---
id: WRK-TASK-085
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, FEAT-RAG-003, RULE-003]
dependencies:
  - id: WRK-TASK-046
    relation: depends-on
  - id: WRK-TASK-086
    relation: depends-on
  - id: ADR-RAG-009
    relation: depends-on
tags: [evaluation, benchmark, acl, selectivity, re-baseline]
---

# WRK-TASK-085 — Evaluación y benchmark conscientes de autorización

## Objective

Separar el coste de la autorización de cualquier otra variación de calidad, para que la caída
esperable de métricas al activar el prefiltrado no sea indiagnosticable.

## File Scope

Incluye la dimensión de principal y tenant en los gold sets, las curvas por selectividad de filtro
en el benchmark, el principal de evaluación con permiso de diagnóstico y el re-baseline documentado.
Excluye la implementación de la autorización, que pertenece a `WRK-TASK-046`.

## Acceptance Criteria

- [ ] Los gold sets declaran principal y tenant; los existentes se ejecutan con ámbito permisivo
      para conservar la serie histórica.
- [ ] El benchmark publica al menos dos curvas, ámbito permisivo total y ámbito realista, con la
      selectividad del filtro registrada como dimensión.
- [ ] `retrieval_diagnostics` se filtra con el mismo ámbito que la respuesta y sólo un principal de
      evaluación con permiso explícito recibe el detalle completo.
- [ ] El informe declara de forma explícita que las cifras anteriores a la activación del
      prefiltrado no son comparables, y publica el re-baseline.
- [ ] Se mide el tamaño de `acl_subjects` y su efecto sobre latencia de filtro con un caso de
      expansión de grupos amplia.

## Evidence

Pendiente.
