---
id: WRK-TASK-084
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-006
activates: [ARCH-002, DOM-RAG-002, FEAT-RAG-002, RULE-002, RULE-004]
dependencies:
  - id: WRK-TASK-031
    relation: depends-on
  - id: ADR-RAG-008
    relation: depends-on
tags: [idempotency, ledger, reconciliation, lease, worker]
---

# WRK-TASK-084 — Contrato de idempotencia y reconciliación del indexado

## Objective

Hacer verificable la promesa de `ADR-003` de que el worker es idempotente, fijando la clave de
efecto, el ledger documental, el orden de efectos y las condiciones bajo las que se puede borrar.

## File Scope

Incluye el ledger documental en PostgreSQL, la clave de efecto, el orden escribir-antes-de-borrar en
el vector store, el lease con heartbeat, la señal de snapshot completo en el descubrimiento y sus
tests. Excluye programaciones y cursores, que permanecen en `WRK-TASK-032`, y la UX de jobs.

## Acceptance Criteria

- [ ] La clave de efecto es `(document_id, content_hash, index_fingerprint)` y el ledger la registra
      al cerrar cada documento; reprocesarla es un no-op contabilizado como `unchanged`.
- [ ] El orden de efectos por documento es escribir chunks nuevos, borrar los obsoletos de ese
      documento y confirmar el ledger: el documento nunca deja de ser consultable durante una
      actualización.
- [ ] Un corte entre el `ack` del vector store y el commit del ledger deja el sistema convergente
      tras el siguiente intento, verificado con una prueba de interrupción.
- [ ] Toda transición de estado es condicional al estado esperado y comprueba filas afectadas.
- [ ] Un job cuyo lease expira es reclamable y su reejecución es segura por construcción.
- [ ] El borrado de documentos huérfanos sólo se ejecuta si el descubrimiento de esa fuente devolvió
      un snapshot completo; un descubrimiento parcial o degradado nunca borra.
- [ ] El mensaje del broker contiene únicamente identificador de job y correlación, verificado por
      test.

## Evidence

Pendiente.
