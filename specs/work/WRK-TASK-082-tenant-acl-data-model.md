---
id: WRK-TASK-082
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
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

- [ ] El payload de todo chunk contiene `tenant_id`, `acl_subjects`, `classification`,
      `acl_policy_id` y `acl_version`.
- [ ] Existen índices de payload de tipo keyword sobre `tenant_id`, `acl_subjects` y
      `classification` antes de cualquier escritura.
- [ ] El filtro de tenant, sujetos y clasificación se aplica dentro de Qdrant como prefiltro; no
      existe ninguna ruta de post-filtrado.
- [ ] La búsqueda exige un `Scope` como argumento obligatorio sin valor por defecto, y `Scope` sólo
      es construible desde `AuthorizationPort`: omitir el filtro es un error de tipos.
- [ ] Un documento cuya ACL no se puede normalizar no se indexa; nunca se escribe un chunk con
      tenant ausente o `acl_subjects` vacío.
- [ ] Existe una ruta de actualización de payload por `document_id` que cambia la ACL sin recalcular
      embeddings, cubierta por test.
- [ ] La implementación de `AuthorizationPort` de esta release devuelve un ámbito de un solo tenant
      y su sustitución en `v1.5.0` no obliga a tocar ningún llamante.
- [ ] La introducción de los campos de ACL cambia el `IndexFingerprint` y obliga a colección nueva,
      verificado por test.

## Evidence

Pendiente.
