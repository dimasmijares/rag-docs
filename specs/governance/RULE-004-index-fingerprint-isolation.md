---
id: RULE-004
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
tags: [indexing, embeddings, migration, mandatory]
---

# RULE-004 — Un fingerprint por colección

## Rule Definition

Una colección física de búsqueda sólo admite un `IndexFingerprint`: extractor, chunking,
modelo y revisión de embeddings, dimensión, prefijos y normalización. Un cambio incompatible crea
otra colección y se publica de forma atómica mediante alias tras validación.

## Enforcement

- El fingerprint se persiste y comprueba antes de escribir o consultar.
- No se actualizan vectores incompatibles dentro de una colección existente.
- La migración mantiene rollback hasta superar el gold set.
