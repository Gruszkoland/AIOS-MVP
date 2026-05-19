#!/usr/bin/env pwsh
<#
.SYNOPSIS
UAP Local Stack Launcher — Samodzielna Automatyzacja
Uruchamia backend API (8002) + frontend (8003) w jednej komendzie.

.DESCRIPTION
Automatycznie:
1. Inicjalizuje bazę danych (SQLite)
2. Uruchamia backend API na http://localhost:8002
3. Uruchamia frontend na http://localhost:8003
4. Monitoruje oba procesy
5. Wyświetla diagnostykę

.USAGE
    pwsh scripts/launch_uap_local.ps1

.NOTES
Po starcie:
- Backend API: http://localhost:8002/mapi/v1/
- Frontend: http://localhost:8003/
- Health check: http://localhost:8002/health
#>

param(
    [switch]$NoMonitor,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$BackendPort = 8002
$FrontendPort = 8003

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🚀 UAP LOCAL STACK LAUNCHER" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 1: Init Database
# ─────────────────────────────────────────────────────────────────────────

Write-Host "🔧 STEP 1: Initializing database..." -ForegroundColor Yellow
python scripts/init_local_db.py | Out-Null
Write-Host "✅ Database ready" -ForegroundColor Green
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 2: Verify ports are free
# ─────────────────────────────────────────────────────────────────────────

Write-Host "🔍 STEP 2: Checking ports..." -ForegroundColor Yellow

$PortsOccupied = $false

# Check backend port
$BackendCheck = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if ($BackendCheck) {
    Write-Host "  ⚠️  Port $BackendPort already in use - killing process..." -ForegroundColor Yellow
    Stop-Process -Id $BackendCheck.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Check frontend port
$FrontendCheck = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
if ($FrontendCheck) {
    Write-Host "  ⚠️  Port $FrontendPort already in use - killing process..." -ForegroundColor Yellow
    Stop-Process -Id $FrontendCheck.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "  ✅ Ports $BackendPort, $FrontendPort are free" -ForegroundColor Green
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 3: Start Backend API (in background)
# ─────────────────────────────────────────────────────────────────────────

Write-Host "🚀 STEP 3: Starting Backend API (port $BackendPort)..." -ForegroundColor Yellow

$BackendProcess = Start-Process `
    -FilePath python `
    -ArgumentList "uap/backend/api.py" `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput "logs/backend.log" `
    -RedirectStandardError "logs/backend.err"

Write-Host "  ✅ Backend process started (PID: $($BackendProcess.Id))" -ForegroundColor Green

# Wait for backend to be ready
Write-Host "  ⏳ Waiting for API initialization..." -ForegroundColor Gray
for ($i = 1; $i -le 30; $i++) {
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -ErrorAction SilentlyContinue
        if ($health.StatusCode -eq 200) {
            Write-Host "  ✅ Backend ready at http://localhost:$BackendPort/mapi/v1/" -ForegroundColor Green
            break
        }
    }
    catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 4: Start Frontend Server (in background)
# ─────────────────────────────────────────────────────────────────────────

Write-Host "🎨 STEP 4: Starting Frontend (port $FrontendPort)..." -ForegroundColor Yellow

# Check if Python simple HTTP server is available or use alternative
$FrontendProcess = Start-Process `
    -FilePath python `
    -ArgumentList "-m", "http.server", "$FrontendPort", "--directory", "uap/frontend" `
    -PassThru `
    -WindowStyle Hidden `
    -RedirectStandardOutput "logs/frontend.log" `
    -RedirectStandardError "logs/frontend.err"

Write-Host "  ✅ Frontend process started (PID: $($FrontendProcess.Id))" -ForegroundColor Green

# Wait for frontend
Write-Host "  ⏳ Waiting for frontend..." -ForegroundColor Gray
for ($i = 1; $i -le 15; $i++) {
    try {
        $frontend = Invoke-WebRequest -Uri "http://localhost:$FrontendPort/" -ErrorAction SilentlyContinue
        if ($frontend.StatusCode -eq 200) {
            Write-Host "  ✅ Frontend ready at http://localhost:$FrontendPort/" -ForegroundColor Green
            break
        }
    }
    catch { }
    Write-Host -NoNewline "."
    Start-Sleep -Seconds 1
}
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 5: Display URLs & Status
# ─────────────────────────────────────────────────────────────────────────

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ UAP LOCAL STACK RUNNING" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "📋 URLS:" -ForegroundColor Cyan
Write-Host "  🌐 Frontend:        http://localhost:$FrontendPort/" -ForegroundColor White
Write-Host "  🔌 Backend API:     http://localhost:$BackendPort/mapi/v1/" -ForegroundColor White
Write-Host "  💚 Health Check:    http://localhost:$BackendPort/health" -ForegroundColor White
Write-Host ""
Write-Host "📊 PROCESSES:" -ForegroundColor Cyan
Write-Host "  Backend (API):      PID $($BackendProcess.Id)" -ForegroundColor White
Write-Host "  Frontend (HTTP):    PID $($FrontendProcess.Id)" -ForegroundColor White
Write-Host ""
Write-Host "📝 LOGS:" -ForegroundColor Cyan
Write-Host "  Backend:  logs/backend.log (errors: logs/backend.err)" -ForegroundColor Gray
Write-Host "  Frontend: logs/frontend.log (errors: logs/frontend.err)" -ForegroundColor Gray
Write-Host ""
Write-Host "⏸️  To stop: Run 'Stop-UAP-Local' or close this window" -ForegroundColor Yellow
Write-Host ""

# ─────────────────────────────────────────────────────────────────────────
# STEP 6: Continuous Monitoring (unless -NoMonitor)
# ─────────────────────────────────────────────────────────────────────────

if (-not $NoMonitor) {
    Write-Host "🔍 MONITORING... Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host ""
    
    while ($true) {
        # Check if processes still running
        $BackendStillRun = Get-Process -Id $BackendProcess.Id -ErrorAction SilentlyContinue
        $FrontendStillRun = Get-Process -Id $FrontendProcess.Id -ErrorAction SilentlyContinue
        
        $BackendStatus = if ($BackendStillRun) { "🟢 Running" } else { "🔴 CRASHED" }
        $FrontendStatus = if ($FrontendStillRun) { "🟢 Running" } else { "🔴 CRASHED" }
        
        Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Backend: $BackendStatus | Frontend: $FrontendStatus" -NoNewline -ForegroundColor Gray
        
        Start-Sleep -Seconds 10
    }
}
else {
    Write-Host "Press any key to stop servers..." -ForegroundColor Yellow
    [void][System.Console]::ReadKey($true)
    
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProcess.Id -Force
    Stop-Process -Id $FrontendProcess.Id -Force
    Write-Host "✅ All processes stopped" -ForegroundColor Green
}
