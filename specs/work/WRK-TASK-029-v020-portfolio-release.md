---
id: WRK-TASK-029
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
activates: [ARCH-002, DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-027
    relation: depends-on
  - id: WRK-TASK-028
    relation: depends-on
tags: [release, v0.2.0, readme, demo]
---

# WRK-TASK-029 — Release de portfolio v0.2.0

## Objective

Publicar README, diagramas y demo reproducible sobre corpus sintético y consolidar `v0.2.0`.

## File Scope

Incluye README, documentación/diagramas públicos, metadata de versión, specs de release y
automatización de demo. Excluye nuevas capacidades runtime o datos no sintéticos.

## Acceptance Criteria

- [ ] README explica propósito, arquitectura, privacidad, quickstart, evaluación y roadmap.
- [ ] La demo funciona desde un clon limpio con el flujo documentado.
- [ ] CI está verde y el diff de release supera el gate público.
- [ ] Paquete y API declaran `0.2.0` y la evidencia pública referencia artefactos sintéticos.
- [ ] `WRK-SPEC/PLAN-005` se consolidan y sus tareas se archivan antes de etiquetar.
- [ ] El tag `v0.2.0` y la GitHub Release sólo se crean desde `main` fusionada y verificada.

## Evidence

Pendiente.
