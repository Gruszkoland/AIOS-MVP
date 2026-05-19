<#
.SYNOPSIS
    ADRION 369 — Continuous Service Health Monitor
.DESCRIPTION
    Monitoruje wszystkie serwisy co 30 sekund. Auto-recovery dla krytycznych usług.
    Loguje stan do logs\monitor\. Wyświetla live dashboard w konsoli.
.PARAMETER Interval
    Interwał sprawdzania w sekundach (domyślnie: 30)
.PARAMETER NoAutoRecover
    Wyłącz auto-recovery (tylko monitoring)
.PARAMETER Daemon
    Uruchom bez interaktywnego dashboardu (tryb background)
.EXAMPLE
    .\scripts\monitoring\monitor-services.ps1
    .\scripts\monitoring\monitor-services.ps1 -Interval 10 -Daemon
#>
[CmdletBinding()]
param(
    [int]$Interval      = 30,
    [switch]$NoAutoRecover,
    [switch]$Daemon,
    [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = 'SilentlyContinue'

# ── Config ────────────────────────────────────────────────────────────────────
$LOG_DIR  = Join-Path $Root "logs\monitor"
$VENV_PY  = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VENV_PY)) { $VENV_PY = "python" }

$RECOVER_SCRIPT = Join-Path $PSScriptRoot "recover-services.ps1"
$COMPOSE_FILE   = Join-Path $Root "adrion-swarm\docker-compose.yml"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

# ── Service definitions ───────────────────────────────────────────────────────
$SERVICES = @(
    @{
        Name    = "adrion-db"
        Type    = "docker"
        Critical = $true
        Port    = 5432
    }
    @{
        Name    = "adrion-vortex"
        Type    = "docker"
        Critical = $true
        Port    = 1740
        HealthUrl = "http://localhost:1740/health"
    }
    @{
        Name    = "adrion-healer"
        Type    = "docker"
        Critical = $false
        Port    = $null
    }
    @{
        Name    = "adrion-n8n"
        Type    = "docker"
        Critical = $false
        Port    = 5678
        HealthUrl = "http://localhost:5678/healthz"
    }
    @{
        Name    = "arbitrage-api"
        Type    = "http"
        Critical = $true
        Port    = 8001
        HealthUrl = "http://localhost:8001/api/arbitrage/status"
    }
    @{
        Name    = "admin-dashboard"
        Type    = "http"
        Critical = $false
        Port    = 8003
        HealthUrl = "http://localhost:8003/health"
    }
)

# ── State tracking ────────────────────────────────────────────────────────────
$state        = @{}  # service name → last status
$failCount    = @{}  # service name → consecutive failures
$recoverCount = @{}  # service name → recovery attempts today
$startTime    = Get-Date

foreach ($svc in $SERVICES) {
    $state[$svc.Name]        = "unknown"
    $failCount[$svc.Name]    = 0
    $recoverCount[$svc.Name] = 0
}

# ── Helpers ───────────────────────────────────────────────────────────────────
function Get-LogFile {
    return Join-Path $LOG_DIR "monitor-$(Get-Date -Format 'yyyyMMdd').log"
}

function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Add-Content -Path (Get-LogFile) -Value $line -Encoding UTF8
    if ($Daemon) { Write-Host $line }
}

function Test-DockerService {
    param([string]$Name)
    $status = docker inspect $Name --format '{{.State.Status}}' 2>$null
    $health = docker inspect $Name --format '{{.State.Health.Status}}' 2>$null
    if ($status -eq "running") {
        if ($health -and $health -ne "") {
            return $health  # healthy / unhealthy / starting
        }
        return "running"
    }
    return $status  # exited / restarting / dead / ""
}

function Test-HttpEndpoint {
    param([string]$Url, [int]$TimeoutSec = 5)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return @{ OK = $true; Code = $resp.StatusCode }
    } catch [System.Net.WebException] {
        $code = [int]$_.Exception.Response.StatusCode
        return @{ OK = ($code -lt 500); Code = $code }
    } catch {
        return @{ OK = $false; Code = 0 }
    }
}

function Get-ServiceStatus {
    param($Svc)
    switch ($Svc.Type) {
        "docker" {
            $s = Test-DockerService -Name $Svc.Name
            if ($s -in @("running", "healthy")) { return "OK" }
            if ($s -eq "starting")              { return "STARTING" }
            if ($s -eq "unhealthy")             { return "UNHEALTHY" }
            if ([string]::IsNullOrEmpty($s))    { return "NOT_RUNNING" }
            return "FAIL:$s"
        }
        "http" {
            if ($Svc.HealthUrl) {
                $r = Test-HttpEndpoint -Url $Svc.HealthUrl
                return $(if ($r.OK) { "OK" } else { "FAIL:HTTP$($r.Code)" })
            }
            return "UNKNOWN"
        }
        default { return "UNKNOWN" }
    }
}

function Get-StatusColor {
    param([string]$Status)
    switch -Wildcard ($Status) {
        "OK"        { return "Green"  }
        "STARTING"  { return "Yellow" }
        "UNKNOWN"   { return "DarkGray" }
        default     { return "Red" }
    }
}

# ── Display dashboard ─────────────────────────────────────────────────────────
function Show-Dashboard {
    param([hashtable]$CurrentState, [int]$Iteration)
    if ($Daemon) { return }

    $uptime = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    $ts     = Get-Date -Format "HH:mm:ss"

    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor DarkCyan
    Write-Host "  ║    ADRION 369 — Health Monitor                  ║" -ForegroundColor DarkCyan
    Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "  Czas: $ts  |  Uptime: ${uptime}min  |  Iteracja: $Iteration  |  Interval: ${Interval}s"  -ForegroundColor Gray
    Write-Host ""
    Write-Host ("  {0,-25} {1,-12} {2,-8} {3}" -f "SERWIS", "STATUS", "BŁĘDY", "RECOVERY") -ForegroundColor White
    Write-Host ("  " + ("─" * 58)) -ForegroundColor DarkGray

    foreach ($svc in $SERVICES) {
        $s     = $CurrentState[$svc.Name]
        $fails = $failCount[$svc.Name]
        $recs  = $recoverCount[$svc.Name]
        $color = Get-StatusColor -Status $s
        $crit  = if ($svc.Critical) { "*" } else { " " }
        Write-Host ("  {0,-25}" -f "$crit$($svc.Name)") -NoNewline -ForegroundColor White
        Write-Host ("{0,-12}" -f $s) -NoNewline -ForegroundColor $color
        Write-Host ("{0,-8}" -f $fails) -NoNewline -ForegroundColor $(if ($fails -gt 0) {"Yellow"} else {"DarkGray"})
        Write-Host ("{0}" -f $recs) -ForegroundColor $(if ($recs -gt 0) {"Cyan"} else {"DarkGray"})
    }

    Write-Host ""
    Write-Host "  * = krytyczny serwis" -ForegroundColor DarkGray
    Write-Host "  Ctrl+C aby zatrzymać" -ForegroundColor DarkGray
    Write-Host ""

    # Quick KPIs from arbitrage API
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8001/api/arbitrage/status" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        $d = $r.Content | ConvertFrom-Json
        Write-Host ("  Jobs: {0}  Bids: {1}  Pending: {2}  LLM: {3}" -f `
            $d.total_jobs, $d.bids_sent, $d.pending_bids, $d.llm_backend) -ForegroundColor Cyan
    } catch {}
    Write-Host ""
}

# ── Recovery trigger ──────────────────────────────────────────────────────────
function Invoke-Recovery {
    param($Svc)
    if ($NoAutoRecover) { return }
    if ($recoverCount[$Svc.Name] -ge 5) {
        Write-Log "ERROR" "$($Svc.Name): MAX RECOVERY osiągnięty (5) — pomijam"
        return
    }

    Write-Log "RECOVER" "Próba odzyskania: $($Svc.Name)"
    $recoverCount[$Svc.Name]++

    if (Test-Path $RECOVER_SCRIPT) {
        & $RECOVER_SCRIPT -ServiceName $Svc.Name -Root $Root
    } elseif ($Svc.Type -eq "docker" -and (Test-Path $COMPOSE_FILE)) {
        docker compose -f $COMPOSE_FILE restart $Svc.Name 2>&1 | Out-Null
        Start-Sleep 5
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# MAIN MONITORING LOOP
# ═════════════════════════════════════════════════════════════════════════════
Write-Log "INFO" "Monitor started (interval=${Interval}s, autoRecover=$(-not $NoAutoRecover))"
Write-Host "  Monitorowanie uruchomione. Ctrl+C = stop" -ForegroundColor Green

$iteration = 0
Register-EngineEvent PowerShell.Exiting -Action {
    Write-Log "INFO" "Monitor zatrzymany"
} | Out-Null

while ($true) {
    $iteration++
    $checkTime = Get-Date
    $criticalFail = $false

    foreach ($svc in $SERVICES) {
        $prevStatus = $state[$svc.Name]
        $newStatus  = Get-ServiceStatus -Svc $svc
        $state[$svc.Name] = $newStatus

        # Track failures
        if ($newStatus -notmatch "^OK$|^STARTING$") {
            $failCount[$svc.Name]++
            if ($prevStatus -eq "OK" -or $prevStatus -eq "unknown") {
                Write-Log "WARN" "$($svc.Name): $prevStatus → $newStatus"
            }
            if ($svc.Critical) { $criticalFail = $true }

            # Auto-recovery after 2 consecutive failures
            if ($failCount[$svc.Name] -ge 2) {
                Write-Log "WARN" "$($svc.Name): $($failCount[$svc.Name]) consecutive failures"
                Invoke-Recovery -Svc $svc
            }
        } else {
            if ($failCount[$svc.Name] -gt 0 -and $prevStatus -ne "OK") {
                Write-Log "INFO" "$($svc.Name): recovered ($($failCount[$svc.Name]) failures)"
            }
            $failCount[$svc.Name] = 0
        }
    }

    # Log summary every 10 iterations
    if ($iteration % 10 -eq 0) {
        $okCount   = ($state.Values | Where-Object { $_ -eq "OK" }).Count
        $failTotal = ($state.Values | Where-Object { $_ -notmatch "OK|STARTING|UNKNOWN" }).Count
        Write-Log "INFO" "Iteration $iteration: $okCount/$($SERVICES.Count) OK, $failTotal FAIL"
    }

    # Rotate log files older than 7 days
    if ($iteration % 288 -eq 0) {  # roughly daily at 30s intervals
        Get-ChildItem $LOG_DIR -Filter "monitor-*.log" |
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } |
            Remove-Item -Force
    }

    Show-Dashboard -CurrentState $state -Iteration $iteration

    Start-Sleep -Seconds $Interval
}
