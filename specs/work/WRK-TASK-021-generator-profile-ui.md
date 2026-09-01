---
id: WRK-TASK-021
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-31
updated: 2026-08-31
owner: rag-docs-team
parent: WRK-PLAN-003
activates: [ARCH-001, FEAT-RAG-001, DOC-RAG-001]
dependencies:
  - id: WRK-TASK-011
    relation: depends-on
tags: [llm, configuration, health-check, web, ux]
---

# WRK-TASK-021 — Selector de generador local/remoto

## Objective

Permitir seleccionar desde la aplicación un generador Ollama local o remoto previamente
autorizado, comprobar su disponibilidad y conocer el modelo efectivo sin editar código.

## File Scope

Incluye configuración de perfiles, registro de generadores, endpoints de control, web estática,
tests y documentación KDD. Excluye URLs arbitrarias, persistencia multiusuario, autenticación y
cambio de embeddings o índice.

## Technical Direction

Los perfiles se definen por variables de entorno y se exponen como una lista cerrada. El cambio
es en memoria y afecta a las consultas posteriores; al reiniciar se recupera el perfil por defecto
de `.env`. La activación exige un health check correcto y que el modelo configurado exista.

## Acceptance Criteria

- [x] La web muestra perfil activo, endpoint y modelo configurado.
- [x] Local y remoto pueden comprobarse sin cambiar el perfil activo.
- [x] Sólo puede activarse un perfil cuyo endpoint responde y contiene el modelo configurado.
- [x] Las consultas posteriores usan el generador activado sin reindexar.
- [x] Fallos de red o modelo se muestran de forma explícita sin perder el perfil anterior.
- [x] API, UI y registro de perfiles tienen pruebas automatizadas.

## Evidence

- Registro cerrado de perfiles en `src/rag_docs/generator_profiles.py`, con health check,
  capacidades, comprobación de modelo y cambio atómico del perfil activo.
- Endpoints `GET /api/generator`, `POST /api/generator/check` y
  `POST /api/generator/activate`; un fallo devuelve error explícito y no cambia el activo.
- Bloque web responsive con perfil, endpoint, modelo, disponibilidad y acciones de comprobar y
  activar. El perfil predeterminado sigue procediendo de `.env`.
- Prueba real local → remoto → local: ambos endpoints disponibles con `qwen2.5:3b`; la aplicación
  terminó en local para proteger por defecto el corpus operativo.
- Smoke test visual en navegador: selección, health check y activación reflejados correctamente.
- Ruff, sintaxis JavaScript, KDD y 33 pruebas superadas el 2026-08-31.
