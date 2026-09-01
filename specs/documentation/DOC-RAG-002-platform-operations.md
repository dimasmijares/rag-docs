---
id: DOC-RAG-002
type: spec
layer: documentation
scope: persistent
status: draft
confidence: low
version: 0.2.0
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
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
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

## Iteration Protocol

Cada iteración implementa una sola `WRK-TASK` en una rama `codex/wrk-task-NNN-slug` y una PR.
Los números identifican artefactos; la selección respeta dependencias, release activo y reducción
de riesgo. Antes de activar la tarea se sincroniza `main`, se comprueba que no haya trabajo local o
PR solapadas y se ejecutan `validate`, `orphans` y `context`.

La tarea sólo se completa tras pruebas, Evidence, gate público y checks remotos. La PR se fusiona
cuando todos los gates están verdes y la iteración termina después de sincronizar `main`; no se
activa otra tarea en el mismo ciclo.

## Discovered Work

Trabajo necesario dentro del objetivo y scope se incorpora a la tarea actual. Trabajo separable
recibe el siguiente ID `WRK-TASK` disponible, padre, dependencias, activaciones, scope y criterios,
y se añade al plan antes de ejecutarse. Un prerrequisito descubierto antes de la activación pasa a
ser la tarea seleccionada; si aparece después, se registra como bloqueo y se resuelve en la
siguiente iteración. Decisiones nuevas crean ADR y cambios transversales requieren RFC.

Al cerrar un release se consolida conocimiento, se completa su work spec y se archivan spec, plan
y tareas conservando Evidence antes de publicar el tag.

## Acceptance Criteria

- Cada release tiene prerrequisitos, un camino reproducible, verificación y rollback.
- Compose continúa siendo el flujo sencillo y Kubernetes aparece como evolución.
- No se documentan valores de secretos, IP privadas ni rutas personales.
- La V3 se describe como simulación local, no como alta disponibilidad física.
- Una sola WRK-TASK puede estar activa y toda tarea terminal conserva criterios y Evidence cerrados.
