---
id: WRK-TASK-047
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [FEAT-RAG-003, RULE-002, RULE-003]
dependencies:
  - id: WRK-TASK-046
    relation: depends-on
tags: [security-tests, tenant, acl, leakage]
---

# WRK-TASK-047 — Pruebas de aislamiento

## Objective

Probar que contenido no autorizado no aparece en hits, contexto, citas, errores, logs ni métricas.

## Acceptance Criteria

- [ ] Matriz multiusuario/multitenant cubre permisos directos, grupos y revocación.
- [ ] Títulos y confirmación de existencia también quedan protegidos.
- [ ] Fallos del autorizador se comportan fail-closed.
- [ ] Los fixtures son enteramente sintéticos.

## Evidence

Pendiente.
