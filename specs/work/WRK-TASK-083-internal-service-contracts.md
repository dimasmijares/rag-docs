---
id: WRK-TASK-083
type: spec
layer: work-task
scope: ephemeral
status: completed
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [ARCH-002, DOM-RAG-002, DOC-RAG-002, RULE-003, RULE-004]
dependencies:
  - id: WRK-TASK-029
    relation: depends-on
  - id: ADR-RAG-010
    relation: depends-on
tags: [contracts, ports, value-objects, errors, boundaries]
---

# WRK-TASK-083 — Contratos de puertos internos

## Objective

Crear `rag_docs.contracts` con los objetos de valor y los puertos que definen los límites de
`ARCH-002`, de modo que la extracción posterior a servicios sea la implementación de un adaptador y
no una reescritura.

## File Scope

Incluye el paquete `rag_docs/contracts/**`, el traslado de los DTO existentes, la firma de los
puertos, el mapeo de la taxonomía de errores en `api.py` y sus tests. Excluye cualquier cambio de
comportamiento observable, transporte HTTP entre servicios, autenticación entre servicios y
contract tests de red, que permanecen en `WRK-TASK-057`.

## Acceptance Criteria

- [x] `rag_docs.contracts` no importa `qdrant_client`, `sentence_transformers`, `httpx`, `fastapi`
      ni ningún cliente de I/O, y un test lo verifica.
- [x] Existen los objetos de valor `IndexFingerprint`, `Scope`, `ErrorKind`, `CorrelationId` e
      `IdempotencyKey`, y los DTO de dominio quedan alojados en el paquete.
- [x] Existen los puertos `EmbeddingPort`, `GenerationPort`, `RetrievalPort`, `AuthorizationPort`,
      `GroundingPort` y `DocumentSourcePort`.
- [x] `GenerationPort` declara ya la variante de streaming y la contabilidad de tokens y latencia,
      aunque su implementación llegue en `WRK-TASK-041`.
- [x] `RetrievalPort.search` recibe pregunta y ámbito, no vector: la resolución del embedding de
      consulta queda del lado de retrieval.
- [x] `api.py` deja de responder `503` con el texto de la excepción y mapea `ErrorKind` a códigos
      HTTP sin filtrar detalles internos.
- [x] La política de compatibilidad de los DTO queda escrita: campos aditivos, nunca renombrados ni
      con semántica cambiada en sitio.
- [x] Los gold sets existentes producen resultados idénticos antes y después del cambio.

## Evidence

- Paquete `rag_docs/contracts/` creado: `value_objects.py` (`IndexFingerprint`, `Scope`,
  `ErrorKind`, `CorrelationId`, `IdempotencyKey`), `dtos.py` (DTO de dominio movidos:
  `DocumentChunk`, `SearchHit`, `Citation`, `AnswerClaim`, `RetrievalDiagnostic`, `QueryResult`,
  `IndexReport`/`IndexError`, `DocumentCandidate`, `ExtractedUnit`), `ports.py` (`EmbeddingPort`,
  `GenerationPort` con variante de streaming y `GenerationMetrics`, `RetrievalPort` con firma
  `search(question, scope, k, threshold, fingerprint)`, `AuthorizationPort`, `GroundingPort`,
  `DocumentSourcePort`, `VectorStorePort`), `errors.py` (`AppError`, `http_status_for`).
  `rag_docs.models`, `query.py` e `indexing.py` re-exportan estos símbolos para no romper los
  ~20 puntos de importación existentes.
- `api.py` mapea `ValueError`→`ErrorKind.VALIDATION`, `InvalidGeneratedResponse`→
  `ErrorKind.INVALID_MODEL_OUTPUT`, `GenerationError`→`ErrorKind.DEPENDENCY_UNAVAILABLE`,
  `AppError`→su propio `kind`, y cualquier excepción no prevista queda registrada con
  `logger.exception` y responde un mensaje genérico sin el texto de la excepción.
- `tests/test_contracts.py` (5 tests): sin imports de I/O, los 7 puertos son `Protocol`,
  los objetos de valor son inmutables, `ErrorKind` mapea a códigos HTTP distintos y las DTO
  movidas exponen `__module__` bajo `rag_docs.contracts`.
- `tests/test_api.py`: nuevo test `test_unexpected_error_maps_to_error_kind_without_leaking_exception_text`
  verifica que una excepción con datos sensibles no aparece en el `detail` de la respuesta.
- `uv run --no-sync pytest -q`: 63 tests, verde (incluye gold sets sin cambios de resultado).
- `uv run --no-sync ruff check .`: verde.

Rama: `codex/wrk-task-083-internal-service-contracts`.
