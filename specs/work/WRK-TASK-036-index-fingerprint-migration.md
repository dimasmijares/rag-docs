---
id: WRK-TASK-036
type: spec
layer: work-task
scope: ephemeral
status: draft
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

- [ ] El fingerprint cubre extractor, chunking con sus parámetros, modelo de embeddings con
      revisión, dimensión, normalización y convención de prefijos; ninguno de esos componentes
      queda incrustado y opaco dentro de un adaptador.
- [ ] El fingerprint se persiste asociado a la colección y se comprueba antes de escribir y antes
      de consultar; la discrepancia falla de forma explícita y nunca degrada.
- [ ] `ensure_collection` deja de aceptar una colección existente por el mero hecho de existir; una
      colección con otro fingerprint y la misma dimensión se rechaza.
- [ ] La identidad del chunk incorpora `content_hash` e `index_fingerprint`, de modo que contenido
      distinto produce puntos distintos y la reescritura deja de exigir borrado previo.
- [ ] El nombre físico de la colección deriva del fingerprint y el nombre configurado actúa como
      alias.
- [ ] Una colección nueva se valida contra el gold set antes de mover el alias.
- [ ] Rollback conserva la colección anterior durante la ventana definida.

## Evidence

Pendiente.
