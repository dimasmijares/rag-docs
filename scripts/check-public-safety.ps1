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
            ($normalized -eq 'ollama-remote-setup.zip')
        if ($forbiddenPath) {
            $violations.Add("ruta privada candidata: $normalized")
        }
    }

    $textExtensions = @(
        '.cfg', '.css', '.dockerignore', '.env.example', '.html', '.ini', '.js', '.json',
        '.md', '.ps1', '.py', '.toml', '.txt', '.yaml', '.yml'
    )
    $contentPatterns = [ordered]@{
        'ruta personal de Windows' = '(?i)C:\\Users\\[^\\\r\n]+'
        'IPv4 privada' = '(?<![0-9])(?:10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.(?:[0-9]{1,3}\.)[0-9]{1,3})(?![0-9])'
    }
    $derivedIdentifierPattern = Get-DerivedIdentifierPattern
    if ($null -ne $derivedIdentifierPattern) {
        $contentPatterns['identificador derivado conocido'] = $derivedIdentifierPattern
    }

    foreach ($path in $candidateFiles) {
        if ($path.Replace('\', '/') -eq 'scripts/check-public-safety.ps1') {
            continue
        }
        $item = Get-Item -LiteralPath $path -ErrorAction SilentlyContinue
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
