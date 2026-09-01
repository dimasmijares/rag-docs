---
id: WRK-TASK-011
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 1.0.0
created: 2026-08-30
updated: 2026-08-31
owner: rag-docs-team
parent: WRK-PLAN-003
activates: [ARCH-001, DOC-RAG-001, RULE-001]
dependencies:
  - id: WRK-TASK-010
    relation: depends-on
tags: [llm, provider, ollama, remote, benchmark, privacy]
---

# WRK-TASK-011 — Portabilidad y benchmark de generadores

## Objective

Extender el contrato `Generator` existente para probar generadores intercambiables en el portátil y en el PC personal sin cambiar retrieval, índice ni API.

## File Scope

Incluye contrato `Generator`, configuración, adaptadores, health checks, benchmark y documentación de red. Excluye enviar corpus corporativo al PC personal sin autorización.

## Acceptance Criteria

- [x] Endpoint, modelo, timeout y opciones se configuran sin cambios de código.
- [x] El adaptador declara capacidades como salida estructurada, visión y streaming.
- [x] El mismo gold set compara calidad, idioma, cobertura, latencia p50/p95 y errores.
- [x] La caída del generador remoto produce un error controlado o fallback explícito, nunca silencioso.
- [x] El benchmark remoto usa corpus sintético por defecto y registra hardware/modelo/cuantización.
- [x] La exposición de Ollama se limita a la IP/subred necesaria o se protege mediante gateway.

## Decision Record

Crear ADR tras el benchmark si se cambia el modelo baseline o la topología de ejecución.

## Evidence

- Contexto activado y grafo validado el 2026-08-31.
- `GeneratorCapabilities` y `GeneratorHealth` implementados. URL, modelo, timeout,
  temperatura y seed se configuran mediante `RAG_DOCS_*`.
- El fallo del generador conserva un `503` explícito y está cubierto por una prueba de API.
- Benchmark aislado sobre corpus sintético, sin acceso a fuentes privadas, ejecutado en el host
  local y en un endpoint privado autorizado.
- La prueba confirmó que el generador puede cambiar de host sin reindexar y que la latencia se
  mide separadamente; IP, hardware detallado e informes permanecen locales.
- Los scripts genéricos permiten limitar el firewall a la IPv4 del cliente; la configuración
  efectiva no se versiona ni se presenta como verificada remotamente.
- Ruff correcto y 29 pruebas superadas el 2026-08-31.
