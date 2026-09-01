---
id: WRK-SPEC-011
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-010
    relation: depends-on
  - id: ADR-005
    relation: depends-on
  - id: ADR-006
    relation: depends-on
tags: [release, v3.0.0, kubernetes, helm, kind]
---

# WRK-SPEC-011 — Kubernetes v3.0.0

## Proposed Change

Desplegar la plataforma en `kind` mediante Helm, Gateway API/Envoy, controles de seguridad,
telemetría, escalado y cadena de suministro GHCR.

## Acceptance Criteria

- [ ] Una orden documentada instala core y security; observabilidad es opcional.
- [ ] El chart acepta dependencias internas o endpoints externos.
- [ ] CI construye, escanea, firma y prueba imágenes y chart en `kind`.
- [ ] Rollback, restore, rolling update y disaster drill están ensayados.

## Evidence

Pendiente de `WRK-PLAN-011`.
