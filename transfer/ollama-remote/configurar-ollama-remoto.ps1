param(
    [string]$LaptopIp = '',
    [string]$Model = 'qwen2.5:3b'
)

$ErrorActionPreference = 'Stop'
$firewallRuleName = 'Ollama RAG desde portatil'

if ([string]::IsNullOrWhiteSpace($LaptopIp)) {
    $LaptopIp = Read-Host 'IPv4 del portatil que ejecuta rag-docs (ejemplo documental: 192.0.2.25)'
}

$parsedIp = $null
if (-not [System.Net.IPAddress]::TryParse($LaptopIp, [ref]$parsedIp) -or
    $parsedIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw "La direccion '$LaptopIp' no es una IPv4 valida."
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    throw 'El nombre del modelo no puede estar vacio.'
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
$isAdministrator = $principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdministrator) {
    Write-Host 'Solicitando permisos de administrador para configurar el firewall...'
    $arguments = @(
        '-NoProfile'
        '-ExecutionPolicy', 'Bypass'
        '-File', ('"{0}"' -f $PSCommandPath)
        '-LaptopIp', ('"{0}"' -f $LaptopIp)
        '-Model', ('"{0}"' -f $Model)
    ) -join ' '
    Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $arguments
    exit 0
}

$ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
if ($null -eq $ollamaCommand) {
    Write-Host ''
    Write-Host 'Ollama no esta instalado o no aparece en PATH.' -ForegroundColor Yellow
    Write-Host 'Instalalo desde https://ollama.com/download/windows y vuelve a ejecutar este archivo.'
    Read-Host 'Pulsa Enter para cerrar'
    exit 2
}

Write-Host "Descargando o comprobando el modelo $Model..."
& $ollamaCommand.Source pull $Model
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo preparar el modelo $Model."
}

[Environment]::SetEnvironmentVariable(
    'OLLAMA_HOST',
    '0.0.0.0:11434',
    [EnvironmentVariableTarget]::User
)

$existingRule = Get-NetFirewallRule -DisplayName $firewallRuleName -ErrorAction SilentlyContinue
if ($null -eq $existingRule) {
    New-NetFirewallRule `
        -DisplayName $firewallRuleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort 11434 `
        -RemoteAddress $LaptopIp `
        -Profile Private | Out-Null
}
else {
    $existingRule | Set-NetFirewallRule `
        -Direction Inbound `
        -Action Allow `
        -Enabled True `
        -Profile Private | Out-Null
    $existingRule | Get-NetFirewallAddressFilter |
        Set-NetFirewallAddressFilter -RemoteAddress $LaptopIp | Out-Null
}

$localAddresses = Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred |
    Where-Object {
        $_.IPAddress -notlike '127.*' -and
        $_.InterfaceAlias -notlike '*vEthernet*'
    } |
    Select-Object -ExpandProperty IPAddress -Unique

Write-Host ''
Write-Host 'Configuracion terminada.' -ForegroundColor Green
Write-Host "Modelo: $Model"
Write-Host "Acceso permitido solamente desde: $LaptopIp"
Write-Host "IPv4 candidatas de este PC: $($localAddresses -join ', ')"
Write-Host ''
Write-Host 'IMPORTANTE: cierra Ollama desde la bandeja de Windows y vuelve a abrirlo desde Inicio.'
Write-Host 'Despues, desde el portatil, abre probar-desde-portatil.ps1 incluido en el paquete.'
Write-Host 'Usa inicialmente solo el corpus didactico; no envies documentacion corporativa sin autorizacion.'
Read-Host 'Pulsa Enter para cerrar'
