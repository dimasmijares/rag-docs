---
id: ADR-RAG-010
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
  - id: ADR-002
    relation: depends-on
  - id: ARCH-002
    relation: implements
  - id: WRK-SPEC-010
    relation: constrained-by
  - id: RULE-003
    relation: constrained-by
  - id: RULE-004
    relation: constrained-by
tags: [architecture-decision, contracts, ports, boundaries, microservices, review]
---

# ADR-RAG-010 — Puertos internos a estabilizar en el monolito

## Context

`ARCH-002` ya establece el principio correcto: «cada límite debe existir primero como contrato
interno». `WRK-TASK-057` fija esos contratos, pero está programada en `v2.5.0`, es decir, después de
que cinco releases de código se hayan escrito sin ellos. Un contrato que se escribe el día de la
extracción no es un contrato: es la documentación de lo que salió.

La pregunta operativa es: qué interfaces deben congelarse **ya** para que la extracción de `v2.5.0`
sea mecánica en lugar de una reescritura.

Lo que hoy existe y funciona como puerto, aunque no esté nombrado así:

- `Embedder` (Protocol) — limpio, sin estado, orientado a lote. Casi listo.
- `Generator` con `capabilities()`, `health()` y `model_name` — el mejor puerto del repositorio;
  `generator_profiles.py` ya lo conmuta entre local y remoto en caliente, que es exactamente el
  comportamiento de un gateway.
- `VectorStore` (Protocol) — bien delimitado, pero su firma de `search()` no admite ámbito de
  autorización (`ADR-RAG-009`) ni fingerprint (`RULE-004`).
- `DocumentSource` — puerto de conector, base de `WRK-TASK-050`.
- `ApplicationContainer` — raíz de composición explícita. Es lo que hace la extracción viable.

Lo que no existe como puerto y es el riesgo principal: `QueryService` tiene 576 líneas y mezcla, en
una sola clase, selección y deduplicación de hits, priorización heurística por pregunta técnica,
construcción de contexto y citas, prompting, validación de grounding, fallback extractivo,
detección de idioma y diagnóstico de retrieval. En `ARCH-002` eso son tres servicios distintos
(`retrieval-service`, `context-grounding-service`, `query-api`). **Es aquí donde `v2.5.0` se
convierte en reescritura, no en los servicios de infraestructura.**

## Options Considered

1. **Dejar `WRK-TASK-057` donde está.** Cero coste ahora; la deuda se paga entera en `v2.5.0` sobre
   código que para entonces tendrá streaming, ACL, multimodal y observabilidad enredados en las
   mismas funciones.
2. **Adelantar `WRK-TASK-057` completa** con contratos HTTP `/v1`, versionado y contract tests
   antes de que exista ningún servicio. Congela decisiones de nivel de transporte sin información y
   produce contratos ceremoniales.
3. **Adelantar sólo los puertos en proceso y los objetos de valor compartidos**, dejando en `v2.5.0`
   el nivel HTTP, la autenticación entre servicios y los contract tests de red. Los puertos son
   Protocols de Python sobre DTO puros, sin dependencias de I/O.

## Decision

Se adopta la opción 3. Se crea un paquete `rag_docs.contracts` sin dependencias de infraestructura
que contiene objetos de valor y puertos, y del que dependen tanto el monolito hoy como los
servicios de `v2.5.0` mañana.

**Objetos de valor a congelar ya** (el orden importa: son transversales a todos los puertos):

- `IndexFingerprint` — extractor, chunker con sus parámetros, modelo de embeddings con revisión,
  dimensión, normalización y convención de prefijos. Hoy los prefijos `passage:` y `query:` de e5
  están incrustados en `SentenceTransformerEmbedder` y `chunk_tokens`/`chunk_overlap` son enteros
  sueltos en `Settings`: ninguno de los dos es observable desde fuera, que es justo lo que
  `RULE-004` necesita.
- `Scope` — tenant, conjunto de sujetos expandido, clasificaciones, versión (`ADR-RAG-009`).
- `ErrorKind` — taxonomía cerrada: validación, autorización, no encontrado, dependencia no
  disponible, tiempo agotado, salida inválida del modelo. Es la que después mapea a códigos HTTP;
  hoy `api.py` colapsa casi todo en `503` con el texto de la excepción, lo que además filtra
  detalles internos al cliente.
- `CorrelationId` e `IdempotencyKey` — atraviesan API, jobs y llamadas (`ADR-RAG-008`).
- Los DTO ya existentes (`DocumentChunk`, `SearchHit`, `Citation`, `AnswerClaim`, `QueryResult`,
  `IndexReport`, y el `JobResource` de `v1.0.0`) se mueven a `contracts` y se les fija política de
  compatibilidad: campos aditivos, nunca renombrados ni con semántica cambiada en sitio.

**Puertos a congelar ya, y la decisión de diseño que cada uno cierra:**

1. `EmbeddingPort` (futuro `embedding-service`). Ya existe como `Embedder`. Se le añade
   `fingerprint` y semántica explícita de lote y de error. Sin estado, orientado a lote: mapea a
   HTTP sin cambios.
2. `GenerationPort` (futuro `model-gateway`). Ya existe como `Generator`. **Se le añade ahora la
   variante de streaming y la contabilidad de tokens y latencia**, aunque no se implementen hasta
   `WRK-TASK-041`. Si no, streaming fuerza un cambio de firma después de la extracción, que es el
   caso caro.
3. `RetrievalPort` (futuro `retrieval-service`). Decisión de diseño que hay que cerrar ahora, no en
   `v2.5.0`: **retrieval recibe texto de pregunta y `Scope`, y es él quien embebe la consulta**
   llamando a `EmbeddingPort`. La alternativa —que el llamante embeba y pase el vector— obliga a
   mover vectores por la red en cada consulta y filtra el detalle del modelo al `query-api`. Firma:
   `search(question, scope, k, threshold, fingerprint) -> list[SearchHit]`.
4. `AuthorizationPort` (futuro `authz-service`). `resolve_scope(principal) -> Scope`. En `v0.3.0` la
   implementación devuelve un `Scope` de un solo tenant; en `v1.5.0` se sustituye la implementación
   sin tocar a ningún llamante. Congelar la *forma* de `Scope` ahora es lo que hace posible eso.
5. `GroundingPort` (futuro `context-grounding-service`). **La refactorización urgente.** Se divide
   `QueryService` en tres piezas puras y una de orquestación:
   - `ContextBuilder`: hits más pregunta produce contexto y citas. Absorbe `_select_hits`,
     `_prioritize_context`, `_technical_evidence_hints` y la construcción de `Citation`.
   - `AnswerValidator`: respuesta generada más evidencia produce veredicto de grounding. Absorbe
     `_validation_errors` y el fallback extractivo.
   - `LanguagePolicy`: ya aislado en `language.py`.
   - `QueryService` queda como orquestador delgado sobre los cuatro puertos.
   Las tres piezas son funciones puras sobre DTO: testables de inmediato, extraíbles sin
   arqueología. Este cambio se justifica por sí solo aunque `v2.5.0` no llegue a ejecutarse nunca.
6. `JobPort` (frontera `index-api` a `index-worker`). `JobResource`, máquina de estados,
   `IdempotencyKey`. Se congela en `v1.0.0` con `WRK-TASK-030` y `031`; es además contrato público
   de la API.
7. `DocumentSourcePort` (futuro SDK de conectores, `WRK-TASK-050`). Ya existe como
   `DocumentSource`. Se le añade la señal de snapshot completo que exige `ADR-RAG-008` para poder
   borrar huérfanos con seguridad.

**Anti-frontera, explícita.** No se crea frontera de red donde la interacción es una llamada
síncrona 1:1 en la ruta de petición con ciclo de vida compartido y sin perfil de escalado propio.
Bajo ese criterio `query-api` y `context-grounding-service` son un solo desplegable, e `index-api`
vive con `query-api`. El contrato existe igualmente en proceso, de modo que la decisión es
reversible en cualquier momento con evidencia de `WRK-TASK-055`.

## Consequences

Positivas: la extracción de `v2.5.0` se reduce a implementar un adaptador HTTP por puerto ya
existente; `authz-service` puede aparecer sin tocar llamantes; la división de `QueryService` mejora
la testabilidad de la parte más compleja del sistema desde `v0.3.0`; la taxonomía de errores
elimina el patrón actual de responder `503` con el texto de la excepción.

Costes: `rag_docs.contracts` introduce una capa de indirección que en un monolito de 3000 líneas
parece innecesaria, y hay que resistir la tentación de meter lógica en ella. Congelar
`GenerationPort` con streaming antes de implementarlo es diseño especulativo acotado y consciente:
se acepta por el coste asimétrico de cambiar la firma después. Mover DTO a `contracts` toca casi
todos los módulos e imports a la vez, lo que produce un diff grande y un merge conflictivo si se
hace tarde; otra razón para hacerlo ahora.

## Work Impact

Aplicado en el grafo KDD:

- Creada `WRK-TASK-083` en `v0.3.0`: paquete `rag_docs.contracts`, objetos de valor, los seis
  puertos, prohibición de dependencias de I/O verificada por test y mapeo de `ErrorKind` en
  `api.py`, que hoy responde `503` con el texto de la excepción.
- Creada `WRK-TASK-090` en `v0.3.0`: división de `QueryService` en `ContextBuilder` y
  `AnswerValidator` puros, sin cambio de comportamiento observable, verificada contra los gold sets.
- `WRK-TASK-057` se reduce al transporte HTTP `/v1`, versionado, correlación entre procesos y
  contract tests de red, y depende de `WRK-TASK-083`.
- `WRK-TASK-036` produce `IndexFingerprint` como objeto de valor de `contracts`, no como detalle
  interno de un adaptador.
- `WRK-TASK-037` depende de `WRK-TASK-090`, para que la estrategia híbrida se escriba contra piezas
  ya separadas.
- `WRK-TASK-084` fija la señal de snapshot completo que `DocumentSourcePort` debe exponer.

## Human Checkpoint

**PARAR y validar antes de `WRK-TASK-083`** la decisión 3: si el `RetrievalPort` recibe pregunta o
recibe vector. Es la única de este ADR que no es reversible barata, porque determina qué proceso
carga el modelo de embeddings, dónde está el coste de CPU y qué cruza la red en cada consulta. Es
también la decisión que más condiciona `WRK-TASK-058` y `061`.

No hace falta parar para `WRK-TASK-090`: la división de `QueryService` es una refactorización sin
cambio de comportamiento, cubierta por los gold sets, y es beneficiosa con independencia del destino
del roadmap.
