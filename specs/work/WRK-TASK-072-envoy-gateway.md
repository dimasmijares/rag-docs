---
id: WRK-TASK-072
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-011
activates: [ARCH-002, FEAT-RAG-003, DOC-RAG-002, RULE-003]
dependencies:
  - id: WRK-TASK-071
    relation: depends-on
tags: [envoy, gateway-api, httproute, tls, rate-limit]
---

# WRK-TASK-072 — Envoy Gateway y entrada

## Objective

Exponer APIs mediante Gateway API/HTTPRoute con Envoy, TLS y rate limiting.

## Acceptance Criteria

- [ ] Sólo fachadas públicas tienen rutas externas.
- [ ] TLS local reproducible y certificados externos son configurables.
- [ ] Límites distinguen consulta, jobs y administración.
- [ ] Errores del gateway conservan correlación sin filtrar detalles internos.

## Evidence

Pendiente.
