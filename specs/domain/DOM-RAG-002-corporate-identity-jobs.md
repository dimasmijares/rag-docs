---
id: DOM-RAG-002
type: spec
layer: domain
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: DOM-RAG-001
    relation: extends
  - id: ARCH-002
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [domain, identity, tenant, acl, jobs, synchronization]
---

# DOM-RAG-002 — Identidad, ACL, jobs y sincronización

## Intent

Formalizar los tipos que permiten operación multiusuario, autorización documental e indexación
incremental durable.

## Definition

- `Principal`: `user_id`, `tenant_id`, grupos, roles y claims validados.
- `DocumentIdentity`: tenant, fuente, identificador externo estable y versión.
- `DocumentAcl`: sujetos, grupos, clasificación e herencia normalizada.
- `IndexFingerprint`: extractor, chunking, modelo/revisión, dimensión, prefijos y normalización.
- `JobResource`: identidad, clave idempotente, progreso, timestamps, errores y estado.
- Estados: `queued`, `running`, `cancelling`, `cancelled`, `succeeded`, `failed`.

PostgreSQL es la fuente de verdad de jobs, fuentes, cursores, configuración y auditoría. Los
cursores sólo avanzan tras consolidar una sincronización; los reintentos no duplican efectos.

## Acceptance Criteria

- Los tipos se comparten entre contratos sin propagar representaciones de infraestructura.
- Tenant y ACL acompañan al documento y a todos sus chunks.
- La autorización denegada no confirma existencia ni devuelve metadatos.
