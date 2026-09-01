---
id: ADR-001
type: adr
layer: adr
scope: persistent
status: accepted
confidence: medium
version: 1.0.0
created: 2026-08-25
updated: 2026-08-25
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: implements
tags: [architecture-decision, python, qdrant, ollama]
---

# ADR-001 — Stack local para la PoC RAG

## Context

La PoC debe ser comprensible, funcionar en CPU con 16 GB de RAM, conservar privacidad y poder evolucionar a servidor o cloud.

## Decision

Usar Python 3.11 y FastAPI, Qdrant en Compose, `intfloat/multilingual-e5-small` para embeddings y Ollama con `qwen2.5:3b` como generador configurable. La web será estática y servida por la API.

## Rationale

Los parsers Python cubren los formatos solicitados, Qdrant introduce un vector database real sin exigir infraestructura corporativa y los modelos locales evitan salida de contenido.

## Consequences

### Positive

- Componentes reemplazables y ejecución local reproducible.
- API reutilizable por futuros clientes.

### Negative

- La generación será lenta en CPU.
- Docker Desktop y Ollama son prerrequisitos externos.

## Alternatives Considered

- Índice embebido: menor operación, menor continuidad hacia servidor.
- API de modelos: mejor latencia potencial, incompatible con privacidad local por defecto.
- Todo en contenedores: reproducible, menos cómodo para iteración inicial en Windows.
