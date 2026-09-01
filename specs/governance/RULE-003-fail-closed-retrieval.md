---
id: RULE-003
type: rule
layer: rule
scope: persistent
status: active
confidence: low
version: 0.2.0
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

## Applicability

La baseline `v0.1.x`/`v0.2.x` sólo ofrece un modo de desarrollo local monousuario. Ese modo no
afirma aislamiento, autorización documental ni aptitud productiva y debe permanecer limitado al
operador y a fuentes autorizadas. Cualquier modo que exponga identidad, tenants o ACL queda sujeto
a esta regla desde su introducción.

`WRK-TASK-046` elimina la excepción transitoria de la PoC: desde `v1.5.0`, toda consulta —incluido
desarrollo— debe recibir un principal y un ámbito válido o fallar antes del retrieval.

## Enforcement

- Filtro obligatorio de tenant y ACL en la consulta al índice.
- Pruebas multiusuario, multitenant y de fallos de autorización.
- Los servicios validan tokens recibidos y aplican mínimo privilegio.
- Logs y métricas no convierten una denegación en canal lateral.
- Hasta `WRK-TASK-046`, la documentación y los despliegues no pueden presentar la PoC local como
  entorno autorizado o multiusuario.
