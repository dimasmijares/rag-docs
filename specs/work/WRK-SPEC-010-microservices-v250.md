---
id: WRK-SPEC-010
type: spec
layer: work-spec
scope: ephemeral
status: draft
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-04
owner: rag-docs-team
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, FEAT-RAG-003, FEAT-RAG-004, DOC-RAG-002, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-SPEC-009
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ADR-003
    relation: depends-on
  - id: ADR-004
    relation: depends-on
  - id: ADR-006
    relation: depends-on
  - id: ADR-RAG-007
    relation: depends-on
  - id: ADR-RAG-010
    relation: depends-on
tags: [release, v2.5.0, microservices, contracts, conditional-extraction]
---

# WRK-SPEC-010 — Extracción condicional por frontera v2.5.0

## Proposed Change

Extraer con contratos `/v1`, imágenes, health checks, seguridad servicio a servicio y trazas
distribuidas **sólo las fronteras de `ARCH-002` con motor demostrable o con evidencia de escalado
divergente**, en vez de las ocho por defecto. El resto permanece como contrato en proceso
(`ADR-RAG-010`), reversible en cualquier momento con evidencia posterior.

## Scope Decision

Aplicada `ADR-RAG-007`, decisión D. Alcance por defecto, fijado en este work spec:

- **Extracción aprobada sin más evidencia** (motor ya demostrable hoy): `embedding-service`
  (`WRK-TASK-058`), `model-gateway` (`WRK-TASK-059`) e `index-worker` (`WRK-TASK-065`).
- **Extracción condicional**, supeditada al informe de `WRK-TASK-088` sobre la evidencia de carga y
  SLO de `WRK-TASK-055`: `authz-service` (`060`, se promueve sólo si la política deja de ser
  evaluable en proceso), `retrieval-service` (`061`), `context-grounding-service` (`062`),
  `query-api` (`063`) e `index-api` (`064`). Por defecto estas cinco fronteras permanecen en un
  único desplegable junto con `query-api`, salvo que `088` documente escalado, aislamiento de fallo
  o despliegue divergente.

`WRK-TASK-088` sigue siendo el gate formal: puede confirmar el alcance mínimo anterior, ampliarlo con
evidencia, pero no reducirlo por debajo del mínimo aprobado.

## Acceptance Criteria

- [ ] Cada servicio efectivamente extraído tiene contrato, imagen, liveness, readiness y pruebas.
- [ ] Sólo los servicios autorizadores reciben el token de usuario cuando es necesario.
- [ ] El resto usa OAuth2 client credentials y valida tokens.
- [ ] Fallos parciales producen errores explícitos y retries acotados.
- [ ] Las fronteras no extraídas conservan su contrato en proceso (`ADR-RAG-010`) y quedan
      documentadas como reversibles, no como trabajo cancelado.

## Evidence

Pendiente de `WRK-PLAN-010`.
