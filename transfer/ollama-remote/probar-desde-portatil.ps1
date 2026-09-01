param(
    [string]$RemotePcIp = ''
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($RemotePcIp)) {
    $RemotePcIp = Read-Host 'IPv4 del PC personal que ejecuta Ollama'
}

$parsedIp = $null
if (-not [System.Net.IPAddress]::TryParse($RemotePcIp, [ref]$parsedIp) -or
    $parsedIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw "La direccion '$RemotePcIp' no es una IPv4 valida."
}

$connection = Test-NetConnection $RemotePcIp -Port 11434 -WarningAction SilentlyContinue
if (-not $connection.TcpTestSucceeded) {
    throw "No se puede acceder a ${RemotePcIp}:11434. Revisa Ollama, la IP y el firewall."
}

$models = Invoke-RestMethod -Uri "http://${RemotePcIp}:11434/api/tags" -TimeoutSec 10

Write-Host ''
Write-Host 'Conexion correcta.' -ForegroundColor Green
Write-Host "URL para rag-docs: http://${RemotePcIp}:11434"
Write-Host 'Modelos disponibles:'
$models.models | ForEach-Object { Write-Host "  - $($_.name)" }
Write-Host ''
Write-Host 'Configura en el .env del portatil:'
Write-Host "RAG_DOCS_OLLAMA_URL=http://${RemotePcIp}:11434"
Read-Host 'Pulsa Enter para cerrar'
