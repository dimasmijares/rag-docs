---
id: WRK-TASK-099
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
activates: [ARCH-002, DOC-RAG-003, RULE-002]
dependencies:
  - id: WRK-TASK-097
    relation: depends-on
  - id: RFC-004
    relation: depends-on
tags: [fabric, bootstrap, identity, environment]
---

# WRK-TASK-099 — Bootstrap del workspace Fabric

## Objective

Montar de forma reproducible el workspace Fabric del perfil opcional, con identidad de mínimo
privilegio y sin secretos versionados.

## File Scope

Incluye la carpeta `fabric/` sincronizada por Git integration, el extra opcional `[fabric]` en
`pyproject.toml` (y `uv.lock` regenerado por `uv`), el build del wheel para el Environment y
`specs/documentation/DOC-RAG-003-*`. Excluye el backend vectorial y cualquier dato no sintético.

## Acceptance Criteria

- [ ] Lakehouse, SQL database y Environment con el wheel del proyecto existen y están descritos en
      `DOC-RAG-003`.
- [ ] La variable library contiene sólo parámetros no sensibles; ningún ID de tenant, cliente o
      workspace se versiona.
- [ ] El service principal tiene el rol mínimo necesario en el workspace; la habilitación del tenant
      la confirma la persona administradora.
- [ ] `fabric/` pasa el gate público ampliado de `WRK-TASK-097`.
- [ ] `scripts/verify.ps1` no requiere el extra `[fabric]`.

## Evidence

Pendiente.
