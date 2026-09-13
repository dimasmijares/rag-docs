[CmdletBinding()]
param(
    # fabric.env local (fuera del repo), el mismo que usa fabric/bootstrap.ps1.
    [Parameter(Mandatory)]
    [string]$EnvFile
)

# Gate opcional del perfil Fabric (WRK-TASK-100, DOC-RAG-003). Ejecuta la suite de contrato de
# VectorStore contra FabricSqlVectorStore autenticando como service principal con certificado.
# Nunca forma parte de scripts/verify.ps1 ni de CI: requiere capacidad Fabric y credenciales del
# operador. No imprime identificadores ni tokens.

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$withFabric = @('--no-sync', '--with', 'azure-identity', '--with', 'mssql-python')
$managed = @(
    'RAG_DOCS_FABRIC_SQL_SERVER', 'RAG_DOCS_FABRIC_SQL_DATABASE', 'RAG_DOCS_FABRIC_SQL_CREDENTIAL',
    'RAG_DOCS_FABRIC_TENANT_ID', 'RAG_DOCS_FABRIC_CLIENT_ID', 'RAG_DOCS_FABRIC_CLIENT_CERT_PATH',
    'RAG_DOCS_CONTRACT_LIVE_FACTORY'
)
$previous = @{}
foreach ($name in $managed) { $previous[$name] = [Environment]::GetEnvironmentVariable($name) }

Push-Location $projectRoot
try {
    uv run @withFabric python fabric/tools/fabric_api.py --env-file $EnvFile sql-connection --as sp
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo resolver la conexión de la SQL database.' }

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

    uv run @withFabric pytest tests/contract -m live -p no:cacheprovider
    if ($LASTEXITCODE -ne 0) { throw 'La suite de contrato falló contra Fabric SQL.' }
    Write-Host 'Gate Fabric superado: FabricSqlVectorStore cumple el contrato de VectorStore.'
}
finally {
    foreach ($name in $managed) { [Environment]::SetEnvironmentVariable($name, $previous[$name]) }
    Pop-Location
}
