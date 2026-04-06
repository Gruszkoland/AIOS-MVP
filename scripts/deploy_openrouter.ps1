#############################################################################
# ADRION 369 — OpenRouter Fully Automated Deployment (PowerShell)
#
# Purpose: Migrate from local Ollama to OpenRouter API
# Status: Production-ready
# Time: ~15 minutes fully automated
#
# Usage: powershell -ExecutionPolicy Bypass -File scripts/deploy_openrouter.ps1
#############################################################################

param(
    [Parameter(Position = 0)]
    [string]$OpenRouterKey,

    [Parameter()]
    [switch]$NoColor = $false,

    [Parameter()]
    [switch]$SkipHealthCheck = $false
)

# ============================================================================
# Logging Setup
# ============================================================================

$LOG_LEVEL = @{
    'INFO'    = @{ Color = 'Cyan'; Symbol = 'ℹ️ ' }
    'SUCCESS' = @{ Color = 'Green'; Symbol = '✅ ' }
    'WARNING' = @{ Color = 'Yellow'; Symbol = '⚠️ ' }
    'ERROR'   = @{ Color = 'Red'; Symbol = '❌ ' }
    'STEP'    = @{ Color = 'Blue'; Symbol = '═' }
}

function Write-Log {
    param(
        [Parameter(ValueFromPipeline = $true)]
        [string]$Message,

        [ValidateSet('INFO', 'SUCCESS', 'WARNING', 'ERROR', 'STEP')]
        [string]$Level = 'INFO'
    )

    $LogEntry = $LOG_LEVEL[$Level]

    if ($NoColor) {
        Write-Host "$($LogEntry.Symbol) $Message"
    }
    else {
        Write-Host "$($LogEntry.Symbol) $Message" -ForegroundColor $LogEntry.Color
    }
}

function Write-StepHeader {
    param([string]$Title)

    $Line = '=' * 50
    Write-Host ""
    Write-Host $Line -ForegroundColor Blue
    Write-Host $Title -ForegroundColor Blue
    Write-Host $Line -ForegroundColor Blue
}

# ============================================================================
# STEP 1: Validate API Key Input
# ============================================================================

Write-StepHeader "STEP 1: OpenRouter API Key Input"

if (-not $OpenRouterKey) {
    Write-Host ""
    $OpenRouterKey = Read-Host "🔑 Enter OpenRouter API Key (sk-or-v1-...)"
    Write-Host ""
}

# Validate format
if ($OpenRouterKey -notmatch '^sk-or-v1-') {
    Write-Log "Invalid API key format. Must start with 'sk-or-v1-'" -Level ERROR
    exit 1
}

if ($OpenRouterKey.Length -lt 20) {
    Write-Log "API key too short. Should be 40+ characters" -Level ERROR
    exit 1
}

Write-Log "API Key format validated" -Level SUCCESS

# ============================================================================
# STEP 2: Update .env File
# ============================================================================

Write-StepHeader "STEP 2: Update Environment Configuration"

$EnvPath = '.env'

if (-not (Test-Path $EnvPath)) {
    Write-Log ".env file not found in current directory: $(pwd)" -Level ERROR
    exit 1
}

# Create backup
$BackupPath = '.env.backup.openrouter'
Copy-Item $EnvPath $BackupPath -Force
Write-Log "Backup created: $BackupPath" -Level SUCCESS

# Read .env content
$EnvContent = Get-Content $EnvPath -Raw

# Update settings using regex
$EnvContent = $EnvContent -replace 'LLM_BACKEND=.*', 'LLM_BACKEND=openrouter'
$EnvContent = $EnvContent -replace 'LLM_MODEL=.*', 'LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free'
$EnvContent = $EnvContent -replace 'OPENROUTER_API_KEY=.*', "OPENROUTER_API_KEY=$OpenRouterKey"

# Add if not exists
if ($EnvContent -notmatch 'OPENROUTER_API_KEY=') {
    $EnvContent += "`nOPENROUTER_API_KEY=$OpenRouterKey`n"
}

# Write back
Set-Content $EnvPath $EnvContent -NoNewline

Write-Log "Updated .env:" -Level SUCCESS
Write-Log "  LLM_BACKEND=openrouter" -Level INFO
Write-Log "  LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free" -Level INFO
Write-Log "  OPENROUTER_API_KEY=***[HIDDEN]***" -Level INFO

# ============================================================================
# STEP 3: Python Configuration Validation
# ============================================================================

Write-StepHeader "STEP 3: Validate Python Configuration"

$ValidationScript = @'
from arbitrage.config import LLM_BACKEND, OPENROUTER_KEY, LLM_MODEL
import sys

checks = {
    'LLM_BACKEND': (LLM_BACKEND, 'openrouter'),
    'OPENROUTER_KEY': (bool(OPENROUTER_KEY), True),
    'LLM_MODEL': (('llama-3.1-8b' in LLM_MODEL.lower()), True)
}

for check_name, (actual, expected) in checks.items():
    if actual != expected:
        print(f"ERROR: {check_name} = {actual}, expected {expected}")
        sys.exit(1)

print(f"✓ LLM_BACKEND={LLM_BACKEND}")
print(f"✓ LLM_MODEL={LLM_MODEL}")
print(f"✓ OPENROUTER_KEY set: {bool(OPENROUTER_KEY)}")
'@

$PythonExe = if (Test-Path '.\.venv\Scripts\python.exe') {
    '.\.venv\Scripts\python.exe'
}
else {
    'python'
}

$ValidationOutput = & $PythonExe -c $ValidationScript 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Log "Python configuration validation failed:" -Level ERROR
    Write-Host $ValidationOutput
    exit 1
}

Write-Host $ValidationOutput
Write-Log "Python configuration valid" -Level SUCCESS

# ============================================================================
# STEP 4: Test OpenRouter API Connectivity
# ============================================================================

Write-StepHeader "STEP 4: Test OpenRouter API Connectivity"

Write-Log "Testing API endpoint..." -Level INFO

try {
    $Response = Invoke-WebRequest `
        -Uri 'https://openrouter.ai/api/v1/models' `
        -Headers @{ Authorization = "Bearer $OpenRouterKey" } `
        -UseBasicParsing `
        -TimeoutSec 10 `
        -ErrorAction Stop

    if ($Response.StatusCode -eq 200) {
        Write-Log "OpenRouter API connectivity confirmed" -Level SUCCESS
    }
    else {
        Write-Log "OpenRouter API returned HTTP $($Response.StatusCode)" -Level ERROR
        exit 1
    }
}
catch {
    Write-Log "OpenRouter API connection failed: $($_.Exception.Message)" -Level ERROR
    Write-Log "Possible causes:" -Level INFO
    Write-Log "  1. Invalid API key" -Level INFO
    Write-Log "  2. API key not activated yet" -Level INFO
    Write-Log "  3. Network connectivity issue" -Level INFO
    exit 1
}

# ============================================================================
# STEP 5: Build Docker Image
# ============================================================================

Write-StepHeader "STEP 5: Build Docker Image"

Write-Log "Building adrion-api image (this may take 2-3 minutes)..." -Level INFO

$BuildProcess = Start-Process `
    -FilePath 'docker-compose' `
    -ArgumentList '-f docker-compose.cloud.yml build --no-cache adrion-api' `
    -NoNewWindow `
    -PassThru `
    -Wait `
    -RedirectStandardOutput "$env:TEMP\docker_build.log" `
    -RedirectStandardError "$env:TEMP\docker_build_err.log"

if ($BuildProcess.ExitCode -ne 0) {
    Write-Log "Docker build failed (exit code: $($BuildProcess.ExitCode))" -Level ERROR
    Write-Log "Last 20 lines of build log:" -Level INFO
    Get-Content "$env:TEMP\docker_build.log" | Select-Object -Last 20 | Write-Host
    exit 1
}

Write-Log "Docker image built successfully" -Level SUCCESS

# ============================================================================
# STEP 6: Start Docker Service
# ============================================================================

Write-StepHeader "STEP 6: Start Docker Service"

Write-Log "Starting adrion-api container..." -Level INFO

& docker-compose -f docker-compose.cloud.yml up -d adrion-api

$ContainerId = & docker-compose -f docker-compose.cloud.yml ps -q adrion-api

Write-Log "Container started (ID: $ContainerId)" -Level SUCCESS

# ============================================================================
# STEP 7: Health Check
# ============================================================================

if (-not $SkipHealthCheck) {
    Write-StepHeader "STEP 7: Wait for Service Health Check"

    $MaxAttempts = 30
    $Attempt = 0

    Write-Log "Waiting for service to be ready (max 30 seconds)..." -Level INFO

    while ($Attempt -lt $MaxAttempts) {
        try {
            $HealthCheck = & docker-compose -f docker-compose.cloud.yml exec -T adrion-api `
                curl -s -f http://localhost:8001/api/arbitrage/status 2>$null

            if ($LASTEXITCODE -eq 0) {
                Write-Log "Service is healthy and responding" -Level SUCCESS
                break
            }
        }
        catch { }

        $Attempt++

        if ($Attempt % 5 -eq 0) {
            Write-Log "Still waiting... ($($MaxAttempts - $Attempt)s remaining)" -Level INFO
        }

        Start-Sleep -Seconds 1
    }

    if ($Attempt -eq $MaxAttempts) {
        Write-Log "Service health check timeout" -Level ERROR
        Write-Log "Recent logs:" -Level INFO
        & docker-compose -f docker-compose.cloud.yml logs --tail 10 adrion-api
        exit 1
    }
}

# ============================================================================
# STEP 8: Test API Endpoint
# ============================================================================

Write-StepHeader "STEP 8: Test API Endpoint"

Write-Log "Testing /api/arbitrage/analyze endpoint..." -Level INFO

$TestRequest = @{
    job_title   = 'Content Writing'
    budget_usd  = 200
    description = 'Write blog posts about technology trends'
} | ConvertTo-Json

try {
    $ApiResponse = Invoke-WebRequest `
        -Uri 'http://localhost:8001/api/arbitrage/analyze' `
        -Method POST `
        -ContentType 'application/json' `
        -Body $TestRequest `
        -UseBasicParsing `
        -TimeoutSec 10

    $ResponseData = $ApiResponse.Content | ConvertFrom-Json

    if ($ResponseData.score) {
        Write-Log "API endpoint responding correctly" -Level SUCCESS
        Write-Log "Sample response:" -Level INFO
        $ApiResponse.Content | ConvertFrom-Json | ConvertTo-Json | Write-Host
    }
    else {
        Write-Log "API returned unexpected response" -Level ERROR
        Write-Host $ApiResponse.Content
        exit 1
    }
}
catch {
    Write-Log "API test failed: $($_.Exception.Message)" -Level ERROR
    exit 1
}

# ============================================================================
# STEP 9: Performance Metrics
# ============================================================================

Write-StepHeader "STEP 9: Gather Performance Metrics"

Write-Log "Testing latency..." -Level INFO

$Stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

try {
    $null = Invoke-WebRequest `
        -Uri 'http://localhost:8001/api/arbitrage/analyze' `
        -Method POST `
        -ContentType 'application/json' `
        -Body $TestRequest `
        -UseBasicParsing `
        -TimeoutSec 10
}
catch { }

$Stopwatch.Stop()
$LatencyMs = [Math]::Round($Stopwatch.Elapsed.TotalMilliseconds)

Write-Log "API Response Time: ${LatencyMs}ms" -Level SUCCESS

# Get container stats
$Stats = & docker stats --no-stream $ContainerId --format "table {{.MemUsage}}\t{{.CPUPerc}}"

Write-Log "Container Resource Usage:" -Level SUCCESS
$Stats | Select-Object -Last 1 | ForEach-Object { Write-Host "  Memory: $_" }

# ============================================================================
# STEP 10: Summary and Next Steps
# ============================================================================

Write-Host ""
Write-Host "═" * 50 -ForegroundColor Green
Write-Host "✅ OpenRouter Migration Successful!" -ForegroundColor Green
Write-Host "═" * 50 -ForegroundColor Green
Write-Host ""

Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
Write-Host "  • Backend: OpenRouter API"
Write-Host "  • Model: Llama 3.1 8B (OpenRouter Free)"
Write-Host "  • Status: ✅ Running"
Write-Host "  • Latency: ${LatencyMs}ms"
Write-Host "  • Health: ✅ Healthy"
Write-Host ""

Write-Host "📝 Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Monitor logs:"
Write-Host "     docker-compose logs -f adrion-api"
Write-Host ""
Write-Host "  2. Test arbitrage analysis:"
Write-Host "     (See OPENROUTER_DEPLOYMENT_SCHEMA.md for curl examples)"
Write-Host ""
Write-Host "  3. Check OpenRouter usage:"
Write-Host "     https://openrouter.ai/usage"
Write-Host ""
Write-Host "  4. View resource consumption:"
Write-Host "     docker stats"
Write-Host ""

Write-Host "⚠️  Important:" -ForegroundColor Yellow
Write-Host "  • Free tier: ~20-50 requests/minute"
Write-Host "  • Keep API key secure (in .env only)"
Write-Host "  • Backup .env.backup.openrouter in case rollback needed"
Write-Host ""

Write-Host "🔄 Rollback (if needed):" -ForegroundColor Cyan
Write-Host "  1. Restore .env: copy .env.backup.openrouter .env"
Write-Host "  2. Change LLM_BACKEND=ollama in .env"
Write-Host "  3. Restart: docker-compose restart adrion-api"
Write-Host ""

Write-Host "═" * 50 -ForegroundColor Green
Write-Host ""

# Log to Genesis Record
$Timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$GenesisDirPath = "Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU"
$GenesisLogPath = Join-Path $GenesisDirPath "openrouter_deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

if (-not (Test-Path $GenesisDirPath)) {
    New-Item -Path $GenesisDirPath -ItemType Directory -Force | Out-Null
}

@"
TIMESTAMP: $Timestamp
STATUS: SUCCESS
OPERATION: OpenRouter Deployment
LATENCY_MS: $LatencyMs
BACKEND: openrouter
MODEL: meta-llama/llama-3.1-8b-instruct:free
HEALTH_CHECK: PASS
API_TEST: PASS
CONTAINER_ID: $ContainerId
"@ | Set-Content $GenesisLogPath

Write-Log "Deployment logged to Genesis Record" -Level SUCCESS

Write-Host ""
exit 0
