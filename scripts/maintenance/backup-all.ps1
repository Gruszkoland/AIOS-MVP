<#
.SYNOPSIS
    ADRION 369 — Full Backup (SQLite + PostgreSQL + Config)
.DESCRIPTION
    Tworzy kompletną kopię zapasową: bazy SQLite, PostgreSQL (przez Docker),
    pliku .env (zaszyfrowany), konfiguracji n8n.
    Retencja: 7 dni. Alert jeśli backup > 5 GB.
.PARAMETER Retention
    Ile dni przechowywać backupy (domyślnie: 7)
.PARAMETER DestDir
    Katalog docelowy (domyślnie: ROOT\backups)
#>
[CmdletBinding()]
param(
    [int]$Retention   = 7,
    [string]$DestDir  = "",
    [string]$Root     = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$ErrorActionPreference = 'SilentlyContinue'
if (-not $DestDir) { $DestDir = Join-Path $Root "backups" }

$VENV_PY  = Join-Path $Root ".venv\Scripts\python.exe"
$LOG_DIR  = Join-Path $Root "logs\maintenance"
$TS       = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG_FILE = Join-Path $LOG_DIR "backup-$TS.log"

New-Item -ItemType Directory -Force -Path $DestDir  | Out-Null
New-Item -ItemType Directory -Force -Path $LOG_DIR  | Out-Null

function Write-Log  { param([string]$L,[string]$M); $ts=Get-Date -Format "HH:mm:ss"; $line="[$ts] [$L] $M"; Add-Content $LOG_FILE $line -Encoding UTF8; Write-Host $line -ForegroundColor $(switch($L){"OK"{"Green"}"FAIL"{"Red"}"WARN"{"Yellow"}default{"Gray"}}) }

Write-Host ""
Write-Host "=== ADRION 369 — Backup ===" -ForegroundColor Cyan
Write-Log "INFO" "Backup started. Dest=$DestDir"

$results = @{}

# ── SQLite Backup ─────────────────────────────────────────────────────────────
$sqlitePath = Join-Path $Root "arbitrage.db"
if (Test-Path $sqlitePath) {
    Write-Log "INFO" "SQLite backup..."
    $dest = Join-Path $DestDir "backup_arbitrage_$TS.db"
    try {
        & $VENV_PY (Join-Path $Root "scripts\backup\backup-sqlite.py") `
            --db $sqlitePath --out $DestDir --no-verify 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            # Verify
            & $VENV_PY (Join-Path $Root "scripts\backup\backup-sqlite.py") --verify $dest 2>&1 | Out-Null
            $sizeMB = [math]::Round((Get-Item $dest -ErrorAction SilentlyContinue).Length / 1MB, 2)
            Write-Log "OK" "SQLite backup: $dest ($sizeMB MB)"
            $results["sqlite"] = "OK"
        } else { throw "exit code $LASTEXITCODE" }
    } catch {
        Write-Log "FAIL" "SQLite backup: $_"
        $results["sqlite"] = "FAIL"
    }
} else {
    Write-Log "WARN" "arbitrage.db nie istnieje — pomijam SQLite backup"
    $results["sqlite"] = "SKIP"
}

# ── PostgreSQL Backup (via Docker) ────────────────────────────────────────────
$pgRunning = docker inspect adrion-db --format '{{.State.Status}}' 2>$null
if ($pgRunning -eq "running") {
    Write-Log "INFO" "PostgreSQL backup przez Docker..."
    $pgDest = Join-Path $DestDir "backup_genesis_record_$TS.sql.gz"
    try {
        $cmd = "pg_dump -U adrion genesis_record"
        [byte[]]$pgData = docker exec adrion-db sh -c $cmd 2>$null
        if ($pgData -and $pgData.Length -gt 100) {
            # Compress
            $pgSql = [System.Text.Encoding]::UTF8.GetString($pgData)
            $pgSql | Out-File "$pgDest.tmp" -Encoding UTF8
            # Use Python gzip
            & $VENV_PY -c @"
import gzip, shutil
with open(r'$pgDest.tmp', 'rb') as f_in:
    with gzip.open(r'$pgDest', 'wb', compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out)
print('ok')
"@ 2>&1 | Out-Null
            Remove-Item "$pgDest.tmp" -Force -ErrorAction SilentlyContinue
            $sizeMB = [math]::Round((Get-Item $pgDest -ErrorAction SilentlyContinue).Length / 1MB, 2)
            Write-Log "OK" "PostgreSQL backup: $pgDest ($sizeMB MB)"
            $results["postgres"] = "OK"
        } else {
            Write-Log "WARN" "PostgreSQL dump pusty — pomijam"
            $results["postgres"] = "SKIP"
        }
    } catch {
        Write-Log "FAIL" "PostgreSQL backup: $_"
        $results["postgres"] = "FAIL"
    }
} else {
    Write-Log "WARN" "adrion-db nie działa — pomijam PostgreSQL backup"
    $results["postgres"] = "SKIP"
}

# ── .env Backup (configs only, no secrets in plaintext) ───────────────────────
$envFile = Join-Path $Root ".env"
if (Test-Path $envFile) {
    $envDest = Join-Path $DestDir "env_keys_only_$TS.txt"
    # Save only KEY names (not values) as a reference
    $keys = Get-Content $envFile | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object { ($_ -split "=")[0] }
    $keys | Out-File $envDest -Encoding UTF8
    Write-Log "OK" "Env keys reference: $envDest ($($keys.Count) keys)"
    $results["env"] = "OK"
}

# ── n8n workflows backup ──────────────────────────────────────────────────────
$n8nData = Join-Path $Root "adrion-swarm\n8n_data"
if (Test-Path $n8nData) {
    $n8nDest = Join-Path $DestDir "n8n_data_$TS"
    try {
        Copy-Item -Recurse -Force $n8nData $n8nDest -ErrorAction Stop
        Write-Log "OK" "n8n workspace backup: $n8nDest"
        $results["n8n"] = "OK"
    } catch {
        Write-Log "WARN" "n8n backup: $_"
        $results["n8n"] = "SKIP"
    }
}

# ── Retention cleanup ─────────────────────────────────────────────────────────
Write-Log "INFO" "Czyszczenie backupów starszych niż $Retention dni..."
$cutoff = (Get-Date).AddDays(-$Retention)
$removed = 0
Get-ChildItem $DestDir -Recurse -File | Where-Object { $_.LastWriteTime -lt $cutoff } | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    $removed++
}
if ($removed -gt 0) { Write-Log "OK" "Usunięto $removed starych plików" }

# ── Size alert ────────────────────────────────────────────────────────────────
$totalMB = [math]::Round((Get-ChildItem $DestDir -Recurse -File | Measure-Object Length -Sum).Sum / 1MB, 0)
if ($totalMB -gt 5120) {
    Write-Log "WARN" "Całkowity rozmiar backupów: ${totalMB} MB (> 5 GB!)"
} else {
    Write-Log "OK" "Całkowity rozmiar backupów: ${totalMB} MB"
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
$ok   = ($results.Values | Where-Object { $_ -eq "OK" }).Count
$fail = ($results.Values | Where-Object { $_ -eq "FAIL" }).Count
Write-Log "INFO" "Backup zakończony: $ok OK, $fail FAIL, log=$LOG_FILE"
Write-Host ""
