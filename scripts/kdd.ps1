param(
    [ValidateSet('validate', 'stats', 'orphans', 'context', 'impact')]
    [string]$Command = 'validate',
    [string]$Id = ''
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$cli = Join-Path $projectRoot '.kdd/framework/apps/spec-graph/spec-graph.mjs'
$specs = Join-Path $projectRoot 'specs'

if (-not (Test-Path -LiteralPath $cli)) {
    throw 'Falta el submódulo KDD. Ejecuta: git submodule update --init --recursive'
}

if ($Command -in @('context', 'impact') -and [string]::IsNullOrWhiteSpace($Id)) {
    throw "El comando $Command requiere -Id."
}

$arguments = @($cli, '--specs', $specs, $Command)
if ($Id) { $arguments += $Id }
& node @arguments
exit $LASTEXITCODE
