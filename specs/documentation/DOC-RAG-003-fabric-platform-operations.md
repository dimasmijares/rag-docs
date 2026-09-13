---
id: DOC-RAG-003
type: spec
layer: documentation
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RFC-004
    relation: implements
  - id: ADR-RAG-013
    relation: implements
  - id: ADR-RAG-014
    relation: implements
  - id: DOC-RAG-002
    relation: extends
  - id: RULE-002
    relation: constrained-by
tags: [documentation, fabric, operations, security, cost]
---

# DOC-RAG-003 — Operación de la plataforma Fabric

## Intent

Mantener una guía verificable para montar, operar y desmontar el perfil opcional de Fabric sin
exponer secretos ni identificadores del entorno.

## Definition

La documentación cubrirá:

- Prerrequisitos: capacidad Fabric (Trial o F-SKU), workspace dedicado y corpus sintético.
- Identidad: service principal de Entra ID con certificado, rol de mínimo privilegio en el
  workspace, y habilitación del uso de APIs de Fabric por service principals, que hace una persona
  administradora del tenant.
- Git integration de la carpeta `fabric/` (notebooks, pipelines, informes PBIP).
- Environment con el wheel del proyecto (`uv build`) y extra opcional `[fabric]`; no activar
  outbound access protection.
- Variable library para parámetros por entorno, sin valores sensibles versionados.
- Gate `scripts/verify-fabric.ps1`: cuándo se ejecuta, credenciales introducidas por la persona
  usuaria y nunca en CI obligatorio.
- Worker de inferencia local (`ADR-RAG-014`): ventana batch, arranque, parada y dead-letter.
- Monitorización de consumo de capacidad (CU) y teardown completo del workspace.

## Acceptance Criteria

- Un entorno nuevo se monta desde cero siguiendo la guía, sin pasos implícitos.
- No se documentan secretos, certificados, IDs de tenant, cliente o workspace ni rutas personales.
- El teardown elimina todos los artefactos y la identidad deja de tener acceso.
- `scripts/verify.ps1` y el quickstart Compose siguen funcionando sin Fabric.
