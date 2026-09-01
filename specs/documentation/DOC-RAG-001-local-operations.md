---
id: DOC-RAG-001
type: spec
layer: documentation
scope: persistent
status: active
confidence: medium
version: 1.3.0
created: 2026-08-25
updated: 2026-08-31
owner: rag-docs-team
dependencies:
  - id: ARCH-001
    relation: implements
tags: [operations, setup, evaluation]
---

# DOC-RAG-001 — Operación local

## Intent

Definir la documentación mínima para instalar, configurar, ejecutar, evaluar y diagnosticar la PoC.

## Definition

La guía debe cubrir Python 3.11, KDD, Docker/Qdrant, Ollama, `sources.yaml`, API/web, gold set, privacidad y solución de problemas.

## Acceptance Criteria

- [x] Un desarrollador puede ejecutar validaciones sin conocimiento previo del repositorio.
- [x] Las dependencias externas y sus comprobaciones de salud están documentadas.
- [x] Se diferencia el corpus didáctico del corporativo ignorado por Git.

## Evidence

- README, configuración de ejemplo y Compose creados en `WRK-TASK-006`.
- `docker compose config --quiet` y smoke test HTTP superados.
- Topología Ollama remota, variables, privacidad y paquete transferible documentados en
  `README.md` y `transfer/ollama-remote/`; benchmark reproducible en `WRK-TASK-011`.
- Perfiles local/remoto y comportamiento temporal del selector web documentados en README y
  `.env.example`; flujo validado en `WRK-TASK-021`.
- Descubrimiento de modelos instalados y activación segura documentados y verificados en
  `WRK-TASK-022`.

## Traceability

- Documentación raíz y ejemplos de configuración.
