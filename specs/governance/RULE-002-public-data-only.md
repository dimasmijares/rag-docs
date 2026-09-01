---
id: RULE-002
type: rule
layer: rule
scope: persistent
status: active
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies: []
tags: [privacy, public, mandatory, supply-chain]
---

# RULE-002 — Sólo datos publicables en Git

## Rule Definition

Git, CI, imágenes, releases y artefactos públicos sólo pueden incluir datos sintéticos o datos con
autorización explícita y verificable de publicación. Documentos Sareb y sus derivados —chunks,
embeddings, citas, respuestas, logs, capturas y gold sets— permanecen fuera del repositorio aunque
el documento original no se considere confidencial.

## Enforcement

- Allowlist de corpus público y denylist de rutas/configuración local.
- Secret scan y búsqueda de rutas, IP y nombres privados en CI.
- Evaluaciones públicas escriben sólo en directorios sintéticos controlados.
- Revisión explícita del diff y del contenido de imágenes antes de publicar.
