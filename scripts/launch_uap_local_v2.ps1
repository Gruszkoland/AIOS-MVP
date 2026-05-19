# ════════════════════════════════════════════════════════════════════════════
# launch_uap_local_v2.ps1 — Autonomous UAP Stack Launcher (Clean Unicode)
# ════════════════════════════════════════════════════════════════════════════

param(
    [switch]$NoMonitor,
    [switch]$Verbose,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
UAP Local Stack Launcher
========================

Usage: .\scripts\launch_uap_local_v2.ps1 [OPTIONS]

Options:
  -NoMonitor   Skip continuous process monitoring (exit after startup)
  -Verbose     Show detailed diagnostic output
  -Help        Show this help message

Ports:
  - Backend API: http://localhost:8002/mapi/v1/
  - Frontend:    http://localhost:8003/
  - Health:      http://localhost:8002/mapi/v1/health

Log Files:
  - logs/backend.log   (stdout)
  - logs/backend.err   (stderr)
  - logs/frontend.log  (stdout)
  - logs/frontend.err  (stderr)

"@
    exit 0
}

# Set working directory
$WorkDir = Split-Path -Parent $PSScriptRoot
Set-Location $WorkDir

$VerbosePreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

Write-Host "=" * 70
Write-Host "  ADRION 369 — UAP LOCAL STACK LAUNCHER"
Write-Host "=" * 70
Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 1: Initialize SQLite Database
# ────────────────────────────────────────────────────────────────────────────

Write-Host "[STEP 1] Initializing SQLite database..." -ForegroundColor Cyan

if (Test-Path "scripts/init_local_db.py") {
    try {
        $output = python scripts/init_local_db.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Database initialized successfully" -ForegroundColor Green
            Write-Verbose $output
        } else {
            Write-Host "[ERROR] Database initialization failed" -ForegroundColor Red
            Write-Host $output
            exit 1
        }
    } catch {
        Write-Host "[ERROR] Failed to run init_local_db.py: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERROR] scripts/init_local_db.py not found" -ForegroundColor Red
    exit 1
}

Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 2: Check and Clear Ports
# ────────────────────────────────────────────────────────────────────────────

Write-Host "[STEP 2] Checking ports 8002-8003..." -ForegroundColor Cyan

function Check-PortOccupied {
    param([int]$Port)
    try {
        $TcpConnection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        return $null -ne $TcpConnection
    } catch {
        return $false
    }
}

# Kill processes on port 8002
if (Check-PortOccupied 8002) {
    Write-Host "[WARN] Port 8002 is occupied, killing process..." -ForegroundColor Yellow
    try {
        $proc = Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty OwningProcess | 
                Get-Process -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            Write-Host "[OK] Process terminated" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARN] Could not forcefully kill port 8002: $_" -ForegroundColor Yellow
    }
}

# Kill processes on port 8003
if (Check-PortOccupied 8003) {
    Write-Host "[WARN] Port 8003 is occupied, killing process..." -ForegroundColor Yellow
    try {
        $proc = Get-NetTCPConnection -LocalPort 8003 -ErrorAction SilentlyContinue | 
                Select-Object -ExpandProperty OwningProcess | 
                Get-Process -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            Write-Host "[OK] Process terminated" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARN] Could not forcefully kill port 8003: $_" -ForegroundColor Yellow
    }
}

Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 3: Start Backend API (Port 8002)
# ────────────────────────────────────────────────────────────────────────────

Write-Host "[STEP 3] Starting Backend API on port 8002..." -ForegroundColor Cyan

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Start backend in background
$BackendProcess = Start-Process `
    -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "uap/backend/api.py" `
    -RedirectStandardOutput "logs/backend.log" `
    -RedirectStandardError "logs/backend.err" `
    -WindowStyle Hidden `
    -PassThru

Write-Host "[INFO] Backend process started (PID: $($BackendProcess.Id))" -ForegroundColor Cyan
Write-Host "[INFO] Waiting for health endpoint response (timeout: 30s)..." -ForegroundColor Cyan

# Health check with exponential backoff
$MaxAttempts = 30
$Attempt = 0
$BackendReady = $false

while ($Attempt -lt $MaxAttempts) {
    $Attempt++
    
    try {
        $response = Invoke-WebRequest `
            -Uri "http://localhost:8002/mapi/v1/health" `
            -Method GET `
            -TimeoutSec 2 `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Backend API responding (Status: $($response.StatusCode))" -ForegroundColor Green
            $BackendReady = $true
            break
        }
    } catch {
        Write-Verbose "[ATTEMPT $Attempt] Health check failed: $_"
    }

    if ($Attempt -lt $MaxAttempts) {
        Start-Sleep -Milliseconds 1000
    }
}

if (-not $BackendReady) {
    Write-Host "[ERROR] Backend API failed to respond after 30 seconds" -ForegroundColor Red
    Write-Host "[ERROR] Backend log:" -ForegroundColor Red
    Get-Content "logs/backend.log" -Tail 20 | ForEach-Object { Write-Host "  $_" }
    Write-Host "[ERROR] Backend errors:" -ForegroundColor Red
    Get-Content "logs/backend.err" -Tail 20 | ForEach-Object { Write-Host "  $_" }
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 4: Start Frontend HTTP Server (Port 8003)
# ────────────────────────────────────────────────────────────────────────────

Write-Host "[STEP 4] Starting Frontend HTTP server on port 8003..." -ForegroundColor Cyan

# Check if frontend directory exists
if (-not (Test-Path "uap/frontend")) {
    Write-Host "[ERROR] uap/frontend directory not found" -ForegroundColor Red
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Start frontend in background (serving from uap/frontend/)
$FrontendProcess = Start-Process `
    -FilePath ".venv\Scripts\python.exe" `
    -ArgumentList "-m", "http.server", "8003", "--directory", "uap/frontend" `
    -RedirectStandardOutput "logs/frontend.log" `
    -RedirectStandardError "logs/frontend.err" `
    -WindowStyle Hidden `
    -PassThru

Write-Host "[INFO] Frontend process started (PID: $($FrontendProcess.Id))" -ForegroundColor Cyan
Write-Host "[INFO] Waiting for HTTP response (timeout: 15s)..." -ForegroundColor Cyan

# Health check for frontend
$MaxAttempts = 15
$Attempt = 0
$FrontendReady = $false

while ($Attempt -lt $MaxAttempts) {
    $Attempt++
    
    try {
        $response = Invoke-WebRequest `
            -Uri "http://localhost:8003/" `
            -Method GET `
            -TimeoutSec 2 `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] Frontend server responding (Status: $($response.StatusCode))" -ForegroundColor Green
            $FrontendReady = $true
            break
        }
    } catch {
        Write-Verbose "[ATTEMPT $Attempt] Frontend check failed: $_"
    }

    if ($Attempt -lt $MaxAttempts) {
        Start-Sleep -Milliseconds 1000
    }
}

if (-not $FrontendReady) {
    Write-Host "[ERROR] Frontend server failed to respond after 15 seconds" -ForegroundColor Red
    Write-Host "[ERROR] Frontend log:" -ForegroundColor Red
    Get-Content "logs/frontend.log" -Tail 10 | ForEach-Object { Write-Host "  $_" }
    Write-Host "[ERROR] Frontend errors:" -ForegroundColor Red
    Get-Content "logs/frontend.err" -Tail 10 | ForEach-Object { Write-Host "  $_" }
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 5: Display Startup Summary
# ────────────────────────────────────────────────────────────────────────────

Write-Host "[STEP 5] Startup Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "████████████████████████████████████████" -ForegroundColor Green
Write-Host "  UAP Local Stack is READY" -ForegroundColor Green
Write-Host "████████████████████████████████████████" -ForegroundColor Green
Write-Host ""
Write-Host "ENDPOINTS:" -ForegroundColor White
Write-Host "  Frontend:  http://localhost:8003/" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8002/mapi/v1/" -ForegroundColor Cyan
Write-Host "  Health:    http://localhost:8002/mapi/v1/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "PROCESSES:" -ForegroundColor White
Write-Host "  Backend PID:  $($BackendProcess.Id)" -ForegroundColor Yellow
Write-Host "  Frontend PID: $($FrontendProcess.Id)" -ForegroundColor Yellow
Write-Host ""
Write-Host "LOGS:" -ForegroundColor White
Write-Host "  Backend:  logs/backend.log" -ForegroundColor Gray
Write-Host "  Frontend: logs/frontend.log" -ForegroundColor Gray
Write-Host ""

# ────────────────────────────────────────────────────────────────────────────
# STEP 6: Optional Continuous Monitoring
# ────────────────────────────────────────────────────────────────────────────

if ($NoMonitor) {
    Write-Host "[INFO] -NoMonitor flag set. Exiting (processes will continue running)." -ForegroundColor Cyan
    exit 0
}

Write-Host "[STEP 6] Starting Continuous Health Monitoring..." -ForegroundColor Cyan
Write-Host "[INFO] Press Ctrl+C to stop monitoring and exit" -ForegroundColor Gray
Write-Host ""

# Monitor loop with graceful shutdown on Ctrl+C
$MonitorInterval = 10  # seconds

try {
    while ($true) {
        # Check backend process
        $BackendStillRun = -not $BackendProcess.HasExited
        $BackendStatus = if ($BackendStillRun) { "Running [OK]" } else { "CRASHED [FAIL]" }
        
        # Check frontend process
        $FrontendStillRun = -not $FrontendProcess.HasExited
        $FrontendStatus = if ($FrontendStillRun) { "Running [OK]" } else { "CRASHED [FAIL]" }

        # Check health endpoints
        $BackendHealthOk = $false
        $FrontendHealthOk = $false

        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8002/mapi/v1/health" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
            $BackendHealthOk = $resp.StatusCode -eq 200
        } catch { }

        try {
            $resp = Invoke-WebRequest -Uri "http://localhost:8003/" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
            $FrontendHealthOk = $resp.StatusCode -eq 200
        } catch { }

        $timestamp = Get-Date -Format "HH:mm:ss"

        Write-Host "[$timestamp] Backend: $BackendStatus  |  Health: $(if ($BackendHealthOk) { '$true' } else { '$false' })" -ForegroundColor $(if ($BackendStillRun -and $BackendHealthOk) { "Green" } else { "Red" })
        Write-Host "[$timestamp] Frontend: $FrontendStatus  |  Health: $(if ($FrontendHealthOk) { '$true' } else { '$false' })" -ForegroundColor $(if ($FrontendStillRun -and $FrontendHealthOk) { "Green" } else { "Red" })

        # Check for crashes and restart if needed
        if (-not $BackendStillRun) {
            Write-Host "[ALERT] Backend process has exited. Consider restarting." -ForegroundColor Red
        }

        if (-not $FrontendStillRun) {
            Write-Host "[ALERT] Frontend process has exited. Consider restarting." -ForegroundColor Red
        }

        Start-Sleep -Seconds $MonitorInterval
    }
} catch [System.OperationCanceledException] {
    Write-Host ""
    Write-Host "[INFO] Monitoring stopped by user" -ForegroundColor Yellow
} finally {
    Write-Host ""
    Write-Host "[CLEANUP] Terminating processes..." -ForegroundColor Yellow
    
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    
    Start-Sleep -Milliseconds 500
    
    Write-Host "[OK] All processes stopped" -ForegroundColor Green
}
