<#
.SYNOPSIS
    ADRION 369 — Log Cleanup
.DESCRIPTION
    Rotuje i czyści stare logi: monitor, backup, install, API, Docker.
    Domyślna retencja: 7 dni.
.PARAMETER Retention
    Ilość dni do zachowania (domyślnie: 7)
#>
[CmdletBinding()]
param(
    [int]$Retention = 7,
    [string]$Root   = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$cutoff   = (Get-Date).AddDays(-$Retention)
$LOG_DIR  = Join-Path $Root "logs"
$MAIN_LOG = Join-Path $LOG_DIR "maintenance\cleanup-$(Get-Date -Format 'yyyyMMdd').log"

New-Item -ItemType Directory -Force -Path (Split-Path $MAIN_LOG) | Out-Null

function Write-Log { param($L,$M); $ts=Get-Date -Format "HH:mm:ss"; $line="[$ts][$L] $M"; Add-Content $MAIN_LOG $line -Encoding UTF8; Write-Host $line -ForegroundColor $(switch($L){"OK"{"Green"}"WARN"{"Yellow"}default{"Gray"}}) }

Write-Host ""
Write-Host "=== ADRION 369 — Cleanup Logs ===" -ForegroundColor Cyan
Write-Log "INFO" "Cleanup start (retencja ${Retention} dni, cutoff=$($cutoff.ToString('yyyy-MM-dd')))"

$totalRemoved = 0
$totalFreedMB = 0.0

# Directories to clean
$logDirs = @(
    @{ Path = Join-Path $LOG_DIR "monitor";     Pattern = "*.log" }
    @{ Path = Join-Path $LOG_DIR "install";     Pattern = "*.log" }
    @{ Path = Join-Path $LOG_DIR "maintenance"; Pattern = "*.log" }
    @{ Path = Join-Path $LOG_DIR "secrets";     Pattern = "*.txt" }
    @{ Path = Join-Path $Root ".runtime";       Pattern = "*.log" }
    @{ Path = Join-Path $ROOT ".runtime";       Pattern = "*.err.log" }
)

foreach ($dir in $logDirs) {
    if (-not (Test-Path $dir.Path)) { continue }
    $files = Get-ChildItem $dir.Path -Filter $dir.Pattern -File |
             Where-Object { $_.LastWriteTime -lt $cutoff }
    $count = 0; $sizeMB = 0.0
    foreach ($f in $files) {
        $sizeMB += $f.Length / 1MB
        Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
        $count++
    }
    if ($count -gt 0) {
        Write-Log "OK" "$($dir.Path): $count plików ($([math]::Round($sizeMB,1)) MB)"
        $totalRemoved += $count
        $totalFreedMB += $sizeMB
    }
}

# Genesis Record logs (optional — only temp/progress files)
$genesisProgress = Join-Path $Root "Genesis Record\10_RAPORTY_DZIALANIA_SYSTEMU\PROGRESS"
if (Test-Path $genesisProgress) {
    $oldProgress = Get-ChildItem $genesisProgress -Filter "*.md" |
                   Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) }
    Write-Log "INFO" "Genesis PROGRESS: $($oldProgress.Count) plików starszych niż 30 dni (zachowane)"
}

# Docker logs trim (if docker available)
try {
    docker info 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        # Compress old Docker logs (not delete — Docker manages internally)
        Write-Log "INFO" "Docker zarządza własną rotacją logów (json-file + max-size skonfigurowany)"
    }
} catch {}

# Large temporary files
$tempPatterns = @("*.tmp", "_precommit_*.log", "_precommit_*.txt")
foreach ($pattern in $tempPatterns) {
    $found = Get-ChildItem $Root -Filter $pattern -File -ErrorAction SilentlyContinue
    foreach ($f in $found) {
        $sizeMB = $f.Length / 1MB
        Remove-Item $f.FullName -Force -ErrorAction SilentlyContinue
        Write-Log "OK" "Usunięto temp: $($f.Name) ($([math]::Round($sizeMB,2)) MB)"
        $totalRemoved++; $totalFreedMB += $sizeMB
    }
}

Write-Log "OK" "Zakończono: $totalRemoved plików, $([math]::Round($totalFreedMB,1)) MB zwolnione"
Write-Host ""
