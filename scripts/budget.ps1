$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$script = Join-Path $PSScriptRoot 'budget_forecast.py'

Push-Location $projectRoot
try {
    uv run --no-sync python $script @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
