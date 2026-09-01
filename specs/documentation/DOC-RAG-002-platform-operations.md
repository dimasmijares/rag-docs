---
id: DOC-RAG-002
type: spec
layer: documentation
scope: persistent
status: draft
confidence: low
version: 0.3.0
created: 2026-09-01
updated: 2026-09-01
owner: rag-docs-team
dependencies:
  - id: RFC-003
    relation: implements
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

Una iteración implementa una sola `WRK-TASK` en una rama `codex/wrk-task-NNN-slug` y una PR. Una
sesión coordinadora puede ejecutar varias iteraciones en serie o coordinar iteraciones
independientes en paralelo cuando la petición del usuario autorice varias tareas.

Los números identifican artefactos; la selección respeta dependencias terminales en `main`,
release activo, reducción de riesgo y capacidad de desbloqueo. Antes de activar una tarea se
sincroniza `main`, se comprueba que el checkout esté limpio y que no haya PR con scope de
implementación solapado, y se ejecutan `validate`, `orphans` y `context`.

Una solicitud singular ejecuta una tarea lista. Una solicitud de continuar el release permite
repetir iteraciones en serie: tras cada merge se sincroniza `main` y se recalcula el DAG antes de
seleccionar la siguiente tarea.

## Agentic Orchestration

Dentro de una tarea se usan subagentes para análisis o workstreams acotados e independientes
cuando reduzcan el tiempo sin provocar ediciones conflictivas. Se prefiere análisis paralelo de
solo lectura antes de modificar archivos compartidos; el agente principal conserva síntesis,
integración, gates y resultado final.

Pueden coexistir inicialmente hasta dos tareas independientes si el usuario autoriza trabajo
múltiple, todas sus dependencias están terminales en `main`, ninguna depende directa o
transitivamente de la otra y sus scopes de implementación no se solapan. Cada una usa worktree,
rama y PR propios, y cada checkout contiene como máximo una WRK-TASK activa. Los archivos KDD de
coordinación compartidos son responsabilidad del coordinador.

Las PR concurrentes se fusionan de una en una. Antes de integrar la siguiente se actualiza desde
el nuevo `main`, se resuelve drift y se repiten los gates. Una tarea dependiente nunca empieza
antes de que sus predecesoras estén fusionadas y terminales. Ante dudas de dependencia, scope u
orden de integración, el trabajo se serializa.

La tarea sólo se completa tras pruebas proporcionales, Evidence, lifecycle, gate público y checks
remotos. La PR se fusiona cuando todos los gates obligatorios están verdes y la iteración termina
después de verificar el merge y sincronizar `main`.

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
- Cada checkout contiene como máximo una WRK-TASK activa y toda tarea terminal conserva criterios
  y Evidence cerrados.
- La ejecución serial y paralela respeta el DAG, scopes aislados, gates por PR e integración una a
  una desde `main` actualizado.
