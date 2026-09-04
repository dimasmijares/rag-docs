---
id: ADR-RAG-008
type: adr
layer: adr
scope: persistent
status: proposed
confidence: medium
version: 0.1.0
created: 2026-09-04
updated: 2026-09-04
owner: rag-docs-team
dependencies:
  - id: ADR-003
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-002
    relation: implements
  - id: WRK-SPEC-006
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [architecture-decision, outbox, celery, idempotency, transactions, review]
---

# ADR-RAG-008 — Límite transaccional y contrato de idempotencia del worker de indexado

## Context

`ADR-003` decide PostgreSQL como fuente de verdad, Celery sobre Redis como transporte de
identificadores y un worker idempotente, pero no fija dónde está el límite transaccional ni qué
significa exactamente idempotente. `WRK-SPEC-006` exige que reinicios de API, Redis o worker no
pierdan jobs ni dupliquen efectos, lo que sólo es verificable si ese contrato está escrito.

El estado actual del monolito determina el diseño más de lo que parece:

- `IndexingService.index()` es síncrono y hace, por documento: comparar `content_hash`, extraer,
  chunkear, embeber, `delete_document(document_id)` y luego `upsert`. La secuencia borrar-luego-
  escribir deja una ventana en la que el documento no existe en el índice; un fallo dentro de esa
  ventana lo pierde hasta la siguiente indexación completa.
- El identificador de punto es `uuid5(NAMESPACE_URL, chunk_id)` y `chunk_id` es un SHA-256 de
  `{document_id, unit_index, local_index, locator, section}`. **No incluye `content_hash` ni
  ninguna noción de fingerprint.** Los ids son deterministas frente a reejecución del mismo
  contenido —lo cual es una base excelente para idempotencia— pero también son estables cuando el
  contenido cambia, que es la razón por la que hoy hace falta borrar antes de escribir.
- El único estado es Qdrant. `list_documents()` reconstruye qué está indexado recorriendo la
  colección entera con `scroll`.
- El borrado de huérfanos sólo se aplica a fuentes cuyo `discover()` terminó sin excepción
  (`discovered_sources`), pero no distingue entre un descubrimiento completo y uno parcialmente
  degradado.
- Los tests usan `FakeVectorStore` o Qdrant `:memory:`; no hay estado entre tests, y `verify.ps1`
  se ejecuta sin infraestructura.

## Options Considered

**Sobre el límite transaccional:**

1. **Transacción distribuida sobre PostgreSQL y Qdrant** (2PC o saga con compensación estricta).
   Da atomicidad real del efecto completo. Coste desproporcionado, Qdrant no participa en 2PC y las
   compensaciones sobre un índice vectorial son ellas mismas efectos no atómicos.
2. **Una transacción por job**: el job entero se confirma o se descarta. Semántica simple pero
   incompatible con jobs de minutos: no hay resumibilidad, un fallo en el documento 900 de 1000
   descarta 899 documentos correctamente indexados y una cancelación pierde todo el trabajo.
3. **Una transacción por documento, con PostgreSQL como único recurso transaccional y Qdrant como
   modelo derivado.** El job es orquestación; el checkpoint durable es el documento. Requiere un
   ledger documental en PostgreSQL y aceptar explícitamente una ventana de inconsistencia entre el
   `ack` de Qdrant y el commit del ledger.

**Sobre la identidad de los puntos:**

4. Mantener `chunk_id` como está y conservar borrar-antes-de-escribir.
5. Incluir `content_hash` y `index_fingerprint` en la identidad del chunk, de modo que contenido
   distinto produce puntos distintos y se pueda escribir antes de borrar.

## Decision

**Límite transaccional (opción 3).** PostgreSQL es el único recurso transaccional. Ninguna
transacción abarca PostgreSQL y Qdrant, ni PostgreSQL y Redis. Se confirman en una sola transacción
exactamente dos clases de agrupación:

- creación o transición de estado de un job **junto con** su evento outbox;
- cierre de un documento en el ledger **junto con** la actualización de contadores y progreso del
  job.

Qdrant es un **modelo derivado**: PostgreSQL guarda la intención (qué debe estar indexado, con qué
`content_hash` y qué `index_fingerprint`) y el ledger de lo confirmado; Qdrant guarda la
materialización. La reconciliación siempre va del ledger hacia Qdrant, nunca al revés.

**Unidad de trabajo: el documento.** El worker recibe únicamente `job_id` y un id de correlación
(`ADR-003`), recupera el plan desde PostgreSQL y procesa documento a documento, confirmando cada
uno. Cancelación y reintento se evalúan en las fronteras entre documentos.

**Orden de efectos por documento (opción 5).** Se cambia la identidad del chunk para incluir
`content_hash` e `index_fingerprint`, y el orden pasa a ser:

1. `upsert` de los chunks nuevos (ids deterministas derivados del contenido actual);
2. `delete` por filtro de los puntos de ese `document_id` cuyo `content_hash` o
   `index_fingerprint` no sea el vigente;
3. commit del ledger en PostgreSQL.

Con este orden el documento nunca deja de ser consultable durante una actualización, y una caída en
cualquier punto deja como peor caso puntos obsoletos que el siguiente intento elimina. Es
estrictamente mejor que el borrar-luego-escribir actual y es la razón por la que este cambio debe
hacerse antes de introducir el worker, no después.

**Contrato de idempotencia del worker de indexado.** Se declara normativo:

- *Clave de idempotencia de creación de job*: `Idempotency-Key` de cliente en `POST /api/index`, con
  unicidad en base de datos y ventana de retención explícita. Repetir la petición con la misma clave
  devuelve el mismo `JobResource`, nunca un job nuevo.
- *Clave de efecto*: `(document_id, content_hash, index_fingerprint)`. Es la unidad que el worker
  comprueba antes de trabajar y la que registra al terminar. Si el ledger ya la contiene, el
  documento se salta y cuenta como `unchanged`.
- *Garantía*: **entrega al menos una vez, efectos exactamente una vez, estado observable
  convergente**. Reprocesar la misma clave de efecto produce el mismo conjunto de puntos con los
  mismos ids; no hay duplicación posible porque el id es función del contenido.
- *Ventana de inconsistencia aceptada*: caída entre el `ack` de Qdrant y el commit del ledger. El
  siguiente intento rehace el trabajo (coste: reembeber ese documento) y el resultado es idéntico.
  Se acepta explícitamente; no se intenta cerrar.
- *Transiciones de estado*: toda transición es un `UPDATE ... WHERE status = <esperado>` con
  comprobación de filas afectadas. Un worker que pierde la carrera no escribe.
- *Lease y recuperación*: cada job en ejecución mantiene `lease_expires_at` renovado por heartbeat.
  Un job cuyo lease expira es reclamable por el reconciliador (`WRK-TASK-032`) y su reejecución es
  segura por construcción, no por convención.
- *Reintentos*: contador por documento y por job, tope explícito y estado terminal `failed` con
  motivo estructurado. Un documento fallido no invalida el job.
- *Borrado de huérfanos*: sólo se ejecuta si el `discover()` de esa fuente devolvió un **snapshot
  completo**. Se añade a `DocumentSource.discover()` una señal explícita de completitud. Un
  descubrimiento parcial o degradado **nunca** borra documentos. Con conectores corporativos
  (`v2.0.0`) esta regla es la diferencia entre un error transitorio de red y el vaciado silencioso
  del índice de un tenant.
- *Payload del mensaje Celery*: `job_id` y correlación. Nada más. Ni configuración, ni rutas, ni
  texto documental (invariante de `ARCH-002`), verificado por test.

## Consequences

**Qué se rompe al reintroducir estado persistente** —esto es lo que hay que asumir de forma
explícita:

1. `VectorStore.list_documents()` deja de ser la fuente de qué está indexado y pasa a ser una API
   exclusivamente de reconciliación. El `scroll` completo de la colección desaparece de la ruta
   caliente de indexación. Es un cambio de contrato en `vector_store.py`, no una optimización.
2. **Los tests dejan de ser herméticos.** Hoy `verify.ps1` corre sin infraestructura. Con PostgreSQL
   hay que separar la suite en unitaria (sin infraestructura, sigue siendo el gate por defecto) e
   integración (PostgreSQL real, exigido por `WRK-TASK-030`), con aislamiento por transacción o por
   esquema y arranque explícito en CI. Si no se separa, el gate local deja de poder ejecutarse
   offline y la fricción de cada tarea sube de forma permanente.
3. **La reproducibilidad del benchmark se degrada en silencio.** `benchmark.py` mide etapas
   asumiendo un índice construido en la ejecución. Con estado persistente, los documentos
   `unchanged` cortocircuitan extracción y embedding, y los tiempos por etapa dejan de ser
   comparables con la baseline de `v0.2.0`. Se exige que el benchmark opere sobre colección
   dedicada y ledger vacío, y que el informe registre si hubo reutilización de estado.
4. **La configuración deja de ser inmutable durante una ejecución.** `WRK-TASK-033` mueve la
   configuración a PostgreSQL; `min_score`, `top_k`, `context_chunks` y `chunk_tokens` afectan
   directamente a las métricas. Todo job y toda evaluación deben persistir un snapshot de la
   configuración efectiva, o los resultados dejan de ser interpretables.
5. **El contenedor de aplicación se bifurca.** Hoy `ApplicationContainer` construye todo con avidez
   y `api.py` instancia `app = create_app()` a nivel de módulo, lo que carga el modelo de
   embeddings en el proceso de la API. Con worker separado, API y worker necesitan composiciones
   distintas: la API no debe cargar `sentence-transformers` y el worker no debe montar estáticos.
   Sin esta separación, cada réplica de API reserva memoria de modelo que no usa.
6. `IndexReport` deja de ser el valor de retorno de `POST /api/index` y pasa a ser el resultado
   final de un job. El contrato HTTP cambia de `200 IndexReport` a `202 JobResource`; es un breaking
   change de la API pública y de la web estática.

Positivas: resumibilidad, cancelación real, reejecución segura sin coordinación, y un modelo mental
único (PostgreSQL manda, Qdrant se reconstruye) que sobrevive intacto a la extracción de servicios
de `v2.5.0`.

## Work Impact

Crear:

- `WRK-TASK-084` — Contrato de idempotencia y reconciliación del worker: clave de efecto, ledger
  documental, orden escribir-antes-de-borrar, lease y heartbeat, señal de snapshot completo en
  `discover()`. Escisión de `WRK-TASK-031`, que se queda con dispatcher y wiring de Celery.

Reordenar y ampliar:

- La identidad de chunk con `content_hash` e `index_fingerprint` es prerrequisito de este ADR y de
  `WRK-TASK-036`; ambos van juntos en la release `v0.3.0` propuesta en `ADR-RAG-007`.
- `WRK-TASK-030` incorpora el ledger documental y el snapshot de configuración por job, además del
  `tenant_id` que exige `ADR-RAG-009`.
- `WRK-TASK-032` incorpora explícitamente la reclamación por lease expirado y la prohibición de
  borrado de huérfanos ante descubrimiento incompleto.
- Nueva subtarea dentro de `WRK-TASK-030`: separación de la suite en unitaria e integración y
  ajuste de `scripts/verify.ps1` para que el gate por defecto siga siendo ejecutable sin
  infraestructura.
- `WRK-TASK-014` (rendimiento) debe recalibrar la baseline del benchmark tras el cambio de orden de
  efectos.

## Human Checkpoint

**PARAR y validar antes de `WRK-TASK-030`** dos puntos:

1. La separación de la suite en unitaria e integración cambia el contrato de `scripts/verify.ps1`,
   que hoy es la puerta única del repositorio y está documentado en `CLAUDE.md` y en CI. Conviene
   decidir de antemano si el gate obligatorio pasa a exigir Docker.
2. El cambio de `200 IndexReport` a `202 JobResource` rompe la API pública y la web de `v0.2.0`,
   que es la release de portfolio ya publicada. Hay que decidir si `v1.0.0` mantiene el endpoint
   síncrono como modo degradado para la demo pública o si la demo se actualiza a la vez.
