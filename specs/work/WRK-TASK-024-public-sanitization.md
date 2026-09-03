---
id: WRK-TASK-024
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
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-023
    relation: depends-on
tags: [privacy, sanitation, public]
---

# WRK-TASK-024 — Saneamiento público

## Objective

Eliminar o anonimizar documentos, derivados, rutas, IP, identidades y configuración privada antes
del primer commit.

## File Scope

Incluye ignores, Docker context, tests, specs y scripts de detección. Excluye borrar los datos
locales ignorados que el usuario necesita para sus pruebas.

## Acceptance Criteria

- [x] Ningún artefacto candidato contiene hechos o derivados Sareb.
- [x] `.gitignore` y `.dockerignore` cubren configuraciones, logs, índices y artefactos privados.
- [x] La imagen no copia `sources.local.yaml` ni `.env`.
- [x] Un gate reproducible escanea secretos, rutas, IP y nombres privados.

## Evidence

- Auditoría independiente identificó derivados en tests/specs, IP real y riesgo de copiar
  configuración local al contexto Docker; todos se anonimizaron o excluyeron.
- Tests de regresión conservan el comportamiento con un dominio completamente sintético.
- Dockerfile copia únicamente `config/sources.container.yaml`; ignores cubren `.env*`, variantes
  `*.local.*`, logs, estado, vectores, dumps y artefactos privados.
- `scripts/check-public-safety.ps1` superó 182 archivos candidatos y los archivos locales
  sensibles fueron confirmados como ignorados mediante `git check-ignore`.
- KDD válido, cero huérfanos, Ruff correcto y 35 pruebas superadas el 2026-09-01.
- La comprobación de build Docker queda para la tarea de publicación/runtime porque el daemon no
  estaba disponible; este gate validó estáticamente el contexto y las instrucciones `COPY`.
