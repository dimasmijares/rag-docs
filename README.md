# rag-docs

PoC local de RAG documental para consultar PDF, DOCX, PPTX, XLSX, TXT y Markdown con respuestas grounded y fuentes localizables. El desarrollo está gobernado por KDD: conocimiento persistente, trabajo trazable y decisiones enlazadas en `specs/`.

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

## Problemas comunes

- **Qdrant no conecta**: inicia Docker Desktop y comprueba `docker compose ps`.
- **Ollama no conecta**: ejecuta `ollama serve` y verifica que el modelo exista con `ollama list`.
- **Primera consulta lenta**: la primera indexación descarga/carga el modelo de embeddings; la generación en CPU también puede tardar.
- **Fuente no disponible**: revisa la ruta resuelta mostrada por `GET /api/sources`.
- **Umbral demasiado estricto**: ajusta `RAG_DOCS_MIN_SCORE` usando primero los resultados del gold set.

## Licencia

Este proyecto se distribuye bajo [Apache License 2.0](LICENSE).
