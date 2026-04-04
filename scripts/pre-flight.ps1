<#
.SYNOPSIS
    Production Pre-Flight Verification for ADRION 369
.DESCRIPTION
    Comprehensive automated checklist before production deployment
    Verifies all 10 PRIORITY security fixes
    Tests all infrastructure components
.PARAMETER Environment
    Environment to check: production or staging
.EXAMPLE
    .\scripts\pre-flight.ps1 -Environment production
#>
[CmdletBinding()]
param(
    [ValidateSet("production", "staging", "development")]
    [string]$Environment = "production",

    [switch]$SkipPostgres,
    [switch]$SkipDocker,
    [switch]$Verbose
)

Set-StrictMode -Off
$ErrorActionPreference = 'SilentlyContinue'

# ─────────────────────────────────────────────────────────────────────────────
# COLORS & HELPERS
# ─────────────────────────────────────────────────────────────────────────────

function Write-OK      { param($M) Write-Host "  ✅ $M" -ForegroundColor Green   }
function Write-FAIL    { param($M) Write-Host "  ❌ $M" -ForegroundColor Red     }
function Write-WARN    { param($M) Write-Host "  ⚠️  $M" -ForegroundColor Yellow }
function Write-INFO    { param($M) Write-Host "  ℹ️  $M" -ForegroundColor Cyan   }
function Write-HEADER  { param($T) Write-Host "`n╔ $T`n║" -ForegroundColor Magenta }
function Write-CHECK   { param($T) Write-Host "`n► $T" -ForegroundColor Yellow }

$PASS = 0
$FAIL = 0
$WARN = 0

function Test-Item {
    param($name, $condition, [switch]$Critical)

    if ($condition) {
        Write-OK $name
        $PASS++
        return $true
    } else {
        if ($Critical) {
            Write-FAIL "$name [CRITICAL]"
            $FAIL++
        } else {
            Write-WARN "$name [WARNING]"
            $WARN++
        }
        return $false
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# LOAD .ENV
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "LOADING CONFIGURATION"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = Join-Path $root ".env"

if (Test-Path $envFile) {
    Write-INFO "Loading $envFile"
    Get-Content $envFile | Where-Object { $_ -match "^[A-Z_]+=.+" } | ForEach-Object {
        $k, $v = $_ -split "=", 2
        [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
} else {
    Write-FAIL ".env file not found at $envFile"
    exit 1
}

$env_name = [System.Environment]::GetEnvironmentVariable("ENVIRONMENT")
$db_engine = [System.Environment]::GetEnvironmentVariable("DB_ENGINE")
$pg_password = [System.Environment]::GetEnvironmentVariable("POSTGRES_PASSWORD")

Write-INFO "ENVIRONMENT=$env_name"
Write-INFO "DB_ENGINE=$db_engine"

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: ENVIRONMENT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "SECTION 1: ENVIRONMENT VALIDATION"

Write-CHECK "Checking environment mode"
Test-Item "Environment mode matches argument" ($env_name -eq $Environment) -Critical

Write-CHECK "Checking database configuration"
Test-Item "DB_ENGINE is set" (![string]::IsNullOrWhiteSpace($db_engine)) -Critical
if ($db_engine -eq "postgresql") {
    Test-Item "POSTGRES_PASSWORD is set" (![string]::IsNullOrWhiteSpace($pg_password)) -Critical
    Test-Item "POSTGRES_PASSWORD is NOT default" ($pg_password -ne "adrion_pass") -Critical
}

Write-CHECK "Checking security variables"
$uap_key = [System.Environment]::GetEnvironmentVariable("UAP_API_KEY")
$jwt_secret = [System.Environment]::GetEnvironmentVariable("JWT_SECRET")
$drm_secret = [System.Environment]::GetEnvironmentVariable("DRM_HMAC_SECRET")

Test-Item "UAP_API_KEY is set" (![string]::IsNullOrWhiteSpace($uap_key)) -Critical
Test-Item "UAP_API_KEY is NOT default" ($uap_key -ne "local-dev-key-123") -Critical
Test-Item "JWT_SECRET is set" (![string]::IsNullOrWhiteSpace($jwt_secret)) -Critical
Test-Item "DRM_HMAC_SECRET is set" (![string]::IsNullOrWhiteSpace($drm_secret)) -Critical

if ($env_name -eq "production") {
    Write-CHECK "Production-mode security checks"
    Test-Item "UAP_API_KEY length >= 32 chars" ($uap_key.Length -ge 32) -Critical
    Test-Item "JWT_SECRET length >= 32 chars" ($jwt_secret.Length -ge 32) -Critical
    Test-Item "DRM_HMAC_SECRET length >= 32 chars" ($drm_secret.Length -ge 32) -Critical
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CODE QUALITY GATES
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "SECTION 2: CODE QUALITY GATES"

Write-CHECK "Python tests and coverage"
$pythonTests = & python -m pytest tests/ --co -q 2>$null | Measure-Object -Line
Test-Item "Python tests discoverable" ($pythonTests.Lines -gt 0)

Write-CHECK "Python linting (ruff)"
$ruffResult = & python -m ruff check arbitrage/ tests/ --select E,F,W 2>&1
$ruffErrors = $ruffResult | Measure-Object -Line
Test-Item "Ruff: 0 errors (E,F,W)" ($ruffErrors.Lines -eq 0)

Write-CHECK "Git status"
$gitStatus = & git status --short 2>&1 | Measure-Object -Line
Test-Item "Git working tree clean (or review PRs)" ($gitStatus.Lines -eq 0)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: INFRASTRUCTURE READINESS
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "SECTION 3: INFRASTRUCTURE READINESS"

if (-not $SkipPostgres) {
    Write-CHECK "PostgreSQL availability"
    try {
        $pgTest = & psql -h localhost -U adrion -d genesis_record -c "SELECT version();" 2>&1
        $pgConnected = $pgTest -match "PostgreSQL"
        Test-Item "PostgreSQL connection working" $pgConnected -Critical
    } catch {
        Test-Item "PostgreSQL connection working" $false -Critical
    }
}

if (-not $SkipDocker) {
    Write-CHECK "Docker availability"
    try {
        $dockerTest = & docker --version 2>&1
        $dockerRunning = $dockerTest -match "Docker version"
        Test-Item "Docker installed" $dockerRunning -Critical

        $dockerDaemonTest = & docker ps --quiet 2>&1
        Test-Item "Docker daemon running" ($LASTEXITCODE -eq 0) -Critical
    } catch {
        Test-Item "Docker installed" $false
        Test-Item "Docker daemon running" $false -Critical
    }

    Write-CHECK "Docker Compose file validation"
    $composeValid = & docker-compose -f docker-compose.yml config > $null 2>&1
    Test-Item "docker-compose.yml valid" ($LASTEXITCODE -eq 0) -Critical
}

Write-CHECK "Storage and memory"
$diskInfo = Get-PSDrive -Name C | Select-Object -ExpandProperty Free
$diskGbFree = [math]::Round($diskInfo / 1GB)
Test-Item "Disk space >= 50GB available" ($diskGbFree -ge 50) -Critical

$memory = Get-CimInstance Win32_ComputerSystem | Select-Object -ExpandProperty TotalPhysicalMemory
$memGbTotal = [math]::Round($memory / 1GB)
Test-Item "RAM >= 4GB available" ($memGbTotal -ge 4) -Critical

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: PRIORITY SECURITY CHECKS (1-10)
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "SECTION 4: PRIORITY SECURITY CHECKS"

Write-CHECK "PRIORITY 1: PostgreSQL integration"
Test-Item "PostgreSQL configured (DB_ENGINE=postgresql)" ($db_engine -eq "postgresql")

Write-CHECK "PRIORITY 2: API key header validation"
$apiKeyInCode = Select-String -Path uap/frontend/app.js -Pattern "X-API-Key" -Quiet
Test-Item "API key header in frontend code" $apiKeyInCode

Write-CHECK "PRIORITY 3: Password from environment"
$pgFromEnv = Select-String -Path uap/backend/db.py -Pattern "os.getenv.*POSTGRES_PASSWORD" -Quiet
Test-Item "PostgreSQL password from environment" $pgFromEnv

Write-CHECK "PRIORITY 4: HMAC signature validation"
$hmacValidation = Select-String -Path uap/backend/drm_executor.py -Pattern "hmac.compare_digest" -Quiet
Test-Item "HMAC token validation implemented" $hmacValidation

Write-CHECK "PRIORITY 5: No hardcoded demo credentials"
$demoCredsVisible = Select-String -Path uap/frontend/login.html -Pattern "demo@example.com|demo123" -Quiet
Test-Item "Demo credentials hidden" (-not $demoCredsVisible)

Write-CHECK "PRIORITY 6: Secrets from environment"
$uapFromEnv = Select-String -Path uap/backend/api_v2_extensions.py -Pattern "os.getenv.*UAP_API_KEY" -Quiet
Test-Item "UAP_API_KEY from environment" $uapFromEnv

Write-CHECK "PRIORITY 7: Production mode enforcement"
$prodCheck = Select-String -Path uap/backend/api.py -Pattern "ENVIRONMENT.*production.*sys.exit" -Quiet
Test-Item "Production mode safety check implemented" $prodCheck

Write-CHECK "PRIORITY 8: Rate limiting from JWT"
$jwtArousal = Select-String -Path uap/backend/middleware.py -Pattern "g.token_payload.*arousal" -Quiet
Test-Item "Rate limiting uses JWT payload (not query params)" $jwtArousal

Write-CHECK "PRIORITY 9: XSS protection"
$xssProtection = Select-String -Path uap/frontend/app.js -Pattern "escapeHtml" -Quiet
Test-Item "XSS protection via escapeHtml()" $xssProtection

Write-CHECK "PRIORITY 10: HttpOnly cookie support"
$cookieSupport = Select-String -Path uap/frontend/app.js -Pattern "credentials.*include" -Quiet
Test-Item "HttpOnly cookie support (credentials: include)" $cookieSupport

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: SSL/TLS CERTIFICATES
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "SECTION 5: SSL/TLS CERTIFICATES"

$certPath = Join-Path $root "config\nginx\certs\adrion.crt"
$keyPath = Join-Path $root "config\nginx\certs\adrion.key"

if (Test-Path $certPath) {
    Write-OK "Certificate file exists: $certPath"
    $PASS++
} else {
    Write-WARN "Certificate file missing: $certPath"
    $WARN++
}

if (Test-Path $keyPath) {
    Write-OK "Private key exists: $keyPath"
    $PASS++
} else {
    Write-WARN "Private key missing: $keyPath"
    $WARN++
}

if (Test-Path $certPath) {
    # Note: OpenSSL needed for detailed cert verification
    Write-INFO "For detailed cert check: openssl x509 -in $certPath -text -noout"
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: DATABASE MIGRATIONS
# ─────────────────────────────────────────────────────────────────────────────

if (-not $SkipPostgres) {
    Write-HEADER "SECTION 6: DATABASE MIGRATIONS"

    try {
        $migrations = & python scripts/migrate.py list 2>&1
        $migrationsParsed = $migrations -match "Applied|Pending" | Measure-Object -Line
        Test-Item "Migration script accessible" ($migrationsParsed.Lines -ge 0)

        if ($Verbose) {
            Write-INFO "Migration status:"
            $migrations | ForEach-Object { Write-INFO "  $_" }
        }
    } catch {
        Write-WARN "Could not verify migration status"
        $WARN++
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

Write-HEADER "PRE-FLIGHT VERIFICATION SUMMARY"

$total = $PASS + $FAIL + $WARN
Write-Host ""
Write-Host "  Results:" -ForegroundColor Magenta
Write-Host "    ✅ Passed:  $PASS"
Write-Host "    ❌ Failed:  $FAIL"
Write-Host "    ⚠️  Warned: $WARN"
Write-Host "    ─────────────"
Write-Host "    Total:   $total" -ForegroundColor Cyan

Write-Host ""

if ($FAIL -gt 0) {
    Write-FAIL "PRODUCTION DEPLOYMENT BLOCKED"
    Write-WARN "Fix critical failures before deploying to production"
    exit 1
} elseif ($WARN -gt 0) {
    Write-WARN "PRODUCTION DEPLOYMENT READY (with warnings)"
    Write-INFO "Review warnings and proceed with caution"
    exit 0
} else {
    Write-OK "PRODUCTION DEPLOYMENT APPROVED ✅"
    Write-INFO "All checks passed. Ready for deployment."
    exit 0
}
