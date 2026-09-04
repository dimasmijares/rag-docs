[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$gate = Join-Path $PSScriptRoot 'check-public-safety.ps1'
$buildRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot '_build'))
$testRoot = [System.IO.Path]::GetFullPath((Join-Path $buildRoot 'public-safety-test'))

if (-not $testRoot.StartsWith($buildRoot + [System.IO.Path]::DirectorySeparatorChar)) {
    throw "El directorio temporal no está contenido en _build: $testRoot"
}

function Assert-GateFails {
    param(
        [Parameter(Mandatory)]
        [string[]]$Paths,
        [Parameter(Mandatory)]
        [string]$ExpectedMessage
    )

    try {
        & $gate -Paths $Paths
    }
    catch {
        if ($_.Exception.Message -notmatch $ExpectedMessage) {
            throw "El gate falló por un motivo inesperado: $($_.Exception.Message)"
        }
        return
    }

    throw "El gate aceptó un caso negativo: $($Paths -join ', ')"
}

New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
try {
    $fixture = Join-Path $testRoot 'private-ip.txt'
    $privateIp = @('192', '168', '50', '25') -join '.'
    Set-Content -LiteralPath $fixture -Value "synthetic endpoint $privateIp" -Encoding utf8
    $relativeFixture = [System.IO.Path]::GetRelativePath($projectRoot, $fixture)

    Assert-GateFails -Paths $relativeFixture -ExpectedMessage 'IPv4 privada'
    Assert-GateFails -Paths ('logs/' + 'synthetic-fixture.json') -ExpectedMessage 'ruta privada candidata'

    $identifierFixture = Join-Path $testRoot 'derived-identifier.txt'
    $syntheticIdentifier = 'SYNTHETIC_DERIVED_IDENTIFIER_' + 'FOR_TEST'
    Set-Content -LiteralPath $identifierFixture -Value "reference $syntheticIdentifier here" -Encoding utf8
    $relativeIdentifierFixture = [System.IO.Path]::GetRelativePath($projectRoot, $identifierFixture)

    $previousEnvValue = $env:PUBLIC_SAFETY_IDENTIFIERS
    $env:PUBLIC_SAFETY_IDENTIFIERS = $syntheticIdentifier
    try {
        Assert-GateFails -Paths $relativeIdentifierFixture -ExpectedMessage 'identificador derivado conocido'
    }
    finally {
        $env:PUBLIC_SAFETY_IDENTIFIERS = $previousEnvValue
    }

    Write-Host 'Pruebas negativas del gate de publicación superadas.'
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
