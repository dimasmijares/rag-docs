---
id: WRK-PLAN-008
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-008
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v1.5.0, oidc, acl]
---

# WRK-PLAN-008 — Seguridad preparada v1.5.0

## Task Decomposition

`017` define identidad sobre el modelo de datos de `WRK-TASK-082`; `043/044` propagan ACL y
preparan el IdP; `045 → 046 → 047 → 048 → 049` valida autenticación, autorización, aislamiento,
threat model y release. `085` re-baseliniza evaluación y benchmark tras activar el prefiltrado y
es prerrequisito de `049`.

## Gate

Autorización fail-closed y ausencia comprobada de contenido o metadatos no autorizados.
