---
id: WRK-PLAN-003
type: spec
layer: work-plan
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
parent: WRK-SPEC-003
activates: [ARCH-001, DOM-RAG-001, FEAT-RAG-001, RULE-001]
dependencies: []
tags: [quality-plan, evaluation, generation, retrieval, vision]
---

# WRK-PLAN-003 — Plan de calidad RAG y modelos

## Architecture Approach

Separar retrieval, generación y verificación. El generador devolverá una estructura interna validable; la API seguirá ofreciendo una respuesta sencilla. La evaluación será la puerta de entrada para cualquier cambio de modelo, chunking o búsqueda.

## Task Decomposition

| Orden | Task | Entrega | Dependencias | Gate |
|---:|---|---|---|---|
| 1 | WRK-TASK-009 | Evaluación v2 y regresión reproducida | — | Baseline |
| 2 | WRK-TASK-010 | Contrato de idioma, cobertura, identificadores y citas | 009 | G1 |
| 3 | WRK-TASK-011 | Proveedor desacoplado y benchmark con PC remoto | 010 | G1/G4 |
| — | WRK-TASK-021 | Selector de endpoint autorizado | 011 | Operación |
| — | WRK-TASK-022 | Descubrimiento y selección de modelos instalados | 021 | Operación |

## Quality Gates

- No cambiar de modelo antes de medir el contrato corregido con Qwen 3B.
- No añadir reranker si hybrid/dense no demuestra mejora relevante en validación separada.
- No activar visión para páginas con texto extraíble suficiente.
- Ningún benchmark remoto con contenido corporativo sin autorización.
- Agentic retrieval queda fuera hasta superar G1–G3 y demostrar un caso que no resuelva el pipeline fijo.

## Risks

- Sobreajuste al gold set: separar casos de desarrollo y validación.
- Validación rígida: combinar reglas deterministas con métricas semánticas auditables.
- Duplicados DOCX/Markdown: relacionar equivalentes y conservar trazabilidad.
- Mayor latencia: medir p50/p95 y aplicar reintentos sólo ante fallos concretos.

## Evidence

- `WRK-TASK-009` completada: evaluación v2 separa retrieval, estado, hechos, idioma y
  citas, y mantiene desarrollo y validación en conjuntos distintos.
- `WRK-TASK-010` completada: contrato estructurado, validación determinista, reintento
  limitado y fallback extractivo auditable.
- Gate G1 superado en la regresión de desarrollo (1/1) y en validación reservada (5/5).
- `WRK-TASK-011` completada: proveedor configurable y benchmark local/remoto 4/4; el PC
  personal redujo la p50 de 26,70 s a 11,87 s sin mover índice ni documentos.
- `WRK-TASK-021` completada: selector web de perfiles preautorizados con comprobación y cambio
  en caliente, manteniendo local como perfil predeterminado.
- `WRK-TASK-022` completada: descubrimiento de `/api/tags`, selector de modelos y activación
  atómica restringida a nombres anunciados por el endpoint.
- Los antiguos pendientes `012–014` se refinaron y reubicaron en los planes de release 005–007.
