---
id: WRK-TASK-007
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-08-30
owner: rag-docs-team
parent: WRK-PLAN-002
activates: [ARCH-001, DOM-RAG-001, DOC-RAG-001]
dependencies:
  - id: WRK-PLAN-002
    relation: implements
tags: [source, local-folder, indexing, privacy]
---

# WRK-TASK-007 — Indexar corpus operativo

## Objective

Configurar una fuente privada local independiente y dejarla indexada en Qdrant.

## Scope

Incluye `.env`, configuración local ignorada, reinicio controlado de la API e indexación selectiva. Excluye copiar o modificar documentos de origen.

## Acceptance Criteria

- [x] Sólo se descubren formatos documentales soportados.
- [x] La API carga ambas fuentes y Qdrant contiene los chunks operativos.
- [x] El informe de indexación registra documentos, chunks y errores.

## Test Plan

Validar el grafo, consultar `/api/sources`, ejecutar `POST /api/index` para la fuente local y revisar el resultado.

## Evidence

- Configuración local ignorada por Git con fuente sintética y fuente privada independiente.
- Primera indexación y segundo pase incremental verificados sin exponer recuentos o rutas.
- Los formatos no incluidos quedaron fuera por los patrones configurados.
- La evidencia detallada permanece local y no forma parte de ningún artefacto publicable.
