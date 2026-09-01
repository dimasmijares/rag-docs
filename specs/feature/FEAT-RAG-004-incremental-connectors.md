---
id: FEAT-RAG-004
type: spec
layer: feature
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: FEAT-RAG-002
    relation: extends
  - id: ARCH-002
    relation: implements
  - id: DOM-RAG-002
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [feature, connectors, sharepoint, synchronization]
---

# FEAT-RAG-004 — Conectores incrementales

## Intent

Añadir repositorios remotos conservando identidad, versión, cursor, hash y permisos de origen sin
alterar extracción, índice ni consulta.

## Definition

Un SDK de conectores expone descubrimiento paginado, descarga temporal, cursor y metadatos ACL.
El adaptador SharePoint/Microsoft Graph será opcional, probado con servidor simulado en CI y con
credenciales reales sólo en pruebas locales autorizadas.

## Acceptance Criteria

- Un conector puede reanudar una sincronización sin duplicar documentos.
- Rate limits y errores transitorios tienen retries limitados y observables.
- Las descargas temporales se eliminan de forma segura.
- La prueba live nunca es requisito de CI ni almacena credenciales.
