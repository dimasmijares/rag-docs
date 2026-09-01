---
id: WRK-TASK-049
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-003, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-048
    relation: depends-on
tags: [release, v1.5.0, oidc, security]
---

# WRK-TASK-049 — Release de seguridad v1.5.0

## Objective

Ejecutar E2E con varios usuarios, confirmar fail-closed y consolidar `v1.5.0`.

## Acceptance Criteria

- [ ] Login OIDC y consultas autorizadas funcionan end-to-end.
- [ ] Denegaciones no filtran contenido ni existencia.
- [ ] El modo inseguro no arranca en configuración productiva.
- [ ] `WRK-SPEC-008` se consolida antes de la release.

## Evidence

Pendiente.
