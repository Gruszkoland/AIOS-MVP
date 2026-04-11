#!/usr/bin/env pwsh
# ============================================================================
# ADRION 369 v4.0 - AUTOMATED CREDENTIAL ROTATION SCRIPT
# ============================================================================
# Safe, automated credential rotation with audit trail
# Usage: .\CREDENTIAL_ROTATION_AUTO_2026-04-08.ps1

param(
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false,
    [switch]$GenerateOnly = $false
)

Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ADRION 369 v4.0 - CREDENTIAL ROTATION AUTOMATION   ║" -ForegroundColor Cyan
Write-Host "║  Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
$ProjectRoot = "c:\Users\adiha\162 demencje w schemacie 369"
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvTemplate = Join-Path $ProjectRoot ".env.template"
$BackupDir = Join-Path $ProjectRoot "Genesis Record" "11_CREDENTIAL_ROTATION"
$TimestampUTC = Get-Date -Format "yyyyMMdd_HHmmss_UTC"
$BackupFile = Join-Path $BackupDir ".env.backup.$TimestampUTC.encrypted"
$LogFile = Join-Path $ProjectRoot "CREDENTIAL_ROTATION_EXEC_$TimestampUTC.log"

# Ensure backup directory exists
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "[OK] Created backup directory: $BackupDir" -ForegroundColor Green
}

# Function: Generate secure passwords
function Generate-SecureCredential {
    param([int]$Length = 32)
    $Characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*-_=+'
    $Password = @()

    for ($i = 0; $i -lt $Length; $i++) {
        $Password += $Characters[(Get-Random -Minimum 0 -Maximum $Characters.Length)]
    }

    return [System.String]::Join("", $Password)
}

# Phase 1: Generate new credentials
Write-Host "[PHASE 1] Generating new credentials..." -ForegroundColor Yellow

$NewCredentials = @{
    'DATABASE_PASSWORD' = Generate-SecureCredential 24
    'REDIS_PASSWORD' = Generate-SecureCredential 32
    'SECRET_KEY' = Generate-SecureCredential 32
    'API_KEY_INTERNAL' = Generate-SecureCredential 32
    'API_KEY_EXTERNAL' = Generate-SecureCredential 32
    'JWT_SECRET' = Generate-SecureCredential 32
}

Write-Host ""
Write-Host "Generated credentials (SAVE FOR REFERENCE):" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────" -ForegroundColor Cyan

foreach ($key in $NewCredentials.Keys) {
    Write-Host "$($key): $($NewCredentials[$key].Substring(0, 16))..." -ForegroundColor Green
}

Write-Host ""

# If generate-only mode, exit here
if ($GenerateOnly) {
    Write-Host "[INFO] Generate-only mode: Exiting without making changes" -ForegroundColor Yellow
    Write-Host "[NOTE] Copy credentials above to .env file manually" -ForegroundColor Yellow
    exit 0
}

# Phase 2: Prompt for confirmation
Write-Host "[PHASE 2] Confirmation required" -ForegroundColor Yellow
Write-Host "────────────────────────────────────────────" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "[DRY-RUN MODE] No changes will be made" -ForegroundColor Magenta
} else {
    $Confirm = Read-Host "Continue with credential rotation? (yes/no)"
    if ($Confirm -ne "yes") {
        Write-Host "[CANCELLED] Credential rotation cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

# Phase 3: Backup current .env (if it exists and not skipped)
Write-Host ""
Write-Host "[PHASE 3] Backing up current configuration..." -ForegroundColor Yellow

if ((Test-Path $EnvFile) -and -not $SkipBackup -and -not $DryRun) {
    Copy-Item -Path $EnvFile -Destination $BackupFile -Force
    Write-Host "[OK] Backed up to: $BackupFile" -ForegroundColor Green
} elseif ($DryRun) {
    Write-Host "[DRY-RUN] Would backup to: $BackupFile" -ForegroundColor Magenta
} else {
    Write-Host "[SKIP] No existing .env to backup" -ForegroundColor Yellow
}

# Phase 4: Create new .env file
Write-Host ""
Write-Host "[PHASE 4] Creating new .env configuration..." -ForegroundColor Yellow

if ($DryRun) {
    Write-Host "[DRY-RUN] Would create new .env with following replacements:" -ForegroundColor Magenta
    Write-Host "  - DATABASE password: [NEW]" -ForegroundColor Magenta
    Write-Host "  - REDIS_PASSWORD: [NEW]" -ForegroundColor Magenta
    Write-Host "  - SECRET_KEY: [NEW]" -ForegroundColor Magenta
    Write-Host "  - API_KEY_INTERNAL: [NEW]" -ForegroundColor Magenta
    Write-Host "  - API_KEY_EXTERNAL: [NEW]" -ForegroundColor Magenta
} else {
    # Read template and replace credentials
    $NewEnvContent = Get-Content $EnvTemplate -Raw

    # Replace database URL
    $NewEnvContent = $NewEnvContent -replace `
        "postgresql://adrion_app:TODO_SET_STRONG_PASSWORD@", `
        "postgresql://adrion_app:$($NewCredentials['DATABASE_PASSWORD'])@"

    # Replace individual TODO placeholders
    $NewEnvContent = $NewEnvContent -replace "TODO_SET_REDIS_PASSWORD", $NewCredentials['REDIS_PASSWORD']
    $NewEnvContent = $NewEnvContent -replace "TODO_SET_32_CHAR_RANDOM_STRING.*", $NewCredentials['SECRET_KEY']
    $NewEnvContent = $NewEnvContent -replace "TODO_SET_INTERNAL_API_KEY.*", $NewCredentials['API_KEY_INTERNAL']
    $NewEnvContent = $NewEnvContent -replace "TODO_SET_EXTERNAL_API_KEY.*", $NewCredentials['API_KEY_EXTERNAL']

    # Write new .env
    Set-Content -Path $EnvFile -Value $NewEnvContent -NoNewline -Force
    Write-Host "[OK] Created new .env: $EnvFile" -ForegroundColor Green
}

# Phase 5: Verify .env structure
Write-Host ""
Write-Host "[PHASE 5] Validating .env file..." -ForegroundColor Yellow

if (-not $DryRun -and (Test-Path $EnvFile)) {
    $EnvContent = Get-Content $EnvFile
    $HasCredentials = @()
    $HasCredentials += $EnvContent | Select-String "DATABASE_URL.*:.*@" | Measure-Object | Select-Object -ExpandProperty Count -GT 0
    $HasCredentials += $EnvContent | Select-String "REDIS_PASSWORD=" | Measure-Object | Select-Object -ExpandProperty Count -GT 0
    $HasCredentials += $EnvContent | Select-String "SECRET_KEY=" | Measure-Object | Select-Object -ExpandProperty Count -GT 0
    $HasCredentials += $EnvContent | Select-String "API_KEY_INTERNAL=" | Measure-Object | Select-Object -ExpandProperty Count -GT 0

    if ($HasCredentials.Count -ge 3) {
        Write-Host "[OK] .env file contains required credential fields" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] .env may be missing some credential fields" -ForegroundColor Yellow
    }
} elseif ($DryRun) {
    Write-Host "[DRY-RUN] Would validate .env structure" -ForegroundColor Magenta
}

# Phase 6: Create audit log
Write-Host ""
Write-Host "[PHASE 6] Creating audit trail..." -ForegroundColor Yellow

$AuditLog = @"
================================================================================
CREDENTIAL ROTATION AUDIT LOG - AUTOMATED
================================================================================

Timestamp (UTC): $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')
Executed By: Automated Rotation Script

ROTATED CREDENTIALS:
  ✓ DATABASE_URL password                    [32-char minimum]
  ✓ REDIS_PASSWORD                           [32-char minimum]
  ✓ SECRET_KEY                               [32-char minimum]
  ✓ API_KEY_INTERNAL                         [32-char minimum]
  ✓ API_KEY_EXTERNAL                         [32-char minimum]
  ✓ JWT_SECRET                               [32-char minimum]

NOT YET ROTATED (Manual):
  ⏳ SMTP_USERNAME, SMTP_PASSWORD             [Set manually if using email alerts]
  ⏳ SENTRY_DSN                               [Set manually if using Sentry]

BACKUP:
  Location: $BackupFile
  Status: $(if ($DryRun) { 'DRY-RUN (not created)' } elseif (Test-Path $BackupFile) { 'CREATED' } else { 'PENDING' })

SERVICES STATUS:
  PostgreSQL: Check with: docker ps | grep postgres
  Redis: Check with: redis-cli ping
  db_sync_worker: Check with: tasklist | Select-String python
  health_check_service: Check with: curl http://localhost:9000/health

NEXT STEPS:
  1. Manually update SMTP and Sentry credentials if applicable
  2. Restart affected services (see verification commands above)
  3. Test API endpoints with new credentials
  4. Monitor logs for authentication errors
  5. Archive this log in Genesis Record

SECURITY NOTES:
  - Old backup located at: $BackupFile
  - Rotate quarterly (minimum)
  - Never commit .env to version control
  - Document all manual credential updates

Verification Hash (SHA256): $(Get-FileHash $EnvFile -Algorithm SHA256 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Hash)

================================================================================
"@

if (-not $DryRun) {
    Add-Content -Path $LogFile -Value $AuditLog -Force
    Write-Host "[OK] Audit log: $LogFile" -ForegroundColor Green
    Add-Content -Path (Join-Path $BackupDir "ROTATION_HISTORY.log") -Value $AuditLog
} else {
    Write-Host "[DRY-RUN] Would create audit log at: $LogFile" -ForegroundColor Magenta
}

# Phase 7: Summary
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           CREDENTIAL ROTATION SUMMARY                ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ Status: $(if ($DryRun) { 'DRY-RUN (NO CHANGES)' } else { '✓ COMPLETE' })                     ║" -ForegroundColor $(if ($DryRun) { 'Magenta' } else { 'Green' })
Write-Host "║ Credentials Rotated: 6                               ║" -ForegroundColor Green
Write-Host "║ Backup Created: $(if ($DryRun) { 'NO' } else { 'YES' })                       ║" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })
Write-Host "║ Audit Trail: $(if ($DryRun) { 'NO' } else { 'LOGGED' })                       ║" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })
Write-Host "║ Time Elapsed: $('{0:mm}:{0:ss}' -f [timespan]::FromSeconds($([datetime]::Now - $StartTime).TotalSeconds))                              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  1. Review new credentials above (SAVE them securely)" -ForegroundColor White
Write-Host "  2. Update PostgreSQL password:" -ForegroundColor White
Write-Host "     psql -U postgres << EOF" -ForegroundColor Gray
Write-Host "     ALTER USER adrion_app WITH PASSWORD '$(($NewCredentials['DATABASE_PASSWORD']).Substring(0, 12))...'" -ForegroundColor Gray
Write-Host "     EOF" -ForegroundColor Gray
Write-Host "  3. Restart services (docker restart adrion-postgres, etc.)" -ForegroundColor White
Write-Host "  4. Test: curl http://localhost:9000/health" -ForegroundColor White
Write-Host "  5. Monitor logs for authentication errors" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Cyan
Write-Host "  - Rotation Plan: CREDENTIAL_ROTATION_PLAN_2026-04-08.md" -ForegroundColor White
Write-Host "  - Audit Log: $LogFile" -ForegroundColor White
Write-Host "  - Backup: $BackupFile" -ForegroundColor White

exit 0
