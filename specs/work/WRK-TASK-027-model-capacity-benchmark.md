---
id: WRK-TASK-027
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-005
activates: [ARCH-001, FEAT-RAG-001, DOC-RAG-002, RULE-001, RULE-002]
dependencies:
  - id: WRK-TASK-012
    relation: depends-on
  - id: WRK-TASK-026
    relation: depends-on
tags: [benchmark, llm, embeddings, latency, memory]
---

# WRK-TASK-027 — Benchmark de modelos y capacidad

## Objective

Comparar generadores 3B/14B, embeddings y fallback con métricas de calidad, p50/p95, memoria y
configuración efectiva.

## File Scope

Incluye runner, configuración y resultados sintéticos de benchmark. Excluye modificar el split de
validación, publicar resultados locales privados o adoptar hybrid/reranking.

## Acceptance Criteria

- [ ] Separar latencia de embedding, retrieval, grounding y generación.
- [ ] Seleccionar modelos y parámetros exclusivamente sobre desarrollo y bloquear la decisión.
- [ ] Ejecutar validación una sola vez como confirmación, sin modificarla tras conocer resultados.
- [ ] Registrar runs cold/warm, hardware, revisión, parámetros, semillas, memoria y errores reproducibles.
- [ ] Recomendar baseline local y remoto con sus límites.

## Evidence

Pendiente.
