---
id: RULE-003
type: rule
layer: rule
scope: persistent
status: active
confidence: low
version: 0.3.0
created: 2026-09-01
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RULE-001
    relation: extends
tags: [security, authorization, retrieval, mandatory]
---

# RULE-003 — Autorización fail-closed antes del retrieval

## Rule Definition

Toda búsqueda documental requiere un principal validado y un ámbito de autorización calculado
antes de consultar Qdrant. Cualquier identidad, política, token, tenant o ACL ausente, inválido o
ambiguo produce denegación sin recuperar ni revelar contenido o existencia.

## Applicability

La baseline `v0.1.x`/`v0.2.x` sólo ofrece un modo de desarrollo local monousuario. Ese modo no
afirma aislamiento, autorización documental ni aptitud productiva y debe permanecer limitado al
operador y a fuentes autorizadas. Cualquier modo que exponga identidad, tenants o ACL queda sujeto
a esta regla desde su introducción.

`WRK-TASK-046` elimina la excepción transitoria de la PoC: desde `v1.5.0`, toda consulta —incluido
desarrollo— debe recibir un principal y un ámbito válido o fallar antes del retrieval.

## Enforcement

- Filtro obligatorio de tenant y ACL en la consulta al índice, en todo backend de
  `VectorStorePort` (`ADR-RAG-013`):
  - Qdrant: filtro de payload `tenant_id`/`acl_subjects`/`classification` con índices `KEYWORD`
    en la misma llamada de búsqueda (`QdrantVectorStore._scope_filter`).
  - Fabric SQL: `WHERE` sobre `tenant_id` y `classification` y `EXISTS` sobre la tabla hija de
    subjects, aplicado antes de `TOP k`; un ámbito sin subjects o clasificaciones devuelve vacío
    sin consultar (`FabricSqlVectorStore.search`/`scan_chunks`, `WRK-TASK-100`).
  - La suite de contrato (`tests/contract`) exige ese prefiltro a ambos backends.
- Pruebas multiusuario, multitenant y de fallos de autorización.
- Los servicios validan tokens recibidos y aplican mínimo privilegio.
- Logs y métricas no convierten una denegación en canal lateral.
- Hasta `WRK-TASK-046`, la documentación y los despliegues no pueden presentar la PoC local como
  entorno autorizado o multiusuario.
