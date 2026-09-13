---
id: WRK-TASK-103
type: spec
layer: work-task
scope: ephemeral
status: archived
confidence: medium
version: 0.2.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
parent: WRK-PLAN-013
activates: [DOC-RAG-003, RULE-002]
dependencies:
  - id: WRK-TASK-102
    relation: depends-on
tags: [fabric, power-bi, pbip, evaluation]
---

# WRK-TASK-103 — Informe Power BI de calidad

## Objective

Visualizar la calidad del retrieval y de las respuestas por perfil, backend, corpus y fingerprint.

## File Scope

Incluye el informe y modelo semántico PBIP/TMDL en `fabric/` y su documentación. Excluye páginas
operativas de indexación y cola (`WRK-TASK-114`).

## Acceptance Criteria

- [x] El informe se versiona como PBIP y pasa el gate público.
- [x] El modelo usa Direct Lake sobre las tablas Delta de `WRK-TASK-102`.
- [x] Las métricas se filtran por perfil, backend, `corpus_version` y fingerprint, y la latencia se
      muestra segregada por backend.

## Evidence

- **PBIP versionado** en `fabric/`: `ragdocs_quality.pbip`, `ragdocs_quality.SemanticModel`
  (`definition.pbism` + TMDL) y `ragdocs_quality.Report` (PBIR: `definition.pbir`, `report.json`,
  2 páginas y 11 visuales).
  - Ningún fichero del PBIP contiene GUIDs, host ni id del endpoint. La conexión Direct Lake se
    versiona como `Sql.Database("#{SQL_ENDPOINT_HOST}#", "#{SQL_ENDPOINT_ID}#")` y el informe
    referencia el modelo por ruta.
  - `scripts/check-public-safety.ps1` supera el repositorio completo (339 ficheros) y los 35
    ficheros de `fabric/`. El gate de `WRK-TASK-097` rechazaría un endpoint real si llegara a
    versionarse.
- **Direct Lake sobre Delta:**
  - Particiones `mode: directLake` con `expressionSource: DatabaseQuery` sobre las tablas
    `evaluation_profiles` y `evaluation_runs` de `ragdocs_eval` (`WRK-TASK-102`), relacionadas por
    `run_id`.
  - `fabric/deploy_quality_report.ps1` resuelve el endpoint con `fab get`, sustituye los marcadores
    en `_build/quality-deploy/`, importa modelo e informe (`byConnection` con el id resuelto), hace
    refresh y valida con `executeQueries`.
  - Ejecución live (2026-09-13): modelo e informe importados. La consulta DAX de validación
    devolvió `qdrant` (18 perfiles, Recall@8 0.991, p95 2.97 ms) y `fabric_sql` (4 perfiles,
    Recall@8 1.0, p95 140.4 ms) para `corpus_version 0.2.0` y fingerprint `724f6786a9170f8b`.
    Una consulta previa con `evaluation_runs[phase]` confirmó que la relación filtra por fase.
- **Filtros y latencia**, verificados exportando el informe publicado a PDF con la API de Power BI
  (`ExportTo`, estado `Succeeded`):
  - Página "Calidad de retrieval": slicers de perfil, `vector_backend`, `corpus_version`,
    fingerprint y fase; tabla con Recall@1/3/8, MRR y score medio por perfil, backend, modo y
    fingerprint; gráfico de MRR por perfil coloreado por backend. Los perfiles de Qdrant y Fabric
    SQL muestran métricas idénticas, coherente con la paridad de `WRK-TASK-102`.
  - Página "Latencia por backend": p95 de retrieval con el backend como eje (Fabric SQL ~127–154 ms,
    Qdrant ~2–4 ms) y tabla p50/p95 por backend y perfil.
  - La primera exportación mostraba una fila "Total" que promediaba latencias de ambos backends
    (18.3 / 28.0 ms). Se desactivó en la tabla de latencia y la segunda exportación ya no la
    muestra.
  - Las medidas de latencia declaran en su descripción que solo son comparables dentro del mismo
    backend.
  - Detalle cosmético conocido: el slicer de fase muestra el miembro `(Blank)` del lado uno de la
    relación Direct Lake; ningún perfil tiene fase vacía (los 22 perfiles se reparten entre
    `development` y `validation`).
- **Documentación:** `DOC-RAG-003`, sección "Informe Power BI de calidad".
- **Fuera del File Scope literal:** `fabric/deploy_quality_report.ps1`, necesario para desplegar
  sin versionar identificadores. `scripts/verify.ps1` en verde.
