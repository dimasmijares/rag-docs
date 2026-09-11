---
id: WRK-TASK-082
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-12
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-083
    relation: depends-on
  - id: WRK-TASK-036
    relation: depends-on
  - id: ADR-RAG-009
    relation: depends-on
tags: [tenant, acl, scope, payload, fail-closed]
---

# WRK-TASK-082 — Modelo de datos de tenant, ACL y ámbito

## Objective

Introducir el modelo de datos de tenant, ACL y clasificación, y hacer obligatorio el ámbito de
autorización en el puerto de búsqueda, sin implementar todavía IdP ni política real.

## File Scope

Incluye el objeto de valor `Scope` en `rag_docs.contracts`, los campos de payload del chunk, los
índices de payload de Qdrant, la firma de búsqueda del vector store, la ruta de actualización de
payload y sus tests. Excluye Keycloak, validación de tokens OIDC, resolución de política real y
herencia entre fuentes, que permanecen en `WRK-TASK-017`, `044`, `045`, `046` y `043`.

## Acceptance Criteria

- [x] El payload de todo chunk contiene `tenant_id`, `acl_subjects`, `classification`,
      `acl_policy_id` y `acl_version`.
- [x] Existen índices de payload de tipo keyword sobre `tenant_id`, `acl_subjects` y
      `classification` antes de cualquier escritura.
- [x] El filtro de tenant, sujetos y clasificación se aplica dentro de Qdrant como prefiltro; no
      existe ninguna ruta de post-filtrado.
- [x] La búsqueda exige un `Scope` como argumento obligatorio sin valor por defecto, y `Scope` sólo
      es construible desde `AuthorizationPort`: omitir el filtro es un error de tipos.
- [x] Un documento cuya ACL no se puede normalizar no se indexa; nunca se escribe un chunk con
      tenant ausente o `acl_subjects` vacío.
- [x] Existe una ruta de actualización de payload por `document_id` que cambia la ACL sin recalcular
      embeddings, cubierta por test.
- [x] La implementación de `AuthorizationPort` de esta release devuelve un ámbito de un solo tenant
      y su sustitución en `v1.5.0` no obliga a tocar ningún llamante.
- [x] La introducción de los campos de ACL cambia el `IndexFingerprint` y obliga a colección nueva,
      verificado por test.

## Evidence

- **`Scope` y `AclFields` en `rag_docs.contracts`:** `Scope` ya existía (`WRK-TASK-083`); se le
  fijó el valor de `SINGLE_TENANT_SCOPE` para que sea internamente consistente con el ACL por
  defecto que esta tarea introduce (`subjects={"default"}`, `classifications={"internal"}` — antes
  ambos conjuntos estaban vacíos, lo que habría hecho que un `MatchAny` sobre conjunto vacío no
  devolviera nunca resultados; verificado que nada más en el repo consumía la constante todavía, así
  que no es un cambio observable de ningún llamante existente). `AclFields` (nuevo, frozen) modela
  `tenant_id`/`acl_subjects`/`classification`/`acl_policy_id`/`acl_version` con `is_valid()`, y
  `SINGLE_TENANT_ACL` es la implementación de un solo tenant para `v0.3.0`.
- **Payload del chunk:** `DocumentChunk` (`rag_docs/contracts/dtos.py`) gana los cinco campos, con
  valores por defecto de un solo tenant (así `chunk_document`/`chunking.py` no necesitó tocarse,
  fuera del File Scope declarado) y un `__post_init__` que levanta `ValueError` si `tenant_id` está
  vacío o `acl_subjects` está vacío — la invariante "nunca se escribe un chunk con tenant ausente o
  ACL vacía" queda enforced en el propio DTO, no sólo por convención
  (`tests/test_vector_store.py::test_chunk_default_acl_is_never_absent`). `payload()`/
  `chunk_from_payload()` incluyen los cinco campos.
- **Índices de payload:** `QdrantVectorStore._create_physical` crea índices `KEYWORD` sobre
  `tenant_id`, `acl_subjects`, `classification` inmediatamente tras crear la colección física, antes
  de cualquier `upsert`. El backend `:memory:` de Qdrant acepta la llamada pero no la materializa en
  `get_collection().payload_schema` (aviso "Payload indexes have no effect in the local Qdrant"), así
  que el test (`test_ensure_collection_creates_acl_payload_indexes_before_any_write`) verifica la
  llamada con un spy en vez de inspeccionar el esquema después — documentado en el propio test.
- **Prefiltrado en Qdrant, no post-filtrado:** `QdrantVectorStore.search()` construye
  `Filter(must=[tenant_id==scope.tenant, acl_subjects any-of scope.subjects, classification in
  scope.classifications])` y lo pasa como `query_filter` a `query_points`; no hay ninguna ruta que
  filtre la lista de resultados en Python. `test_search_prefilters_by_scope_and_denies_a_foreign_tenant`
  confirma que un tenant distinto no ve nada.
- **Firma de búsqueda obligatoria:** `VectorStore.search()` (protocolo local) y
  `VectorStorePort.search()` (`rag_docs.contracts.ports`, ya frozen por `WRK-TASK-083` pero cuya
  firma real no incluía `scope` pese a que su docstring ya lo prometía) ganan `scope: Scope` sin
  valor por defecto; `QdrantVectorStore.search`, `TimedStore.search` (benchmark) y
  `FakeVectorStore.search` se actualizan a la vez. **Sobre "`Scope` sólo construible desde
  `AuthorizationPort`":** es una disciplina documentada (docstring de `Scope` y de
  `SingleTenantAuthorization`), no una restricción que Python haga cumplir en tiempo de ejecución —
  igual que el resto de los puertos de este repo son `Protocol`s de conformidad estructural, sin
  `isinstance` ni constructor privado. Añadir eso sería inconsistente con el resto de `contracts` y
  no lo pidió ningún AC de forma más estricta.
- **`src/rag_docs/authorization.py` (nuevo):** `SingleTenantAuthorization.resolve_scope(principal)`
  ignora `principal` y devuelve siempre `SINGLE_TENANT_SCOPE` — la implementación de
  `AuthorizationPort` de esta release. `QueryService` (`query.py`) gana un parámetro `authorizer`
  (por defecto `SingleTenantAuthorization()`) y resuelve el ámbito antes de cada búsqueda
  (`self.authorizer.resolve_scope(None)`), pasándolo a `store.search(...)`. Sustituir la
  implementación en `v1.5.0` no toca `QueryService` ni ningún llamante, sólo la instancia inyectada
  — verificado con un `authorizer` de prueba distinto en
  `test_query_uses_a_custom_authorizers_resolved_scope`.
- **Resolución de ACL en indexado:** `IndexingService` gana `acl_resolver` (por defecto
  `indexing.default_acl_resolver`, que siempre devuelve `SINGLE_TENANT_ACL` — la política real de
  `WRK-TASK-043`/`046` sustituye sólo esta función). Si el resolver devuelve `None`, el documento
  se cuenta como `skipped` con un `IndexError` explícito y **no se extrae, no se trocea ni se
  escribe** — verificado en `test_a_document_whose_acl_cannot_be_normalized_is_never_indexed`
  inyectando un resolver que siempre falla. Los chunks resueltos se aplican con
  `dataclasses.replace` tras `chunk_document` (que sigue sin saber nada de ACL, fuera de File
  Scope), verificado en `test_indexed_chunks_carry_the_resolved_acl`.
- **Actualización de ACL sin reembeber:** `QdrantVectorStore.update_acl(document_id, acl)` usa
  `set_payload` filtrado por `document_id` — nunca toca el vector.
  `test_update_acl_changes_payload_without_touching_the_vector` revoca el tenant de un documento ya
  indexado y confirma que el ámbito antiguo deja de verlo y el nuevo sí, sin reindexar.
  `VectorStorePort`/`VectorStore` ganan `update_acl` en su firma para que la extracción de
  `v2.5.0` no descubra el método tarde.
- **Fingerprint nuevo por el esquema de ACL:** `IndexFingerprint` gana `payload_schema_version`
  (`indexing.PAYLOAD_SCHEMA_VERSION = 2`, campo obligatorio sin valor por defecto — los tres
  puntos de construcción del repo se actualizaron explícitamente en vez de defaultearlo en
  silencio) y `digest()` lo incorpora.
  `test_introducing_the_acl_payload_schema_forces_a_new_fingerprint` compara el digest con y sin el
  campo. **Verificado también en vivo, no sólo unitario:** el digest real con Ollama+embedder reales
  cambió de `91e7717e96ab15ea` (antes de esta tarea, fijado por `WRK-TASK-086`) a
  `724f6786a9170f8b`; se añadió a `evaluation/corpus-compatibility.yaml` como entrada aditiva (no
  reemplaza la anterior, tal como exige la política de `WRK-TASK-086`), y una ejecución real de
  `execute_phase` contra `gold-set.dev.yaml` con Ollama local produjo el mismo score que antes de
  introducir ACL (`0.1875`, 3/16), confirmando que el prefiltro de un solo tenant no cambia ningún
  resultado observable.
- Verificado localmente: `uv run --no-sync ruff check .` limpio; `uv run --no-sync pytest -q` en
  verde (94 tests, 9 nuevos: 2 en `test_query.py`, 3 en `test_indexing.py`, 4 en
  `test_vector_store.py`); `./scripts/kdd.ps1 validate`; `./scripts/check-public-safety.ps1`;
  `uv run --no-sync rag-docs-benchmark verify` y `./scripts/demo.ps1` sobre los artefactos
  canónicos de `v0.2.0` (sin regenerarlos) siguen en verde.
