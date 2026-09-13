---
id: RFC-004
type: rfc
layer: rfc
status: accepted
confidence: medium
version: 1.0.0
created: 2026-09-13
updated: 2026-09-13
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: extends
  - id: ADR-RAG-007
    relation: extends
  - id: ARCH-002
    relation: extends
  - id: DOM-RAG-001
    relation: extends
  - id: RULE-001
    relation: constrained-by
  - id: RULE-002
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [roadmap, fabric, data-platform, evaluation, optional-profile]
---

# RFC-004 — Microsoft Fabric como plataforma opcional de datos y evaluación

## Problem Statement

`RFC-002` fija un núcleo neutral respecto de cloud y dependencias de datos configurables, pero no
contempla una plataforma de datos gestionada. Se quiere usar Microsoft Fabric con fines educativos y
profesionales para que ingesta, índice vectorial, evaluación y BI puedan ejecutarse allí, manteniendo
el LLM en el equipo local y sin APIs de pago. `RULE-001` exige RFC, ADR y configuración explícita de
privacidad para cualquier integración externa, y `DOM-RAG-001` declara que los datos permanecen en el
equipo durante la PoC.

## Decision

Adoptar Fabric como **perfil de despliegue opcional** (opción C del análisis de viabilidad): plano de
indexación y evaluación en Fabric; servicio interactivo (API, web, grounding y generación) local,
leyendo vectores de SQL database in Fabric.

- El núcleo sigue siendo cloud-neutral. El quickstart Compose y `scripts/verify.ps1` nunca requieren
  Fabric ni credenciales.
- Los tests live contra Fabric nunca son obligatorios en CI; viven en un gate aparte
  (`scripts/verify-fabric.ps1`) que se ejecuta con login interactivo o service principal.
- En Fabric sólo se carga el corpus sintético público (`RULE-002`); el corpus corporativo nunca sale.
- La identidad de procesos es un service principal de Entra ID con mínimo privilegio en el workspace.
  Secretos, certificados e identificadores de tenant, cliente o workspace nunca se versionan.
- El backend vectorial y el ledger se deciden por perfil en `ADR-RAG-013`; la inferencia local
  invocada desde Fabric, en `ADR-RAG-014`.

## Release Sequence

La secuencia de `ADR-RAG-007` se amplía sin reordenar lo ya decidido:

`v0.3.0 → v0.4.0 (WRK-SPEC-013) → v1.0.0 (WRK-SPEC-006) → v1.1.0 (WRK-SPEC-014) → v1.2.0
(WRK-SPEC-007) → v1.5.0 → v2.0.0 → v2.5.0 → v3.0.0`

- `v0.4.0` — Backend neutral y plano de evaluación en Fabric, sin runtime asíncrono: costuras de
  store, suite de contrato, gate público para artefactos Fabric, `FabricSqlVectorStore`, walking
  skeleton, evaluación en Delta e informe Power BI.
- `v1.1.0` — Plano de indexación en Fabric sobre el runtime durable de `v1.0.0`: fuente OneLake,
  ledger en Fabric SQL, indexación Spark, orquestación por eventos y cola de inferencia local.
- `v1.2.0` — Multimodal (antes `v1.1.0`), cuyos extractores funcionan también en el Environment de
  Fabric.

## Compatibility Strategy

- Los contratos HTTP de `v0.3.0` no cambian; el perfil Fabric se selecciona por configuración.
- Las costuras de backend y el ledger portable preceden al esquema PostgreSQL de `v1.0.0`.
- Todo artefacto Fabric versionado (notebooks, `.platform`, PBIP/TMDL) pasa el gate público ampliado
  antes de su primer commit.
- Latencia medida en backends distintos nunca se compara; recall sí, con la clave de
  comparabilidad ampliada de `ADR-RAG-013`.

## Consequences

El proyecto gana un camino profesional sobre una plataforma de datos gestionada sin sacrificar el
flujo local. El coste es una segunda implementación de store y ledger, un gate adicional no
obligatorio y la dependencia de capacidades en preview (DiskANN), que se tratan como experimentos.
La capacidad Trial puede desaparecer: por eso ninguna release depende de Fabric para cerrar sus
gates obligatorios.

## Alternatives Considered

1. **Todo en Fabric, incluido el servicio interactivo**: exige exponer el LLM local o usar modelos de
   pago; se descarta.
2. **Sólo evaluación y BI en Fabric**: poco valor educativo en el plano de datos; queda subsumida
   como `v0.4.0`.
3. **No integrar Fabric**: mantiene la simplicidad, pero pierde el objetivo profesional declarado.
