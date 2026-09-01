---
id: WRK-TASK-004
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-25
owner: rag-docs-team
parent: WRK-PLAN-001
activates: [DOM-RAG-001, RULE-001, ARCH-001]
dependencies:
  - id: WRK-TASK-003
    relation: depends-on
tags: [retrieval, ollama, grounding]
---

# WRK-TASK-004 — Consulta grounded

## Objective

Recuperar contexto, llamar a Ollama y producir respuestas citadas o insuficientes.

## Scope

Incluye retrieval, prompt, generador y política de respuesta. Excluye HTTP y web.

## Acceptance Criteria

- [ ] Se recuperan ocho candidatos y se entregan hasta cinco fragmentos deduplicados.
- [ ] No puede emitirse `grounded` sin citas válidas.

## Test Plan

Generador y vector store falsos para casos con evidencia, sin evidencia y fallo del modelo.

## Evidence

Pruebas grounded, sin hits y rechazo explícito del generador superadas.

## Traceability

Implementado en `generation.py`, `query.py` y `tests/test_query.py`.
