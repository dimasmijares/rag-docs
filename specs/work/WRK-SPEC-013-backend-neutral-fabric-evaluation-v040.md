---
id: WRK-SPEC-013
type: spec
layer: work-spec
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-012
    relation: depends-on
  - id: RFC-004
    relation: depends-on
  - id: ADR-RAG-013
    relation: depends-on
tags: [release, v0.4.0, fabric, vector-store, evaluation, power-bi]
---

# WRK-SPEC-013 — Backend neutral y plano de evaluación en Fabric v0.4.0

## Proposed Change

Introducir las costuras de backend vectorial y publicación que el esquema de `v1.0.0` da por
supuestas, y usarlas para un primer perfil Fabric sin runtime asíncrono: el índice construido en
local se publica en SQL database in Fabric, la API y la web locales consultan ese backend con Ollama,
y la evaluación se almacena en Delta y se visualiza en Power BI.

## Rationale

`RFC-004` y `ADR-RAG-013` exigen que ledger y store queden tras puertos antes de modelar PostgreSQL;
hacerlo después obligaría a rehacer el esquema de `WRK-TASK-030`. Validar un segundo backend real
antes de `v1.0.0` demuestra que los puertos no están diseñados sólo para Qdrant.

## Acceptance Criteria

- [x] El monolito consume un único `VectorStorePort` e `IndexPublicationPort`, y el backend se elige
      por configuración sin cambiar el comportamiento con Qdrant.
- [x] App y benchmark producen el mismo digest de fingerprint para la misma configuración.
- [x] Una suite de contrato común pasa contra Qdrant en el gate por defecto y contra Fabric SQL en
      `scripts/verify-fabric.ps1`.
- [x] El gate público rechaza notebooks con outputs, cadenas de conexión con credenciales e IDs de
      tenant o workspace antes de versionar cualquier artefacto Fabric.
- [x] La API local responde con citas válidas consultando vectores en Fabric SQL, con el prefiltro de
      ámbito y el fingerprint aplicados.
- [x] Todo informe declara `vector_backend` y `vector_search_mode`; la latencia no se compara entre
      backends.
- [x] Gold sets e informes se cargan en Delta por `corpus_version` y un informe Power BI versionado
      en PBIP los muestra por perfil, backend y fingerprint.
- [x] `scripts/verify.ps1` sigue en verde sin Fabric ni credenciales.

## Evidence

Las once tareas funcionales de `WRK-PLAN-013` están mergeadas en `main` y archivadas con Evidence
completa. `WRK-TASK-104` las consolida. Por criterio:

1. **Puertos únicos y backend por configuración** (`WRK-TASK-094`, #32):
   - `VectorStorePort` es el único protocolo de store y se añade `IndexPublicationPort`.
   - `Settings.vector_backend` y la factoría del contenedor eligen la implementación, y la migración
     opera sobre puertos.
   - La suite previa pasó sin cambios de comportamiento y el drill con Qdrant sigue igual.
2. **Mismo digest app ↔ benchmark** (`WRK-TASK-095`, #34): `Settings.embedding_revision` fija la
   revisión del benchmark y un test verifica la igualdad (`724f6786a9170f8b`, ya declarado). La
   exposición del fingerprint en la API (`WRK-TASK-093`, #33) permitió detectar y cerrar la
   divergencia previa (`8270a45e87e30cc7`).
3. **Suite de contrato común** (`WRK-TASK-096`, #35; `WRK-TASK-100`, #38): 11 casos contra Qdrant
   `:memory:` en `scripts/verify.ps1` y 11/11 contra `FabricSqlVectorStore` en
   `scripts/verify-fabric.ps1`, sin tablas residuales.
4. **Gate público ampliado** (`WRK-TASK-097`, #31, mergeada antes de cualquier artefacto Fabric):
   notebooks con outputs, cadenas de conexión y URLs con credenciales, GUIDs de tenant/workspace,
   endpoints SQL de Fabric y datos Delta/PBIP locales, con fixtures negativas y positivas. Durante la
   tarea destapó y corrigió que los ficheros ocultos no se escaneaban en Linux. Todos los artefactos
   de `fabric/` lo superan.
5. **API con citas desde Fabric SQL** (`WRK-TASK-101`, #39):
   - índice local publicado sin reembeber y con validación previa, digest publicado igual al local;
   - `rag-docs-eval` 4/4 con citas contra la API servida desde Fabric, con prefiltro de ámbito antes
     de `TOP k` y verificación de fingerprint antes de puntuar;
   - drill de migración y rollback en SQL, con rechazo de la vinculación obsoleta.
6. **Backend y modo en todo informe** (`WRK-TASK-098`, #36; `WRK-TASK-101`):
   - `schema_version` 1.1; los 1.0 se leen como `qdrant`/`hnsw`;
   - `compare_reports` exige re-baseline entre backends o modos y solo compara latencia bajo la
     clave completa;
   - la API declara backend y modo para que `rag-docs-eval` los registre.
7. **Delta y Power BI** (`WRK-TASK-102`, #40; `WRK-TASK-103`, #41):
   - Carga append-only e idempotente de 3 gold sets, manifiesto y 8 informes por `corpus_version`.
   - Paridad de recall exacta entre Qdrant y Fabric SQL (`dense` y `dense-reranked`, dev y
     validation).
   - DiskANN evaluado como experimento G2 y no adoptado.
   - Informe PBIP con Direct Lake sin identificadores versionados, filtrable por perfil, backend,
     `corpus_version` y fingerprint, con la latencia segregada por backend (render verificado por
     exportación).
8. **Gate por defecto sin Fabric:** `scripts/verify.ps1` en verde en todas las PRs de la release
   (152 tests al cierre) sin el extra `[fabric]` ni credenciales. CI (`quality-gates`) verde en
   #31–#41.

Documentación: `README.md` (release, API, comparabilidad, backends y perfil opcional Fabric),
`DOC-RAG-001` 1.5.0 y `DOC-RAG-003` 1.0.0. Versión del proyecto `0.4.0`.
