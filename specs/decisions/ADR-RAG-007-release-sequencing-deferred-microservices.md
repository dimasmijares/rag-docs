---
id: ADR-RAG-007
type: adr
layer: adr
scope: persistent
status: proposed
confidence: medium
version: 0.2.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
dependencies:
  - id: RFC-002
    relation: depends-on
  - id: ADR-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: WRK-PLAN-004
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [architecture-decision, roadmap, sequencing, microservices, review]
---

# ADR-RAG-007 — Secuencia de releases y extracción condicional de microservicios

## Context

`WRK-PLAN-004` fija la secuencia `v0.2.0 → v1.0.0 → v1.1.0 → v1.5.0 → v2.0.0 → v2.5.0 → v3.0.0`
con la regla de que cada plan empieza cuando el gate anterior está consolidado. Tras cerrar
`v0.2.0` (baseline evaluable con corpus sintético, gold sets y `benchmark.py`) la secuencia
presenta tres tensiones observables en el grafo KDD y en el código actual.

Primera: `WRK-TASK-036` (fingerprint del índice y migración por alias) vive en `WRK-PLAN-007`
(v1.1.0), pero `RULE-004` ya es `active` y hoy sólo está aplicada por documentación. En
`QdrantVectorStore.ensure_collection` la colección existente se acepta sin comprobar nada más que
su existencia, de modo que un cambio de modelo de embeddings con la misma dimensión escribe
vectores incompatibles en la colección anterior sin error. Además `WRK-TASK-043` depende
explícitamente de `036`, y el ledger documental que introduce `WRK-TASK-030` necesita el
fingerprint como clave. El invariante está declarado dos releases antes de existir.

Segunda: el modelo de identidad y tenant llega en `v1.5.0` (`WRK-TASK-017`, `043`), mientras que
el esquema PostgreSQL se diseña en `v1.0.0` (`WRK-TASK-030`). Un esquema de jobs, fuentes,
configuración, cursores y auditoría concebido sin `tenant_id` obliga a migrar todas las tablas y a
reescribir sus tests dos releases después. La secuencia genera retrabajo garantizado, no
hipotético.

Tercera: la mejora de calidad de retrieval pendiente (`WRK-TASK-037` y `038`, sobre el contrato
diagnóstico que `WRK-TASK-012` ya dejó cerrado en `v0.2.0`) es trabajo interno al monolito que no
requiere infraestructura nueva, y es exactamente lo que determina si merece la pena industrializar.
Está programada después de introducir PostgreSQL, Redis y Celery.

Sobre la pregunta explícita de microservicios: `WRK-SPEC-010` extrae ocho servicios antes de que
exista tracción de uso. Los tres motores legítimos de una extracción —escalado independiente,
frontera de equipo y despliegue independiente— no están presentes. El sistema tiene un operador,
un despliegue y ningún dato de carga real: `WRK-TASK-055` (SLO y carga) es la primera tarea que
produciría esa evidencia y vive en la release inmediatamente anterior. Existe, sin embargo, un
requisito no técnico real y legítimo: el repositorio es portfolio y la topología distribuida forma
parte de lo que demuestra.

## Options Considered

1. **Mantener el orden actual sin cambios.** Preserva la narrativa orgánica de `WRK-PLAN-004` y no
   toca el grafo. Acepta el retrabajo del esquema, deja `RULE-004` sin enforcement durante dos
   releases y paga la complejidad de ocho servicios sin evidencia de necesidad.
2. **Adelantar todo lo barato y dejar el resto igual** (fingerprint, calidad y modelo de datos de
   identidad antes de la infraestructura asíncrona), manteniendo `v2.5.0` como extracción
   completa. Elimina el retrabajo pero conserva la complejidad prematura.
3. **Adelantar lo barato y convertir `v2.5.0` en extracción condicional y por fronteras**, con los
   ocho límites existentes como contratos en proceso y sólo aquellas fronteras con motor real
   promovidas a servicio. Reduce superficie operativa, conserva el valor demostrativo y hace que
   `v3.0.0` siga siendo posible con tres o cuatro workloads.
4. **Eliminar `v2.5.0` y saltar a Kubernetes desde el monolito contenedorizado.** Es la opción de
   menor coste técnico y la que mejor refleja lo que un equipo prudente haría, pero renuncia por
   completo al objetivo de portfolio declarado en `RFC-002` y `ARCH-002`.

## Decision

Se adopta la opción 3, con cuatro movimientos concretos.

**A. Insertar una release `v0.3.0` de invariantes de índice y calidad**, anterior a `v1.0.0`, que
contiene el enforcement del fingerprint y los experimentos de retrieval. Es trabajo dentro del
monolito, sin dependencias de infraestructura, y produce la evidencia que justifica —o no— seguir
industrializando.

**B. Adelantar el modelo de datos de identidad, tenant y clasificación** a un artefacto previo a
`WRK-TASK-030`, limitado al modelo de datos y a su propagación por payload. Keycloak, OIDC,
validación de tokens y autorización efectiva permanecen en `v1.5.0`. Se separa el *esquema* de la
*aplicación del esquema*: el primero es barato ahora y carísimo después; la segunda no gana nada
por adelantarse y sí obliga a operar un IdP durante tres releases.

**C. Adelantar la parte de `WRK-TASK-057` que fija puertos y objetos de valor internos** al
monolito, dejando en `v2.5.0` sólo el trabajo de nivel HTTP `/v1` y los contract tests. El detalle
de los límites está en `ADR-RAG-010`.

**D. `v2.5.0` deja de ser «extraer ocho servicios» y pasa a ser «extraer las fronteras con motor
demostrable, con un mínimo de tres».** Las fronteras cuyo motor ya existe hoy son
`embedding-service` y `model-gateway` (perfil de hardware, memoria y ciclo de vida distintos del
resto; `model-gateway` ya está de facto separado por los perfiles local/remoto de
`generator_profiles.py`) e `index-worker` (proceso separado desde `v1.0.0` por decisión de
`ADR-003`). `authz-service` se promueve si y sólo si la política deja de ser evaluable en proceso.
`query-api`, `retrieval-service`, `context-grounding-service` e `index-api` permanecen como un
único desplegable salvo que `WRK-TASK-055` produzca evidencia de escalado divergente: son llamadas
síncronas 1:1 en la ruta de petición con ciclo de vida compartido, el caso donde una frontera de
red sólo añade latencia y modos de fallo.

`v3.0.0` no depende de la extracción completa: depende de workloads contenedorizados con health
checks, que existen al cerrar `v2.0.0`. Si `v2.5.0` se pospone, `v3.0.0` sigue siendo ejecutable
con el conjunto reducido.

Secuencia resultante:

| Orden | Release | Contenido |
|---:|---|---|
| 1 | v0.2.0 | Cerrada. Baseline evaluable |
| 2 | v0.3.0 | Fingerprint aplicado, modelo de datos de identidad, calidad de retrieval |
| 3 | v1.0.0 | Runtime asíncrono durable sobre esquema ya tenant-aware |
| 4 | v1.1.0 | Multimodal: OCR, visión, provenance visual, streaming |
| 5 | v1.5.0 | OIDC, ACL efectiva, aislamiento verificado |
| 6 | v2.0.0 | Conectores, observabilidad, backup/restore, SLO y carga |
| 7 | v2.5.0 | Extracción condicional por frontera, mínimo tres servicios |
| 8 | v3.0.0 | Helm sobre `kind` |

## Consequences

Positivas: `RULE-004` deja de ser una regla sin enforcement dos releases antes de tenerlo; el
esquema PostgreSQL nace tenant-aware y evita una migración transversal; la decisión de
industrializar se toma con datos de calidad medidos, no antes; la superficie operativa de `v2.5.0`
baja de ocho a tres o cuatro servicios y la de `v3.0.0` con ella.

Negativas y costes aceptados: se introduce una release adicional en `WRK-PLAN-004` y hay que
reordenar aristas del grafo KDD (`036`, `037`, `038`, `017`, `043`, `046`, `057` y la entrada de
`WRK-TASK-030`). La narrativa de portfolio pierde el titular de los ocho
microservicios y gana el de fronteras extraídas con criterio; es una elección de posicionamiento
que el propietario debe validar, no una consecuencia técnica. `WRK-SPEC-010` pasa de release de
ejecución a release con gate de decisión previo, lo que hace su fecha menos predecible.

## Work Impact

Aplicado en el grafo KDD:

- Creados `WRK-SPEC-012` y `WRK-PLAN-012` para la release `v0.3.0`.
- `WRK-TASK-036` reubicada de `WRK-PLAN-007` a `WRK-PLAN-012`, con dependencia en `WRK-TASK-083` y
  con enforcement e identidad de chunk incorporados a sus criterios.
- `WRK-TASK-037` y `WRK-TASK-038` reubicadas a `WRK-PLAN-012`. `WRK-TASK-012` **no** se reubica:
  está `archived` desde `v0.2.0` y su contrato diagnóstico ya es la baseline de partida.
- Creadas `WRK-TASK-082` (modelo de tenant y ámbito), `083` (contratos de puertos internos), `086`
  (manifiesto de corpus), `090` (división de `QueryService`), `092` (saneamiento del gate público) y
  `091` (release `v0.3.0`), todas bajo `WRK-PLAN-012`.
- `WRK-TASK-030` pasa a depender de `WRK-TASK-091` y `WRK-TASK-082`, de modo que el esquema
  PostgreSQL nace multi-tenant.
- `WRK-TASK-017` pasa a depender también de `WRK-TASK-082`.
- `WRK-TASK-057` se reduce al transporte HTTP `/v1` y depende de `WRK-TASK-083`.
- Creada `WRK-TASK-088` bajo `WRK-PLAN-009`: gate de decisión de extracción alimentado por
  `WRK-TASK-055`, que ahora mide consumo por frontera.
- `WRK-PLAN-004` actualiza tabla, ordenación crítica y Evidence.

Pendiente de decisión del propietario, **no aplicado**:

- La reducción de alcance de `WRK-SPEC-010` (decisión D). El work spec registra la propuesta en una
  sección `Scope Decision` y remite al gate de `WRK-TASK-088`, pero conserva su objetivo original.
- `WRK-TASK-089` (extracción mínima de `embedding-service`, `model-gateway` e `index-worker` como
  alcance por defecto) no se ha creado: presupone la aprobación de D.

## Human Checkpoint

**PARAR antes de ejecutar este ADR.** La decisión D cambia el objetivo declarado de `WRK-SPEC-010`
y con él el argumento de portfolio de `RFC-002`. Es una decisión de posicionamiento profesional, no
técnica, y sólo el propietario del repositorio puede tomarla. Las decisiones A, B y C son
reordenaciones internas del grafo y pueden aprobarse por separado; recomiendo aprobarlas aunque D
se rechace.
