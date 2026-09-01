---
id: WRK-TASK-028
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

- [x] Pull requests ejecutan `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan` sin secretos corporativos.
- [x] Un fixture privado o una ruta/IP prohibida hace fallar el pipeline.
- [x] Acciones están fijadas por SHA, dependencias auditadas y permisos de workflow son mínimos.
- [x] Los checks son reutilizables por releases posteriores.
- [x] Los contextos exitosos quedan exigidos en la protección de `main` y se verifican mediante API.
- [x] El pipeline funciona desde un clon sin archivos locales ignorados.

## Evidence

- PR `#3` ejecutó correctamente los cinco jobs del workflow `quality-gates` en el run
  `33532869665`: `kdd`, `python-quality`, `public-safety`, `dependency-review` y
  `secret-scan`.
- `scripts/test-public-safety.ps1` demostró que una IPv4 privada sintética y una ruta
  `logs/**` hacen fallar el gate; el gate nominal revisó 187 archivos candidatos.
- Todas las acciones de terceros quedaron fijadas por SHA. El workflow sólo concede
  `contents: read`; Gitleaks no comenta en PR y usa exclusivamente el `GITHUB_TOKEN` efímero.
- Se habilitó Dependency Graph/vulnerability alerts mediante API y el job de revisión de
  dependencias pasó con umbral `moderate`.
- La protección de `main`, verificada mediante API, exige con `strict: true` los contextos
  `kdd`, `python-quality`, `public-safety`, `dependency-review` y `secret-scan`; se
  conservaron PR obligatorio, historial lineal, resolución de conversaciones y bloqueo de
  force-push/deletion.
- Un worktree limpio en el commit `7f29906`, sin ignorados ni submódulos, ejecutó
  `uv sync --frozen --extra dev`, KDD (123 specs, 855 edges, 0 orphans), lifecycle, Ruff,
  35 tests, gate público, fixtures negativos y `git diff --check` correctamente.
- Se eliminó el submódulo que apuntaba fuera de `dimasmijares`; el CLI KDD quedó versionado
  en `scripts/kdd_graph.py` y reprodujo los conteos del grafo previo. No quedan referencias
  rastreadas al repositorio externo.
