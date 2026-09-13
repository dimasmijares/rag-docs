[CmdletBinding()]
param(
    [string[]]$Paths
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

function Get-DerivedIdentifierPattern {
    # Los identificadores corporativos derivados nunca viven en claro en este script.
    # Fuente 1 (CI): variable de entorno PUBLIC_SAFETY_IDENTIFIERS, cargada desde un
    # secreto, con los identificadores separados por '|'.
    # Fuente 2 (local): config/public-safety-identifiers.local.txt, ignorado por Git
    # (coincide con el patrón config/**/*.local.* de .gitignore), un identificador por
    # línea. Ver config/public-safety-identifiers.example.txt para el formato.
    $identifiers = [System.Collections.Generic.List[string]]::new()

    $envValue = $env:PUBLIC_SAFETY_IDENTIFIERS
    if (-not [string]::IsNullOrWhiteSpace($envValue)) {
        foreach ($item in $envValue -split '\|') {
            if (-not [string]::IsNullOrWhiteSpace($item)) {
                $identifiers.Add($item.Trim())
            }
        }
    }

    $localFile = Join-Path $projectRoot 'config/public-safety-identifiers.local.txt'
    if (Test-Path -LiteralPath $localFile) {
        foreach ($line in Get-Content -LiteralPath $localFile) {
            $trimmed = $line.Trim()
            if ($trimmed -and -not $trimmed.StartsWith('#')) {
                $identifiers.Add($trimmed)
            }
        }
    }

    if ($identifiers.Count -eq 0) {
        Write-Warning ('Gate de publicación: sin lista de identificadores derivados cargada ' +
            '(ni PUBLIC_SAFETY_IDENTIFIERS ni config/public-safety-identifiers.local.txt). ' +
            'El gate no puede detectar identificadores corporativos derivados en esta ejecución.')
        return $null
    }

    $escaped = $identifiers | Sort-Object -Unique | ForEach-Object { [regex]::Escape($_) }
    return '(?i)(' + ($escaped -join '|') + ')'
}

# GUIDs de ejemplo admitidos en documentación y fixtures. Cualquier otro GUID asociado a un
# tenant, workspace o item de datos Fabric se trata como identificador real del entorno.
$exampleGuidMarkers = @(
    '00000000-0000-0000-0000-000000000000',
    '11111111-1111-1111-1111-111111111111',
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'ffffffff-ffff-ffff-ffff-ffffffffffff'
)
$guidPattern = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
# El GUID debe aparecer en la misma línea que una clave o URL de entorno. `logicalId` de
# `.platform` no es un identificador de entorno y no se incluye.
$environmentGuidPattern =
    '(?i)(?:tenant|workspace|lakehouse|warehouse|capacity|directory|groups/|' +
    'onelake\.[^\s"'']*/|microsoftonline\.com/)[^\r\n]{0,60}?(?<guid>' + $guidPattern + ')'

function Test-HasEnvironmentGuid {
    param([string]$Content)

    foreach ($match in [regex]::Matches($Content, $environmentGuidPattern)) {
        $guid = $match.Groups['guid'].Value.ToLowerInvariant()
        if ($guid -notin $exampleGuidMarkers) {
            return $true
        }
    }
    return $false
}

function Test-NotebookHasOutputs {
    param([string]$Content)

    try {
        $notebook = $Content | ConvertFrom-Json
    }
    catch {
        return 'notebook ilegible'
    }
    foreach ($cell in @($notebook.cells)) {
        if ($null -ne $cell -and @($cell.outputs | Where-Object { $null -ne $_ }).Count -gt 0) {
            return 'notebook con outputs'
        }
    }
    return $null
}

Push-Location $projectRoot
try {
    if ($PSBoundParameters.ContainsKey('Paths')) {
        $candidateFiles = @($Paths | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }
    else {
        $candidateFiles = @(
            git ls-files --cached --others --exclude-standard |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )
        if ($LASTEXITCODE -ne 0) {
            throw 'No se pudo obtener la lista de archivos candidatos a Git.'
        }
    }

    $violations = [System.Collections.Generic.List[string]]::new()
    foreach ($path in $candidateFiles) {
        $normalized = $path.Replace('\', '/')
        $forbiddenPath =
            (($normalized -match '(^|/)\.env($|\.)') -and $normalized -ne '.env.example') -or
            ($normalized -match '^config/.+\.local\.') -or
            ($normalized -match '^evaluation/.+\.(local|private)\.') -or
            ($normalized -match '^(logs|state|qdrant_storage|artifacts/private)/') -or
            ($normalized -match '^examples/corporate/.+' -and $normalized -ne 'examples/corporate/.gitkeep') -or
            ($normalized -eq 'ollama-remote-setup.zip') -or
            # Estado local de PBIP y datos materializados de lakehouse o Delta.
            ($normalized -match '(^|/)\.pbi/(localSettings\.json|cache\.abf)$') -or
            ($normalized -match '(^|/)_delta_log/') -or
            ($normalized -match '(?i)\.(parquet|abf)$')
        if ($forbiddenPath) {
            $violations.Add("ruta privada candidata: $normalized")
        }
    }

    $textExtensions = @(
        '.cfg', '.css', '.dockerignore', '.env.example', '.html', '.ini', '.js', '.json',
        '.md', '.ps1', '.py', '.toml', '.txt', '.yaml', '.yml',
        # Artefactos Fabric y Power BI (PBIP/TMDL).
        '.bim', '.ipynb', '.pbip', '.pbir', '.pbism', '.platform', '.pq', '.sql', '.tmdl'
    )
    # Valores de credencial admitidos como marcador: <...>, {...}, ${...}, $env:..., %...%, ***.
    $credentialKeys = '(?:password|pwd|accountkey|sharedaccesskey|sharedaccesssignature|client ?secret)'
    $credentialValue = '(?![<{$%*])[^;"''\s<>]+'
    $contentPatterns = [ordered]@{
        'ruta personal de Windows' = '(?i)C:\\Users\\[^\\\r\n]+'
        'IPv4 privada' = '(?<![0-9])(?:10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.(?:[0-9]{1,3}\.)[0-9]{1,3})(?![0-9])'
        'cadena de conexión con credenciales' =
            "(?i)(?:;\s*$credentialKeys\s*=\s*$credentialValue|$credentialKeys\s*=\s*$credentialValue\s*;)"
        'URL con credenciales' = '(?i)\b[a-z][a-z0-9+.-]*://[^/\s:@"''<>]+:(?![<{$%*])[^/\s@"''<>]+@'
        'endpoint SQL de Fabric' = '(?i)(?<![<{$%*.\w-])[a-z0-9-]{12,}\.(?:datawarehouse|database)\.fabric\.microsoft\.com'
    }
    $derivedIdentifierPattern = Get-DerivedIdentifierPattern
    if ($null -ne $derivedIdentifierPattern) {
        $contentPatterns['identificador derivado conocido'] = $derivedIdentifierPattern
    }

    foreach ($path in $candidateFiles) {
        if ($path.Replace('\', '/') -eq 'scripts/check-public-safety.ps1') {
            continue
        }
        # -Force: en Linux los ficheros con punto inicial (.platform, .gitignore) son ocultos.
        $item = Get-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
        if ($null -eq $item -or $item.PSIsContainer) {
            continue
        }
        $extension = [System.IO.Path]::GetExtension($item.Name).ToLowerInvariant()
        if ($item.Name -notin @('Dockerfile', 'README.md', '.gitignore', '.dockerignore') -and
            $extension -notin $textExtensions) {
            continue
        }
        $content = Get-Content -LiteralPath $item.FullName -Raw
        foreach ($entry in $contentPatterns.GetEnumerator()) {
            if ($content -match $entry.Value) {
                $violations.Add("$($entry.Key): $path")
            }
        }
        if (Test-HasEnvironmentGuid -Content $content) {
            $violations.Add("GUID de tenant o workspace fuera de marcadores de ejemplo: $path")
        }
        if ($extension -eq '.ipynb') {
            $notebookIssue = Test-NotebookHasOutputs -Content $content
            if ($notebookIssue) {
                $violations.Add("${notebookIssue}: $path")
            }
        }
    }

    if ($violations.Count -gt 0) {
        $details = $violations | Sort-Object -Unique | ForEach-Object { " - $_" }
        throw "Gate de publicación fallido:`n$($details -join "`n")"
    }

    Write-Host "Gate de publicación superado para $($candidateFiles.Count) archivos candidatos."
}
finally {
    Pop-Location
}
