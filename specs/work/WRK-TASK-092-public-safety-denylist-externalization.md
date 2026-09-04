---
id: WRK-TASK-092
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
parent: WRK-PLAN-012
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: WRK-TASK-029
    relation: depends-on
  - id: ADR-RAG-011
    relation: depends-on
tags: [public-safety, privacy, gate, denylist]
---

# WRK-TASK-092 — Saneamiento del gate de publicación

## Objective

Sacar del repositorio público la lista de identificadores corporativos derivados que
`scripts/check-public-safety.ps1` incrusta en claro, sin perder capacidad de detección en CI.

## File Scope

Incluye `scripts/check-public-safety.ps1`, `scripts/test-public-safety.ps1`, `.gitignore`, el
workflow de calidad y la documentación del gate. Excluye `src/**`, `specs/**` salvo Evidence,
corpus y gold sets.

## Acceptance Criteria

- [ ] El script carga los identificadores derivados desde un fichero local ignorado por Git o desde
      un secreto de CI, y la lista versionada queda vacía.
- [ ] La ausencia del fichero produce una advertencia visible, nunca un falso verde silencioso.
- [ ] CI ejecuta el gate con la lista completa cargada desde secreto.
- [ ] Los tests del gate siguen demostrando detección usando identificadores sintéticos.
- [ ] La decisión sobre el historial de Git queda registrada de forma explícita en Evidence, se
      actúe o no sobre él.

## Evidence

Pendiente.
