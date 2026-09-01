---
id: WRK-TASK-022
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
  - id: WRK-TASK-021
    relation: depends-on
tags: [llm, model-discovery, configuration, web, ux]
---

# WRK-TASK-022 — Descubrimiento y selección dinámica de modelos

## Objective

Descubrir desde la web los modelos instalados en cada endpoint Ollama autorizado y permitir
activar uno de ellos sin modificar el código ni reiniciar la aplicación.

## File Scope

Incluye registro de generadores, contrato de activación, selector web, pruebas y documentación
operativa/KDD. Excluye endpoints arbitrarios, descarga o eliminación de modelos, persistencia
multiusuario y envío de documentos durante la comprobación.

## Technical Direction

`POST /api/generator/check` seguirá consultando `/api/tags` y devolverá todos los nombres
anunciados por el endpoint. La web poblará un selector únicamente con esa lista. La activación
aceptará un modelo opcional, verificará su pertenencia exacta a la lista y reemplazará el
generador de ese perfil de forma atómica, conservando el perfil anterior ante cualquier error.

## Acceptance Criteria

- [x] La comprobación muestra todos los modelos disponibles en el endpoint seleccionado.
- [x] La web permite elegir y activar cualquiera de los modelos anunciados.
- [x] Un modelo desconocido se rechaza sin cambiar el generador activo.
- [x] La consulta siguiente usa el endpoint y modelo activados sin reindexar.
- [x] El perfil activo y el modelo efectivo quedan visibles en la web.
- [x] API, registro y JavaScript superan sus pruebas y validaciones.

## Evidence

- `GeneratorProfileRegistry` descubre modelos, valida pertenencia exacta y reemplaza perfil y
  generador de forma atómica; API de activación acepta el modelo seleccionado.
- Web validada con Playwright: remoto detectó `qwen3:14b`, lo mostró en un desplegable y actualizó
  la insignia al activarlo; después se restauró `local · qwen2.5:3b`.
- Prueba HTTP real: modelo inventado rechazado con 503 y `qwen3:14b` permaneció activo hasta la
  restauración explícita. Sólo se consultó `/api/tags`; no se enviaron documentos ni preguntas.
- Configuración local actualizada para conservar `qwen3:14b` como modelo remoto inicial tras un
  reinicio, manteniendo el perfil local como predeterminado.
- KDD válido sin huérfanos, Ruff y 35 pruebas superadas el 2026-08-31; JavaScript válido con
  `node --check`.
