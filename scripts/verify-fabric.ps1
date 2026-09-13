[CmdletBinding()]
param(
    # fabric.env local (fuera del repo), el mismo que usa fabric/bootstrap.ps1.
    [Parameter(Mandatory)]
    [string]$EnvFile,
    # Además de la suite de contrato: publica el índice local, ejecuta el drill de migración en
    # SQL y evalúa la API local servida desde Fabric con Ollama (WRK-TASK-101).
    [switch]$WalkingSkeleton,
    [int]$ApiPort = 8765
)

# Gate opcional del perfil Fabric (WRK-TASK-100/101, DOC-RAG-003). Autentica como service
# principal con certificado. Nunca forma parte de scripts/verify.ps1 ni de CI: requiere capacidad
# Fabric y credenciales del operador. No imprime identificadores ni tokens.

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$withFabric = @('--no-sync', '--with', 'azure-identity', '--with', 'mssql-python')
$managed = @(
    'RAG_DOCS_FABRIC_SQL_SERVER', 'RAG_DOCS_FABRIC_SQL_DATABASE', 'RAG_DOCS_FABRIC_SQL_CREDENTIAL',
    'RAG_DOCS_FABRIC_TENANT_ID', 'RAG_DOCS_FABRIC_CLIENT_ID', 'RAG_DOCS_FABRIC_CLIENT_CERT_PATH',
    'RAG_DOCS_CONTRACT_LIVE_FACTORY', 'RAG_DOCS_VECTOR_BACKEND'
)
$previous = @{}
foreach ($name in $managed) { $previous[$name] = [Environment]::GetEnvironmentVariable($name) }

function Invoke-Checked([string]$Description, [scriptblock]$Command) {
    # Avisos por stderr (p. ej. del Hub de modelos) no son fallos: decide el código de salida.
    $ErrorActionPreference = 'Continue'
    & $Command 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "$Description falló." }
}

Push-Location $projectRoot
$api = $null
try {
    Invoke-Checked 'La resolución de la conexión SQL' {
        uv run @withFabric python fabric/tools/fabric_api.py --env-file $EnvFile sql-connection --as sp
    }

    $config = @{}
    foreach ($line in Get-Content -LiteralPath $EnvFile) {
        if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $config[$Matches[1]] = $Matches[2].Trim() }
    }
    $env:RAG_DOCS_FABRIC_SQL_SERVER = $config.FABRIC_SQL_SERVER
    $env:RAG_DOCS_FABRIC_SQL_DATABASE = $config.FABRIC_SQL_DATABASE
    $env:RAG_DOCS_FABRIC_SQL_CREDENTIAL = 'certificate'
    $env:RAG_DOCS_FABRIC_TENANT_ID = $config.FABRIC_TENANT_ID
    $env:RAG_DOCS_FABRIC_CLIENT_ID = $config.FABRIC_CLIENT_ID
    $env:RAG_DOCS_FABRIC_CLIENT_CERT_PATH = $config.FABRIC_CLIENT_CERT_PATH
    $env:RAG_DOCS_CONTRACT_LIVE_FACTORY = 'rag_docs.fabric_sql_store:contract_store'

    Invoke-Checked 'La suite de contrato contra Fabric SQL' {
        uv run @withFabric pytest tests/contract -m live -p no:cacheprovider
    }
    Write-Host 'Contrato superado: FabricSqlVectorStore cumple el contrato de VectorStore.'

    if ($WalkingSkeleton) {
        Invoke-Checked 'La publicación del índice local en Fabric' {
            uv run @withFabric python scripts/publish_index_to_fabric.py
        }
        Invoke-Checked 'El drill de migración y rollback en Fabric SQL' {
            uv run @withFabric python scripts/migration_drill.py --backend fabric_sql
        }

        $env:RAG_DOCS_VECTOR_BACKEND = 'fabric_sql'
        $logDir = Join-Path $projectRoot '_build/verify-fabric'
        New-Item -ItemType Directory -Force $logDir | Out-Null
        $api = Start-Process -FilePath 'uv' -PassThru -NoNewWindow `
            -RedirectStandardOutput (Join-Path $logDir 'api.out.log') `
            -RedirectStandardError (Join-Path $logDir 'api.err.log') `
            -ArgumentList (@('run') + $withFabric + @(
                'uvicorn', 'rag_docs.api:app', '--host', '127.0.0.1', '--port', "$ApiPort"))
        $baseUrl = "http://127.0.0.1:$ApiPort"
        $sources = $null
        for ($attempt = 0; $attempt -lt 60 -and -not $sources; $attempt++) {
            Start-Sleep -Seconds 5
            try { $sources = Invoke-RestMethod "$baseUrl/api/sources" -TimeoutSec 60 } catch { }
        }
        if (-not $sources) { throw "La API local no arrancó (ver $logDir)." }
        if ($sources.vector_backend -ne 'fabric_sql') { throw 'La API no sirve el backend Fabric.' }
        Write-Host "API sobre Fabric SQL; fingerprint vigente $($sources.index_fingerprint.digest)."

        $report = Join-Path $logDir 'evaluation-fabric.json'
        Invoke-Checked 'La evaluación smoke contra la API servida desde Fabric' {
            uv run @withFabric rag-docs-eval --base-url $baseUrl --output $report
        }
        Write-Host 'Walking skeleton superado: consulta grounded con citas desde Fabric SQL.'
    }
}
finally {
    if ($api) { taskkill /PID $api.Id /T /F 2>&1 | Out-Null }
    foreach ($name in $managed) { [Environment]::SetEnvironmentVariable($name, $previous[$name]) }
    Pop-Location
}
