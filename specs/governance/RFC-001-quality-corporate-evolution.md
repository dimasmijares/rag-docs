---
id: RFC-001
type: rfc
layer: rfc
status: accepted
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: extends
  - id: DOM-RAG-001
    relation: extends
  - id: FEAT-RAG-001
    relation: extends
  - id: RULE-001
    relation: constrained-by
tags: [roadmap, answer-quality, model-portability, multimodal, corporate]
---

# RFC-001 — Evolución de calidad RAG y preparación corporativa

## Problem Statement

La PoC recuperaba evidencia pertinente, pero una consulta compuesta mostró que el generador
podía omitir identificadores técnicos presentes en el contexto, simplificar partes de la
respuesta y mezclar idiomas. La evaluación inicial podía aprobar esa salida porque comprobaba
una única subcadena y una cita, no la cobertura completa de la pregunta. Este riesgo quedó
mitigado por `WRK-TASK-009` y `WRK-TASK-010`; se conserva aquí como motivación histórica.

La evolución prevista incluye además documentos visuales, modelos remotos, conectores y operación multiusuario. Estas capacidades necesitan un orden basado en evidencia para evitar añadir infraestructura antes de corregir los contratos de calidad.

## Proposed Change

Separar la evolución en dos work streams:

1. **Calidad RAG y portabilidad de modelos**: evaluación por hechos atómicos, contrato de idioma y completitud, generación estructurada, diagnóstico del retrieval, comparación de modelos, deduplicación, recuperación avanzada, contenido visual y rendimiento.
2. **Preparación corporativa**: trabajos en segundo plano, contenedores, identidad y permisos, conectores, observabilidad, backups, CI/CD y escalado.

La propuesta se acepta como dirección. `RFC-002` concreta sus releases, gates y arquitectura
distribuida; este RFC conserva las reglas de calidad que motivaron la evolución.

## Mandatory Answer Requirements

- La respuesta estará en el idioma de la pregunta salvo petición explícita distinta.
- Cada parte material de una pregunta compuesta se responderá o se marcará como no respaldada.
- Los identificadores técnicos se copiarán literalmente desde la evidencia.
- Una cita estará asociada a la afirmación que respalda; añadir una lista genérica de fuentes no demuestra grounding.
- Una salida que incumpla idioma, esquema, cobertura o citas no se considerará `grounded` sin validación o regeneración.

## Decision Gates

| Gate | Evidencia requerida | Decisión |
|---|---|---|
| G1 Generación | Gold set con hechos requeridos, idioma y citas | Mantener Qwen 3B si cumple; comparar modelos si no |
| G2 Retrieval | Recall@k/MRR y análisis de contexto | Añadir híbrido/reranker sólo ante mejora medible |
| G3 Visual | Casos con capturas, escaneos y diagramas | OCR primero; visión sólo donde aporte comprensión |
| G4 Remoto | Autorización de datos y red protegida | Corpus sintético por defecto; datos reales sólo autorizados |
| G5 Corporativo | SLO, usuarios, permisos y repositorios definidos | Elegir topología y servicios gestionados/self-hosted |
| G6 Agentic | Fallos persistentes que exijan planificación o herramientas | Adoptar sólo si supera al pipeline fijo en calidad/coste |

## Impact Assessment

| Area | Impact |
|---|---|
| Evaluación | Nuevo esquema con múltiples hechos obligatorios, idioma, fuentes alternativas y métricas separadas |
| Generación | Salida estructurada interna, validación determinista y posible reintento |
| Retrieval | Diagnóstico primero; deduplicación, híbrido y reranking quedan condicionados por métricas |
| Modelos | Contrato de proveedor y benchmark local/remoto sin acoplar API, índice ni embeddings |
| Ingestión | OCR y unidades visuales con localizadores y provenance |
| Privacidad | El contexto no saldrá a un equipo personal con documentación corporativa sin autorización explícita |
| Operación | Evolución posterior a workers, identidad, ACL, observabilidad y backups |

## Alternatives Considered

1. **Cambiar inmediatamente a un LLM mayor**: puede mejorar la salida, pero no garantiza idioma, cobertura ni evaluación correcta; se conserva como experimento tras fijar el contrato.
2. **Añadir hybrid retrieval de inmediato**: no corrige el fallo observado porque la evidencia exacta ya se recuperó; queda sujeto a resultados del gold set.
3. **Usar un segundo LLM como juez desde el inicio**: añade latencia y variabilidad. Se priorizan validaciones deterministas; el juez se evaluará sólo para criterios semánticos no verificables.
4. **Introducir agentic retrieval ahora**: complicaría diagnóstico, costes y reproducibilidad. Se aplaza hasta medir un pipeline con generación validada, hybrid retrieval y reranking.

## Open Questions

- Hardware, RAM/VRAM y sistema operativo del PC personal.
- Autorización para procesar fragmentos corporativos fuera del portátil.
- SLO objetivo de latencia y concurrencia para una futura versión corporativa.
- Proveedor de identidad y modelo de permisos documental definitivo.
