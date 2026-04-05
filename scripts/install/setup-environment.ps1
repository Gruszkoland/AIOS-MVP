<#
.SYNOPSIS
    ADRION 369 — Environment Configuration Setup
.DESCRIPTION
    Generuje .env z szablonu, waliduje zmienne, wspiera tryb offline.
.PARAMETER Root
    Katalog główny projektu (domyślnie: 2 poziomy wyżej niż skrypt)
.PARAMETER EnvFile
    Ścieżka do pliku .env (domyślnie: ROOT\.env)
.PARAMETER Offline
    Użyj konfiguracji offline (żadnych zewnętrznych API)
#>
[CmdletBinding()]
param(
    [string]$Root     = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$EnvFile  = "",
    [switch]$Offline,
    [switch]$Force
)

if (-not $EnvFile) { $EnvFile = Join-Path $Root ".env" }
$EnvExample  = Join-Path $Root ".env.example"
$EnvOffline  = Join-Path $Root ".env.offline"
$EnvLocal    = Join-Path $Root ".env.local"

function Write-OK   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-WARN { param($m) Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-INFO { param($m) Write-Host "       $m" -ForegroundColor Gray   }

Write-Host ""
Write-Host "=== ADRION 369 — Setup Environment ===" -ForegroundColor Cyan

# ── Choose source template ────────────────────────────────────────────────────
if ($Offline -and (Test-Path $EnvOffline)) {
    $source = $EnvOffline
    Write-OK "Tryb offline: używam $EnvOffline"
} elseif (Test-Path $EnvExample) {
    $source = $EnvExample
    Write-OK "Szablon: $EnvExample"
} else {
    Write-WARN "Brak szablonu .env.example — tworzę minimalny plik .env"
    $source = $null
}

# ── Create .env if missing or force ──────────────────────────────────────────
if ((Test-Path $EnvFile) -and -not $Force) {
    Write-OK ".env już istnieje: $EnvFile"
} else {
    if ($source) {
        Copy-Item $source $EnvFile -Force
        Write-OK "Skopiowano $source → $EnvFile"
    } else {
        @"
# ADRION 369 — Auto-generated environment
DB_ENGINE=sqlite
DB_PATH=arbitrage.db
LLM_BACKEND=mock
MOCK_LLM=true
ARB_PORT=8001
VORTEX_PORT=1740
ADMIN_PORT=8003
"@ | Set-Content $EnvFile -Encoding UTF8
        Write-OK "Wygenerowano minimalny .env"
    }
}

# ── Apply .env.local overrides (if present) ───────────────────────────────────
if (Test-Path $EnvLocal) {
    Write-INFO "Nakładam overrides z .env.local..."
    $localLines = Get-Content $EnvLocal | Where-Object { $_ -match "^\s*[A-Z_]+=.+" -and $_ -notmatch "^\s*#" }
    $envContent = Get-Content $EnvFile
    foreach ($line in $localLines) {
        $key = ($line -split "=")[0].Trim()
        $envContent = $envContent | Where-Object { $_ -notmatch "^$key=" }
        $envContent += $line
    }
    Set-Content $EnvFile $envContent -Encoding UTF8
    Write-OK "$($localLines.Count) overrides z .env.local zastosowanych"
}

# ── Validate required variables ───────────────────────────────────────────────
$required = @("DB_ENGINE", "ARB_PORT")
$envVars  = @{}
Get-Content $EnvFile | Where-Object { $_ -match "^\s*([A-Z_0-9]+)\s*=\s*(.*)$" } | ForEach-Object {
    if ($_ -match "^\s*([A-Z_0-9]+)\s*=\s*(.*)$") {
        $envVars[$matches[1]] = $matches[2].Trim().Trim('"').Trim("'")
    }
}

$missing = @()
foreach ($key in $required) {
    if (-not $envVars.ContainsKey($key) -or [string]::IsNullOrEmpty($envVars[$key])) {
        Write-WARN "Brakuje: $key"
        $missing += $key
    } else {
        Write-OK "${key}=$($envVars[$key])"
    }
}

# ── Security check ────────────────────────────────────────────────────────────
$sensitiveDefaults = @{
    "POSTGRES_PASSWORD" = "adrion_pass"
    "N8N_BASIC_AUTH_PASSWORD" = "adrion_pass"
    "STRIPE_SECRET_KEY" = "sk_test_"
}
foreach ($kv in $sensitiveDefaults.GetEnumerator()) {
    if ($envVars.ContainsKey($kv.Key) -and $envVars[$kv.Key] -like "$($kv.Value)*") {
        Write-WARN "UWAGA: $($kv.Key) używa domyślnego/przykładowego hasła!"
        Write-INFO "  Zmień to hasło w $EnvFile przed uruchomieniem w sieci"
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
if ($missing.Count -eq 0) {
    Write-OK "Konfiguracja zweryfikowana ($($envVars.Count) zmiennych)"
} else {
    Write-WARN "Brakuje $($missing.Count) zmiennych — edytuj $EnvFile"
}
Write-Host ""
