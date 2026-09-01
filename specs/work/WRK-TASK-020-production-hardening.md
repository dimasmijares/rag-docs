---
id: WRK-TASK-020
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-PLAN-011
activates: [ARCH-002, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-069
    relation: depends-on
  - id: WRK-TASK-070
    relation: depends-on
  - id: WRK-TASK-071
    relation: depends-on
  - id: WRK-TASK-072
    relation: depends-on
  - id: WRK-TASK-073
    relation: depends-on
  - id: WRK-TASK-074
    relation: depends-on
  - id: WRK-TASK-075
    relation: depends-on
tags: [cicd, ghcr, sbom, signing, kind]
---

# WRK-TASK-020 — CI/CD y cadena de suministro

## Objective

Construir, escanear, firmar y publicar imágenes y chart, y ejecutar lint y E2E en `kind`.

## Acceptance Criteria

- [ ] CI ejecuta pruebas, lint, KDD, evaluación y escaneo de dependencias/imágenes.
- [ ] Imágenes versionadas se publican en GHCR con SBOM y firma verificable.
- [ ] Helm lint y E2E en `kind` forman parte del gate.
- [ ] El pipeline no incluye datos, secretos ni derivados privados.

## Evidence

Pendiente.
