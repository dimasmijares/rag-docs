---
id: WRK-TASK-025
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
  - id: WRK-TASK-024
    relation: depends-on
tags: [git, github, license, public]
---

# WRK-TASK-025 — Bootstrap público en GitHub

## Objective

Añadir Apache-2.0, crear una historia saneada sobre `main` y publicar
`dimasmijares/rag-docs` con protección básica.

## Acceptance Criteria

- [x] El primer commit usa correo noreply y no contiene material privado.
- [x] `main` es la rama por defecto y requiere los checks disponibles.
- [x] El repositorio y su metadata declaran Apache-2.0.
- [x] La publicación sólo ocurre después del gate de saneamiento.

## Evidence

- Repositorio público: <https://github.com/dimasmijares/rag-docs>; `main` está configurada
  como rama predeterminada y la integración se realiza mediante la PR
  <https://github.com/dimasmijares/rag-docs/pull/1>.
- El commit raíz `8e1d60f532336a10020c88481b91010ccde3323c` usa como autor y committer
  `dimasmijares <109075093+dimasmijares@users.noreply.github.com>`.
- `LICENSE` coincide exactamente, normalizando finales de línea, con el texto oficial
  Apache License 2.0 expuesto por la API de GitHub; `pyproject.toml` declara
  `license = "Apache-2.0"` y README enlaza la licencia.
- La API de protección de ramas confirma PR obligatoria sin aprobaciones mientras el proyecto
  tenga un único mantenedor, resolución de conversaciones e historial lineal. Force push y
  eliminación están deshabilitados. No hay checks remotos disponibles todavía; WRK-TASK-028
  los añadirá y endurecerá esta regla.
- Gates locales superados: KDD validate (`122` specs, `842` relaciones), cero huérfanos,
  Ruff, `35` pruebas, `scripts/check-public-safety.ps1` sobre `184` archivos candidatos y
  `git diff --check`. El warning de deprecación Starlette/httpx no bloquea la publicación.
