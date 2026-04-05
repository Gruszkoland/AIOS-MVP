<#
.SYNOPSIS
    ADRION 369 — Database Validator
.DESCRIPTION
    Weryfikuje konfigurację bazy danych: SQLite integrity, PostgreSQL connection,
    schema completeness, migration status.
.PARAMETER Root
    Katalog główny projektu
.PARAMETER EnvFile
    Ścieżka do pliku .env
.PARAMETER Quiet
    Tylko błędy krytyczne na wyjściu
#>
[CmdletBinding()]
param(
    [string]$Root    = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$EnvFile = "",
    [switch]$Quiet
)

if (-not $EnvFile) { $EnvFile = Join-Path $Root ".env" }

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { $VenvPy = "python" }

function Write-OK   { param($m) if (-not $Quiet) { Write-Host "  [OK] $m" -ForegroundColor Green  } }
function Write-WARN { param($m) Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-FAIL { param($m) Write-Host "  [XX] $m" -ForegroundColor Red    }
function Write-INFO { param($m) if (-not $Quiet) { Write-Host "       $m" -ForegroundColor Gray   } }

if (-not $Quiet) {
    Write-Host ""
    Write-Host "=== ADRION 369 — Database Validation ===" -ForegroundColor Cyan
}

# ── Load env vars ─────────────────────────────────────────────────────────────
$envVars = @{}
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*([A-Z_0-9]+)\s*=\s*(.*)$") {
            $envVars[$matches[1]] = $matches[2].Trim('"').Trim("'")
        }
    }
}

$dbEngine = if ($envVars["DB_ENGINE"]) { $envVars["DB_ENGINE"] } else { "sqlite" }
$dbPath   = if ($envVars["DB_PATH"])   { $envVars["DB_PATH"]   } else { "arbitrage.db" }
if (-not [System.IO.Path]::IsPathRooted($dbPath)) {
    $dbPath = Join-Path $Root $dbPath
}

Write-INFO "Engine: $dbEngine"
Write-INFO "Path:   $dbPath"

$issues = @()

# ── SQLite validation ─────────────────────────────────────────────────────────
if ($dbEngine -eq "sqlite") {
    if (-not (Test-Path $dbPath)) {
        Write-WARN "SQLite DB nie istnieje — zostanie utworzona przy starcie"
    } else {
        $sizeMB = [math]::Round((Get-Item $dbPath).Length / 1MB, 2)
        Write-OK "SQLite DB istnieje ($sizeMB MB)"

        # Integrity check
        $integrityResult = & $VenvPy -c @"
import sqlite3, sys
try:
    conn = sqlite3.connect(r'$dbPath')
    result = conn.execute('PRAGMA integrity_check').fetchone()[0]
    quick  = conn.execute('PRAGMA quick_check').fetchone()[0]
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    print(f'integrity={result}|tables={len(tables)}|names={",".join(tables)}')
except Exception as e:
    print(f'error={e}')
    sys.exit(1)
"@ 2>$null

        if ($integrityResult -match "integrity=ok") {
            if ($integrityResult -match "tables=(\d+)") { $tc = $matches[1] }
            Write-OK "SQLite integrity: OK ($tc tabel)"
        } else {
            Write-FAIL "SQLite integrity: $integrityResult"
            $issues += "SQLite integrity failed"
        }

        # Check required tables
        $requiredTables = @("jobs","bids","kpis","settings","deals","alerts","payment_events")
        $tablesRaw = ($integrityResult -split "names=")[-1]
        foreach ($tbl in $requiredTables) {
            if ($tablesRaw -notmatch $tbl) {
                Write-WARN "Brakuje tabeli: $tbl — uruchom migracje"
                $issues += "Missing table: $tbl"
            }
        }
        if ($issues.Count -eq 0) { Write-OK "Wymagane tabele: obecne" }
    }
}

# ── PostgreSQL validation ─────────────────────────────────────────────────────
if ($dbEngine -eq "postgres") {
    $dbUrl = $envVars["DB_URL"]
    if ([string]::IsNullOrEmpty($dbUrl)) {
        Write-WARN "DB_URL nie ustawiona — PostgreSQL niedostępny"
        $issues += "DB_URL missing"
    } else {
        $pgResult = & $VenvPy -c @"
import sys
try:
    import psycopg2
    conn = psycopg2.connect(r'$dbUrl', connect_timeout=5)
    cur = conn.cursor()
    cur.execute('SELECT version()')
    ver = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
    tc = cur.fetchone()[0]
    conn.close()
    print(f'ok|version={ver[:30]}|tables={tc}')
except ImportError:
    print('error=psycopg2 not installed')
    sys.exit(1)
except Exception as e:
    print(f'error={e}')
    sys.exit(2)
"@ 2>$null

        if ($pgResult -match "^ok\|") {
            if ($pgResult -match "tables=(\d+)") { $ptc = $matches[1] }
            Write-OK "PostgreSQL: połączono ($ptc tabel publicznych)"
        } else {
            Write-FAIL "PostgreSQL: $pgResult"
            $issues += "PostgreSQL connection failed"
        }
    }
}

# ── Migration status ──────────────────────────────────────────────────────────
$migrateScript = Join-Path $Root "scripts\migrate.py"
if (Test-Path $migrateScript) {
    $migStatus = & $VenvPy $migrateScript list 2>&1
    $appliedCount = ($migStatus | Where-Object { $_ -match "applied" }).Count
    $pendingCount = ($migStatus | Where-Object { $_ -match "pending" }).Count
    Write-OK "Migracje: $appliedCount zastosowanych, $pendingCount oczekujących"
    if ($pendingCount -gt 0) {
        Write-WARN "$pendingCount migracji niezastosowanych"
        Write-INFO "Uruchom: python scripts\migrate.py up --target 999"
    }
}

# ── WAL mode check (SQLite performance) ──────────────────────────────────────
if ($dbEngine -eq "sqlite" -and (Test-Path $dbPath)) {
    $walResult = & $VenvPy -c @"
import sqlite3
conn = sqlite3.connect(r'$dbPath')
mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
conn.close()
print(mode)
"@ 2>$null
    if ($walResult -match "wal") {
        Write-OK "SQLite WAL mode: aktywny (optymalna wydajność)"
    } else {
        Write-WARN "SQLite journal mode: $walResult (zalecany WAL)"
    }
}

# ── Result ────────────────────────────────────────────────────────────────────
Write-Host ""
if ($issues.Count -eq 0) {
    Write-OK "Baza danych zweryfikowana"
    exit 0
} else {
    Write-WARN "Znaleziono $($issues.Count) problemów"
    $issues | ForEach-Object { Write-Host "  ✗ $_" -ForegroundColor Red }
    exit 1
}
