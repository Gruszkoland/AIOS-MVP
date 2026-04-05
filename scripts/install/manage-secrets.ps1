<#
.SYNOPSIS
    ADRION 369 — Secrets Manager
.DESCRIPTION
    Generuje, rotuje i waliduje sekrety (.env) bez przechowywania ich w repo.
    Wspiera: POSTGRES_PASSWORD, N8N_AUTH_PASSWORD, STRIPE_KEY, APIFY_TOKEN.
.EXAMPLE
    .\manage-secrets.ps1 -Action generate
    .\manage-secrets.ps1 -Action rotate -Key POSTGRES_PASSWORD
    .\manage-secrets.ps1 -Action validate
#>
[CmdletBinding()]
param(
    [ValidateSet("generate","rotate","validate","show-keys")]
    [string]$Action  = "validate",
    [string]$Root    = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Key     = "",
    [int]$Length     = 32
)

$EnvFile = Join-Path $Root ".env"

function Write-OK   { param($m) Write-Host "  [OK] $m" -ForegroundColor Green  }
function Write-WARN { param($m) Write-Host "  [!!] $m" -ForegroundColor Yellow }
function Write-INFO { param($m) Write-Host "       $m" -ForegroundColor Gray   }

# ── Secret generation ─────────────────────────────────────────────────────────
function New-RandomSecret {
    param([int]$Len = 32)
    $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#%^&*'
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $bytes = New-Object byte[] $Len
    $rng.GetBytes($bytes)
    return ($bytes | ForEach-Object { $chars[$_ % $chars.Length] }) -join ""
}

# ── Load env ──────────────────────────────────────────────────────────────────
function Get-EnvDict {
    $d = @{}
    if (Test-Path $EnvFile) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match "^\s*([A-Z_0-9]+)\s*=\s*(.*)$") {
                $d[$matches[1]] = $matches[2].Trim('"').Trim("'")
            }
        }
    }
    return $d
}

function Set-EnvKey {
    param([string]$Key, [string]$Value)
    $lines = if (Test-Path $EnvFile) { Get-Content $EnvFile } else { @() }
    $newLines = $lines | Where-Object { $_ -notmatch "^$Key=" }
    $newLines += "$Key=$Value"
    Set-Content $EnvFile $newLines -Encoding UTF8
}

Write-Host ""
Write-Host "=== ADRION 369 — Manage Secrets ===" -ForegroundColor Cyan
Write-Host "  Env: $EnvFile" -ForegroundColor DarkGray

# ── Secret definitions ────────────────────────────────────────────────────────
$secretKeys = @(
    @{ Key = "POSTGRES_PASSWORD";      Mask = $true;  Required = $false; Default = "" }
    @{ Key = "N8N_BASIC_AUTH_PASSWORD"; Mask = $true;  Required = $false; Default = "" }
    @{ Key = "STRIPE_SECRET_KEY";      Mask = $true;  Required = $false; Default = "" }
    @{ Key = "STRIPE_WEBHOOK_SECRET";  Mask = $true;  Required = $false; Default = "" }
    @{ Key = "APIFY_TOKEN";            Mask = $true;  Required = $false; Default = "" }
    @{ Key = "OPENAI_API_KEY";         Mask = $true;  Required = $false; Default = "" }
    @{ Key = "ANTHROPIC_API_KEY";      Mask = $true;  Required = $false; Default = "" }
    @{ Key = "GOOGLE_API_KEY";         Mask = $true;  Required = $false; Default = "" }
)

switch ($Action) {
    "generate" {
        Write-INFO "Generuję silne losowe hasła dla kluczy infrastrukturalnych..."
        $envDict = Get-EnvDict

        $generated = @()
        foreach ($s in @("POSTGRES_PASSWORD", "N8N_BASIC_AUTH_PASSWORD")) {
            if ([string]::IsNullOrEmpty($envDict[$s]) -or $envDict[$s] -eq "adrion_pass") {
                $newVal = New-RandomSecret -Len $Length
                Set-EnvKey -Key $s -Value $newVal
                $generated += $s
                Write-OK "$s — wygenerowano ($Length znaków)"
            } else {
                Write-INFO "$s — już ustawiony (pominięto)"
            }
        }

        # Synchronize docker-compose env (N8N and postgres passwords)
        if ($generated.Count -gt 0) {
            Write-WARN "Pamiętaj: zaktualizuj adrion-swarm/docker-compose.yml lub użyj `${ENV_VAR} składni"
        }
        Write-OK "Gotowe — $($generated.Count) sekretów wygenerowanych"
    }

    "rotate" {
        if ([string]::IsNullOrEmpty($Key)) {
            Write-WARN "Podaj -Key <NAZWA_KLUCZA> do rotacji"
            exit 1
        }
        $envDict = Get-EnvDict
        $oldVal = $envDict[$Key]
        $newVal = New-RandomSecret -Len $Length
        Set-EnvKey -Key $Key -Value $newVal

        # Backup old value
        $backupFile = Join-Path $Root "logs\secrets\secrets-backup-$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        New-Item -ItemType Directory -Force -Path (Split-Path $backupFile) | Out-Null
        "$Key (previous): $($oldVal.Substring(0,[math]::Min(4,$oldVal.Length)))***" | Out-File $backupFile
        Write-OK "$Key — zrotowany. Backup: $backupFile"
        Write-WARN "Zrestartuj serwisy które używają tego sekretu!"
    }

    "validate" {
        $envDict = Get-EnvDict
        $issues  = @()

        # Check for default/weak passwords
        $weakPatterns = @("password", "adrion_pass", "changeme", "12345", "admin", "secret")
        foreach ($s in $secretKeys) {
            $val = $envDict[$s.Key]
            if ([string]::IsNullOrEmpty($val)) {
                if ($s.Required) {
                    Write-WARN "$($s.Key): BRAK (wymagany)"
                    $issues += $s.Key
                } else {
                    Write-INFO "$($s.Key): nieskonfigurowany (opcjonalny)"
                }
                continue
            }
            foreach ($weak in $weakPatterns) {
                if ($val.ToLower().Contains($weak)) {
                    Write-WARN "$($s.Key): słabe hasło! (zawiera '$weak')"
                    $issues += "$($s.Key) weak"
                    break
                }
            }
            if ($val.Length -lt 12 -and $s.Key -like "*PASSWORD*") {
                Write-WARN "$($s.Key): za krótkie hasło ($($val.Length) znaków, min 12)"
                $issues += "$($s.Key) short"
            } else {
                $masked = $val.Substring(0,[math]::Min(4,$val.Length)) + "***"
                Write-OK "$($s.Key): $masked"
            }
        }

        Write-Host ""
        if ($issues.Count -eq 0) {
            Write-OK "Wszystkie sekrety OK"
        } else {
            Write-WARN "$($issues.Count) problemów z sekretami"
            Write-INFO "Uruchom: .\manage-secrets.ps1 -Action generate"
        }
    }

    "show-keys" {
        Write-INFO "Wymagane klucze środowiskowe:"
        $secretKeys | ForEach-Object {
            $req = if ($_.Required) { "[WYMAGANY]" } else { "[opcjonalny]" }
            Write-Host "  $($_.Key.PadRight(30)) $req" -ForegroundColor Gray
        }
    }
}
Write-Host ""
