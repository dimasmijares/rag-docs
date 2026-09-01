---
id: WRK-PLAN-005
type: spec
layer: work-plan
scope: ephemeral
status: active
confidence: low
version: 0.2.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-005
activates: [ARCH-001, ARCH-002, DOM-RAG-001, FEAT-RAG-001, DOC-RAG-001, DOC-RAG-002, RULE-001, RULE-002]
dependencies: []
tags: [release-plan, v0.2.0, portfolio, public]
---

# WRK-PLAN-005 — Plan de portfolio público v0.2.0

## Architecture Approach

Cerrar primero gobierno, privacidad y reproducibilidad; después medir la calidad de retrieval y
modelos antes de publicar la baseline.

## Task Decomposition

| Orden | Tarea | Estado | Dependencias | Entrega |
|---:|---|---|---|---|
| 1 | WRK-TASK-023 | completed | 022 | Roadmap KDD completo |
| 2 | WRK-TASK-024 | completed | 023 | Saneamiento público |
| 3 | WRK-TASK-025 | completed | 024 | Licencia, GitHub y rama `main` |
| 4 | WRK-TASK-079 | completed | 025 | Lifecycle y protocolo KDD |
| 5 | WRK-TASK-028 | completed | 025, 079 | CI y gates de seguridad |
| 6 | WRK-TASK-026 | draft | 024, 079 | Corpus y gold sets sintéticos |
| 7 | WRK-TASK-012 | draft | 009, 023, 026, 079 | Métricas de retrieval |
| 8 | WRK-TASK-027 | draft | 012, 026 | Benchmark de modelos y recursos |
| 9 | WRK-TASK-029 | draft | 027, 028 | Documentación y release `v0.2.0` |

## Evidence

- `WRK-TASK-023` consolidó el roadmap corporativo y validó el DAG completo.
- `WRK-TASK-024` superó el gate público sin versionar documentos o derivados privados.
- `WRK-TASK-025` publicó el repositorio Apache-2.0, protegió `main` y fusionó la PR inicial.
- `WRK-TASK-079` normalizó lifecycle y Definition of Ready; `028` y `026` quedan desbloqueadas.
