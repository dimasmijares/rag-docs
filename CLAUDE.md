# Guía para Claude Code

Las instrucciones de agente canónicas están en @AGENTS.md (fuente de verdad KDD,
orquestación agentic, criterios de cierre). Léelas antes de seleccionar trabajo.

## Entorno

- Windows + PowerShell. Usa sintaxis PowerShell para los scripts `scripts/*.ps1`.
- Gestión de dependencias con `uv` (Python 3.11). No edites `uv.lock` a mano.
- Servicios externos locales: Qdrant (`docker compose up -d qdrant`) y Ollama
  (`ollama serve`, modelo `qwen2.5:3b`).

## Servicios locales durante una tarea

Si una tarea necesita Qdrant u Ollama y no responden, arráncalos y continúa:
`docker compose up -d qdrant`, `ollama serve` en segundo plano y `ollama pull <modelo>`
si falta el modelo declarado. Detente y avísame solo si el arranque falla, Docker u
Ollama no están instalados, o el modelo requerido no puede descargarse. Nunca simules
resultados de un servicio que no está disponible.

## Comandos frecuentes

```powershell
uv sync --extra dev              # instalar dependencias bloqueadas
uv run --no-sync pytest          # tests
uv run --no-sync ruff check .    # estilo
./scripts/kdd.ps1 validate       # validar grafo KDD
./scripts/kdd.ps1 orphans
./scripts/kdd.ps1 context -Id WRK-TASK-000
./scripts/verify.ps1             # puerta completa (KDD + estilo + tests + seguridad)
```

Antes de abrir PR, `./scripts/verify.ps1` debe estar verde. Los mismos gates corren
en CI (`.github/workflows/quality-gates.yml`): KDD, ruff, pytest, public-safety y
dependency-review.

## Trabajo gobernado por specs

- `specs/**` es la fuente de verdad. Cada WRK-TASK declara File Scope, Acceptance
  Criteria y Evidence; mantén los cambios dentro de ese scope y completa Evidence al
  cerrar.
- Protocolo de iteración: `specs/documentation/DOC-RAG-002-platform-operations.md`.
- Rama y PR por tarea: `codex/wrk-task-NNN-slug` (convención heredada, se mantiene).
- No versiones documentos ni derivados privados; el gate `public-safety` los rechaza.

## Modelo y esfuerzo sugeridos

- Tareas de release y decisiones de arquitectura (ADR/RFC): sesión con razonamiento
  alto y revisión cuidadosa.
- Análisis read-only de varios ficheros o specs en paralelo: subagentes `Explore`.
  El agente primario mantiene síntesis, edición de ficheros compartidos, integración
  y validación final.
