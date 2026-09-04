---
id: WRK-TASK-036
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-002, RULE-004]
dependencies:
  - id: WRK-TASK-083
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [chunking, tokenizer, fingerprint, qdrant]
---

# WRK-TASK-036 — Fingerprint y migración del índice

## Objective

Chunkear con tokenizer, calcular `IndexFingerprint`, hacerlo obligatorio en escritura y consulta y
migrar colecciones mediante alias atómico.

## File Scope

Incluye `chunking.py`, `embeddings.py`, `vector_store.py`, `models.py`, el objeto de valor
`IndexFingerprint` en `rag_docs.contracts`, la derivación del nombre de colección, el alias y sus
tests. Excluye estrategias de retrieval, ACL y cualquier cambio de infraestructura.

## Acceptance Criteria

- [x] El fingerprint cubre extractor, chunking con sus parámetros, modelo de embeddings con
      revisión, dimensión, normalización y convención de prefijos; ninguno de esos componentes
      queda incrustado y opaco dentro de un adaptador.
- [x] El fingerprint se persiste asociado a la colección y se comprueba antes de escribir y antes
      de consultar; la discrepancia falla de forma explícita y nunca degrada.
- [x] `ensure_collection` deja de aceptar una colección existente por el mero hecho de existir; una
      colección con otro fingerprint y la misma dimensión se rechaza.
- [x] La identidad del chunk incorpora `content_hash` e `index_fingerprint`, de modo que contenido
      distinto produce puntos distintos y la reescritura deja de exigir borrado previo.
- [x] El nombre físico de la colección deriva del fingerprint y el nombre configurado actúa como
      alias.
- [x] Una colección nueva se valida contra el gold set antes de mover el alias.
- [x] Rollback conserva la colección anterior durante la ventana definida.

## Evidence

- `IndexFingerprint` (definido en `WRK-TASK-083`) se construye en
  `indexing.build_fingerprint()` a partir de `EXTRACTOR_VERSION` (`extractors.py`),
  `CHUNKER_VERSION` (`chunking.py`), `chunk_tokens`/`chunk_overlap`, y
  `embedder.model_name/revision/dimension/normalize/query_prefix/passage_prefix` — los
  prefijos `passage:`/`query:` y `normalize` dejan de estar incrustados en
  `SentenceTransformerEmbedder.embed_*` y pasan a ser propiedades observables del `Embedder`.
- `QdrantVectorStore.collection_name` es siempre un alias de Qdrant; el nombre físico se deriva
  con `physical_name_for(fingerprint) = f"{collection_name}__{fingerprint.digest()}"`.
  `ensure_collection` crea la colección física y el alias si no existe; si el alias ya apunta a
  otra colección física (`current != physical`), rechaza con `AppError(ErrorKind.VALIDATION)` en
  lugar de escribir vectores incompatibles.
- `bind_fingerprint`/`verify_fingerprint`/`_check_bound` hacen la comprobación antes de cada
  `upsert()` y `search()`, incluidos procesos que sólo consultan (`ApplicationContainer` vincula
  el fingerprint en el constructor, no sólo al indexar).
- `chunking.chunk_document(..., fingerprint=...)` incorpora `content_hash` (siempre) y el dígito
  del fingerprint (si se pasa) a la identidad del chunk; `IndexingService.index()` ya no borra el
  documento antes de reescribir: hace `upsert` y luego `store.prune_document(document_id,
  keep_chunk_ids)`, que sólo elimina los puntos que quedaron obsoletos.
- `QdrantVectorStore.publish_alias`/`rollback_alias` mueven el alias atómicamente (una sola
  llamada a `update_collection_aliases`) y nunca borran la colección física anterior;
  `delete_physical` cierra la ventana de rollback explícitamente y se niega a borrar el objetivo
  actual del alias.
- `indexing.migrate_and_publish(live, validate)` puebla una colección candidata a través de un
  `QdrantVectorStore.for_physical_collection` (modo directo, invisible tras el alias), y sólo
  mueve el alias si `validate(report, candidate_store)` —pensado para ejecutar el gold set contra
  el candidato— devuelve `True`; si falla, el alias no se toca y la colección candidata queda
  disponible para inspección.
- Tests nuevos: `tests/test_vector_store.py` (naming, rechazo de reutilización, fallo explícito de
  `search()` ante fingerprint no coincidente, publish/rollback de alias, poda de chunks obsoletos)
  y `tests/test_indexing.py` (`migrate_and_publish` mueve el alias sólo tras validar, y lo deja
  intacto si la validación falla).
- `uv run --no-sync pytest -q` y `./scripts/verify.ps1`: verdes (70 tests), incluidos los gold
  sets existentes sin cambio de resultado.

Rama: `codex/wrk-task-036-index-fingerprint-migration`.
