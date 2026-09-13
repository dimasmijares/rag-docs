---
id: WRK-PLAN-014
type: spec
layer: work-plan
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-SPEC-014
activates: [ARCH-002, DOM-RAG-001, DOM-RAG-002, FEAT-RAG-002, DOC-RAG-003, RULE-001, RULE-002, RULE-003, RULE-004]
dependencies: []
tags: [release-plan, v1.1.0, fabric, indexing, spark, inference-queue]
---

# WRK-PLAN-014 — Plano de indexación en Fabric v1.1.0

## Task Decomposition

Dos líneas convergen. Indexación: `105` (tras `101`) y `106` (tras `030` y `100`) abren `107`,
seguido de `108` y `109` (que también requiere `015`). Inferencia: `110` requiere `100` y abre
`111`, `112` y `113`, que además dependen de la evaluación en Delta (`102`); `111` también de `107`.
`114` reúne `103`, `108` y `112`; `115` consolida.

## Critical Ordering

- El ledger en Fabric SQL (`106`) precede a cualquier escritura de Spark (`107`): sin ledger, Fabric
  sería una segunda fuente de verdad.
- La idempotencia ante eventos duplicados (`108`) precede a exponer el pipeline como job (`109`).
- La cola de inferencia (`110`) precede a cualquier uso del LLM desde Fabric; ningún uso fuera de
  los tres autorizados por `ADR-RAG-014`.
- Los candidatos de gold set (`113`) nunca entran en un gold set sin revisión humana.

## Gate

Un documento sintético nuevo en OneLake queda consultable desde la API local con el mismo
fingerprint, sin duplicados ante eventos repetidos, y las cargas batch de LLM funcionan sin puertos
entrantes.

## Tareas

| Orden | Tarea | Estado | Dependencias | Entrega |
|---:|---|---|---|---|
| 1 | WRK-TASK-105 | draft | 101 | Fuente OneLake |
| 2 | WRK-TASK-106 | draft | 030, 100 | Ledger en Fabric SQL |
| 3 | WRK-TASK-110 | draft | 100 | Cola de inferencia pull y worker local |
| 4 | WRK-TASK-107 | draft | 105, 106 | Notebook de indexación Spark |
| 5 | WRK-TASK-108 | draft | 107 | Orquestación por eventos y calendario |
| 6 | WRK-TASK-109 | draft | 015, 108 | Gateway `JobResource` ↔ job Fabric |
| 7 | WRK-TASK-111 | draft | 102, 107, 110 | Experimento de enriquecimiento batch |
| 8 | WRK-TASK-112 | draft | 102, 110 | LLM-as-judge en evaluación |
| 9 | WRK-TASK-113 | draft | 102, 110 | Candidatos de gold set |
| 10 | WRK-TASK-114 | draft | 103, 108, 112 | Páginas operativas Power BI |
| 11 | WRK-TASK-115 | draft | todas | Consolidación de `v1.1.0` |

## Evidence

Pendiente.
