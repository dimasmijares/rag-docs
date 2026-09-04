---
id: WRK-TASK-087
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-009
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-004, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-092
    relation: depends-on
  - id: WRK-TASK-050
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [public-safety, connectors, logging, telemetry, fixtures]
---

# WRK-TASK-087 — Endurecimiento de publicación para conectores

## Objective

Sustituir el crecimiento indefinido de la denylist por controles estructurales sobre el contenido en
tránsito, que es donde vive el riesgo real cuando entran conectores corporativos.

## File Scope

Incluye la configuración de logging estructurado, los atributos de telemetría, la política de
fixtures de conector, el formato de errores de conector y sus tests. Excluye la implementación de
conectores concretos y el gate de rutas de Git, que ya cubre `WRK-TASK-092`.

## Acceptance Criteria

- [ ] El logging estructurado declara una allowlist de campos y un test falla si un logger emite un
      campo no declarado.
- [ ] Las respuestas de error de conector no incluyen contenido documental ni identificadores de
      origen no saneados.
- [ ] Los atributos de span no incluyen contenido por defecto, verificado por test, conforme al
      invariante de `ARCH-002`.
- [ ] Los fixtures de conector se generan exclusivamente desde el corpus sintético; no se admiten
      grabaciones de peticiones o respuestas de sistemas corporativos reales.
- [ ] Los criterios anteriores quedan incorporados como requisito de aceptación de cualquier
      conector futuro del SDK.

## Evidence

Pendiente.
