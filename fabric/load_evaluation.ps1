[CmdletBinding()]
param(
    [string]$WorkspaceName = 'rag-docs',
    [string]$LakehouseName = 'ragdocs_eval',
    [int]$TimeoutSeconds = 1800
)

# Carga del plano de evaluación en Delta (WRK-TASK-102, DOC-RAG-003). Requiere `fab` con sesión.
# 1. Valida en local cada informe de benchmark: mismo corpus_version que
#    evaluation/corpus-compatibility.yaml, referencia al sha256 del manifiesto del corpus sintético
#    y sin campos de contenido documental.
# 2. Aterriza compatibilidad, manifiesto, gold sets e informes en
#    Files/landing/<corpus_version>/ del Lakehouse (`fab cp`).
# 3. Importa fabric/ragdocs_eval_loader.Notebook y lo ejecuta (`fab job run`), que añade a Delta
#    de forma append-only e idempotente (un fichero ya cargado se omite).

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$forbidden = @('answer', 'snippet', 'text', 'claims')

function Invoke-Fab {
    $ErrorActionPreference = 'Continue'
    $output = (& fab @args 2>&1 | ForEach-Object { "$_" }) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "fab $($args[0]) falló: $output" }
    return $output.Trim()
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
}

function Test-ForbiddenKey($Node) {
    if ($Node -is [System.Management.Automation.PSCustomObject]) {
        foreach ($property in $Node.PSObject.Properties) {
            if ($property.Name -in $forbidden -or (Test-ForbiddenKey $property.Value)) { return $true }
        }
    }
    elseif ($Node -is [System.Collections.IEnumerable] -and $Node -isnot [string]) {
        foreach ($item in $Node) { if (Test-ForbiddenKey $item) { return $true } }
    }
    return $false
}

Push-Location $repoRoot
$staging = Join-Path $repoRoot '_build/evaluation-landing'
try {
    $compatibilityPath = 'evaluation/corpus-compatibility.yaml'
    $corpusVersion = ((Select-String -LiteralPath $compatibilityPath -Pattern '^corpus_version:\s*"?([^"\s]+)').Matches[0].Groups[1].Value)
    $manifestPath = 'examples/corpus/demo/manifest.sha256'
    $manifestSha = Get-Sha256 $manifestPath

    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force }
    New-Item -ItemType Directory -Force (Join-Path $staging 'gold-sets'), (Join-Path $staging 'reports') | Out-Null
    Copy-Item $compatibilityPath (Join-Path $staging 'corpus-compatibility.yaml')
    Copy-Item $manifestPath (Join-Path $staging 'manifest.sha256')
    foreach ($gold in Get-ChildItem evaluation -Filter 'gold-set*.yaml') {
        Copy-Item $gold.FullName (Join-Path $staging "gold-sets/$($gold.Name)")
    }

    $excluded = @()
    foreach ($report in Get-ChildItem evaluation/benchmarks -Recurse -Filter '*.json') {
        $content = Get-Content -LiteralPath $report.FullName -Raw -Encoding utf8 | ConvertFrom-Json
        $name = "$($report.Directory.Name)__$($report.Name)"
        if (-not $content.PSObject.Properties['profiles']) { continue }
        $reason = if ($content.corpus_version -ne $corpusVersion) { 'corpus_version' }
            elseif ($content.corpus_manifest_sha256 -ne $manifestSha) { 'manifiesto' }
            elseif (Test-ForbiddenKey $content) { 'contenido documental' }
            else { $null }
        if ($reason) { $excluded += "$name ($reason)"; continue }
        Copy-Item $report.FullName (Join-Path $staging "reports/$name")
    }
    if ($excluded) { Write-Host "Informes excluidos: $($excluded -join '; ')" }

    $lakehouse = "$WorkspaceName.Workspace/$LakehouseName.Lakehouse"
    $landing = "$lakehouse/Files/landing/$corpusVersion"
    foreach ($folder in "$lakehouse/Files/landing", $landing, "$landing/gold-sets", "$landing/reports") {
        if ((Invoke-Fab exists $folder) -ne 'true') { Invoke-Fab mkdir $folder | Out-Null }
    }
    foreach ($file in Get-ChildItem -LiteralPath $staging -Recurse -File) {
        $relative = $file.FullName.Substring($staging.Length + 1).Replace('\', '/')
        Invoke-Fab cp $file.FullName "$landing/$relative" -f | Out-Null
    }
    $staged = (Get-ChildItem -LiteralPath $staging -Recurse -File).Count
    Write-Host "Aterrizados $staged ficheros en Files/landing/$corpusVersion"

    $notebook = "$WorkspaceName.Workspace/ragdocs_eval_loader.Notebook"
    Invoke-Fab import $notebook -i (Join-Path $PSScriptRoot 'ragdocs_eval_loader.Notebook') -f | Out-Null
    $run = Invoke-Fab job run $notebook -P "corpus_version:string=$corpusVersion" `
        --timeout $TimeoutSeconds --polling_interval 20
    Write-Host $run
}
finally {
    Pop-Location
}
