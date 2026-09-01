$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot 'kdd.ps1') validate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $PSScriptRoot 'kdd.ps1') orphans
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& (Join-Path $PSScriptRoot 'check-kdd-lifecycle.ps1')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $projectRoot
try {
    uv run --no-sync ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    uv run --no-sync pytest
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
