---
id: WRK-TASK-046
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-008
activates: [DOM-RAG-002, FEAT-RAG-003, RULE-003]
dependencies:
  - id: WRK-TASK-043
    relation: depends-on
  - id: WRK-TASK-045
    relation: depends-on
tags: [authorization, fail-closed, retrieval, qdrant]
---

# WRK-TASK-046 — Autorización previa al retrieval

## Objective

Sustituir el ámbito de un solo tenant de `WRK-TASK-082` por la resolución real de política desde el
principal validado, y retirar la excepción transitoria de `RULE-003`.

## Acceptance Criteria

- [ ] Sin principal o política válida no se consulta el índice, ni en producción ni en desarrollo.
- [ ] La indisponibilidad del almacén de políticas es denegación, nunca continuación con ámbito
      vacío ni con ámbito por defecto.
- [ ] Tenant, sujetos y clasificación forman parte del filtro enviado al vector store como
      prefiltro; no existe ninguna ruta de post-filtrado.
- [ ] Errores, conteos y diagnósticos no revelan existencia documental: una denegación es
      indistinguible de una ausencia de evidencia.
- [ ] Ningún caller puede omitir el filtro autorizado, garantizado por la firma obligatoria de
      ámbito introducida en `WRK-TASK-082`.
- [ ] La excepción transitoria de `RULE-003` queda retirada y la regla actualizada.

## Evidence

Pendiente.
