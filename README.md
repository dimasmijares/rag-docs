# rag-docs

PoC local de RAG documental para consultar PDF, DOCX, PPTX, XLSX, TXT y Markdown con respuestas grounded y fuentes localizables. El desarrollo está gobernado por KDD: conocimiento persistente, trabajo trazable y decisiones enlazadas en `specs/`.

Release actual: **v0.3.0** — invariantes de índice reforzados (fingerprint con migración y
rollback, ámbito de autorización obligatorio, ACL sin recalcular embeddings) y calidad de
retrieval medida con evidencia reproducible (hybrid, reranking) sobre la baseline pública de
`v0.2.0`.

## Arquitectura

```text
Web estática → FastAPI → QueryService → Qdrant → contexto → Ollama
                     ↘ IndexingService → fuentes → extractores → chunks → embeddings
```

- Los documentos, embeddings e índice permanecen en el portátil. Por defecto también lo
  hacen consultas y contexto; un endpoint Ollama remoto sólo se configura explícitamente.
- Qdrant escucha solo en `127.0.0.1:6333`.
- El modelo de embeddings se carga bajo demanda en CPU.
- Una respuesta sin evidencia suficiente no invoca conocimiento general.

## Privacidad

- El repositorio público sólo contiene corpus, gold sets, configuración y resultados
  **sintéticos**. El gate `public-safety` (local y en CI) rechaza rutas privadas, IPs internas,
  rutas personales de Windows e identificadores derivados conocidos antes de cada commit.
- La documentación corporativa se coloca en `examples/corporate/` (ignorado por Git) o en otra
  carpeta fuera del árbol; nunca se versiona.
- Todo el procesamiento —extracción, chunking, embeddings, índice, recuperación y generación— es
  local. Sólo un perfil Ollama remoto declarado de forma explícita envía pregunta y fragmentos por
  HTTP a otro equipo autorizado.

## Requisitos

- Python 3.11
- Docker Desktop para Qdrant
- Ollama para generación local o en otro equipo autorizado de la red

La validación del grafo KDD la realiza un CLI propio del repositorio
(`scripts/kdd_graph.py`), sin submódulos ni Node.js. El directorio `.kdd/` es una
copia local opcional del framework original y está ignorada por Git.

## Instalación

```powershell
uv sync --extra dev
uv run python scripts/generate_demo_corpus.py
Copy-Item .env.example .env
```

El generador acepta `--output-dir <ruta>` y produce siempre los mismos bytes junto con
`examples/corpus/demo/manifest.sha256`. Usa `--check` para contrastar el corpus versionado sin
modificarlo.

Instala Ollama y descarga el baseline:

```powershell
ollama pull qwen2.5:3b
```

## Demo reproducible desde un clon limpio

`scripts/demo.ps1` ejecuta el flujo verificable de `v0.2.0`: instala dependencias bloqueadas,
contrasta el corpus sintético contra su manifiesto, valida los artefactos de benchmark y comprueba
si Qdrant y Ollama están disponibles.

```powershell
./scripts/demo.ps1            # comprobación reproducible sin servicios
./scripts/demo.ps1 -Serve     # además arranca Qdrant y la API en http://127.0.0.1:8000
```

El paso manual equivalente es `uv sync --extra dev`, luego
`uv run python scripts/generate_demo_corpus.py --check`, `uv run rag-docs-benchmark verify` y la
ejecución híbrida de abajo.

## Ejecución híbrida recomendada

Inicia Docker Desktop y después:

```powershell
docker compose up -d qdrant
ollama serve
uv run rag-docs
```

Abre `http://127.0.0.1:8000`, pulsa **Indexar fuentes** y formula una pregunta. La documentación interactiva de la API está en `http://127.0.0.1:8000/docs`.

Para contenerizar también la aplicación:

```powershell
docker compose --profile full up --build
```

## Fuentes documentales

`config/sources.yaml` admite varias fuentes `local_folder`. Las rutas relativas se resuelven respecto al propio YAML.

```yaml
sources:
  - id: demo
    type: local_folder
    root: ../examples/corpus/demo
    include: ["**/*.pdf", "**/*.docx", "**/*.pptx", "**/*.xlsx", "**/*.txt", "**/*.md"]
    exclude: ["**/~$*", "**/.*/**"]
```

Coloca documentación autorizada en `examples/corporate/` o apunta a otra carpeta; ese directorio está ignorado por Git. No incluyas secretos ni documentos corporativos en commits.

## API

- `GET /api/sources`: configuración y disponibilidad de raíces.
- `POST /api/index`: sincronización incremental; acepta opcionalmente `{"source_ids": ["demo"]}`.
- `POST /api/query`: `{"question": "¿Qué ETL carga clientes?"}`.

La consulta devuelve `answer_status`, `answer`, `citations`, `model` y `embedding_model`. Cada cita incluye ruta/URI, fragmento, score, sección y localizador específico del formato.

También devuelve `claims`, `answer_language` y `generation_mode` para auditar afirmaciones,
idioma y si intervino el LLM o el fallback extractivo.

## Ollama en otro PC

El generador se puede mover a otro equipo sin copiar Qdrant, documentos, embeddings ni la
aplicación. Los scripts de [transfer/ollama-remote](transfer/ollama-remote) ayudan a configurar el
servidor Windows y una regla de firewall limitada al portátil; el ZIP de transferencia se genera
localmente y no se versiona. Los perfiles autorizados se declaran en `.env`:

```dotenv
RAG_DOCS_OLLAMA_ACTIVE_PROFILE=local
RAG_DOCS_OLLAMA_LOCAL_URL=http://127.0.0.1:11434
RAG_DOCS_OLLAMA_LOCAL_MODEL=qwen2.5:3b
RAG_DOCS_OLLAMA_REMOTE_URL=http://IP_DEL_PC:11434
RAG_DOCS_OLLAMA_REMOTE_MODEL=qwen2.5:3b
RAG_DOCS_OLLAMA_TIMEOUT=180
RAG_DOCS_OLLAMA_TEMPERATURE=0
RAG_DOCS_OLLAMA_SEED=0
```

La web muestra el perfil activo, endpoint y modelo. **Comprobar** consulta los modelos instalados
en el endpoint sin cambiar el activo y habilita el selector de modelo. Tras elegir uno,
**Usar esta configuración** aplica perfil y modelo a las consultas siguientes. Sólo se pueden
activar nombres anunciados por ese Ollama; un nombre desconocido no altera el generador activo.
El cambio es en memoria y al reiniciar vuelve la configuración inicial de `.env`.

Cambiar sólo el generador no exige reindexar. La pregunta y los fragmentos recuperados sí viajan
al servidor remoto por HTTP: se usará corpus didáctico salvo autorización expresa para contenido
corporativo. En una red corporativa, esta conexión requerirá cifrado/autenticación o un gateway
aprobado.

## KDD y calidad

Antes de trabajar en una tarea:

```powershell
./scripts/kdd.ps1 validate
./scripts/kdd.ps1 orphans
./scripts/kdd.ps1 context -Id WRK-TASK-003
```

Puerta completa:

```powershell
./scripts/verify.ps1
```

Los specs viven en `specs/`. Las decisiones nuevas se registran como ADR; cambios transversales requieren RFC. Al cerrar un trabajo se actualizan evidencia, trazabilidad y confianza.

El roadmap completo desde la PoC hasta los ocho servicios en Kubernetes está gobernado por
`WRK-SPEC-004` y sus planes de release `WRK-PLAN-005` a `011`.

## Índice: fingerprint, ámbito y comparabilidad

**Fingerprint del índice (`RULE-004`).** `IndexFingerprint` (`rag_docs.contracts`) cubre extractor,
chunker, `chunk_tokens`/`chunk_overlap`, modelo y revisión de embeddings, dimensión, normalización,
prefijos `query:`/`passage:` y la versión del esquema de payload. Su hash deriva el nombre físico de
la colección de Qdrant; el nombre lógico configurado (`RAG_DOCS_QDRANT_COLLECTION`) es un alias que
apunta a esa colección física. Escribir o consultar con un proceso cuyo fingerprint vinculado ya no
coincide con el que resuelve el alias falla de forma explícita — nunca se sirve un resultado
plausible sobre vectores incompatibles. Cambiar de configuración (modelo de embeddings, tamaño de
chunk) requiere una migración explícita: `rag_docs.indexing.migrate_and_publish` construye la
colección candidata fuera de línea, la valida contra un callback (típicamente un gold set) y sólo
entonces mueve el alias; la colección anterior no se borra, así que
`QdrantVectorStore.rollback_alias` puede restaurarla durante la ventana que decida el operador.
`scripts/migration_drill.py` ejecuta este ciclo completo (migración, verificación de que una
vinculación de fingerprint desactualizada rechaza la consulta, y rollback) contra el corpus
sintético, sin Docker.

**Ámbito obligatorio (`RULE-003`, `ADR-RAG-009`).** `VectorStorePort.search`/`scan_chunks` exigen un
`Scope` (`tenant`, `subjects`, `classification`) sin valor por defecto: no existe una ruta de
consulta que omita el prefiltrado de autorización. `AuthorizationPort.resolve_scope` lo resuelve por
petición; `v0.3.0` implementa `SingleTenantAuthorization`, que siempre exige el mismo ámbito
single-tenant, y `v1.5.0` puede sustituirla sin tocar `QueryService`. Cada chunk indexado lleva
`tenant_id`/`acl_subjects`/`classification` como payload filtrable (con índices `KEYWORD` en
Qdrant); `VectorStore.update_acl` cambia esos campos sin recalcular embeddings ni tocar el vector.

**Política de comparabilidad (`ADR-RAG-011`, `WRK-TASK-086`).** Todo informe de evaluación o
benchmark declara `corpus_version`, `index_fingerprint` y la configuración efectiva.
`evaluation/corpus-compatibility.yaml` fija qué fingerprints son compatibles con qué gold sets;
`benchmark.py compare` (`compare_reports`) rechaza comparar dos informes cuya tripleta
corpus/fingerprint difiera, salvo que se declare `--rebaseline` explícitamente. Bajo esta misma
política, una técnica de retrieval nueva sólo se adopta como valor por defecto si supera la baseline
con evidencia reproducible sobre un gold set de validación no usado para ajustar (`RFC-001`, gate
G2): `WRK-TASK-037` midió hybrid retrieval (BM25 + fusión por rango) y lo dejó implementado pero
**no** por defecto (regresión en `recall_at_8` de validación); `WRK-TASK-038`/`ADR-RAG-012` midió
reranking por cross-encoder y lo dejó disponible como capacidad opt-in
(`RAG_DOCS_RERANKER_MODEL`) — mejora limpia y sin regresiones en validación, pero no forzada por
defecto para no cambiar el comportamiento de un despliegue existente sin que el operador lo pida. El
informe consolidado que compara los tres perfiles (`dense`, `hybrid`, reranking) sobre el mismo
fingerprint vive en `evaluation/benchmarks/wrk-task-091/`.

## Evaluación

Con API, Qdrant, Ollama e índice activos:

```powershell
uv run rag-docs-eval --gold evaluation/gold-set.yaml
```

El informe se escribe en `logs/` y separa estado, retrieval, hechos, idioma y citas; también
registra latencia por caso, p50/p95 y errores. No usa otro LLM como juez.

`gold-set.yaml` es el smoke set compatible. Para desarrollo y validación separada están
`gold-set.dev.yaml` (16 casos) y `gold-set.validation.yaml` (8 casos); ambos usan exclusivamente
el corpus sintético `0.2.0`, declaran hechos objetivo y localizadores verificables, y no comparten
IDs, preguntas, hechos objetivo ni grupos de equivalencia.

### Benchmark local reproducible

El benchmark de `WRK-TASK-027` se ejecuta directamente contra Qdrant en memoria: no requiere
Docker ni una API activa, pero sí Ollama local con el modelo exacto declarado en
`config/benchmark.yaml`. El runner rechaza endpoints no loopback, fuentes distintas del corpus
`demo`, cambios de hashes y modelos que no sean el 3B bloqueado por digest.

La ejecución canónica tiene tres pasos ordenados. `development` compara los dos perfiles 3B y el
control de fallback extractivo; `lock` selecciona sólo entre perfiles 3B elegibles usando score,
Recall@8 y p95; `validation` acepta ese lock, ejecuta exclusivamente el perfil elegido y no
sobrescribe un resultado existente:

```powershell
uv run rag-docs-benchmark development
uv run rag-docs-benchmark lock
uv run rag-docs-benchmark validation
uv run rag-docs-benchmark verify
```

No se debe borrar ni regenerar `validation-results.json` para ajustar la selección. En un clon
limpio se instalan las dependencias bloqueadas, se descarga el modelo Ollama indicado, se ejecuta
`python scripts/generate_demo_corpus.py --check` y después `rag-docs-benchmark verify`; una nueva
medición sobre desarrollo puede ejecutarse en otra ruta, pero no sustituye la evidencia canónica.

Cada perfil recrea índice y embedder. El primer caso se etiqueta `cold` después de desalojar el
modelo de Ollama; los restantes son `warm` en el mismo proceso. Esto controla residencia del
modelo, pero no vacía la caché de disco del sistema operativo. `embedding` mide `embed_query`,
`retrieval` mide la búsqueda vectorial, `generation` suma llamadas al modelo y `grounding` es el
residuo local de selección, contexto, validación, render y fallback. La memoria registra pico RSS
del proceso Python, pico de RAM usada en el host y residencia/VRAM publicada por Ollama; no es una
medición aislada de consumo energético. Los p50/p95 son descriptivos para 16 casos de desarrollo y
8 de validación y pueden variar con carga, temperatura y política de energía.

Los JSON públicos sólo contienen IDs sintéticos, métricas, códigos de error, configuración y
hardware saneado. No guardan preguntas, respuestas, prompts, fragmentos, rutas absolutas,
hostname, usuario, PID ni direcciones de red. El benchmark 14B remoto queda diferido a
`WRK-TASK-081` y no forma parte de esta baseline.

Los artefactos canónicos viven en `evaluation/benchmarks/wrk-task-027/`
(`dev-results.json`, `decision-lock.json`, `validation-results.json`).

**Resultado (baseline v0.2.0).** El perfil recomendado es `qwen-3b-balanced`
(`intfloat/multilingual-e5-small`, `retrieval_top_k` 8, 5 chunks de contexto, `min_score` 0.45,
`qwen2.5:3b` Q4_K_M, `temperature` 0, `seed` 0). En desarrollo obtiene 13/16 y en la confirmación
de validación 4/8, siempre con Recall@8 = 1.0: la recuperación no es el cuello de botella y todos
los fallos restantes se atribuyen a la generación del modelo 3B. La generación domina la latencia
(p50 ≈ 35 s, p95 ≈ 50–69 s en el hardware registrado) frente a embedding, retrieval y grounding,
que suman decenas de milisegundos. El salto de calidad esperable con un 14B se medirá en
`WRK-TASK-081` sobre el PC personal.

## Problemas comunes

- **Qdrant no conecta**: inicia Docker Desktop y comprueba `docker compose ps`.
- **Ollama no conecta**: ejecuta `ollama serve` y verifica que el modelo exista con `ollama list`.
- **Primera consulta lenta**: la primera indexación descarga/carga el modelo de embeddings; la generación en CPU también puede tardar.
- **Fuente no disponible**: revisa la ruta resuelta mostrada por `GET /api/sources`.
- **Umbral demasiado estricto**: ajusta `RAG_DOCS_MIN_SCORE` usando primero los resultados del gold set.

## Licencia

Este proyecto se distribuye bajo [Apache License 2.0](LICENSE).
