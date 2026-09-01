---
id: RULE-001
type: rule
layer: rule
scope: persistent
status: active
confidence: medium
version: 1.1.0
created: 2026-08-25
updated: 2026-08-31
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: constrained-by
tags: [grounding, privacy, mandatory]
---

# RULE-001 — Respuestas fundamentadas y procesamiento local

## Rule Definition

La aplicación no afirmará hechos sin evidencia recuperada. Cada afirmación de una respuesta
`grounded` contendrá citas válidas y cualquier identificador técnico deberá aparecer
literalmente en su evidencia. `grounded` exige cubrir todas las partes materiales y usar el
idioma de la pregunta; en caso contrario se corrige una vez o se devuelve
`insufficient_evidence`. Un fallback deberá ser explícito, auditable y limitarse a texto
recuperado. Documentos, consultas, embeddings y contexto sólo se enviarán a procesos locales
o endpoints de red autorizados y configurados explícitamente.

## Enforcement

- Validación del contrato de respuesta en el servicio y la API.
- Registro del modo de generación (`llm`, `extractive_fallback` o `none`).
- Pruebas positivas y negativas en el gold set.
- Revisión de configuración para endpoints limitados a localhost o autorizados expresamente.

## Exceptions

Una integración externa futura requerirá RFC, ADR y configuración explícita de privacidad.
