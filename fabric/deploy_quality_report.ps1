[CmdletBinding()]
param(
    [string]$WorkspaceName = 'rag-docs',
    [string]$LakehouseName = 'ragdocs_eval'
)

# Despliegue del informe Power BI de calidad (WRK-TASK-103, DOC-RAG-003). Requiere `fab` con sesión.
# El PBIP versionado en fabric/ no contiene identificadores del entorno:
# - ragdocs_quality.SemanticModel usa marcadores #{SQL_ENDPOINT_HOST}# y #{SQL_ENDPOINT_ID}# para el
#   SQL analytics endpoint del Lakehouse sobre el que opera en Direct Lake;
# - ragdocs_quality.Report referencia el modelo por ruta (byPath), válido en Power BI Desktop.
# Este script resuelve esos valores con `fab get`, los sustituye en una copia bajo _build/ (ignorado
# por Git), importa modelo e informe, reencuadra el modelo (refresh) y valida con una consulta DAX.

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Invoke-Fab {
    $ErrorActionPreference = 'Continue'
    $output = (& fab @args 2>&1 | ForEach-Object { "$_" }) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "fab $($args[0]) falló: $output" }
    return $output.Trim()
}

$workspace = "$WorkspaceName.Workspace"
$lakehouse = "$workspace/$LakehouseName.Lakehouse"
$stage = Join-Path $repoRoot '_build/quality-deploy'
if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
New-Item -ItemType Directory -Force $stage | Out-Null

$endpointHost = Invoke-Fab get $lakehouse -q properties.sqlEndpointProperties.connectionString
$endpointId = Invoke-Fab get $lakehouse -q properties.sqlEndpointProperties.id
if (-not $endpointHost -or -not $endpointId) { throw 'El Lakehouse no expone su SQL analytics endpoint.' }

Copy-Item -Recurse (Join-Path $PSScriptRoot 'ragdocs_quality.SemanticModel') $stage
$expressions = Join-Path $stage 'ragdocs_quality.SemanticModel/definition/expressions.tmdl'
$text = [System.IO.File]::ReadAllText($expressions).
    Replace('#{SQL_ENDPOINT_HOST}#', $endpointHost).Replace('#{SQL_ENDPOINT_ID}#', $endpointId)
[System.IO.File]::WriteAllText($expressions, $text, $utf8)
Invoke-Fab import "$workspace/ragdocs_quality.SemanticModel" -i (Join-Path $stage 'ragdocs_quality.SemanticModel') -f | Out-Null
Write-Host 'Modelo semántico importado (Direct Lake).'

$workspaceId = Invoke-Fab get $workspace -q id
$modelId = Invoke-Fab get "$workspace/ragdocs_quality.SemanticModel" -q id

Copy-Item -Recurse (Join-Path $PSScriptRoot 'ragdocs_quality.Report') $stage
$reference = [ordered]@{
    version = '4.0'
    datasetReference = [ordered]@{
        byConnection = [ordered]@{
            connectionString = "Data Source=`"powerbi://api.powerbi.com/v1.0/myorg/$WorkspaceName`";" +
                "initial catalog=ragdocs_quality;access mode=readonly;integrated security=ClaimsToken;" +
                "semanticmodelid=$modelId"
            pbiServiceModelId = $null
            pbiModelVirtualServerName = 'sobe_wowvirtualserver'
            pbiModelDatabaseName = $modelId
            name = 'EntityDataSource'
            connectionType = 'pbiServiceXmlaStyleLive'
        }
    }
}
[System.IO.File]::WriteAllText((Join-Path $stage 'ragdocs_quality.Report/definition.pbir'),
    ($reference | ConvertTo-Json -Depth 5), $utf8)
Invoke-Fab import "$workspace/ragdocs_quality.Report" -i (Join-Path $stage 'ragdocs_quality.Report') -f | Out-Null
Write-Host 'Informe importado.'

$refresh = Join-Path $stage 'refresh.json'
[System.IO.File]::WriteAllText($refresh, '{"type":"full"}', $utf8)
Invoke-Fab api -A powerbi -X post "groups/$workspaceId/datasets/$modelId/refreshes" -i $refresh | Out-Null

$query = Join-Path $stage 'query.json'
$dax = 'EVALUATE SUMMARIZECOLUMNS(evaluation_profiles[vector_backend], ' +
    'evaluation_profiles[corpus_version], evaluation_profiles[index_fingerprint_digest], ' +
    '"Perfiles", [Perfiles], "Recall8", [Recall@8], "MRR", [MRR], "RetrievalP95", [Retrieval p95 (ms)])'
[System.IO.File]::WriteAllText($query, (@{ queries = @(@{ query = $dax }) } | ConvertTo-Json -Depth 4), $utf8)
$result = Invoke-Fab api -A powerbi -X post "groups/$workspaceId/datasets/$modelId/executeQueries" -i $query
if ($result -notmatch '"status_code":\s*200' -or $result -notmatch 'vector_backend') {
    throw "La consulta de validación del modelo falló: $result"
}
Write-Host $result
Write-Host 'Informe de calidad desplegado y validado.'
