<#
.SYNOPSIS
    ADRION 369 — Service Recovery Handler
.DESCRIPTION
    Podejmuje próby przywrócenia zatrzymanych serwisów.
    Wywoływany automatycznie przez monitor-services.ps1 lub ręcznie.
.PARAMETER ServiceName
    Nazwa serwisu do odzyskania (lub "all")
.PARAMETER Root
    Katalog główny projektu
.EXAMPLE
    .\scripts\monitoring\recover-services.ps1 -ServiceName adrion-vortex
    .\scripts\monitoring\recover-services.ps1 -ServiceName all
#>
[CmdletBinding()]
param(
    [string]$ServiceName = "all",
    [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = 'SilentlyContinue'

$COMPOSE_FILE = Join-Path $Root "adrion-swarm\docker-compose.yml"
$VENV_PY      = Join-Path $Root ".venv\Scripts\python.exe"
$LOG_DIR      = Join-Path $Root "logs\monitor"
$LOG_FILE     = Join-Path $LOG_DIR "recover-$(Get-Date -Format 'yyyyMMdd').log"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

function Write-Log {
    param([string]$Level, [string]$Msg)
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] [RECOVER/$Level] $Msg"
    Add-Content $LOG_FILE -Value $line -Encoding UTF8
    Write-Host $line -ForegroundColor $(switch ($Level) { "OK" {"Green"} "FAIL" {"Red"} "WARN" {"Yellow"} default {"Gray"} })
}

# ── Docker container recovery ─────────────────────────────────────────────────
function Recover-DockerService {
    param([string]$Name)

    $status = docker inspect $Name --format '{{.State.Status}}' 2>$null

    switch ($status) {
        "exited" {
            Write-Log "WARN" "$Name: exited — restart..."
            docker compose -f $COMPOSE_FILE restart $Name 2>&1 | Out-Null
            Start-Sleep 8
            $newStatus = docker inspect $Name --format '{{.State.Status}}' 2>$null
            if ($newStatus -eq "running") { Write-Log "OK" "$Name: odzyskany (restart)" }
            else { Write-Log "FAIL" "$Name: restart nie pomógł (status=$newStatus)" }
        }
        "restarting" {
            Write-Log "WARN" "$Name: zapętlony restart — czekam 15s..."
            Start-Sleep 15
        }
        "dead" {
            Write-Log "WARN" "$Name: dead — pełne up..."
            docker compose -f $COMPOSE_FILE up -d $Name 2>&1 | Out-Null
            Start-Sleep 10
        }
        { [string]::IsNullOrEmpty($_) } {
            Write-Log "WARN" "$Name: nie znaleziony — docker compose up..."
            docker compose -f $COMPOSE_FILE up -d $Name 2>&1 | Out-Null
            Start-Sleep 10
        }
        default {
            Write-Log "WARN" "$Name: status=$status — restart..."
            docker compose -f $COMPOSE_FILE restart $Name 2>&1 | Out-Null
            Start-Sleep 8
        }
    }

    # Verify
    $finalStatus = docker inspect $Name --format '{{.State.Status}}' 2>$null
    $health      = docker inspect $Name --format '{{.State.Health.Status}}' 2>$null
    Write-Log "OK" "$Name: status=$finalStatus health=$health"
}

# ── PostgreSQL specific recovery ──────────────────────────────────────────────
function Recover-Postgres {
    Write-Log "WARN" "adrion-db: PostgreSQL odzyskiwanie..."
    Recover-DockerService -Name "adrion-db"

    # Wait for pg_isready
    $waited = 0
    while ($waited -lt 30) {
        $ready = docker exec adrion-db pg_isready -U adrion -d genesis_record 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "OK" "adrion-db: pg_isready OK ($waited s)"
            return
        }
        Start-Sleep 3; $waited += 3
    }
    Write-Log "FAIL" "adrion-db: pg_isready timeout"
}

# ── Arbitrage API recovery ────────────────────────────────────────────────────
function Recover-ArbitrageApi {
    Write-Log "WARN" "arbitrage-api: Sprawdzam proces..."

    # Check if process is stuck
    $pidFile = Join-Path $Root ".runtime\waitress.pid"
    if (Test-Path $pidFile) {
        $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($oldPid) {
            $proc = Get-Process -Id ([int]$oldPid) -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Log "WARN" "arbitrage-api: zatrzymuję PID $oldPid..."
                Stop-Process -Id ([int]$oldPid) -Force
                Start-Sleep 2
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }

    # Restart
    $startScript = Join-Path $Root "scripts\prod\start-prod.ps1"
    if (Test-Path $startScript) {
        Write-Log "WARN" "arbitrage-api: uruchamiam przez start-prod.ps1..."
        & $startScript 2>&1 | Out-Null
        Start-Sleep 5

        # Verify
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8001/api/arbitrage/status" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            Write-Log "OK" "arbitrage-api: odzyskana (HTTP $($r.StatusCode))"
        } catch {
            Write-Log "FAIL" "arbitrage-api: nadal niedostępna po restarcie"
        }
    } else {
        Write-Log "WARN" "arbitrage-api: brak start-prod.ps1 — uruchamiam bezpośrednio..."
        $apiScript = Join-Path $Root "arbitrage\main.py"
        if (Test-Path $apiScript) {
            Start-Process -FilePath $VENV_PY -ArgumentList $apiScript -WindowStyle Hidden -WorkingDirectory $Root
            Start-Sleep 5
        }
    }
}

# ── Full stack recovery ───────────────────────────────────────────────────────
function Recover-FullStack {
    Write-Log "WARN" "Full stack recovery — docker compose up..."
    if (Test-Path $COMPOSE_FILE) {
        docker compose -f $COMPOSE_FILE up -d 2>&1 | Out-Null
        Start-Sleep 15
        $running = docker ps --filter "name=adrion" --format "{{.Names}}" 2>$null
        $running | ForEach-Object { Write-Log "OK" "Kontener uruchomiony: $_" }
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
Write-Log "WARN" "Recovery start — target: $ServiceName"

switch ($ServiceName.ToLower()) {
    "all" {
        Recover-FullStack
        Recover-ArbitrageApi
    }
    "adrion-db"     { Recover-Postgres }
    "adrion-vortex" { Recover-DockerService -Name "adrion-vortex" }
    "adrion-healer" { Recover-DockerService -Name "adrion-healer" }
    "adrion-n8n"    { Recover-DockerService -Name "adrion-n8n" }
    "arbitrage-api" { Recover-ArbitrageApi }
    default         { Recover-DockerService -Name $ServiceName }
}

Write-Log "OK" "Recovery zakończony dla: $ServiceName"
