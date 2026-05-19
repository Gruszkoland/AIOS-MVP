<#
.SYNOPSIS
    ADRION 369 — Maintenance Daemon
.DESCRIPTION
    Uruchamia wszystkie zadania konserwacyjne według harmonogramu:
    - Backup (codziennie o 03:00)
    - Cleanup logów (codziennie o 03:30)
    - Optymalizacja DB (co tydzień, niedziela 04:00)
    - Weryfikacja DB (codziennie o 06:00)
    Działa jako background daemon. Logi do logs\maintenance\daemon-YYYYMMDD.log
.PARAMETER Foreground
    Uruchom w trybie foreground (interaktywny) zamiast tła
.EXAMPLE
    .\scripts\maintenance\maintenance-daemon.ps1
    # Uruchom jako Windows Task Scheduler:
    # schtasks /create /tn "ADRION Maintenance" /tr "powershell -File maintenance-daemon.ps1" /sc DAILY /st 02:55
#>
[CmdletBinding()]
param(
    [switch]$Foreground,
    [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = 'SilentlyContinue'

$LOG_DIR  = Join-Path $Root "logs\maintenance"
$PID_FILE = Join-Path $Root ".runtime\maintenance-daemon.pid"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $PID_FILE) | Out-Null

function Get-LogFile { return Join-Path $LOG_DIR "daemon-$(Get-Date -Format 'yyyyMMdd').log" }
function Write-Log {
    param([string]$Level, [string]$Message)
    $ts   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Add-Content -Path (Get-LogFile) -Value $line -Encoding UTF8
    if ($Foreground) {
        Write-Host $line -ForegroundColor $(switch ($Level) {"OK"{"Green"}"WARN"{"Yellow"}"FAIL"{"Red"}default{"Gray"}})
    }
}

# ── Prevent duplicate daemons ─────────────────────────────────────────────────
if (Test-Path $PID_FILE) {
    $existingPid = Get-Content $PID_FILE -ErrorAction SilentlyContinue
    if ($existingPid) {
        $proc = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "[!!] Daemon już działa (PID $existingPid)" -ForegroundColor Yellow
            exit 0
        }
    }
    Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
}

# Save PID
$PID | Out-File $PID_FILE -Encoding ascii -NoNewline
Write-Log "INFO" "Daemon uruchomiony (PID=$PID)"

# ── Scheduled task definitions ────────────────────────────────────────────────
$schedule = @(
    @{
        Name       = "backup"
        Script     = Join-Path $PSScriptRoot "backup-all.ps1"
        Hour       = 3; Minute = 0
        DayOfWeek  = "any"
        LastRun    = [datetime]::MinValue
    }
    @{
        Name       = "cleanup"
        Script     = Join-Path $PSScriptRoot "cleanup-logs.ps1"
        Hour       = 3; Minute = 30
        DayOfWeek  = "any"
        LastRun    = [datetime]::MinValue
    }
    @{
        Name       = "optimize-db"
        Script     = Join-Path $PSScriptRoot "optimize-database.ps1"
        Hour       = 4; Minute = 0
        DayOfWeek  = [DayOfWeek]::Sunday
        LastRun    = [datetime]::MinValue
    }
    @{
        Name       = "validate-db"
        Script     = Join-Path $Root "scripts\install\validate-database.ps1"
        Hour       = 6; Minute = 0
        DayOfWeek  = "any"
        LastRun    = [datetime]::MinValue
    }
)

function Should-RunNow {
    param($Task)
    $now = Get-Date
    # Check hour/minute window (±2 minutes)
    $targetMinutes = $Task.Hour * 60 + $Task.Minute
    $nowMinutes = $now.Hour * 60 + $now.Minute
    if ([math]::Abs($nowMinutes - $targetMinutes) -gt 2) { return $false }
    # Check day of week
    if ($Task.DayOfWeek -ne "any" -and $now.DayOfWeek -ne $Task.DayOfWeek) { return $false }
    # Don't run twice in same hour
    if ($Task.LastRun -gt $now.AddHours(-1)) { return $false }
    return $true
}

function Invoke-MaintenanceTask {
    param($Task)
    if (-not (Test-Path $Task.Script)) {
        Write-Log "WARN" "Skrypt nie istnieje: $($Task.Script)"
        return
    }
    Write-Log "INFO" "Uruchamiam zadanie: $($Task.Name)"
    $t0 = Get-Date
    try {
        & $Task.Script -Root $Root 2>&1 | Out-Null
        $elapsed = [math]::Round(((Get-Date) - $t0).TotalSeconds)
        Write-Log "OK" "Zadanie $($Task.Name) zakończone (${elapsed}s)"
        $Task.LastRun = Get-Date
    } catch {
        Write-Log "FAIL" "Zadanie $($Task.Name): $_"
    }
}

# ── Register Windows Task Scheduler (optional) ────────────────────────────────
function Register-WindowsTask {
    param([string]$RootPath)
    try {
        $action = New-ScheduledTaskAction -Execute "powershell.exe" `
            -Argument "-NoProfile -WindowStyle Hidden -File `"$($MyInvocation.ScriptName)`" -Root `"$RootPath`""
        $trigger = New-ScheduledTaskTrigger -Daily -At "02:55"
        $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false
        Register-ScheduledTask -TaskName "ADRION-369-Maintenance" -Action $action `
            -Trigger $trigger -Settings $settings -Force -RunLevel Highest | Out-Null
        Write-Log "OK" "Windows Task Scheduler: zadanie ADRION-369-Maintenance zarejestrowane"
    } catch {
        Write-Log "WARN" "Task Scheduler: $_"
    }
}

# Try to register Windows Task if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin -and -not $Foreground) {
    Register-WindowsTask -RootPath $Root
}

# ═════════════════════════════════════════════════════════════════════════════
# DAEMON LOOP
# ═════════════════════════════════════════════════════════════════════════════
Write-Log "INFO" "Harmonogram: backup=03:00, cleanup=03:30, optimize-db=Niedziela 04:00, validate-db=06:00"
Write-Host "  Daemon uruchomiony. Ctrl+C aby zatrzymać." -ForegroundColor Green

Register-EngineEvent PowerShell.Exiting -Action {
    Remove-Item $PID_FILE -Force -ErrorAction SilentlyContinue
    Write-Log "INFO" "Daemon zatrzymany"
} | Out-Null

$tickCount = 0
while ($true) {
    $tickCount++

    foreach ($task in $schedule) {
        if (Should-RunNow -Task $task) {
            Invoke-MaintenanceTask -Task $task
        }
    }

    # Log heartbeat every 60 minutes
    if ($tickCount % 120 -eq 0) {
        $uptime = [math]::Round(($tickCount * 30) / 3600, 1)
        Write-Log "INFO" "Heartbeat (uptime=${uptime}h) — wszystkie zadania OK"
    }

    # Rotate old daemon logs (keep 30 days)
    if ($tickCount % 2880 -eq 0) {  # ~1 day
        $cutoff = (Get-Date).AddDays(-30)
        Get-ChildItem $LOG_DIR -Filter "daemon-*.log" |
            Where-Object { $_.LastWriteTime -lt $cutoff } |
            Remove-Item -Force -ErrorAction SilentlyContinue
    }

    Start-Sleep 30
}
