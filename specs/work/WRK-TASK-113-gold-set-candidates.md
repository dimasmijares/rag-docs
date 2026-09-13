---
id: WRK-TASK-113
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-014
activates: [DOM-RAG-001, RULE-002]
dependencies:
  - id: WRK-TASK-102
    relation: depends-on
  - id: WRK-TASK-110
    relation: depends-on
tags: [evaluation, gold-set, human-review]
---

# WRK-TASK-113 — Candidatos de gold set

## Objective

Generar preguntas candidatas para gold sets con el LLM local bajo revisión humana obligatoria.

## File Scope

Incluye la generación vía cola, una tabla de candidatos con estado de revisión y la guardia de fuga.
Excluye incorporar candidatos a gold sets sin revisión.

## Acceptance Criteria

- [ ] Ningún candidato entra en un gold set sin aprobación humana registrada.
- [ ] Una guardia impide que candidatos derivados de `validation` alimenten `dev` o viceversa.
- [ ] Los candidatos sólo se generan sobre el corpus sintético.

## Evidence

Pendiente.
