---
id: RULE-003
type: rule
layer: rule
scope: persistent
status: active
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
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

## Enforcement

- Filtro obligatorio de tenant y ACL en la consulta al índice.
- Pruebas multiusuario, multitenant y de fallos de autorización.
- Los servicios validan tokens recibidos y aplican mínimo privilegio.
- Logs y métricas no convierten una denegación en canal lateral.
