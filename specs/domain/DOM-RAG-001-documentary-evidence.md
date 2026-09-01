---
id: DOM-RAG-001
type: spec
layer: domain
scope: persistent
status: active
confidence: medium
version: 1.1.0
created: 2026-08-25
updated: 2026-08-31
owner: rag-docs-team
dependencies:
  - id: RULE-001
    relation: constrained-by
tags: [rag, grounding, citations, privacy]
---

# DOM-RAG-001 — Evidencia documental y trazabilidad

## Intent

Formalizar cuándo una respuesta puede considerarse respaldada y cómo localizar su evidencia original.

## Definition

- Una afirmación debe derivarse únicamente de fragmentos recuperados.
- Una respuesta sólo puede considerarse `grounded` cuando cubre todas las partes
  materiales de la pregunta y cada afirmación factual tiene al menos una cita válida.
- Los identificadores técnicos se conservan literalmente y deben aparecer en la
  evidencia citada por la afirmación que los utiliza.
- La respuesta usa el idioma de la pregunta; los mecanismos de fallback se declaran
  explícitamente y nunca introducen contenido ajeno a los fragmentos recuperados.
- Toda cita conserva fuente, nombre, URI/ruta, ruta relativa y localizador disponible.
- Si la evidencia no basta, la respuesta declara `insufficient_evidence` y no completa huecos con conocimiento general.
- Los documentos, embeddings, consultas y contextos permanecen en el equipo durante la PoC.

## Acceptance Criteria

- [x] Las respuestas grounded incluyen al menos una cita válida por afirmación.
- [x] Una consulta ajena al corpus produce evidencia insuficiente.
- [x] PDF, PPTX y XLSX conservan página, diapositiva y hoja/rango respectivamente.
- [x] La evaluación separa cobertura, idioma, citas, estado y recuperación.

## Evidence

- Pruebas de respuesta grounded, negativa segura, idioma, identificadores, citas por
  afirmación y preservación de localizadores.
- Gold set didáctico y gold sets operativos v2; validación reservada 5/5 registrada en
  `logs/evaluation-v2-answer-contract-validation-final.json`.

## Traceability

- Aplicado en el servicio de consulta y sus tests.
