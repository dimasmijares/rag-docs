<#
.SYNOPSIS
    Demo reproducible de rag-docs v0.2.0 desde un clon limpio.
.DESCRIPTION
    Instala las dependencias bloqueadas, contrasta el corpus sintetico contra su
    manifiesto SHA-256, valida los artefactos de benchmark de WRK-TASK-027 y
    comprueba la disponibilidad de Qdrant y Ollama. Con -Serve arranca ademas
    Qdrant y la API local. No versiona ni descarga datos no sinteticos.
#>
[CmdletBinding()]
param(
    [switch]$Serve
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    Write-Host '== rag-docs demo (v0.2.0) ==' -ForegroundColor Cyan

    Write-Host '-> uv sync --extra dev'
    uv sync --extra dev
    if ($LASTEXITCODE -ne 0) { throw 'uv sync fallo' }

    Write-Host '-> corpus sintetico (--check)'
    uv run --no-sync python scripts/generate_demo_corpus.py --check
    if ($LASTEXITCODE -ne 0) { throw 'El corpus no coincide con el manifiesto' }

    Write-Host '-> artefactos de benchmark (rag-docs-benchmark verify)'
    uv run --no-sync rag-docs-benchmark verify
    if ($LASTEXITCODE -ne 0) { throw 'Los artefactos de benchmark no son validos' }

    $qdrantUp = $false
    try {
        Invoke-RestMethod -Uri 'http://127.0.0.1:6333/healthz' -TimeoutSec 3 | Out-Null
        $qdrantUp = $true
    } catch { }
    $ollamaUp = $false
    try {
        Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 | Out-Null
        $ollamaUp = $true
    } catch { }
    Write-Host ("Qdrant local  : {0}" -f ($(if ($qdrantUp) { 'disponible' } else { 'no responde' })))
    Write-Host ("Ollama local  : {0}" -f ($(if ($ollamaUp) { 'disponible' } else { 'no responde' })))

    if (-not $Serve) {
        Write-Host ''
        Write-Host 'Comprobacion reproducible superada.' -ForegroundColor Green
        Write-Host 'Para la demo interactiva: docker compose up -d qdrant; ollama serve; uv run rag-docs'
        return
    }

    if (-not $ollamaUp) {
        throw 'Ollama no responde en 127.0.0.1:11434. Ejecuta "ollama serve" y "ollama pull qwen2.5:3b".'
    }
    Write-Host '-> docker compose up -d qdrant'
    docker compose up -d qdrant
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo arrancar Qdrant (Docker Desktop)' }

    Write-Host '-> uv run rag-docs (Ctrl+C para parar)'
    Write-Host 'Abre http://127.0.0.1:8000, pulsa "Indexar fuentes" y formula una pregunta.'
    uv run --no-sync rag-docs
}
finally {
    Pop-Location
}
