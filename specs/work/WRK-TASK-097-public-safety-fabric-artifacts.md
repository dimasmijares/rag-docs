---
id: WRK-TASK-097
type: spec
layer: work-task
scope: ephemeral
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [DOC-RAG-002, RULE-002]
dependencies:
  - id: RFC-004
    relation: depends-on
tags: [public-safety, security, fabric, ci]
---

# WRK-TASK-097 — Gate público para artefactos Fabric

## Objective

Ampliar el gate `public-safety` para que ningún artefacto Fabric pueda versionar datos, outputs,
credenciales ni identificadores del entorno.

## File Scope

Incluye `scripts/check-public-safety.ps1`, `scripts/test-public-safety.ps1`, sus fixtures negativas
y el workflow de CI si cambia la invocación. Excluye crear artefactos Fabric reales.

## Acceptance Criteria

- [ ] Se escanean `.ipynb`, `.platform` y PBIP/TMDL; un notebook con outputs se rechaza.
- [ ] Se rechazan cadenas de conexión con credenciales y GUIDs de tenant o workspace fuera de una
      lista de marcadores de ejemplo.
- [ ] Cada patrón nuevo tiene una fixture negativa que falla y una positiva que pasa.
- [ ] El gate sigue sin contener en claro los identificadores que protege (`WRK-TASK-092`).

## Evidence

Pendiente.
