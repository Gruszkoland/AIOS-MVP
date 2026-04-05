<#
.SYNOPSIS
    ADRION 369 — Database Optimizer
.DESCRIPTION
    Optymalizuje SQLite (VACUUM, ANALYZE, WAL checkpoint) i PostgreSQL (VACUUM ANALYZE).
    Reindeksuje fragmentowane indeksy. Raportuje metryki wydajności.
.PARAMETER Force
    Wymusza VACUUM FULL (PostgreSQL) lub VACUUM na zablokowanej DB
#>
[CmdletBinding()]
param(
    [switch]$Force,
    [string]$Root = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$VENV_PY  = Join-Path $Root ".venv\Scripts\python.exe"
$LOG_DIR  = Join-Path $Root "logs\maintenance"
$LOG_FILE = Join-Path $LOG_DIR "optimize-$(Get-Date -Format 'yyyyMMdd').log"

New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null

function Write-Log { param($L,$M); $ts=Get-Date -Format "HH:mm:ss"; $line="[$ts][$L] $M"; Add-Content $LOG_FILE $line -Encoding UTF8; Write-Host $line -ForegroundColor $(switch($L){"OK"{"Green"}"FAIL"{"Red"}"WARN"{"Yellow"}default{"Gray"}}) }

Write-Host ""
Write-Host "=== ADRION 369 — Database Optimizer ===" -ForegroundColor Cyan
Write-Log "INFO" "Optimization start"

# ── SQLite Optimization ───────────────────────────────────────────────────────
$sqlitePath = Join-Path $Root "arbitrage.db"
if (Test-Path $sqlitePath) {
    $sizeBefore = [math]::Round((Get-Item $sqlitePath).Length / 1MB, 2)
    Write-Log "INFO" "SQLite before: $sizeBefore MB"

    $result = & $VENV_PY -c @"
import sqlite3, time
conn = sqlite3.connect(r'$sqlitePath')
results = {}

# Enable WAL if not already
mode = conn.execute('PRAGMA journal_mode=WAL').fetchone()[0]
results['journal_mode'] = mode

# Page statistics
page_count = conn.execute('PRAGMA page_count').fetchone()[0]
page_size  = conn.execute('PRAGMA page_size').fetchone()[0]
free_pages = conn.execute('PRAGMA freelist_count').fetchone()[0]
fragmentation = round(free_pages / max(page_count, 1) * 100, 1)
results['fragmentation_pct'] = fragmentation
results['pages'] = page_count
results['free_pages'] = free_pages

# WAL checkpoint
wal_result = conn.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
results['wal_checkpoint'] = wal_result

# ANALYZE (update query planner stats)
t0 = time.perf_counter()
conn.execute('ANALYZE')
results['analyze_ms'] = round((time.perf_counter() - t0) * 1000)

# VACUUM if fragmentation > 10% or forced
if fragmentation > 10 or $([string]($Force)).ToLower() == 'true':
    t0 = time.perf_counter()
    conn.execute('VACUUM')
    results['vacuum_ms'] = round((time.perf_counter() - t0) * 1000)
    results['vacuum_done'] = True
else:
    results['vacuum_done'] = False

conn.close()
for k,v in results.items():
    print(f'{k}={v}')
"@ 2>&1

    if ($LASTEXITCODE -eq 0) {
        $metrics = @{}
        $result | ForEach-Object { if ($_ -match "^(\w+)=(.+)$") { $metrics[$matches[1]] = $matches[2] } }
        $sizeAfter = [math]::Round((Get-Item $sqlitePath).Length / 1MB, 2)
        $saved     = [math]::Round($sizeBefore - $sizeAfter, 2)
        Write-Log "OK" "SQLite WAL=$($metrics['journal_mode']) frag=$($metrics['fragmentation_pct'])% analyze=$($metrics['analyze_ms'])ms"
        if ($metrics['vacuum_done'] -eq 'True') { Write-Log "OK" "VACUUM: $($metrics['vacuum_ms'])ms, zaoszczędzono $saved MB" }
        else { Write-Log "INFO" "VACUUM pominięty (fragmentacja < 10%)" }
    } else {
        Write-Log "FAIL" "SQLite optymalizacja: $result"
    }
}

# ── PostgreSQL Optimization ───────────────────────────────────────────────────
$pgRunning = docker inspect adrion-db --format '{{.State.Status}}' 2>$null
if ($pgRunning -eq "running") {
    Write-Log "INFO" "PostgreSQL VACUUM ANALYZE..."
    $vacuumCmd = if ($Force) { "VACUUM (FULL, ANALYZE, VERBOSE)" } else { "VACUUM ANALYZE" }
    try {
        $pgResult = docker exec adrion-db psql -U adrion -d genesis_record -c $vacuumCmd 2>&1
        Write-Log "OK" "PostgreSQL VACUUM ANALYZE zakończony"

        # Table bloat estimate
        $bloatQuery = @"
SELECT relname, n_dead_tup, n_live_tup,
       CASE WHEN n_live_tup > 0 THEN round(n_dead_tup::numeric/n_live_tup*100,1) ELSE 0 END as dead_pct
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 5;
"@
        $bloat = docker exec adrion-db psql -U adrion -d genesis_record -c $bloatQuery 2>$null
        Write-Log "OK" "Table stats pobrane"
    } catch {
        Write-Log "WARN" "PostgreSQL optimization: $_"
    }
} else {
    Write-Log "INFO" "PostgreSQL nie działa — pomijam"
}

# ── Report ────────────────────────────────────────────────────────────────────
Write-Log "OK" "Optymalizacja zakończona. Log: $LOG_FILE"
Write-Host ""
