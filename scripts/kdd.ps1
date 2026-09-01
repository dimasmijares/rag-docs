param(
    [ValidateSet('validate', 'stats', 'orphans', 'context', 'impact')]
    [string]$Command = 'validate',
    [string]$Id = ''
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $PSScriptRoot 'kdd_graph.py'
$specs = Join-Path $projectRoot 'specs'

if (-not (Test-Path -LiteralPath $cli)) {
    throw 'Falta el CLI KDD local en scripts/kdd_graph.py.'
}

if ($Command -in @('context', 'impact') -and [string]::IsNullOrWhiteSpace($Id)) {
    throw "El comando $Command requiere -Id."
}

$arguments = @('run', '--no-sync', 'python', $cli, '--specs', $specs, $Command)
if ($Id) { $arguments += $Id }
& uv @arguments
if ($LASTEXITCODE -ne 0) {
    throw "El comando KDD '$Command' falló con código $LASTEXITCODE."
}
