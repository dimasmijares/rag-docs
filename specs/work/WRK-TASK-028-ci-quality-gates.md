---
id: WRK-TASK-028
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
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-025
    relation: depends-on
  - id: WRK-TASK-079
    relation: depends-on
tags: [ci, github-actions, secrets, dependencies]
---

# WRK-TASK-028 — Gates de GitHub Actions

## Objective

Automatizar KDD, Ruff, tests, secret scan, auditoría de dependencias y política de datos públicos.

## File Scope

Incluye `.github/**`, configuración de auditoría y scripts de gates. Excluye funcionalidad RAG,
corpus y cambios de contratos públicos.

## Acceptance Criteria

- [ ] Pull requests ejecutan `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan` sin secretos corporativos.
- [ ] Un fixture privado o una ruta/IP prohibida hace fallar el pipeline.
- [ ] Acciones están fijadas por SHA, dependencias auditadas y permisos de workflow son mínimos.
- [ ] Los checks son reutilizables por releases posteriores.
- [ ] Los contextos exitosos quedan exigidos en la protección de `main` y se verifican mediante API.
- [ ] El pipeline funciona desde un clon sin archivos locales ignorados.

## Evidence

Pendiente.
