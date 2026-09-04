---
id: WRK-TASK-059
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
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

**Estado por defecto (ADR-RAG-007, decisión D): extracción aprobada.** `generator_profiles.py` ya conmuta en caliente entre perfiles local y remoto; el límite es de facto real hoy y no requiere confirmación adicional de `WRK-TASK-088` para proceder.

## Acceptance Criteria

- [ ] Perfil, capacidades y modelo efectivo acompañan cada respuesta.
- [ ] Timeouts, cancelación y errores se normalizan.
- [ ] Añadir proveedor no cambia query ni grounding.
- [ ] Endpoints autorizados y política de privacidad se aplican por perfil.

## Evidence

Pendiente.
