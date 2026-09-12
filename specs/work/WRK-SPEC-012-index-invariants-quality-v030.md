---
id: WRK-SPEC-012
type: spec
layer: work-spec
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-04
updated: 2026-09-12
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-005
    relation: depends-on
  - id: ADR-RAG-007
    relation: depends-on
  - id: ADR-RAG-010
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [release, v0.3.0, fingerprint, contracts, retrieval, quality]
---

# WRK-SPEC-012 — Invariantes de índice y calidad v0.3.0

## Proposed Change

Aplicar dentro del monolito, y antes de introducir infraestructura nueva, los invariantes que las
releases posteriores dan por supuestos: enforcement del fingerprint del índice, puertos y objetos de
valor compartidos, modelo de datos de tenant y ACL, y la mejora medida del retrieval.

## Rationale

`RULE-004` es `active` con enforcement previsto dos releases más tarde; el esquema PostgreSQL de
`v1.0.0` se diseñaría sin tenant; y la evidencia de calidad que justifica industrializar llegaría
después de haber industrializado. Esta release corrige las tres cosas sin añadir ninguna dependencia
de infraestructura: todo el trabajo ocurre en `src/rag_docs/**`, `evaluation/**` y `specs/**`.

## Acceptance Criteria

- [x] Escribir o consultar con un fingerprint distinto al de la colección falla de forma explícita.
- [x] Los puertos y objetos de valor compartidos existen en `rag_docs.contracts` sin dependencias de
      I/O y son los que consume el monolito.
- [x] El puerto de búsqueda exige un ámbito de autorización sin valor por defecto.
- [x] Un cambio de ACL no requiere recalcular embeddings.
- [x] Toda evaluación declara `corpus_version`, `index_fingerprint` y configuración efectiva.
- [x] Hybrid y reranking sólo se adoptan si superan el baseline con evidencia reproducible.
- [x] El gate de publicación deja de contener en claro los identificadores que protege.

## Evidence

`WRK-PLAN-012` descompone esta spec en ocho tareas, todas mergeadas en `main` y archivadas
conservando su Evidence (`WRK-TASK-092/083/036/090/086/082/037/038`); `WRK-TASK-091` consolida la
release y cierra esta spec:

- **Fingerprint (`RULE-004`):** `IndexFingerprint` (`rag_docs.contracts.value_objects`) se persiste
  como nombre físico de colección Qdrant detrás de un alias lógico; `verify_fingerprint`/
  `_check_bound` rechazan de forma explícita cualquier escritura o consulta cuyo fingerprint
  vinculado no coincida con el que resuelve el alias (`WRK-TASK-036`). `migrate_and_publish`/
  `rollback_alias` ofrecen migración con validación previa y ventana de rollback, verificada en vivo
  con el corpus sintético en `scripts/migration_drill.py` (`WRK-TASK-091`).
- **Puertos y objetos de valor (`ADR-RAG-010`):** `rag_docs.contracts` (`ports.py`, `dtos.py`,
  `value_objects.py`) no tiene dependencias de I/O; `VectorStorePort`, `AuthorizationPort`,
  `GroundingPort`, `RetrievalPort`, `EmbeddingPort`, `GenerationPort` y `DocumentSourcePort` fijan
  las fronteras que el monolito ya consume (`WRK-TASK-083`, `090`).
- **Ámbito obligatorio (`RULE-003`, `ADR-RAG-009`):** `VectorStorePort.search`/`scan_chunks` exigen
  `Scope` sin valor por defecto; `SingleTenantAuthorization.resolve_scope` lo resuelve por petición
  y `QueryService` lo aplica siempre antes de recuperar (`WRK-TASK-082`).
- **ACL sin recalcular embeddings:** `VectorStore.update_acl` cambia `tenant_id`/`acl_subjects`/
  `classification` vía `set_payload`, sin tocar el vector ni reindexar (`WRK-TASK-082`).
- **Comparabilidad de evaluación (`ADR-RAG-011`):** `evaluation/corpus-compatibility.yaml` más
  `verify_gold_corpus_version`/`verify_fingerprint_compatibility` obligan a declarar
  `corpus_version`/`index_fingerprint`/configuración efectiva en todo informe; `compare_reports`
  rechaza comparar tripletas distintas sin `--rebaseline` explícito (`WRK-TASK-086`).
- **Adopción de retrieval basada en evidencia (`RFC-001` gate G2):** hybrid retrieval (`WRK-TASK-037`)
  se midió sobre ambos gold sets y **no** se adoptó por defecto (regresión en `recall_at_8` de
  validación); reranking por cross-encoder (`WRK-TASK-038`, `ADR-RAG-012`) se midió limpio y sin
  regresiones y se adoptó como capacidad opt-in. El informe consolidado que compara los tres
  perfiles sobre el mismo `index_fingerprint` vive en `evaluation/benchmarks/wrk-task-091/`.
- **Gate de publicación sin identificadores en claro:** la lista de identificadores derivados salió
  del repositorio a un fichero local/secreto de CI; el gate público advierte, no falla, en su
  ausencia (`WRK-TASK-092`, `ADR-RAG-011`).
- README y `DOC-RAG-001` documentan fingerprint, ámbito obligatorio y política de comparabilidad
  (`WRK-TASK-091`).
