---
id: WRK-SPEC-001
type: spec
layer: work-spec
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-30
owner: rag-docs-team
activates: [ARCH-001, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, RULE-001]
dependencies:
  - id: ARCH-001
    relation: constrained-by
  - id: DOM-RAG-001
    relation: constrained-by
  - id: FEAT-RAG-001
    relation: implements
tags: [rag, poc, delivery]
---

# WRK-SPEC-001 — PoC RAG documental

## Problem Statement

La documentación técnica distribuida en varios formatos es difícil de localizar y consultar con trazabilidad.

## Proposed Change

Construir un flujo completo desde una carpeta configurable hasta una respuesta local citada, con API, web y evaluación conocida.

## Activated Knowledge

- `ARCH-001`: límites técnicos.
- `DOM-RAG-001` y `RULE-001`: evidencia, citas y privacidad.
- `FEAT-RAG-001`: comportamiento observable.
- `DOC-RAG-001`: operación reproducible.

## Constraints

CPU, 16 GB de RAM, almacenamiento limitado, sin conectores remotos ni técnicas avanzadas en esta entrega.

## Acceptance Criteria

- [x] Se indexan recursivamente los seis formatos indicados.
- [x] Las consultas conocidas recuperan el documento esperado y citan el localizador.
- [x] Las consultas sin respuesta no inventan información.
- [x] API, web, KDD y puesta en marcha están documentados y probados.

## Open Questions

- Ninguna para el alcance de la PoC.

## Evidence

- 17 pruebas automatizadas, lint, Compose y grafo KDD superados.
- Seis formatos presentes en el corpus didáctico.
- Gold set didáctico ejecutado 4/4 y gold set operativo ejecutado 6/6.
- Corpus operativo: 15 documentos, 248 chunks, sin errores de indexación y negativa segura verificada.

## Consolidation

Las decisiones se consolidaron en `ARCH-001`, `ADR-001` y `RULE-001`. La evidencia elevó los artefactos implementados a confianza `medium`; no se proponen nuevos specs hasta analizar el gold set real.
