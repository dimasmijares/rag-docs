---
id: ADR-RAG-009
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
  - id: ADR-004
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: FEAT-RAG-003
    relation: implements
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
  - id: WRK-SPEC-008
    relation: constrained-by
tags: [architecture-decision, acl, authorization, retrieval, cache, benchmark, review]
---

# ADR-RAG-009 — ACL por documento: prefiltrado en Qdrant y puntos fail-closed

## Context

`ADR-004` decide ACL por documento normalizadas a tenant, usuarios, grupos, clasificación e
herencia, y `RULE-003` exige autorización fail-closed antes de cualquier retrieval. Ninguno de los
dos fija la representación en el índice, el punto de aplicación del filtro, ni el efecto sobre
caché y métricas. Esas tres decisiones condicionan `WRK-TASK-046`, `047` y todo el benchmark, y son
muy caras de revertir una vez hay colecciones construidas.

Estado actual relevante:

- El payload del chunk (`DocumentChunk.payload()`) no tiene tenant, ni ACL, ni clasificación.
- `QueryService.query()` llama a `store.search(vector, limit, score_threshold)`; la firma **no
  admite** ningún ámbito de autorización, de modo que hoy no hay ningún punto donde un filtro pueda
  olvidarse: no existe. Cuando exista, la firma es el sitio donde se decide si olvidarlo es posible.
- `QueryResult.retrieval_diagnostics` publica, para cada hit recuperado, `document_id`,
  `relative_path`, `section`, `locator` y `score`, incluidos los descartados. Es el consumidor
  principal de `evaluation.py`.
- No hay caché de ningún tipo todavía. Es el momento barato de decidir su semántica.

## Options Considered

**Representación de la ACL en el índice:**

1. **Por referencia**: el payload guarda `acl_policy_id` y la política se evalúa fuera del índice.
   Mantiene una sola copia de la política y hace la revocación instantánea, pero obliga a
   post-filtrar o a una segunda llamada por hit.
2. **Denormalizada y aplanada**: el payload guarda `tenant_id`, el conjunto de sujetos autorizados
   ya expandido (usuarios y grupos) y la clasificación. Filtro de una sola pasada dentro del índice;
   coste: los cambios de pertenencia a grupo obligan a reescribir payloads.
3. **Colección por tenant**: aislamiento físico fuerte y trivial de auditar; coste operativo lineal
   en número de tenants y multiplicado por el número de fingerprints de `RULE-004`.

**Punto de aplicación:**

4. **Post-filtrado** tras recuperar `top_k`.
5. **Prefiltrado dentro de Qdrant** mediante `Filter` sobre payload con índices de payload.

## Decision

**Representación: opción 2, con el identificador de política conservado para auditoría.** Cada
chunk lleva en el payload:

- `tenant_id` — keyword único, obligatorio;
- `acl_subjects` — lista de identificadores opacos de sujeto (usuarios y grupos ya expandidos en
  tiempo de indexado, con la herencia ya normalizada);
- `classification` — keyword;
- `acl_policy_id` y `acl_version` — sólo para auditoría y reconciliación, nunca para decidir en la
  ruta de consulta.

Se descarta la opción 3 como modelo por defecto porque multiplica colecciones por tenant y por
fingerprint; queda disponible como refuerzo para tenants que exijan aislamiento físico.

**Punto de aplicación: opción 5, prefiltrado en Qdrant.** El post-filtrado se rechaza por dos
motivos, uno de calidad y otro de seguridad: pedir `top_k` y filtrar después convierte `k` en un
número variable y desconocido, destruyendo la semántica de `retrieval_top_k` y degradando recall de
forma invisible; y la diferencia entre lo pedido y lo devuelto es un canal lateral que revela la
densidad de documentos no autorizados para esa consulta. El filtro se construye como
`must: tenant_id == scope.tenant`, `must: acl_subjects any-of scope.subjects`,
`must: classification in scope.classifications`.

Requisito operativo derivado: hay que crear índices de payload de tipo keyword sobre `tenant_id`,
`acl_subjects` y `classification` antes de indexar. Sin ellos el filtro degrada a recorrido y la
latencia se dispara.

**Un cambio de ACL nunca puede reembeber.** Se exige una ruta de actualización de payload por
`document_id` (`set_payload` filtrado) independiente del pipeline de indexado. Es una restricción
de diseño para `WRK-TASK-043`: si la ACL forma parte de la identidad del chunk, revocar un permiso
cuesta una reindexación completa y la revocación deja de ser operable.

**Dónde exactamente es fail-closed.** Seis puntos, en este orden:

1. **Borde HTTP.** Sin token válido, `401` antes de tocar el contenedor de aplicación. Ninguna ruta
   de consulta o de indexado admite principal anónimo, incluido desarrollo, desde `v1.5.0`
   (`RULE-003` retira la excepción de la PoC en `WRK-TASK-046`).
2. **Resolución de ámbito.** Token válido pero sin claim de tenant, sin conjunto de sujetos
   resoluble, con política ambigua o con almacén de políticas no disponible: se deniega. La
   indisponibilidad del autorizador es denegación, no continuación con ámbito vacío ni con ámbito
   por defecto.
3. **Firma del puerto de búsqueda.** `search()` pasa a exigir un `Scope` como argumento obligatorio
   sin valor por defecto, y `Scope` sólo es construible por el resolutor de autorización. Omitir el
   filtro deja de ser un olvido en tiempo de ejecución y pasa a ser un error de tipos. Es la forma
   verificable del criterio de `WRK-TASK-046` de que ningún caller pueda omitir el filtro.
4. **Escritura.** Un documento cuya ACL no se puede normalizar **no se indexa**. Falla ese
   documento, no el job. Nunca se escribe un chunk con `acl_subjects` vacío, ni con tenant ausente,
   ni con una ACL «permisiva por defecto». Un chunk sin tenant y sin sujetos es inválido en
   escritura.
5. **Caché.** Ver más abajo.
6. **Diagnóstico y errores.** La denegación es indistinguible de la ausencia de evidencia: se
   responde con la semántica de `insufficient_evidence` y sin metadatos. No se devuelve un error que
   afirme que el documento existe pero está prohibido. Se distingue únicamente «no autenticado»
   (`401`, no revela nada) de «autenticado sin evidencia visible».

**Caché.** Regla general: nada posterior al retrieval se comparte entre principals.

- *Caché de embeddings de consulta*: clave `(texto, index_fingerprint)`. Es independiente del
  principal y seguro compartirlo; el vector de una pregunta no revela contenido indexado.
- *Caché de retrieval y de respuesta*: clave `(scope_hash, index_fingerprint, pregunta_normalizada,
  snapshot_de_configuración)`, donde `scope_hash` deriva del **conjunto de sujetos expandido** y de
  su versión, no del identificador de usuario. Dos usuarios con exactamente los mismos permisos
  comparten entrada legítimamente; un cambio de pertenencia invalida por versión.
- *Caché de prompt o de respuesta en `model-gateway`*: **prohibida entre principals**. El prompt
  contiene contenido recuperado; compartirlo es exfiltración con pasos extra. Si se activa, se
  particiona por `scope_hash`.

## Consequences

**Impacto en el benchmark y en las métricas** —esto es lo que hay que anticipar antes de publicar
comparaciones:

1. La búsqueda vectorial filtrada con HNSW se comporta distinto según la selectividad del filtro.
   Con filtros restrictivos el motor puede degradar a búsqueda exacta o recorrer más candidatos
   para llenar `top_k`. Cambian a la vez `recall_at_k`, `precision_at_k` y la latencia p95 que
   `evaluation.py` agrega. **Las cifras de `v0.2.0` dejan de ser comparables con las de `v1.5.0`.**
2. Por tanto el benchmark gana una dimensión: selectividad del filtro. Se publican como mínimo dos
   curvas, ámbito permisivo total y ámbito realista, para poder separar el coste de la autorización
   de cualquier otra regresión. Sin esa separación, una caída de calidad en `v1.5.0` es
   indiagnosticable.
3. Los gold sets adquieren dimensión de principal y tenant. Los actuales se ejecutan como
   `tenant=demo`, sujeto de evaluación con ámbito permisivo, para conservar la serie histórica.
4. `retrieval_diagnostics` pasa a ser información sujeta a autorización: revela rutas, secciones y
   existencia de documentos descartados. Debe filtrarse con el mismo ámbito que la respuesta y,
   para principals no privilegiados, reducirse o desactivarse. Esto rompe `evaluation.py`, que
   depende de ella, y obliga a introducir un principal de evaluación con permiso explícito de
   diagnóstico. Es una dependencia oculta entre seguridad y arsenal de medición que conviene
   resolver en el diseño, no en la integración.
5. La expansión de grupos en tiempo de indexado hace que `acl_subjects` pueda crecer mucho en
   corpus corporativos. Hay un tope práctico de tamaño de payload y de coste de filtro que debe
   medirse antes de `v2.0.0`.
6. Consecuencia ya prevista por `ADR-004`: las colecciones anteriores se reconstruyen. Combinado
   con `RULE-004`, introducir ACL es un cambio de fingerprint y por tanto una colección nueva con
   cambio atómico de alias.

## Work Impact

Aplicado en el grafo KDD:

- Creada `WRK-TASK-082` en `v0.3.0`: objeto de valor `Scope`, campos de payload, índices de payload,
  firma obligatoria de ámbito en la búsqueda, ruta de actualización de payload sin reembeber e
  implementación de un solo tenant sustituible sin tocar llamantes.
- `WRK-TASK-043` se reenfoca a propagación, herencia, revocación y reconstrucción, depende de `082`
  y gana el criterio de propagación acotada sin recalcular embeddings.
- `WRK-TASK-046` se reenfoca a la resolución real de política y a la retirada de la excepción
  transitoria de `RULE-003`; la garantía de tipos ya la aporta `082`.
- Creada `WRK-TASK-085` en `v1.5.0`: gold sets con dimensión de principal, curvas por selectividad,
  principal de evaluación con diagnóstico y re-baseline publicado. `WRK-TASK-049` depende de ella.
- `WRK-SPEC-008` gana el criterio de medir el coste de la autorización por separado.
- `WRK-TASK-014` incorpora la regla de particionado de caché por ámbito desde su diseño.

No se han creado tareas `043a`/`043b`: la división se resolvió reenfocando `043` y creando `082`,
que respeta la convención de identificadores del repositorio.

## Human Checkpoint

**PARAR y validar antes de `WRK-TASK-043`.** La denormalización de la ACL en el payload es la
decisión más cara de revertir de todo el roadmap: una vez hay colecciones construidas, cambiar de
modelo obliga a reindexar todo. Conviene validar con una persona, con un caso corporativo real
sobre la mesa, si la expansión de grupos en tiempo de indexado es aceptable para el volumen y la
volatilidad de grupos previstos, o si algún tenant exige colección física separada.

**PARAR también antes de retirar la excepción de desarrollo de `RULE-003`.** Es el momento en que
la demo pública deja de funcionar sin IdP; hay que decidir de forma consciente qué ve un visitante
del portfolio a partir de `v1.5.0`.
