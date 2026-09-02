---
id: WRK-TASK-081
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-02
updated: 2026-09-02
owner: rag-docs-team
parent: WRK-PLAN-007
activates: [ARCH-001, ARCH-002, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-011
    relation: depends-on
  - id: WRK-TASK-027
    relation: depends-on
  - id: WRK-TASK-029
    relation: depends-on
tags: [benchmark, llm, 14b, remote, capacity, deferred]
---

# WRK-TASK-081 — Benchmark 14B en PC personal

## Objective

Comparar la baseline local 3B con un generador 14B ejecutado en el PC personal, reutilizando el
runner y la decisión reproducible de `WRK-TASK-027` sin trasladar documentos, embeddings ni el
índice fuera del portátil.

## File Scope

Incluye configuración declarativa, comprobación de capacidades, ejecución sobre corpus sintético,
resultados saneados y documentación de red del benchmark remoto. Excluye exigir el PC personal
para reproducir releases anteriores, publicar IP, hardware detallado o configuración privada,
usar corpus corporativo y presentar como medido cualquier resultado no ejecutado.

## Acceptance Criteria

- [ ] El portátil conserva fuentes, embeddings, retrieval y grounding; sólo el contexto sintético
  autorizado se envía al generador 14B del PC personal.
- [ ] La misma revisión, configuración bloqueada, semillas y split de desarrollo comparan 3B y
  14B con runs cold/warm, calidad, latencia de generación, memoria y errores.
- [ ] El endpoint remoto verifica modelo y capacidades antes de iniciar y falla de forma explícita
  si el PC personal no está disponible.
- [ ] La evidencia pública omite IP, rutas personales, respuestas, fragmentos y detalles de
  hardware identificables, y distingue claramente configuración planificada de ejecución medida.
- [ ] Cualquier cambio de baseline o topología queda respaldado por una ADR y por una validación
  ejecutada una sola vez después de bloquear la decisión.

## Evidence

Pendiente de disponibilidad explícita del PC personal; esta tarea no bloquea `v0.2.0`.
