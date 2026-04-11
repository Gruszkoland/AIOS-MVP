<#
.SYNOPSIS
    Startup script: Docker Desktop + Harmonia 369 Dashboard + Webhook API
.DESCRIPTION
    Automatyczne uruchomienie calego stacku ADRION 369.
    Port 3690 = Dashboard, Port 3691 = Webhook API
#>

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_PYTHON = Join-Path $ROOT ".venv\Scripts\python.exe"
$DASHBOARD_DIR = Join-Path $ROOT "harmonia-dashboard"

Write-Host "=== ADRION 369 — Harmonia Startup ===" -ForegroundColor Cyan

# 1. Docker Desktop
$docker = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "[1/3] Uruchamiam Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    $timeout = 60
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep 3
        $elapsed += 3
        try {
            docker info 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) { break }
        } catch {}
    }
    if ($elapsed -ge $timeout) {
        Write-Host "[WARN] Docker nie odpowiada po ${timeout}s" -ForegroundColor Red
    } else {
        Write-Host "[1/3] Docker Desktop gotowy ($elapsed s)" -ForegroundColor Green
    }
} else {
    Write-Host "[1/3] Docker Desktop juz dziala" -ForegroundColor Green
}

# 2. Docker containers
Write-Host "[2/3] Sprawdzam kontenery..." -ForegroundColor Yellow
$dbRunning = docker ps --filter "name=adrion-db" --format "{{.Status}}" 2>$null
if (-not $dbRunning) {
    Write-Host "       Uruchamiam compose..." -ForegroundColor Yellow
    docker compose -f (Join-Path $ROOT "docker-compose.prod.yml") up -d 2>$null
    Start-Sleep 5
}
$containers = docker ps --format "{{.Names}}: {{.Status}}" 2>$null
Write-Host "       Kontenery:" -ForegroundColor Green
$containers | ForEach-Object { Write-Host "         $_" }

# 3. Dashboard server (3690)
$port3690 = netstat -ano | Select-String "LISTENING" | Select-String ":3690 "
if (-not $port3690) {
    Write-Host "[3/3] Uruchamiam serve.py (port 3690)..." -ForegroundColor Yellow
    Start-Process -FilePath $VENV_PYTHON -ArgumentList (Join-Path $DASHBOARD_DIR "serve.py") -WindowStyle Hidden
    Start-Sleep 2
} else {
    Write-Host "[3/3] Dashboard (3690) juz aktywny" -ForegroundColor Green
}

# 4. Webhook server (3691)
$port3691 = netstat -ano | Select-String "LISTENING" | Select-String ":3691 "
if (-not $port3691) {
    Write-Host "       Uruchamiam webhook_server.py (port 3691)..." -ForegroundColor Yellow
    Start-Process -FilePath $VENV_PYTHON -ArgumentList (Join-Path $DASHBOARD_DIR "webhook_server.py") -WindowStyle Hidden
    Start-Sleep 3
} else {
    Write-Host "       Webhook API (3691) juz aktywny" -ForegroundColor Green
}

# 5. Health check
Write-Host ""
Write-Host "=== Health Check ===" -ForegroundColor Cyan
try {
    $stats = Invoke-WebRequest -Uri "http://localhost:3691/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  API Health: $($stats.Content)" -ForegroundColor Green
} catch {
    Write-Host "  API Health: NIEDOSTEPNY (poczekaj kilka sekund)" -ForegroundColor Yellow
}
try {
    $dash = Invoke-WebRequest -Uri "http://localhost:3690" -UseBasicParsing -TimeoutSec 5
    Write-Host "  Dashboard:  OK ($($dash.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  Dashboard:  NIEDOSTEPNY" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Dashboard: http://localhost:3690" -ForegroundColor White
Write-Host "  API:       http://localhost:3691" -ForegroundColor White
Write-Host "=== Gotowe ===" -ForegroundColor Cyan
