---
id: WRK-TASK-027
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-02
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

# WRK-TASK-027 — Baseline local reproducible

## Objective

Establecer en el portátil una baseline reproducible comparando el generador local 3B, embeddings
compatibles con sus recursos y fallback mediante métricas de calidad, p50/p95, memoria y
configuración efectiva.

## File Scope

Incluye runner, configuración, bloqueo de decisión y resultados sintéticos de benchmark
reproducibles en este portátil desde un clon limpio. Excluye modelos 14B, ejecuciones dependientes
del PC personal o de un endpoint remoto, modificar el split de validación, publicar resultados
locales privados o adoptar hybrid/reranking.

## Acceptance Criteria

- [ ] Separar latencia de embedding, retrieval, grounding y generación.
- [ ] Comparar sobre desarrollo sólo configuraciones ejecutables íntegramente en el portátil:
  generador 3B, embeddings compatibles y fallback explícito.
- [ ] Seleccionar modelos y parámetros exclusivamente sobre desarrollo y bloquear la decisión
  antes de consultar validación.
- [ ] Ejecutar validación una sola vez como confirmación, sin modificarla ni repetir la selección
  tras conocer resultados.
- [ ] Registrar runs cold/warm, hardware, revisión, parámetros, semillas, memoria y errores de
  forma reproducible y publicable.
- [ ] Recomendar la baseline local, documentar sus límites y verificar el procedimiento desde un
  clon limpio sin depender del PC personal.

## Evidence

Pendiente.

## Deferred Work

La comparación con un 14B ejecutado en el PC personal queda fuera del gate de `v0.2.0` y se
realizará, cuando ese equipo esté disponible, mediante `WRK-TASK-081`. No se publicarán resultados
14B simulados ni se presentará esa configuración como verificada antes de ejecutarla.
