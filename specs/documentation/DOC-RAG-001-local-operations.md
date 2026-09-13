---
id: DOC-RAG-001
type: spec
layer: documentation
scope: persistent
status: active
confidence: medium
version: 1.5.0
created: 2026-08-25
updated: 2026-09-13
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

La guía debe cubrir Python 3.11, KDD, Docker/Qdrant, Ollama, `sources.yaml`, API/web, gold set,
privacidad, solución de problemas, y el modelo de invariantes de índice de `v0.3.0`: fingerprint
del índice, ámbito de autorización obligatorio y política de comparabilidad entre evaluaciones.
Desde `v0.4.0` también cubre la selección de backend vectorial tras puertos, la revisión de
embeddings fijada y su nota de migración, y la existencia del perfil opcional Fabric
(`DOC-RAG-003`), dejando claro que la operación local no lo requiere.

## Acceptance Criteria

- [x] Un desarrollador puede ejecutar validaciones sin conocimiento previo del repositorio.
- [x] Las dependencias externas y sus comprobaciones de salud están documentadas.
- [x] Se diferencia el corpus didáctico del corporativo ignorado por Git.
- [x] El fingerprint del índice, el ámbito obligatorio y la política de comparabilidad están
      documentados con referencia a los mecanismos que los implementan.
- [x] El perfil Fabric se documenta como opcional: el quickstart y `scripts/verify.ps1` no lo
      necesitan.

## Evidence

- README, configuración de ejemplo y Compose creados en `WRK-TASK-006`.
- `docker compose config --quiet` y smoke test HTTP superados.
- Topología Ollama remota, variables, privacidad y paquete transferible documentados en
  `README.md` y `transfer/ollama-remote/`; benchmark reproducible en `WRK-TASK-011`.
- Perfiles local/remoto y comportamiento temporal del selector web documentados en README y
  `.env.example`; flujo validado en `WRK-TASK-021`.
- Descubrimiento de modelos instalados y activación segura documentados y verificados en
  `WRK-TASK-022`.
- **`WRK-TASK-091`:** nueva sección "Índice: fingerprint, ámbito y comparabilidad" en `README.md`
  documenta `IndexFingerprint`/alias/migración (`RULE-004`), `Scope` obligatorio sin valor por
  defecto en `VectorStorePort` (`RULE-003`, `ADR-RAG-009`) y la política de comparabilidad de
  `corpus_version`/`index_fingerprint` entre evaluaciones con el criterio de adopción de retrieval
  (`ADR-RAG-011`, `RFC-001` gate G2), enlazando los resultados medidos de `WRK-TASK-037`/`038` y
  `ADR-RAG-012`.
- **`WRK-TASK-104`:** `README.md` documenta:
  - release `v0.4.0`;
  - campos aditivos de `GET /api/sources` (`index_fingerprint`, `vector_backend`,
    `vector_search_mode`);
  - clave de comparabilidad con backend y modo (`schema_version` 1.1) y verificación de
    fingerprint en `rag-docs-eval`;
  - backends vectoriales tras puertos con suite de contrato;
  - nota de migración de la revisión de embeddings fijada (`WRK-TASK-095`);
  - sección "Perfil opcional Microsoft Fabric" con sus cuatro puntos de entrada y la advertencia
    de que el quickstart y `scripts/verify.ps1` no lo necesitan.

## Traceability

- Documentación raíz y ejemplos de configuración.
