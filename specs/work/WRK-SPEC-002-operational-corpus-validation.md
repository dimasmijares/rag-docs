---
id: WRK-SPEC-002
type: spec
layer: work-spec
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-08-30
owner: rag-docs-team
activates: [ARCH-001, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, RULE-001]
dependencies:
  - id: WRK-SPEC-001
    relation: depends-on
  - id: DOM-RAG-001
    relation: constrained-by
  - id: RULE-001
    relation: constrained-by
tags: [rag, operational-corpus, evaluation, privacy]
---

# WRK-SPEC-002 — Validación con corpus operativo

## Problem Statement

La PoC se ha validado con documentos sintéticos, pero todavía debe medirse con documentación operativa heterogénea y autorizada.

## Proposed Change

Añadir el corpus como fuente local independiente, indexarlo sin retirar el corpus didáctico y crear una evaluación local basada en hechos verificables.

## Constraints

La ruta, las preguntas y las respuestas del corpus operativo no se versionarán. Los documentos y su contenido permanecerán en procesos locales.

## Acceptance Criteria

- [x] La API muestra una fuente sintética y otra local privada como fuentes separadas.
- [x] La indexación local termina y registra errores por documento sin detener el lote.
- [x] Un gold set local comprueba recuperación, citas, grounding y una negativa segura.

## Evidence

- `WRK-TASK-007`: indexación local incremental verificada; recuentos y resultados excluidos.
- `WRK-TASK-008`: evaluación privada y negativa segura verificadas; evidencia local ignorada.
- Pruebas, lint, `validate` y `orphans` fueron superados en la ejecución local.

## Consolidation

La abstracción de fuente local, las reglas de privacidad y el contrato de evidencia existentes fueron suficientes; no se requiere un ADR ni una RULE nueva. El hallazgo sobre documentos equivalentes se conserva como criterio para evolucionar la evaluación hacia fuentes alternativas aceptables.
