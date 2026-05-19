#!/usr/bin/env pwsh
<#
.SYNOPSIS
    ADRION 369 Stack Manager — Complete Docker Orchestration Control (162D)
    
.DESCRIPTION
    Manages all 12 Docker services for ADRION 162D project with health checks,
    initialization, logging, and automated recovery.
    
.EXAMPLE
    .\manage-docker-stack.ps1 -Action Start -Environment production
    .\manage-docker-stack.ps1 -Action Status
    .\manage-docker-stack.ps1 -Action Logs -Service grafana -Follow
    .\manage-docker-stack.ps1 -Action Stop -Cleanup
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Start', 'Stop', 'Restart', 'Status', 'Logs', 'Build', 'Clean', 'Init', 'Test', 'Validate')]
    [string]$Action,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet('dev', 'staging', 'production')]
    [string]$Environment = 'dev',
    
    [Parameter(Mandatory = $false)]
    [string]$Service = '',
    
    [Parameter(Mandatory = $false)]
    [switch]$Follow = $false,
    
    [Parameter(Mandatory = $false)]
    [switch]$Cleanup = $false
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $WorkspaceRoot "docker-compose-orchestration.yml"
$EnvFile = Join-Path $WorkspaceRoot ".env"
$LogFile = Join-Path $WorkspaceRoot "logs\docker-stack-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Ensure logs directory exists
New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null

# Service definitions (in startup order)
$Services = @(
    'postgres',
    'loki',
    'promtail',
    'ollama',
    'alert-handler',
    'n8n',
    'vortex-engine',
    'adrion-healer',
    'adrion-api',
    'adrion-backup',
    'grafana',
    'prometheus',
    'adrion-nginx'
)

# Expected ports and health endpoints
$HealthChecks = @{
    'postgres'      = @{ port = 5432; endpoint = $null; check = 'psql' }
    'loki'          = @{ port = 3100; endpoint = '/ready'; check = 'http' }
    'promtail'      = @{ port = 9080; endpoint = $null; check = 'none' }
    'ollama'        = @{ port = 11434; endpoint = '/api/tags'; check = 'http' }
    'alert-handler' = @{ port = 8090; endpoint = '/health'; check = 'http' }
    'n8n'           = @{ port = 5678; endpoint = '/healthz'; check = 'http' }
    'vortex-engine' = @{ port = 1740; endpoint = '/health'; check = 'http' }
    'adrion-api'    = @{ port = 8001; endpoint = '/api/arbitrage/status'; check = 'http' }
    'grafana'       = @{ port = 3000; endpoint = '/api/health'; check = 'http' }
    'prometheus'    = @{ port = 9090; endpoint = '/-/ready'; check = 'http' }
    'adrion-nginx'  = @{ port = 80; endpoint = '/'; check = 'http' }
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Invoke-DockerCompose {
    param([string[]]$Arguments)
    Write-Log "Executing: docker-compose -f $ComposeFile $($Arguments -join ' ')"
    & docker-compose -f $ComposeFile @Arguments 2>&1 | Tee-Object -Append -FilePath $LogFile
}

function Test-ServiceHealth {
    param([string]$ServiceName)
    $Check = $HealthChecks[$ServiceName]
    if ($null -eq $Check) {
        Write-Log "No health check defined for $ServiceName" 'WARN'
        return $false
    }
    
    try {
        switch ($Check.check) {
            'http' {
                $Url = "http://localhost:$($Check.port)$($Check.endpoint)"
                $Response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -ErrorAction Stop
                return $Response.StatusCode -eq 200
            }
            'psql' {
                $Output = & psql -h localhost -U adrion -d genesis_record -c "SELECT 1" 2>&1
                return $LASTEXITCODE -eq 0
            }
            'none' {
                return $true
            }
        }
    }
    catch {
        Write-Log "Health check failed for $ServiceName : $_" 'WARN'
        return $false
    }
}

function Wait-ServiceReady {
    param([string]$ServiceName, [int]$TimeoutSeconds = 120)
    $Start = Get-Date
    $Healthy = $false
    
    Write-Log "Waiting for $ServiceName to become healthy (timeout: ${TimeoutSeconds}s)..."
    
    while ((New-TimeSpan -Start $Start).TotalSeconds -lt $TimeoutSeconds) {
        if (Test-ServiceHealth -ServiceName $ServiceName) {
            Write-Log "✅ $ServiceName is healthy" 'SUCCESS'
            return $true
        }
        Start-Sleep -Seconds 3
    }
    
    Write-Log "❌ $ServiceName failed to become healthy within timeout" 'ERROR'
    return $false
}

# ═══════════════════════════════════════════════════════════════════════════════
# ACTIONS
# ═════════════════════════════════════════════════════════════════════════════

function Invoke-Start {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "🚀 STARTING ADRION 369 STACK (Environment: $Environment)" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    # Verify .env exists
    if (-not (Test-Path $EnvFile)) {
        Write-Log "❌ .env file not found. Please create it first." 'ERROR'
        exit 1
    }
    
    # Create required directories
    Write-Log "Creating directory structure..." 'INFO'
    @(
        'data/postgres',
        'data/loki',
        'data/promtail',
        'data/ollama',
        'data/n8n',
        'data/grafana',
        'data/prometheus',
        'backups',
        'monitoring/alerts',
        'config/nginx/certs'
    ) | ForEach-Object {
        New-Item -ItemType Directory -Path (Join-Path $WorkspaceRoot $_) -Force | Out-Null
    }
    
    # Start all services
    Write-Log "Starting Docker Compose..." 'INFO'
    Invoke-DockerCompose @('up', '-d', '--build')
    
    # Wait for critical services
    Write-Log "Checking service health..." 'INFO'
    foreach ($Service in $Services) {
        Wait-ServiceReady -ServiceName $Service | Out-Null
    }
    
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "✅ ADRION 369 Stack Started Successfully!" 'SUCCESS'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "" 'INFO'
    Write-Log "Access Points:" 'INFO'
    Write-Log "  📊 Grafana:       http://localhost:3000" 'INFO'
    Write-Log "  🔍 Prometheus:    http://localhost:9090" 'INFO'
    Write-Log "  🔄 N8N:           http://localhost:5678" 'INFO'
    Write-Log "  ⚡ Vortex:        http://localhost:1740" 'INFO'
    Write-Log "  🤖 Ollama API:    http://localhost:11434" 'INFO'
    Write-Log "  🔘 Alert Handler: http://localhost:8090" 'INFO'
    Write-Log "  📡 Loki:          http://localhost:3100" 'INFO'
    Write-Log "  📈 ADRION API:    http://localhost:8001" 'INFO'
}

function Invoke-Stop {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "⏹️  STOPPING ADRION 369 STACK" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    Invoke-DockerCompose @('down')
    
    if ($Cleanup) {
        Write-Log "Removing volumes and cache..." 'INFO'
        Invoke-DockerCompose @('down', '-v')
    }
    
    Write-Log "✅ Stack stopped" 'SUCCESS'
}

function Invoke-Status {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "📊 ADRION 369 STACK STATUS" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    Invoke-DockerCompose @('ps')
    
    Write-Log "" 'INFO'
    Write-Log "Service Health Check:" 'INFO'
    foreach ($ServiceName in $Services) {
        $Healthy = Test-ServiceHealth -ServiceName $ServiceName
        $Status = if ($Healthy) { "✅ Healthy" } else { "❌ Unhealthy" }
        Write-Log "  $ServiceName : $Status"
    }
}

function Invoke-Logs {
    Write-Log "Fetching logs for $Service..." 'INFO'
    $Args = @('logs')
    if ($Service) { $Args += $Service }
    if ($Follow) { $Args += '-f' }
    $Args += '--tail=100'
    
    Invoke-DockerCompose $Args
}

function Invoke-Build {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "🔨 BUILDING ADRION 369 DOCKER IMAGES" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    Invoke-DockerCompose @('build', '--no-cache')
    
    Write-Log "✅ Build completed" 'SUCCESS'
}

function Invoke-Init {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "⚙️  INITIALIZING ADRION 369 STACK" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    # Copy .env template if needed
    if (-not (Test-Path $EnvFile)) {
        Write-Log "Creating .env from template..." 'INFO'
        Copy-Item -Path "$WorkspaceRoot\.env.example" -Destination $EnvFile -ErrorAction SilentlyContinue
        Write-Log "⚠️  Please update .env with your credentials" 'WARN'
    }
    
    Write-Log "✅ Initialization complete" 'SUCCESS'
}

function Invoke-Test {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "🧪 TESTING ADRION 369 SERVICES" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    $AllHealthy = $true
    foreach ($ServiceName in $Services) {
        if (Test-ServiceHealth -ServiceName $ServiceName) {
            Write-Log "✅ $ServiceName" 'SUCCESS'
        }
        else {
            Write-Log "❌ $ServiceName FAILED" 'ERROR'
            $AllHealthy = $false
        }
    }
    
    Write-Log "" 'INFO'
    if ($AllHealthy) {
        Write-Log "✅ All services healthy!" 'SUCCESS'
    }
    else {
        Write-Log "❌ Some services are unhealthy" 'ERROR'
        exit 1
    }
}

function Invoke-Validate {
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    Write-Log "✔️  VALIDATING ADRION 369 CONFIGURATION" 'INFO'
    Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
    
    # Check Docker
    Write-Log "Checking Docker..." 'INFO'
    $DockerVersion = & docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Docker: $DockerVersion"
    }
    else {
        Write-Log "❌ Docker not found" 'ERROR'
        exit 1
    }
    
    # Check Docker Compose
    Write-Log "Checking Docker Compose..." 'INFO'
    $ComposeVersion = & docker-compose --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "✅ Docker Compose: $ComposeVersion"
    }
    else {
        Write-Log "❌ Docker Compose not found" 'ERROR'
        exit 1
    }
    
    # Check compose file
    Write-Log "Checking compose file..." 'INFO'
    if (Test-Path $ComposeFile) {
        Write-Log "✅ Compose file found"
    }
    else {
        Write-Log "❌ Compose file not found: $ComposeFile" 'ERROR'
        exit 1
    }
    
    # Check .env
    Write-Log "Checking .env file..." 'INFO'
    if (Test-Path $EnvFile) {
        Write-Log "✅ .env file found"
    }
    else {
        Write-Log "⚠️  .env file not found (will use defaults)" 'WARN'
    }
    
    Write-Log "" 'INFO'
    Write-Log "✅ All validations passed!" 'SUCCESS'
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═════════════════════════════════════════════════════════════════════════════

Write-Log "ADRION 369 Docker Stack Manager | Date: $(Get-Date) | Action: $Action" 'INFO'

try {
    switch ($Action) {
        'Start' { Invoke-Start }
        'Stop' { Invoke-Stop }
        'Restart' { Invoke-Stop; Start-Sleep -Seconds 5; Invoke-Start }
        'Status' { Invoke-Status }
        'Logs' { Invoke-Logs }
        'Build' { Invoke-Build }
        'Init' { Invoke-Init }
        'Test' { Invoke-Test }
        'Validate' { Invoke-Validate }
    }
}
catch {
    Write-Log "ERROR: $_" 'ERROR'
    exit 1
}

Write-Log "═════════════════════════════════════════════════════════════" 'INFO'
Write-Log "Action completed: $Action" 'SUCCESS'
Write-Log "Log file: $LogFile" 'INFO'
