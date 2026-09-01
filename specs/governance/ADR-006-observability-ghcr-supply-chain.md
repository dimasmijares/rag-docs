---
id: ADR-006
type: adr
layer: adr
scope: persistent
status: accepted
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: DOC-RAG-002
    relation: implements
  - id: RULE-002
    relation: constrained-by
tags: [architecture-decision, opentelemetry, ghcr, supply-chain]
---

# ADR-006 — OpenTelemetry y cadena de suministro GHCR

## Context

La solución distribuida requiere correlación y artefactos públicos verificables sin obligar al
portátil de 16 GB a ejecutar toda la observabilidad continuamente.

## Decision

Instrumentar con OpenTelemetry y ofrecer Collector, Prometheus, Grafana, Loki y Tempo como perfil
opcional. Publicar imágenes versionadas en GHCR con SBOM, escaneo y firma desde CI.

## Consequences

La telemetría será portable y apagable. Se deberán aplicar redacción por defecto, retención y
controles para impedir que preguntas, chunks o respuestas aparezcan en señales operativas.
