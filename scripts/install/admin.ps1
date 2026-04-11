<#
.SYNOPSIS
    ADRION 369 — Master Admin CLI
.DESCRIPTION
    Centralny punkt sterowania systemem ADRION 369.
    Uruchamianie, zatrzymywanie, monitorowanie, backupy, migracje, logi.
.PARAMETER Command
    Polecenie do wykonania (patrz: admin.ps1 help)
.PARAMETER ExtraArgs
    Argumenty polecenia
.EXAMPLE
    .\admin.ps1 status
    .\admin.ps1 start
    .\admin.ps1 logs arbitrage-api -Lines 100
    .\admin.ps1 db migrate --target 002
    .\admin.ps1 backup
    .\admin.ps1 health
#>
[CmdletBinding(PositionalBinding=$false)]
param(
    [Parameter(Position=0)]
    [string]$Command = "help",

    [Parameter(Position=1, ValueFromRemainingArguments=$true)]
    [string[]]$ExtraArgs = @()
)

Set-StrictMode -Off
$ErrorActionPreference = 'SilentlyContinue'

# ── Root detection ────────────────────────────────────────────────────────────
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_PY   = Join-Path $Root ".venv\Scripts\python.exe"
$COMPOSE   = Join-Path $Root "adrion-swarm\docker-compose.yml"
$LOG_DIR   = Join-Path $Root "logs"
$RUNTIME   = Join-Path $Root ".runtime"

New-Item -ItemType Directory -Force -Path $RUNTIME | Out-Null
New-Item -ItemType Directory -Force -Path $LOG_DIR  | Out-Null

# ── Version ───────────────────────────────────────────────────────────────────
$VERSION_FILE = Join-Path $Root "VERSION"
$VERSION = if (Test-Path $VERSION_FILE) {
    (Get-Content $VERSION_FILE -Raw).Trim()
} else { "unknown" }

# ── Color helpers ─────────────────────────────────────────────────────────────
function Write-OK      { param($M) Write-Host "  [OK]  $M" -ForegroundColor Green  }
function Write-FAIL    { param($M) Write-Host " [FAIL] $M" -ForegroundColor Red    }
function Write-WARN    { param($M) Write-Host " [WARN] $M" -ForegroundColor Yellow }
function Write-INFO    { param($M) Write-Host " [INFO] $M" -ForegroundColor Cyan   }
function Write-Section { param($T) Write-Host "`n=== $T ===" -ForegroundColor Magenta }

# ── .env loader ───────────────────────────────────────────────────────────────
function Load-Env {
    $envFile = Join-Path $Root ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
            $k, $v = $_ -split "=", 2
            if (-not [System.Environment]::GetEnvironmentVariable($k)) {
                [System.Environment]::SetEnvironmentVariable($k, $v)
            }
        }
    }
}
Load-Env

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────────────

function Cmd-Help {
    Write-Host ""
    Write-Host "  ADRION 369 Admin CLI v$VERSION" -ForegroundColor Magenta
    Write-Host "  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  USAGE:  .\admin.ps1 <command> [args]" -ForegroundColor White
    Write-Host ""
    Write-Host "  SYSTEM CONTROL" -ForegroundColor Yellow
    Write-Host "    start              Start all services (Docker + arbitrage-api)"
    Write-Host "    stop               Stop all services"
    Write-Host "    restart            Restart all services"
    Write-Host "    status             Show status of all components"
    Write-Host "    health             Full health check (one-shot)"
    Write-Host ""
    Write-Host "  LOGS" -ForegroundColor Yellow
    Write-Host "    logs [service]     Tail logs. Services:"
    Write-Host "                       adrion-db | adrion-vortex | adrion-n8n"
    Write-Host "                       adrion-healer | arbitrage-api | maintenance"
    Write-Host "    logs --lines N     Show last N lines (default: 50)"
    Write-Host ""
    Write-Host "  DATABASE" -ForegroundColor Yellow
    Write-Host "    db migrate         Run pending migrations (up)"
    Write-Host "    db migrate --target NNN  Migrate to version"
    Write-Host "    db rollback --target NNN  Roll back to version"
    Write-Host "    db validate        Check integrity + schema"
    Write-Host "    db backup          Create DB backup now"
    Write-Host "    db optimize        VACUUM + ANALYZE"
    Write-Host "    db status          Migration status + DB info"
    Write-Host ""
    Write-Host "  MAINTENANCE" -ForegroundColor Yellow
    Write-Host "    backup             Full backup (SQLite + PostgreSQL + config)"
    Write-Host "    backup --dest DIR  Backup to custom directory"
    Write-Host "    cleanup            Remove old logs"
    Write-Host "    optimize           Run DB optimizer"
    Write-Host ""
    Write-Host "  SECRETS & CONFIG" -ForegroundColor Yellow
    Write-Host "    secrets generate   Generate new secrets in .env"
    Write-Host "    secrets rotate KEY Rotate a specific secret"
    Write-Host "    secrets validate   Check .env for weak secrets"
    Write-Host "    env                Show loaded environment (secrets masked)"
    Write-Host ""
    Write-Host "  DEVELOPMENT" -ForegroundColor Yellow
    Write-Host "    dev                Start in development mode (debug)"
    Write-Host "    test               Run test suite (pytest + go test)"
    Write-Host "    lint               Run linting (ruff + go vet)"
    Write-Host "    build              Build Go vortex binary"
    Write-Host ""
    Write-Host "  MONITORING" -ForegroundColor Yellow
    Write-Host "    monitor            Start background health monitor"
    Write-Host "    monitor --stop     Stop background monitor"
    Write-Host "    maintain           Start maintenance daemon"
    Write-Host ""
    Write-Host "  MISC" -ForegroundColor Yellow
    Write-Host "    setup              Run full installer"
    Write-Host "    ui                 Open admin dashboard in browser"
    Write-Host "    version            Show version information"
    Write-Host ""
}

# ── version ───────────────────────────────────────────────────────────────────
function Cmd-Version {
    Write-Host ""
    Write-Host "  ADRION 369 v$VERSION" -ForegroundColor Magenta
    $goVer = (go version 2>$null) -replace "go version ", ""
    $pyVer = (& $VENV_PY --version 2>$null) -replace "Python ", ""
    if ($goVer) { Write-INFO "Go:     $goVer" }
    if ($pyVer) { Write-INFO "Python: $pyVer" }
    $goVortex = Join-Path $Root "bin\vortex-server.exe"
    if (Test-Path $goVortex) {
        $sz = [math]::Round((Get-Item $goVortex).Length / 1MB, 1)
        Write-INFO "Vortex: bin\vortex-server.exe ($sz MB)"
    }
    Write-Host ""
}

# ── start ─────────────────────────────────────────────────────────────────────
function Cmd-Start {
    Write-Section "Starting ADRION 369"

    # Docker
    if (Test-Path $COMPOSE) {
        Write-INFO "Starting Docker services..."
        docker compose -f $COMPOSE up -d 2>&1 | ForEach-Object {
            if ($_ -match "Starting|Started|Creating|Created|Running") {
                Write-OK $_
            } elseif ($_ -match "Error|error") {
                Write-WARN $_
            }
        }
        Start-Sleep 5
    } else {
        Write-WARN "docker-compose.yml not found — skipping Docker"
    }

    # Arbitrage API
    $apiPid = Join-Path $RUNTIME "waitress.pid"
    if (Test-Path $apiPid) {
        $existingPid = Get-Content $apiPid -ErrorAction SilentlyContinue
        if ($existingPid) {
            $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($proc) {
                Write-INFO "arbitrage-api already running (PID $existingPid)"
                Cmd-Status
                return
            }
        }
    }

    $startScript = Join-Path $Root "scripts\prod\start-prod.ps1"
    if (Test-Path $startScript) {
        Write-INFO "Starting arbitrage-api via start-prod.ps1..."
        Start-Process powershell `
            -ArgumentList "-NoProfile -WindowStyle Hidden -File `"$startScript`""
        Start-Sleep 4
    } else {
        $apiMain = Join-Path $Root "arbitrage\main.py"
        if (-not (Test-Path $apiMain)) {
            $apiMain = Join-Path $Root "arbitrage\api.py"
        }
        if (Test-Path $apiMain) {
            Write-INFO "Starting arbitrage-api directly..."
            Start-Process -FilePath $VENV_PY -ArgumentList $apiMain `
                -WorkingDirectory $Root -WindowStyle Hidden
            Start-Sleep 4
        } else {
            Write-WARN "No API entrypoint found"
        }
    }

    # Dashboard server (port 8003)
    $dashServer = Join-Path $Root "dashboard\server.py"
    $dashPid    = Join-Path $RUNTIME "dashboard.pid"
    $dashRunning = $false
    if (Test-Path $dashPid) {
        $existingPid = Get-Content $dashPid -ErrorAction SilentlyContinue
        if ($existingPid) {
            $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($proc) { $dashRunning = $true; Write-INFO "admin-dashboard already running (PID $existingPid)" }
        }
    }
    if (-not $dashRunning -and (Test-Path $dashServer)) {
        Write-INFO "Starting admin-dashboard on port 8003..."
        $dashProc = Start-Process -FilePath $VENV_PY `
            -ArgumentList $dashServer `
            -WorkingDirectory $Root -WindowStyle Hidden -PassThru
        if ($dashProc) {
            $dashProc.Id | Out-File $dashPid -Encoding ascii -NoNewline
            Write-OK "admin-dashboard started (PID $($dashProc.Id)) → http://localhost:8003"
        }
        Start-Sleep 2
    }

    Cmd-Status
}

# ── stop ──────────────────────────────────────────────────────────────────────
function Cmd-Stop {
    Write-Section "Stopping ADRION 369"

    # Arbitrage API
    $apiPid = Join-Path $RUNTIME "waitress.pid"
    if (Test-Path $apiPid) {
        $existingPid = Get-Content $apiPid -ErrorAction SilentlyContinue
        if ($existingPid) {
            $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id ([int]$existingPid) -Force
                Write-OK "arbitrage-api stopped (PID $existingPid)"
            }
        }
        Remove-Item $apiPid -Force -ErrorAction SilentlyContinue
    }

    # Dashboard server
    $dashPid = Join-Path $RUNTIME "dashboard.pid"
    if (Test-Path $dashPid) {
        $existingPid = Get-Content $dashPid -ErrorAction SilentlyContinue
        if ($existingPid) {
            $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id ([int]$existingPid) -Force
                Write-OK "admin-dashboard stopped (PID $existingPid)"
            }
        }
        Remove-Item $dashPid -Force -ErrorAction SilentlyContinue
    }

    # Docker
    if (Test-Path $COMPOSE) {
        Write-INFO "Stopping Docker services..."
        docker compose -f $COMPOSE down 2>&1 | Out-Null
        Write-OK "Docker services stopped"
    }

    # Maintenance daemon
    $maintPid = Join-Path $RUNTIME "maintenance-daemon.pid"
    if (Test-Path $maintPid) {
        $existingPid = Get-Content $maintPid -ErrorAction SilentlyContinue
        if ($existingPid) {
            Stop-Process -Id ([int]$existingPid) -Force -ErrorAction SilentlyContinue
            Write-OK "Maintenance daemon stopped"
        }
        Remove-Item $maintPid -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-OK "All services stopped."
    Write-Host ""
}

# ── restart ───────────────────────────────────────────────────────────────────
function Cmd-Restart {
    Write-Section "Restarting ADRION 369"
    Cmd-Stop
    Start-Sleep 2
    Cmd-Start
}

# ── status ────────────────────────────────────────────────────────────────────
function Cmd-Status {
    Write-Section "ADRION 369 Status"

    Write-Host "  Docker Containers:" -ForegroundColor Gray
    foreach ($c in @("adrion-db", "adrion-vortex", "adrion-healer", "adrion-n8n")) {
        $status = docker inspect $c --format '{{.State.Status}}' 2>$null
        $health = docker inspect $c --format '{{.State.Health.Status}}' 2>$null
        $hStr   = if ($health -and $health -ne "<no value>") { " [health=$health]" } else { "" }
        if ($status -eq "running") { Write-OK "  $c : running$hStr" }
        elseif ($status)           { Write-WARN "  $c : $status" }
        else                       { Write-FAIL "  $c : not found" }
    }

    Write-Host ""
    Write-Host "  Python Services:" -ForegroundColor Gray
    $apiPort = if ($env:ARB_PORT) { $env:ARB_PORT } else { "8001" }
    try {
        $r = Invoke-WebRequest "http://localhost:$apiPort/api/arbitrage/status" `
            -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        Write-OK "  arbitrage-api : HTTP $($r.StatusCode) :$apiPort"
    } catch {
        $apiPid = Join-Path $RUNTIME "waitress.pid"
        if (Test-Path $apiPid) {
            $pid = Get-Content $apiPid -ErrorAction SilentlyContinue
            $proc = if ($pid) { Get-Process -Id ([int]$pid) -ErrorAction SilentlyContinue } else { $null }
            if ($proc) { Write-WARN "  arbitrage-api : process running, HTTP unreachable" }
            else       { Write-FAIL "  arbitrage-api : stopped" }
        } else {
            Write-FAIL "  arbitrage-api : stopped"
        }
    }

    try {
        Invoke-WebRequest "http://localhost:8003" -UseBasicParsing -TimeoutSec 2 `
            -ErrorAction Stop | Out-Null
        Write-OK "  admin-dashboard: running :8003"
    } catch {
        Write-WARN "  admin-dashboard: stopped :8003"
    }

    try {
        $ol = Invoke-WebRequest "http://localhost:11434/api/tags" `
            -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $models = ($ol.Content | ConvertFrom-Json).models.Count
        Write-OK "  ollama : running ($models models loaded)"
    } catch {
        Write-WARN "  ollama : not running"
    }

    $maintPid = Join-Path $RUNTIME "maintenance-daemon.pid"
    if (Test-Path $maintPid) {
        $pid = Get-Content $maintPid -ErrorAction SilentlyContinue
        $proc = if ($pid) { Get-Process -Id ([int]$pid) -ErrorAction SilentlyContinue } else { $null }
        if ($proc) { Write-OK "  maintenance-daemon: running (PID $pid)" }
        else       { Write-WARN "  maintenance-daemon: PID stale" }
    } else {
        Write-INFO "  maintenance-daemon: not running"
    }

    Write-Host ""
    Write-Host "  Databases:" -ForegroundColor Gray
    $sqlite = Join-Path $Root "arbitrage.db"
    if (Test-Path $sqlite) {
        $sz = [math]::Round((Get-Item $sqlite).Length / 1MB, 2)
        Write-OK "  SQLite: arbitrage.db ($sz MB)"
    } else {
        Write-WARN "  SQLite: arbitrage.db not found"
    }

    Write-Host ""
    Write-Host "  Version: $VERSION" -ForegroundColor DarkGray
    Write-Host ""
}

# ── health ────────────────────────────────────────────────────────────────────
function Cmd-Health {
    Write-Section "Full Health Check"
    $script = Join-Path $Root "scripts\monitoring\monitor-services.ps1"
    if (Test-Path $script) {
        & $script -Interval 0 -NoAutoRecover 2>&1
    } else {
        Write-WARN "monitor-services.ps1 not found — running basic status"
        Cmd-Status
    }
}

# ── logs ──────────────────────────────────────────────────────────────────────
function Cmd-Logs {
    param([string[]]$LArgs)

    $service = if ($LArgs.Count -gt 0 -and $LArgs[0] -notmatch "^-") { $LArgs[0] } else { "arbitrage-api" }
    $lines   = 50
    for ($i = 1; $i -lt $LArgs.Count; $i++) {
        if ($LArgs[$i] -in @("-Lines", "--lines") -and ($i+1) -lt $LArgs.Count) {
            $lines = [int]$LArgs[$i+1]; $i++
        }
    }

    Write-Section "Logs — $service (last $lines lines)"

    $dockerServices = @("adrion-db","adrion-vortex","adrion-healer","adrion-n8n")
    if ($service -in $dockerServices) {
        docker logs --tail $lines $service 2>&1 | ForEach-Object {
            if ($_ -match "ERROR|FAIL") { Write-Host $_ -ForegroundColor Red }
            elseif ($_ -match "WARN")  { Write-Host $_ -ForegroundColor Yellow }
            else { Write-Host $_ }
        }
        return
    }

    switch ($service.ToLower()) {
        "arbitrage-api" {
            $files = Get-ChildItem (Join-Path $LOG_DIR "monitor") -Filter "*.log" `
                -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
            if ($files) { Get-Content $files[0].FullName -Tail $lines }
            else { Write-WARN "No logs in logs\monitor\" }
        }
        "maintenance" {
            $files = Get-ChildItem (Join-Path $LOG_DIR "maintenance") -Filter "daemon-*.log" `
                -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
            if ($files) { Get-Content $files[0].FullName -Tail $lines }
            else { Write-WARN "No maintenance daemon logs found" }
        }
        default {
            # Try as Docker
            docker logs --tail $lines $service 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-WARN "Unknown service: $service"
                Write-INFO "Available: adrion-db | adrion-vortex | adrion-n8n | adrion-healer | arbitrage-api | maintenance"
            }
        }
    }
    Write-Host ""
}

# ── db ────────────────────────────────────────────────────────────────────────
function Cmd-Db {
    param([string[]]$DArgs)
    $sub = if ($DArgs.Count -gt 0) { $DArgs[0] } else { "status" }

    switch ($sub.ToLower()) {
        "migrate" {
            Write-Section "DB Migrate"
            $target = ""
            for ($i = 1; $i -lt $DArgs.Count; $i++) {
                if ($DArgs[$i] -in @("--target","-target") -and ($i+1) -lt $DArgs.Count) {
                    $target = $DArgs[$i+1]; $i++
                }
            }
            $script = Join-Path $Root "scripts\migrate.py"
            if (Test-Path $script) {
                $mArgs = @($script, "up")
                if ($target) { $mArgs += @("--target", $target) }
                & $VENV_PY @mArgs
            } else { Write-FAIL "scripts\migrate.py not found" }
        }
        "rollback" {
            Write-Section "DB Rollback"
            $target = ""
            for ($i = 1; $i -lt $DArgs.Count; $i++) {
                if ($DArgs[$i] -in @("--target","-target") -and ($i+1) -lt $DArgs.Count) {
                    $target = $DArgs[$i+1]; $i++
                }
            }
            $script = Join-Path $Root "scripts\migrate.py"
            if (Test-Path $script) {
                $mArgs = @($script, "down")
                if ($target) { $mArgs += @("--target", $target) }
                & $VENV_PY @mArgs
            } else { Write-FAIL "scripts\migrate.py not found" }
        }
        "validate" {
            Write-Section "DB Validate"
            $script = Join-Path $Root "scripts\install\validate-database.ps1"
            if (Test-Path $script) { & $script -Root $Root }
            else { Write-FAIL "validate-database.ps1 not found" }
        }
        "backup" {
            Write-Section "DB Backup"
            $script = Join-Path $Root "scripts\maintenance\backup-all.ps1"
            if (Test-Path $script) { & $script -Root $Root }
            else { Write-FAIL "backup-all.ps1 not found" }
        }
        "optimize" {
            Write-Section "DB Optimize"
            $script = Join-Path $Root "scripts\maintenance\optimize-database.ps1"
            if (Test-Path $script) { & $script -Root $Root }
            else { Write-FAIL "optimize-database.ps1 not found" }
        }
        "status" {
            Write-Section "DB Status"
            $sqlite = Join-Path $Root "arbitrage.db"
            if (Test-Path $sqlite) {
                $sz = [math]::Round((Get-Item $sqlite).Length / 1MB, 2)
                Write-INFO "SQLite: $sz MB"
                $result = & $VENV_PY -c @"
import sqlite3
conn = sqlite3.connect(r'$sqlite')
mode  = conn.execute('PRAGMA journal_mode').fetchone()[0]
pages = conn.execute('PRAGMA page_count').fetchone()[0]
free  = conn.execute('PRAGMA freelist_count').fetchone()[0]
frag  = round(free/max(pages,1)*100,1)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print(f'journal={mode} pages={pages} free={free} frag={frag}%')
print(f'tables({len(tables)}): ' + ', '.join(t[0] for t in tables))
try:
    rows = conn.execute('SELECT version, applied_at, file_name FROM migrations_applied ORDER BY version').fetchall()
    print(f'migrations: {len(rows)} applied')
    for r in rows[-5:]:
        print(f'  v{r[0]:03d}  {str(r[1])[:19]}  {r[2]}')
except Exception:
    print('migrations: table not found (run: admin.ps1 db migrate)')
conn.close()
"@ 2>&1
                $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
            } else {
                Write-WARN "arbitrage.db not found"
            }

            $pgStatus = docker inspect adrion-db --format '{{.State.Status}}' 2>$null
            if ($pgStatus -eq "running") {
                Write-INFO "PostgreSQL: running"
            } else {
                Write-WARN "PostgreSQL: $pgStatus"
            }
        }
        default {
            Write-WARN "Unknown: $sub"
            Write-INFO "Available: migrate | rollback | validate | backup | optimize | status"
        }
    }
}

# ── backup ────────────────────────────────────────────────────────────────────
function Cmd-Backup {
    param([string[]]$BArgs)
    $dest = ""
    for ($i = 0; $i -lt $BArgs.Count; $i++) {
        if ($BArgs[$i] -in @("--dest","-dest") -and ($i+1) -lt $BArgs.Count) {
            $dest = $BArgs[$i+1]; $i++
        }
    }
    $script = Join-Path $Root "scripts\maintenance\backup-all.ps1"
    if (Test-Path $script) {
        $sArgs = @("-Root", $Root)
        if ($dest) { $sArgs += @("-DestDir", $dest) }
        & $script @sArgs
    } else { Write-FAIL "backup-all.ps1 not found" }
}

# ── cleanup ───────────────────────────────────────────────────────────────────
function Cmd-Cleanup {
    $script = Join-Path $Root "scripts\maintenance\cleanup-logs.ps1"
    if (Test-Path $script) { & $script -Root $Root }
    else { Write-FAIL "cleanup-logs.ps1 not found" }
}

# ── optimize ──────────────────────────────────────────────────────────────────
function Cmd-Optimize {
    $script = Join-Path $Root "scripts\maintenance\optimize-database.ps1"
    if (Test-Path $script) { & $script -Root $Root }
    else { Write-FAIL "optimize-database.ps1 not found" }
}

# ── secrets ───────────────────────────────────────────────────────────────────
function Cmd-Secrets {
    param([string[]]$SArgs)
    $sub = if ($SArgs.Count -gt 0) { $SArgs[0] } else { "validate" }
    $script = Join-Path $Root "scripts\install\manage-secrets.ps1"
    if (Test-Path $script) {
        $sArgs = @("-Action", $sub, "-Root", $Root)
        if ($SArgs.Count -gt 1) { $sArgs += @("-Key", $SArgs[1]) }
        & $script @sArgs
    } else { Write-FAIL "manage-secrets.ps1 not found" }
}

# ── env ───────────────────────────────────────────────────────────────────────
function Cmd-Env {
    Write-Section "Environment"
    $secretPattern = "PASSWORD|SECRET|KEY|TOKEN|PASS"

    foreach ($f in @(".env", ".env.local", ".env.offline")) {
        $path = Join-Path $Root $f
        if (-not (Test-Path $path)) { continue }
        Write-Host "  [$f]" -ForegroundColor Cyan
        Get-Content $path | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
            if ($_ -match $secretPattern) {
                $k = ($_ -split "=")[0]
                Write-Host "    $k=***" -ForegroundColor DarkGray
            } else {
                Write-Host "    $_" -ForegroundColor Gray
            }
        }
    }
    Write-Host ""
}

# ── dev ───────────────────────────────────────────────────────────────────────
function Cmd-Dev {
    Write-Section "Development Mode"
    $apiMain = Join-Path $Root "arbitrage\main.py"
    if (-not (Test-Path $apiMain)) { $apiMain = Join-Path $Root "arbitrage\api.py" }

    if (Test-Path $apiMain) {
        $env:FLASK_DEBUG = "1"
        $env:FLASK_ENV   = "development"
        $port = if ($env:ARB_PORT) { $env:ARB_PORT } else { "8001" }
        Write-INFO "API: http://localhost:$port  (debug mode)"
        Write-INFO "Press Ctrl+C to stop"
        & $VENV_PY $apiMain
    } else {
        Write-FAIL "arbitrage entrypoint not found (main.py / api.py)"
    }
}

# ── test ──────────────────────────────────────────────────────────────────────
function Cmd-Test {
    Write-Section "Test Suite"
    $failed = 0

    Write-INFO "Running Python tests (pytest)..."
    Push-Location $Root
    & $VENV_PY -m pytest tests/ -v --tb=short -q 2>&1
    if ($LASTEXITCODE -ne 0) { $failed++; Write-FAIL "Python tests FAILED" }
    else { Write-OK "Python tests PASSED" }
    Pop-Location

    Write-INFO "Running Go tests..."
    Push-Location $Root
    go test ./... -timeout 60s -cover 2>&1
    if ($LASTEXITCODE -ne 0) { $failed++; Write-FAIL "Go tests FAILED" }
    else { Write-OK "Go tests PASSED" }
    Pop-Location

    Write-Host ""
    if ($failed -eq 0) { Write-OK "All tests passed!" }
    else { Write-FAIL "$failed test suite(s) failed" }
    Write-Host ""
}

# ── lint ──────────────────────────────────────────────────────────────────────
function Cmd-Lint {
    Write-Section "Linting"
    $failed = 0

    Write-INFO "ruff check..."
    & $VENV_PY -m ruff check arbitrage/ tests/ 2>&1
    if ($LASTEXITCODE -ne 0) { $failed++; Write-FAIL "ruff: issues found" }
    else { Write-OK "ruff: clean" }

    Write-INFO "ruff format check..."
    & $VENV_PY -m ruff format --check arbitrage/ tests/ 2>&1
    if ($LASTEXITCODE -ne 0) { Write-WARN "ruff format: would reformat" }
    else { Write-OK "ruff format: clean" }

    if (Get-Command go -ErrorAction SilentlyContinue) {
        Write-INFO "go vet..."
        Push-Location $Root
        go vet ./... 2>&1
        if ($LASTEXITCODE -ne 0) { $failed++; Write-FAIL "go vet: issues found" }
        else { Write-OK "go vet: clean" }
        Pop-Location
    }

    Write-Host ""
    if ($failed -eq 0) { Write-OK "Linting passed!" }
    else { Write-FAIL "$failed check(s) failed" }
    Write-Host ""
}

# ── build ─────────────────────────────────────────────────────────────────────
function Cmd-Build {
    Write-Section "Build Vortex Engine"
    $binDir = Join-Path $Root "bin"
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null

    Write-INFO "go build ./cmd/vortex-server/..."
    Push-Location $Root
    $outBin = Join-Path $binDir "vortex-server.exe"
    go build -ldflags "-s -w -X main.version=$VERSION" `
        -o $outBin ./cmd/vortex-server/ 2>&1
    if ($LASTEXITCODE -eq 0) {
        $sz = [math]::Round((Get-Item $outBin).Length / 1MB, 1)
        Write-OK "Built: bin\vortex-server.exe ($sz MB)"
    } else {
        Write-FAIL "Build failed"
    }
    Pop-Location
}

# ── monitor ───────────────────────────────────────────────────────────────────
function Cmd-Monitor {
    param([string[]]$MArgs)
    $stopFlag = $MArgs -contains "--stop" -or $MArgs -contains "-stop"
    $script   = Join-Path $Root "scripts\monitoring\monitor-services.ps1"

    if ($stopFlag) {
        $monPid = Join-Path $RUNTIME "monitor.pid"
        if (Test-Path $monPid) {
            $pid = Get-Content $monPid -ErrorAction SilentlyContinue
            if ($pid) {
                Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue
                Write-OK "Monitor stopped (PID $pid)"
            }
            Remove-Item $monPid -Force -ErrorAction SilentlyContinue
        } else {
            Write-WARN "Monitor not running (no PID file)"
        }
        return
    }

    if (Test-Path $script) {
        Write-INFO "Starting monitor daemon in background..."
        $proc = Start-Process powershell `
            -ArgumentList "-NoProfile -WindowStyle Hidden -File `"$script`" -Daemon" `
            -PassThru
        if ($proc) {
            $proc.Id | Out-File (Join-Path $RUNTIME "monitor.pid") -Encoding ascii -NoNewline
            Write-OK "Monitor started (PID $($proc.Id)) — logs: logs\monitor\"
        }
    } else {
        Write-FAIL "monitor-services.ps1 not found"
    }
}

# ── maintain ──────────────────────────────────────────────────────────────────
function Cmd-Maintain {
    $script = Join-Path $Root "scripts\maintenance\maintenance-daemon.ps1"
    if (Test-Path $script) {
        Write-INFO "Starting maintenance daemon..."
        & $script -Root $Root
    } else {
        Write-FAIL "maintenance-daemon.ps1 not found"
    }
}

# ── setup ─────────────────────────────────────────────────────────────────────
function Cmd-Setup {
    $script = Join-Path $Root "scripts\install\setup-ADRION.ps1"
    if (Test-Path $script) {
        Write-INFO "Running ADRION 369 installer..."
        & $script @ExtraArgs
    } else {
        Write-FAIL "setup-ADRION.ps1 not found at scripts\install\"
    }
}

# ── ui ────────────────────────────────────────────────────────────────────────
function Cmd-Ui {
    $liveUrl = "http://localhost:8003"
    $apiPort = if ($env:ARB_PORT) { $env:ARB_PORT } else { "8001" }

    try {
        Invoke-WebRequest $liveUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop | Out-Null
        Write-INFO "Opening $liveUrl"
        Start-Process $liveUrl
        return
    } catch {}

    $dashFile = Join-Path $Root "dashboard\index.html"
    if (Test-Path $dashFile) {
        Write-INFO "Opening local dashboard file..."
        Start-Process $dashFile
    } else {
        Write-INFO "Opening API: http://localhost:$apiPort"
        Start-Process "http://localhost:$apiPort"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# DISPATCH
# ─────────────────────────────────────────────────────────────────────────────
switch ($Command.ToLower()) {
    { $_ -in @("help","--help","-h","/?") } { Cmd-Help }
    { $_ -in @("version","--version","-v") } { Cmd-Version }

    "start"    { Cmd-Start }
    "stop"     { Cmd-Stop }
    "restart"  { Cmd-Restart }
    "status"   { Cmd-Status }
    "health"   { Cmd-Health }

    "logs"     { Cmd-Logs   -LArgs $ExtraArgs }

    "db"       { Cmd-Db     -DArgs $ExtraArgs }
    "backup"   { Cmd-Backup -BArgs $ExtraArgs }
    "cleanup"  { Cmd-Cleanup }
    "optimize" { Cmd-Optimize }

    "secrets"  { Cmd-Secrets -SArgs $ExtraArgs }
    "env"      { Cmd-Env }

    "dev"      { Cmd-Dev }
    "test"     { Cmd-Test }
    "lint"     { Cmd-Lint }
    "build"    { Cmd-Build }

    "monitor"  { Cmd-Monitor  -MArgs $ExtraArgs }
    "maintain" { Cmd-Maintain }
    "setup"    { Cmd-Setup }
    "ui"       { Cmd-Ui }

    default {
        Write-WARN "Unknown command: '$Command'"
        Write-Host "  Run: .\admin.ps1 help" -ForegroundColor DarkGray
        exit 1
    }
}
