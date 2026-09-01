---
id: ARCH-001
type: spec
layer: architecture
scope: persistent
status: active
confidence: medium
version: 1.2.0
created: 2026-08-25
updated: 2026-08-31
owner: rag-docs-team
dependencies: []
tags: [rag, architecture, local-first]
---

# ARCH-001 — Arquitectura de la PoC RAG

## Intent

Definir límites reemplazables para fuentes, extracción, preparación, almacenamiento vectorial, modelos, API y presentación.

## Definition

### Decision

La aplicación será un monolito modular Python 3.11 con FastAPI. `DocumentSource`, extractores,
embeddings, vector store y generador se consumen mediante contratos internos. Qdrant se
ejecuta en Docker Compose; Ollama puede ejecutarse en el portátil o en un endpoint autorizado
de la red. El endpoint procede de configuración y el modelo puede elegirse entre los nombres
que ese endpoint anuncia. La aplicación se ejecuta nativamente durante el
desarrollo y la web estática es un cliente de la API.

### Rationale

El diseño permite recorrer el flujo completo en un portátil y sustituir cada borde sin adoptar microservicios prematuramente.

### Consequences

- La API no conoce parsers concretos ni detalles de Qdrant.
- El índice almacena texto y metadatos localizables junto al vector.
- La disponibilidad de Qdrant y Ollama se comprueba en tiempo de ejecución.

## Acceptance Criteria

- [x] Cada borde externo tiene contrato y prueba aislada.
- [x] La PoC funciona con una fuente local sin acoplar el pipeline a rutas concretas.
- [x] El flujo completo puede ejecutarse desde la API y la web.

## Evidence

- 29 pruebas automatizadas superadas el 2026-08-31.
- Adaptadores de Qdrant, fuentes, modelos y API verificados de forma aislada.
- Generador remoto validado con el mismo gold set sintético que el generador local.
- Descubrimiento y cambio dinámico de modelo Ollama verificados en `WRK-TASK-022`.

## Traceability

- Implementado por `WRK-PLAN-001`.
- Decisiones registradas en `ADR-001`.
