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
        & $gate -Paths $Paths -WarningAction SilentlyContinue 6>$null | Out-Null
    }
    catch {
        if ($_.Exception.Message -notmatch $ExpectedMessage) {
            throw "El gate falló por un motivo inesperado: $($_.Exception.Message)"
        }
        return
    }

    throw "El gate aceptó un caso negativo: $($Paths -join ', ')"
}

function Assert-GatePasses {
    param(
        [Parameter(Mandatory)]
        [string[]]$Paths
    )

    try {
        & $gate -Paths $Paths -WarningAction SilentlyContinue 6>$null | Out-Null
    }
    catch {
        throw "El gate rechazó un caso positivo ($($Paths -join ', ')): $($_.Exception.Message)"
    }
}

function New-Fixture {
    # Crea la fixture bajo _build y devuelve su ruta relativa a la raíz del proyecto.
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [Parameter(Mandatory)]
        [string]$Content
    )

    $path = Join-Path $testRoot $Name
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
    [System.IO.File]::WriteAllText($path, $Content, [System.Text.UTF8Encoding]::new($false))
    return $path.Substring($projectRoot.Length).TrimStart('\', '/')
}

# Los valores sensibles se construyen en tiempo de ejecución para que este script no contenga en
# claro nada que el propio gate rechace.
$randomGuid = [guid]::NewGuid().ToString()
$exampleGuid = ('0' * 8) + '-' + ('0' * 4) + '-' + ('0' * 4) + '-' + ('0' * 4) + '-' + ('0' * 12)
$fabricDomain = '.datawarehouse.fabric' + '.microsoft.com'
$loginHost = 'https://login.microsoftonline' + '.com/'

New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
try {
    # Casos previos: IPv4 privada, ruta privada e identificador derivado.
    $privateIp = @('192', '168', '50', '25') -join '.'
    Assert-GateFails -Paths (New-Fixture 'private-ip.txt' "synthetic endpoint $privateIp") `
        -ExpectedMessage 'IPv4 privada'
    Assert-GateFails -Paths ('logs/' + 'synthetic-fixture.json') -ExpectedMessage 'ruta privada candidata'

    $syntheticIdentifier = 'SYNTHETIC_DERIVED_IDENTIFIER_' + 'FOR_TEST'
    $identifierFixture = New-Fixture 'derived-identifier.txt' "reference $syntheticIdentifier here"
    $previousEnvValue = $env:PUBLIC_SAFETY_IDENTIFIERS
    $env:PUBLIC_SAFETY_IDENTIFIERS = $syntheticIdentifier
    try {
        Assert-GateFails -Paths $identifierFixture -ExpectedMessage 'identificador derivado conocido'
    }
    finally {
        $env:PUBLIC_SAFETY_IDENTIFIERS = $previousEnvValue
    }

    # Notebooks: con outputs o ilegible se rechaza; limpio pasa.
    $outputCell = '{"cell_type":"code","source":["print(1)"],"outputs":[{"output_type":"stream","name":"stdout","text":["1"]}]}'
    $cleanCell = '{"cell_type":"code","source":["print(1)"],"execution_count":null,"outputs":[]}'
    $notebookTemplate = '{"nbformat":4,"nbformat_minor":5,"metadata":{},"cells":[{"cell_type":"markdown","source":["x"]},CELL]}'
    Assert-GateFails -Paths (New-Fixture 'with-outputs.ipynb' $notebookTemplate.Replace('CELL', $outputCell)) `
        -ExpectedMessage 'notebook con outputs'
    Assert-GateFails -Paths (New-Fixture 'broken.ipynb' '{"cells": [') -ExpectedMessage 'notebook ilegible'
    Assert-GatePasses -Paths (New-Fixture 'clean.ipynb' $notebookTemplate.Replace('CELL', $cleanCell))

    # GUIDs de entorno: workspace en .platform y tenant en URL de login; logicalId y marcadores pasan.
    $platformTemplate = '{"metadata":{"type":"Notebook","displayName":"demo"},"config":{"version":"2.0","logicalId":"' +
        $randomGuid + '"},"workspaceId":"WORKSPACE"}'
    Assert-GateFails -Paths (New-Fixture 'real-workspace/.platform' $platformTemplate.Replace('WORKSPACE', [guid]::NewGuid().ToString())) `
        -ExpectedMessage 'GUID de tenant o workspace'
    Assert-GatePasses -Paths (New-Fixture 'example-workspace/.platform' $platformTemplate.Replace('WORKSPACE', $exampleGuid))
    Assert-GateFails -Paths (New-Fixture 'tenant-login.md' "authority: $loginHost$randomGuid/v2.0") `
        -ExpectedMessage 'GUID de tenant o workspace'
    Assert-GatePasses -Paths (New-Fixture 'tenant-example.md' "authority: $loginHost$exampleGuid/v2.0")

    # Endpoints SQL de Fabric en TMDL: host real se rechaza; marcador pasa.
    $tmdlTemplate = "expression DatabaseQuery =`n`tlet`n`t`tdatabase = Sql.Database(`"HOST$fabricDomain`", `"rag`")`n`tin`n`t`tdatabase"
    Assert-GateFails -Paths (New-Fixture 'real-endpoint.tmdl' $tmdlTemplate.Replace('HOST', 'x7k2mq4tzv5abc3fghijklmnop')) `
        -ExpectedMessage 'endpoint SQL de Fabric'
    Assert-GatePasses -Paths (New-Fixture 'example-endpoint.tmdl' $tmdlTemplate.Replace('HOST', '<sql-endpoint>'))

    # Cadenas de conexión: credencial literal se rechaza; marcador de placeholder pasa.
    $connectionTemplate = 'Server=tcp:example;Database=rag;' + 'Pass' + 'word=VALUE;Encrypt=True;'
    Assert-GateFails -Paths (New-Fixture 'real-connection.pq' $connectionTemplate.Replace('VALUE', 'Synthetic-Secret-42')) `
        -ExpectedMessage 'cadena de conexi'
    Assert-GatePasses -Paths (New-Fixture 'example-connection.pq' $connectionTemplate.Replace('VALUE', '<secret>'))

    $urlTemplate = 'postgresql://' + 'rag_user:VALUE@db.example.org/rag'
    Assert-GateFails -Paths (New-Fixture 'real-url.sql' ('-- ' + $urlTemplate.Replace('VALUE', 'synthetic42'))) `
        -ExpectedMessage 'URL con credenciales'
    Assert-GatePasses -Paths (New-Fixture 'example-url.sql' ('-- ' + $urlTemplate.Replace('VALUE', '${DB_PASSWORD}')))

    # Rutas de estado local PBIP y datos materializados se rechazan; artefactos de definición pasan.
    foreach ($privatePath in @(
            'reports/quality.Report/.pbi/' + 'localSettings.json',
            'reports/quality.SemanticModel/.pbi/' + 'cache.abf',
            'fabric/eval.Lakehouse/Tables/runs/' + '_delta_log/00000.json',
            'fabric/eval.Lakehouse/Files/' + 'runs.parquet'
        )) {
        Assert-GateFails -Paths $privatePath -ExpectedMessage 'ruta privada candidata'
    }
    Assert-GatePasses -Paths @(
        'reports/quality.Report/.pbi/' + 'editorSettings.json',
        'reports/quality.Report/' + 'definition.pbir',
        (New-Fixture 'quality.pbip' '{"version":"1.0","artifacts":[{"report":{"path":"quality.Report"}}]}')
    )

    # El gate no contiene en claro los identificadores que protege (WRK-TASK-092): sólo GUIDs de
    # marcador y ningún identificador derivado cargado.
    $gateContent = [System.IO.File]::ReadAllText($gate)
    $guidPattern = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    foreach ($match in [regex]::Matches($gateContent, $guidPattern)) {
        if ($match.Value -notmatch '^([0-9a-fA-F])\1{7}-\1{4}-\1{4}-\1{4}-\1{12}$') {
            throw "El gate contiene un GUID que no es marcador de ejemplo."
        }
    }
    $protectedIdentifiers = @($env:PUBLIC_SAFETY_IDENTIFIERS -split '\|')
    $localIdentifiers = Join-Path $projectRoot 'config/public-safety-identifiers.local.txt'
    if (Test-Path -LiteralPath $localIdentifiers) {
        $protectedIdentifiers += @(Get-Content -LiteralPath $localIdentifiers | Where-Object { -not $_.Trim().StartsWith('#') })
    }
    foreach ($identifier in $protectedIdentifiers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) {
        if ($gateContent.IndexOf($identifier.Trim(), [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            throw 'El gate contiene en claro un identificador derivado protegido.'
        }
    }

    Write-Host 'Pruebas negativas y positivas del gate de publicación superadas.'
}
finally {
    if (Test-Path -LiteralPath $testRoot) {
        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
