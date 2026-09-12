---
id: WRK-PLAN-012
type: spec
layer: work-plan
scope: ephemeral
status: archived
confidence: high
version: 1.0.0
created: 2026-09-04
updated: 2026-09-12
owner: rag-docs-team
parent: WRK-SPEC-012
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-001, DOC-RAG-002, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v0.3.0, fingerprint, contracts, retrieval, quality]
---

# WRK-PLAN-012 — Invariantes de índice y calidad v0.3.0

## Task Decomposition

`092` es independiente y puede ejecutarse desde el primer momento. `083` fija los contratos y
desbloquea el resto: `083 → 036` y `083 → 090` son ramas paralelas; `036 → 082` y `036 → 086`
vuelven a abrirse en paralelo; `037` requiere `036` y `090`, y `038` sigue a `037`. `091` consolida
la release sobre `082`, `086`, `038` y `092`.

`093` es trabajo descubierto durante `086` (ver su Evidence): expone el `IndexFingerprint` vigente
en la API para que `rag-docs-eval` pueda verificarlo igual que `benchmark.py`. Depende sólo de
`086` y no bloquea el cierre de `091`; se puede ejecutar en paralelo o después de la release
v0.3.0.

## Critical Ordering

- El fingerprint (`036`) precede a cualquier cambio de payload, porque un cambio de payload sin
  fingerprint aplicado corrompe la colección en silencio.
- Los contratos (`083`) preceden a la división de `QueryService` (`090`) y al modelo de tenant
  (`082`), que se escriben contra los puertos y no al revés.
- La calidad medida (`037`, `038`) precede a la decisión de industrializar de `WRK-SPEC-006`.

## Gate

Ningún invariante declarado en `RULE-003` o `RULE-004` queda sin enforcement verificable; ninguna
técnica de retrieval se adopta sin mejora medida sobre un baseline comparable.

## Estado final

| Orden | Tarea | Estado | Dependencias | Entrega |
|---:|---|---|---|---|
| 1 | WRK-TASK-092 | archived | — | Identificadores fuera del repositorio |
| 2 | WRK-TASK-083 | archived | 092 | Contratos de puertos internos |
| 3 | WRK-TASK-036 | archived | 083 | Fingerprint del índice y migración |
| 4 | WRK-TASK-090 | archived | 083 | `QueryService` dividido en piezas puras |
| 5 | WRK-TASK-082 | archived | 036 | Modelo de tenant, ACL y ámbito |
| 6 | WRK-TASK-086 | archived | 036 | Manifiesto de corpus/gold sets/fingerprint |
| 7 | WRK-TASK-037 | archived | 036, 090 | Retrieval léxico e híbrido medido |
| 8 | WRK-TASK-038 | archived | 037 | Reranking medido y adoptado como capacidad |
| 9 | WRK-TASK-091 | completed | 082, 086, 038, 092 | Consolidación y cierre de `v0.3.0` |

`093` (fingerprint expuesto en la API, ver el párrafo anterior) queda fuera de esta tabla: es
trabajo descubierto que depende sólo de `086` y explícitamente no bloquea el cierre de `091`.

## Evidence

Las ocho tareas de esta release están mergeadas en `main` y archivadas conservando Evidence
completa (ver cada `WRK-TASK-0NN` para el detalle técnico). `WRK-TASK-091` las consolida:

- Migración de colección completa ejecutada y revertida en vivo contra el corpus sintético
  (`scripts/migration_drill.py`), incluyendo la comprobación de que una vinculación de fingerprint
  desactualizada rechaza la consulta (`RULE-004`) en lugar de servir el resultado equivocado.
- Informe de calidad que compara `dense`, `hybrid` y reranking sobre el mismo `index_fingerprint`
  declarado comparable (`evaluation/benchmarks/wrk-task-091/{dev,validation}-quality-report.json`),
  con la decisión de adopción de cada técnica registrada (`WRK-TASK-037` Evidence, `ADR-RAG-012`).
- README y `DOC-RAG-001` documentan fingerprint, ámbito obligatorio y política de comparabilidad.
- `WRK-SPEC-012` queda archivada con este plan; `scripts/verify.ps1` cierra en verde sin
  infraestructura adicional a la de `v0.2.0`.
