$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$specRoot = Join-Path $projectRoot 'specs'
$issues = [System.Collections.Generic.List[string]]::new()
$nodes = @{}

Get-ChildItem -Path $specRoot -Recurse -Filter '*.md' | ForEach-Object {
    $raw = Get-Content -Raw -LiteralPath $_.FullName
    $frontmatter = [regex]::Match($raw, '(?s)\A---\r?\n(.*?)\r?\n---').Groups[1].Value
    $id = [regex]::Match($frontmatter, '(?m)^id:\s*(\S+)').Groups[1].Value
    if (-not $id) { return }

    $dependencies = @(
        [regex]::Matches($frontmatter, '(?m)^\s+- id:\s*(\S+)') |
            ForEach-Object { $_.Groups[1].Value }
    )
    $nodes[$id] = [pscustomobject]@{
        Id = $id
        Layer = [regex]::Match($frontmatter, '(?m)^layer:\s*(\S+)').Groups[1].Value
        Status = [regex]::Match($frontmatter, '(?m)^status:\s*(\S+)').Groups[1].Value
        Parent = [regex]::Match($frontmatter, '(?m)^parent:\s*(\S+)').Groups[1].Value
        Dependencies = $dependencies
        Raw = $raw
        Path = $_.FullName
    }
}

$activeTasks = @($nodes.Values | Where-Object {
    $_.Layer -eq 'work-task' -and $_.Status -eq 'active'
})
if ($activeTasks.Count -gt 1) {
    $issues.Add("Hay más de una WRK-TASK activa: $($activeTasks.Id -join ', ').")
}

foreach ($node in $nodes.Values | Where-Object { $_.Layer -like 'work-*' }) {
    if ($node.Status -in @('completed', 'archived')) {
        if ($node.Raw -match '(?m)^\s*- \[ \]') {
            $issues.Add("$($node.Id) está $($node.Status) con criterios pendientes.")
        }
        $evidence = [regex]::Match(
            $node.Raw,
            '(?ms)^## Evidence\s*(.*?)(?=^## |\z)'
        ).Groups[1].Value.Trim()
        if (-not $evidence -or $evidence -match '^(Pendiente|Pending)') {
            $issues.Add("$($node.Id) está $($node.Status) sin Evidence consolidada.")
        }
    }

    if ($node.Layer -eq 'work-task' -and $node.Status -eq 'active') {
        if ($node.Raw -notmatch '(?m)^## (File Scope|Scope)\s*$') {
            $issues.Add("$($node.Id) está activa sin scope explícito.")
        }
        foreach ($dependencyId in $node.Dependencies) {
            $dependency = $nodes[$dependencyId]
            if ($dependency -and $dependency.Layer -like 'work-*' -and
                $dependency.Status -notin @('completed', 'archived')) {
                $issues.Add(
                    "$($node.Id) está activa con dependencia no terminal " +
                    "$dependencyId [$($dependency.Status)]."
                )
            }
        }
        $parent = $nodes[$node.Parent]
        $workSpec = if ($parent) { $nodes[$parent.Parent] } else { $null }
        if (-not $parent -or $parent.Layer -ne 'work-plan' -or $parent.Status -ne 'active') {
            $issues.Add("$($node.Id) no tiene un WRK-PLAN activo como padre.")
        }
        if (-not $workSpec -or $workSpec.Layer -ne 'work-spec' -or
            $workSpec.Status -ne 'active') {
            $issues.Add("$($node.Id) no pertenece a un WRK-SPEC activo.")
        }
    }

    if ($node.Status -eq 'archived' -and $node.Parent) {
        $parent = $nodes[$node.Parent]
        if (-not $parent -or $parent.Status -ne 'archived') {
            $issues.Add("$($node.Id) está archivado pero su padre no lo está.")
        }
    }
}

if ($issues.Count) {
    $issues | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Output "Lifecycle KDD válido para $($nodes.Count) artefactos."

