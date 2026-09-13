---
id: WRK-TASK-101
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.2.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-003, RULE-001, RULE-004]
dependencies:
  - id: WRK-TASK-095
    relation: depends-on
  - id: WRK-TASK-100
    relation: depends-on
tags: [fabric, walking-skeleton, migration, end-to-end]
---

# WRK-TASK-101 — Walking skeleton local → Fabric SQL

## Objective

Demostrar el recorrido completo: índice construido en local, publicado en Fabric SQL y consultado
desde la API y la web locales con Ollama.

## File Scope

Incluye scripts de publicación del índice local al backend Fabric, la adaptación de
`scripts/migration_drill.py` para el backend SQL, tests live en `scripts/verify-fabric.ps1` y
documentación en `DOC-RAG-003`. Excluye indexación en Fabric y evaluación en Delta.

## Acceptance Criteria

- [x] El digest del fingerprint publicado en Fabric coincide con el del índice local.
- [x] Una consulta sobre el corpus sintético devuelve respuesta grounded con citas válidas usando el
      backend Fabric.
- [x] El drill de migración y rollback se ejecuta en SQL y una vinculación obsoleta rechaza la
      consulta.

## Evidence

Ejecución live de `scripts/verify-fabric.ps1 -WalkingSkeleton` (2026-09-13, workspace `rag-docs`,
SQL database `ragdocs_vectors`, service principal con Contributor, Ollama `qwen2.5:3b` local).
Terminó en 0 y los logs quedaron en `_build/verify-fabric/`, no versionado.

- Contrato: `11 passed` contra `FabricSqlVectorStore`.
- `scripts/publish_index_to_fabric.py` (nuevo):
  - Indexa en local el corpus sintético (12 documentos, 22 chunks) con el embedder de revisión
    fijada y el cliente Qdrant embebido.
  - Copia chunks y vectores, sin reembeber, a un candidato Fabric del mismo fingerprint.
  - Valida antes de publicar: `same_chunk_count`, `same_chunk_ids`, `same_top_hits` y
    `top_score_delta_below_1e-4`, todos `true`.
  - Publica el alias: `local_fingerprint_digest = 724f6786a9170f8b`, índice publicado
    `rag_docs__724f6786a9170f8b`, `published_digest_matches_local: true`.
  - Docker no está instalado en el equipo. El índice local se construye con el cliente Qdrant
    embebido, igual que el benchmark y el drill; con `--source-qdrant-url` se publica desde un
    Qdrant en marcha tras verificar su fingerprint.
- `scripts/migration_drill.py --backend fabric_sql` (adaptado a los puertos y con código de
  salida):
  - índice inicial `migration_drill__724f6786a9170f8b` (12 documentos, sin errores, 5 hits);
  - migración a `0cade1276cbb89e7` con alias en el nuevo y el anterior conservado;
  - `stale_fingerprint_binding_rejected_search: true`;
  - rollback con alias en el original, el nuevo conservado para forense y 5 hits.

  Empieza y termina con el índice lógico limpio. El drill por defecto con Qdrant sigue terminando en
  0 con los mismos resultados.
- API y consulta:
  - `verify-fabric.ps1` arranca `uvicorn rag_docs.api:app` con `RAG_DOCS_VECTOR_BACKEND=fabric_sql`.
  - `GET /api/sources` declara `vector_backend: fabric_sql`, `vector_search_mode: exact` y el
    fingerprint vigente `724f6786a9170f8b`, el mismo que el publicado.
  - `rag-docs-eval` sobre el smoke gold set, que verifica compatibilidad de fingerprint antes de
    puntuar: `4/4`. `etl-clientes`, `ruta-etl-clientes` e `incidencia-clientes` salen `grounded`
    con `citations_ok` y `retrieval_ok`; `fuera-de-corpus` sale `insufficient_evidence`.
  - Retrieval: `recall_at_3/5/8 = 1.0`, `MRR = 0.78`. El informe sale con `schema_version 1.1`.
  - La web local es la misma app (`/` sirve `static/index.html` sobre esta API). La comprobación
    automatizada se hace sobre la API, no con navegador.
- Cambio adicional necesario: `GET /api/sources` expone `vector_backend` y `vector_search_mode`
  (`container.VECTOR_SEARCH_MODES`: `qdrant → hnsw`, `fabric_sql → exact`). Sin ello
  `rag-docs-eval` habría etiquetado como `qdrant/hnsw` una evaluación servida desde Fabric
  (`WRK-TASK-098`). Es aditivo y está cubierto por
  `test_sources_declare_the_backend_and_search_mode_served`; queda fuera del File Scope literal y se
  declara aquí.
- `verify-fabric.ps1`: los avisos por stderr de herramientas (Hub de modelos) ya no abortan el gate
  en Windows PowerShell 5.1; decide el código de salida. Así se detectó y corrigió en la primera
  ejecución.
- `DOC-RAG-003`: sección "Backend vectorial y walking skeleton" con el gate, los pasos de
  `-WalkingSkeleton` y la configuración de la API local servida desde Fabric.
- El índice `rag_docs__724f6786a9170f8b` queda publicado en Fabric como base de `WRK-TASK-102`.
  `scripts/verify.ps1` en verde sin Fabric.
