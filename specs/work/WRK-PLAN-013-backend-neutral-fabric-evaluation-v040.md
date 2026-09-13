---
id: WRK-PLAN-013
type: spec
layer: work-plan
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-SPEC-013
activates: [ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v0.4.0, fabric, vector-store, evaluation, power-bi]
---

# WRK-PLAN-013 — Backend neutral y plano de evaluación en Fabric v0.4.0

## Task Decomposition

`094` unifica los puertos y abre tres ramas paralelas: `095`, `096` y `098`. `097` es independiente
y precede a cualquier artefacto Fabric: `097 → 099`. `100` requiere `094`, `096` y `099`; `101`
requiere `095` y `100`. `102` reúne `093`, `098` y `101`; `103` sigue a `102` y `104` consolida.

`093` se adopta desde `WRK-PLAN-012` (trabajo descubierto durante `086`, sin cambios de contenido):
depende sólo de `086` y puede ejecutarse en paralelo desde el inicio.

## Critical Ordering

- Las costuras de store (`094`) preceden a cualquier segundo backend y al esquema PostgreSQL de
  `v1.0.0`.
- El gate público ampliado (`097`) precede al primer commit de notebooks, `.platform` o PBIP.
- La suite de contrato (`096`) precede a `FabricSqlVectorStore` (`100`): el backend nuevo se acepta
  por contrato, no por inspección.
- La revisión de embeddings fijada (`095`) precede al walking skeleton (`101`), que exige igualdad
  de digest entre el índice local y el publicado.

## Gate

La API local responde grounded sobre Fabric SQL con el mismo fingerprint que el índice local; la
paridad de recall entre backends está medida; `scripts/verify.ps1` sigue sin requerir Fabric.

## Estado final

| Orden | Tarea | Estado | PR | Entrega |
|---:|---|---|---|---|
| 1 | WRK-TASK-094 | archived | #32 | Costuras de store y factoría por backend |
| 2 | WRK-TASK-097 | archived | #31 | Gate público para artefactos Fabric |
| 3 | WRK-TASK-093 | archived | #33 | Fingerprint vigente expuesto en la API |
| 4 | WRK-TASK-095 | archived | #34 | Revisión de embeddings fijada |
| 5 | WRK-TASK-096 | archived | #35 | Suite de contrato de VectorStore |
| 6 | WRK-TASK-098 | archived | #36 | Comparabilidad por backend |
| 7 | WRK-TASK-099 | archived | #37 | Bootstrap del workspace Fabric |
| 8 | WRK-TASK-100 | archived | #38 | `FabricSqlVectorStore` |
| 9 | WRK-TASK-101 | archived | #39 | Walking skeleton local → Fabric SQL |
| 10 | WRK-TASK-102 | archived | #40 | Plano de evaluación en Delta |
| 11 | WRK-TASK-103 | archived | #41 | Informe Power BI de calidad |
| 12 | WRK-TASK-104 | completed | — | Consolidación de `v0.4.0` |

## Evidence

- **Gate del plan superado, con evidencia live del 2026-09-13:**
  - `scripts/verify-fabric.ps1 -WalkingSkeleton`: la API local responde con citas sobre Fabric SQL
    con el mismo fingerprint (`724f6786a9170f8b`) que el índice local (`WRK-TASK-101`).
  - Paridad de recall medida y exacta entre Qdrant y Fabric SQL (`WRK-TASK-102`,
    `evaluation/benchmarks/wrk-task-102/`).
  - `scripts/verify.ps1` en verde sin Fabric ni credenciales en cada PR.
- **Orden crítico respetado:**
  - `094` antes de `100`;
  - `097` (#31) antes del primer artefacto Fabric versionado (`099`, #37);
  - `096` (#35) antes de `100` (#38), que se aceptó por la suite de contrato (11/11 live);
  - `095` (#34) antes de `101` (#39).
- **Ejecución en serie:** sin tareas concurrentes, cada una en su rama `codex/wrk-task-NNN-*` con PR,
  CI verde y merge squash.
- **Decisiones del propietario durante el plan:**
  - despliegue Fabric con Fabric CLI desde el repositorio en lugar de Git integration;
  - un workspace `rag-docs` por entorno;
  - service principal con rol Contributor (`WRK-TASK-099`).
- **Trabajo derivado para `v1.1.0` (`WRK-PLAN-014`):** worker de inferencia (`WRK-TASK-110`) y
  monitorización de capacidad. `DOC-RAG-003` los declara pendientes.
