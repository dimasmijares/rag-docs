[CmdletBinding()]
param(
    # fabric.env local (fuera del repo): FABRIC_TENANT_ID, FABRIC_CLIENT_ID,
    # FABRIC_CLIENT_CERT_PATH, FABRIC_CAPACITY_NAME, FABRIC_WORKSPACE_NAME.
    [Parameter(Mandatory)]
    [string]$EnvFile,
    [switch]$SkipWheel
)

# Bootstrap idempotente del perfil Fabric (WRK-TASK-099, DOC-RAG-003). Requiere `fab` con sesión
# de una persona administradora del workspace (`fab auth login`), Azure CLI con sesión (`az login`)
# y `uv`. No imprime identificadores ni tokens.

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

$config = @{}
foreach ($line in Get-Content -LiteralPath $EnvFile) {
    if ($line -match '^\s*([A-Z_]+)\s*=\s*(.*)$') { $config[$Matches[1]] = $Matches[2].Trim() }
}
foreach ($key in 'FABRIC_CLIENT_ID', 'FABRIC_CAPACITY_NAME', 'FABRIC_WORKSPACE_NAME') {
    if (-not $config[$key]) { throw "Falta $key en el fichero de entorno." }
}

function Invoke-Fab {
    # fab escribe progreso en stderr: no debe convertirse en error terminante.
    $ErrorActionPreference = 'Continue'
    $output = (& fab @args 2>&1 | ForEach-Object { "$_" }) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "fab $($args[0]) falló: $output" }
    return $output.Trim()
}

function Test-FabPath([string]$Path) {
    return (Invoke-Fab exists $Path) -eq 'true'
}

$workspace = "$($config.FABRIC_WORKSPACE_NAME).Workspace"
if (-not (Test-FabPath $workspace)) {
    Invoke-Fab mkdir $workspace -P "capacityName=$($config.FABRIC_CAPACITY_NAME)" | Out-Null
    Write-Host "Creado $workspace"
}

foreach ($item in 'ragdocs_eval.Lakehouse', 'ragdocs_vectors.SQLDatabase', 'ragdocs_env.Environment',
    'ragdocs_params.VariableLibrary') {
    if (-not (Test-FabPath "$workspace/$item")) {
        Invoke-Fab mkdir "$workspace/$item" | Out-Null
        Write-Host "Creado $item"
    }
}

# Definiciones versionadas en fabric/ (fuente de verdad: el repositorio, no Git integration).
Invoke-Fab import "$workspace/ragdocs_params.VariableLibrary" `
    -i (Join-Path $PSScriptRoot 'ragdocs_params.VariableLibrary') -f | Out-Null
Write-Host 'Variable library importada'

# Rol mínimo del service principal: Contributor (escribe vectores en SQL y tablas Delta).
$principal = az ad sp show --id $config.FABRIC_CLIENT_ID --query id -o tsv
if (-not $principal) { throw 'No se pudo resolver el service principal.' }
Invoke-Fab acl set $workspace -I $principal -R Contributor -f | Out-Null
Write-Host 'Service principal con rol Contributor'

Push-Location $repoRoot
try {
    if (-not $SkipWheel) {
        uv build --wheel --out-dir dist
        if ($LASTEXITCODE -ne 0) { throw 'uv build falló.' }
        $wheel = Get-ChildItem dist -Filter 'rag_docs-*.whl' | Sort-Object LastWriteTime | Select-Object -Last 1
        uv run --no-sync --with azure-identity python fabric/tools/fabric_api.py `
            --env-file $EnvFile publish-wheel $wheel.FullName --as sp
        if ($LASTEXITCODE -ne 0) { throw 'La publicación del Environment falló.' }
    }
    uv run --no-sync --with azure-identity python fabric/tools/fabric_api.py `
        --env-file $EnvFile check-access --as sp
    if ($LASTEXITCODE -ne 0) { throw 'El service principal no ve todos los items.' }
}
finally {
    Pop-Location
}
