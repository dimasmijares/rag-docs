---
id: WRK-TASK-059
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-010
activates: [ARCH-002, DOM-RAG-001, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-057
    relation: depends-on
tags: [service, llm, gateway, ollama]
---

# WRK-TASK-059 — Model gateway

## Objective

Extraer `POST /v1/generate` y el descubrimiento de modelos con Ollama y proveedores configurables.

## Acceptance Criteria

- [ ] Perfil, capacidades y modelo efectivo acompañan cada respuesta.
- [ ] Timeouts, cancelación y errores se normalizan.
- [ ] Añadir proveedor no cambia query ni grounding.
- [ ] Endpoints autorizados y política de privacidad se aplican por perfil.

## Evidence

Pendiente.
