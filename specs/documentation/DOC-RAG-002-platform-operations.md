---
id: DOC-RAG-002
type: spec
layer: documentation
scope: persistent
status: draft
confidence: low
version: 0.1.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: ARCH-002
    relation: implements
  - id: DOC-RAG-001
    relation: extends
  - id: FEAT-RAG-002
    relation: implements
  - id: FEAT-RAG-003
    relation: implements
  - id: FEAT-RAG-004
    relation: implements
  - id: RULE-002
    relation: constrained-by
tags: [documentation, portfolio, compose, kubernetes, operations]
---

# DOC-RAG-002 — Operación de portfolio y plataforma

## Intent

Mantener una guía verificable desde la demo pública hasta el despliegue distribuido.

## Definition

La documentación cubrirá quickstart sintético, privacidad, arquitectura, evaluación, Compose,
OIDC local, observabilidad opcional, conectores, backups, `kind`, Helm, seguridad, CI/CD y mappings
de dependencias externas para servidor, Azure y AWS.

## Acceptance Criteria

- Cada release tiene prerrequisitos, un camino reproducible, verificación y rollback.
- Compose continúa siendo el flujo sencillo y Kubernetes aparece como evolución.
- No se documentan valores de secretos, IP privadas ni rutas personales.
- La V3 se describe como simulación local, no como alta disponibilidad física.
