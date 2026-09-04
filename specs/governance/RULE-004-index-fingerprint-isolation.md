---
id: RULE-004
type: rule
layer: rule
scope: persistent
status: active
confidence: low
version: 0.2.0
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

## Transition

En `v0.1.x`/`v0.2.x` el extractor, chunking y embedding efectivo forman una baseline fija. Si
cambia cualquiera de ellos, el operador debe usar un nombre de colección nuevo; reutilizar la
colección existente está prohibido aunque dimensión y distancia coincidan.

`WRK-TASK-036` sustituye esta salvaguarda operativa por fingerprint persistido, comprobación
automática, colección versionada, validación previa y cambio atómico de alias.

## Enforcement

- El fingerprint se persiste y comprueba antes de escribir o consultar
  (`QdrantVectorStore.ensure_collection`/`bind_fingerprint`/`verify_fingerprint`, `WRK-TASK-036`).
- No se actualizan vectores incompatibles dentro de una colección existente: `ensure_collection`
  rechaza con `AppError(ErrorKind.VALIDATION)` si el alias ya apunta a otra colección física.
- La migración (`indexing.migrate_and_publish`) sólo mueve el alias tras validar la colección
  candidata; el rollback (`rollback_alias`) dispone de la colección anterior hasta que
  `delete_physical` cierra la ventana explícitamente.
