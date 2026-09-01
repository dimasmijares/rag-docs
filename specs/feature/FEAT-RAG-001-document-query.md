---
id: FEAT-RAG-001
type: spec
layer: feature
scope: persistent
status: active
confidence: medium
version: 1.3.0
created: 2026-08-25
updated: 2026-08-31
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: implements
  - id: DOM-RAG-001
    relation: constrained-by
tags: [query, indexing, web, api]
---

# FEAT-RAG-001 — Consulta e indexación documental

## Intent

Permitir que una persona indexe fuentes configuradas, formule preguntas y revise la evidencia.

## Definition

### Inputs

Una configuración de fuentes y una pregunta en español o inglés técnico.

### Behavior

La indexación descubre cambios y sincroniza el índice. La consulta recupera ocho candidatos,
deduplica y usa hasta cinco fragmentos para generar una respuesta estructurada. Antes de
publicarla valida idioma, cobertura, identificadores y citas, con un único reintento
correctivo y degradación segura. La persona puede comprobar un generador local o remoto
preconfigurado, descubrir sus modelos instalados y activar uno de ellos sin reindexar.

### Outputs

Estado de respuesta, texto, afirmaciones, idioma, modo de generación, citas, fragmentos,
puntuaciones y metadatos de localización.

## Acceptance Criteria

- [x] `GET /api/sources`, `POST /api/index` y `POST /api/query` respetan sus contratos.
- [x] La web permite indexar, consultar y copiar o abrir una ruta local.
- [x] Los fallos de un documento no cancelan la indexación completa.
- [x] La API conserva compatibilidad y añade afirmaciones, idioma y modo de generación.
- [x] La web muestra y cambia perfiles de generación sólo después de un health check válido.

## Evidence

- Contratos API y smoke test web superados el 2026-08-25.
- Contrato de respuesta y API probado en `WRK-TASK-010`; una validación local privada fue
  superada y su detalle quedó deliberadamente fuera del repositorio público.
- Selector de perfiles y endpoints de control verificados en `WRK-TASK-021`.
- Selector dinámico limitado a modelos anunciados por Ollama verificado en `WRK-TASK-022`.

## Traceability

- Implementado por `WRK-TASK-002` a `WRK-TASK-006`.
