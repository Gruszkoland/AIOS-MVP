# sync-dokumentacja.ps1
# Bidirectional sync: Desktop\Dokumentacja <-> .1_Projekty\WSZYSTKIE DOKUMENTY ADRIANA
# Wyklucza .1_Projekty aby uniknac petli (junction/symlink)

$A = "C:\Users\adiha\Desktop\Dokumentacja"
$B = "C:\Users\adiha\.1_Projekty\WSZYSTKIE DOKUMENTY ADRIANA"
$LOG = "C:\Users\adiha\sync-dokumentacja.log"
$STATUS_LOG = "C:\Users\adiha\sync-dokumentacja-status.log"
$LAST_STATUS = "C:\Users\adiha\sync-dokumentacja-last-status.txt"
$HEALTH_LOG = "C:\Users\adiha\sync-dokumentacja-health.log"

function Convert-HashBytesToHex {
    param([byte[]]$Bytes)

    return ([System.BitConverter]::ToString($Bytes)).Replace("-", "")
}

function Get-RelativePath {
    param(
        [string]$Root,
        [string]$FullName
    )

    if ($FullName.StartsWith($Root, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $FullName.Substring($Root.Length).TrimStart('\\')
    }

    return $FullName
}

function Test-IsExcludedRelativePath {
    param(
        [string]$RelativePath,
        [string[]]$ExcludedDirs
    )

    foreach ($dir in $ExcludedDirs) {
        if ($RelativePath -eq $dir -or $RelativePath -like "$dir\\*" -or $RelativePath -like "*\\$dir\\*") {
            return $true
        }
    }

    return $false
}

function Get-SyncHealthSnapshot {
    param(
        [string]$Root,
        [string[]]$ExcludedDirs,
        [int]$SampleSize = 25,
        [int]$MaxCountScan = 5000
    )

    $count = 0
    $isCountTruncated = $false
    $sample = @()
    $scanFailed = $false

    try {
        foreach ($f in (Get-ChildItem -Path $Root -Recurse -File -Force -ErrorAction SilentlyContinue)) {
            $rel = Get-RelativePath -Root $Root -FullName $f.FullName
            if (Test-IsExcludedRelativePath -RelativePath $rel -ExcludedDirs $ExcludedDirs) {
                continue
            }

            $count++
            if ($sample.Count -lt $SampleSize) {
                $sample += $f
            }

            if ($count -ge $MaxCountScan) {
                $isCountTruncated = $true
                break
            }
        }
    }
    catch {
        $scanFailed = $true
    }

    $sb = New-Object System.Text.StringBuilder

    foreach ($f in $sample) {
        $rel = Get-RelativePath -Root $Root -FullName $f.FullName
        $fileHash = "ERR"
        try {
            $fileHash = (Get-FileHash -Path $f.FullName -Algorithm SHA256 -ErrorAction Stop).Hash
        }
        catch {
            $fileHash = "ERR"
        }

        [void]$sb.AppendLine("$rel|$($f.Length)|$fileHash")
    }

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($sb.ToString())
        $aggregateHash = Convert-HashBytesToHex -Bytes ($sha.ComputeHash($bytes))
    }
    finally {
        $sha.Dispose()
    }

    return [PSCustomObject]@{
        FileCount        = $count
        IsCountTruncated = $isCountTruncated
        ScanFailed       = $scanFailed
        SampleCount      = @($sample).Count
        SampleHash       = $aggregateHash
    }
}

function Write-HealthLog {
    param(
        [string]$Level,
        [string]$Message
    )

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $HEALTH_LOG -Value "[$ts] [$Level] $Message"
}

function Send-SyncNotification {
    param(
        [string]$Title,
        [string]$Message,
        [bool]$IsError = $false
    )

    $level = if ($IsError) { "FAIL" } else { "SUCCESS" }
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$level] $Message"
    Add-Content -Path $STATUS_LOG -Value $line
    Set-Content -Path $LAST_STATUS -Value $line

    try {
        if (Get-Module -ListAvailable -Name BurntToast) {
            Import-Module BurntToast -ErrorAction Stop
            New-BurntToastNotification -Text $Title, $Message | Out-Null
        }
        elseif (Get-Command msg -ErrorAction SilentlyContinue) {
            msg $env:USERNAME "$Title - $Message" | Out-Null
        }
    }
    catch {
        Add-Content -Path $STATUS_LOG -Value "[$ts] [WARN] Notification dispatch failed: $($_.Exception.Message)"
    }
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $LOG "[$timestamp] === SYNC START ==="

Write-Host "[$timestamp] Sync START"
Write-Host ""

# Foldery do wykluczenia (dev, cache, duze foldery binarne)
$EXCLUDE_DIRS = @(".1_Projekty", "node_modules", ".git", ".venv", "__pycache__", ".vscode", "dist", "build", ".next", ".nuxt", "vendor", "target", "bin", "obj")

# KROK 1: A --> B (kopiuje pliki nowsze lub brakujace w B)
Write-Host "KROK 1: Dokumentacja --> WSZYSTKIE DOKUMENTY ADRIANA"
robocopy $A $B /E /XO /FFT /R:1 /W:1 /NP /XD $EXCLUDE_DIRS /LOG+:$LOG
$exitA = $LASTEXITCODE
Write-Host "Exit A-->B: $exitA"
Write-Host ""

# KROK 2: B --> A (kopiuje pliki nowsze lub brakujace w A)
Write-Host "KROK 2: WSZYSTKIE DOKUMENTY ADRIANA --> Dokumentacja"
robocopy $B $A /E /XO /FFT /R:1 /W:1 /NP /XD $EXCLUDE_DIRS /LOG+:$LOG
$exitB = $LASTEXITCODE
Write-Host "Exit B-->A: $exitB"
Write-Host ""

$timestamp2 = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content $LOG "[$timestamp2] === SYNC END (A->B: $exitA, B->A: $exitB) ==="

# Robocopy exit codes: 0=brak zmian, 1=skopiowane, 2=extra, 3=skopiowane+extra, 8+=bledy
if ($exitA -le 7 -and $exitB -le 7) {
    Write-Host "SYNC OK - brak bledow"

    # Health-check po udanym sync: porownuje liczbe plikow i hash probki po obu stronach.
    $healthA = Get-SyncHealthSnapshot -Root $A -ExcludedDirs $EXCLUDE_DIRS
    $healthB = Get-SyncHealthSnapshot -Root $B -ExcludedDirs $EXCLUDE_DIRS

    $isCountComparable = (-not $healthA.IsCountTruncated) -and (-not $healthB.IsCountTruncated) -and (-not $healthA.ScanFailed) -and (-not $healthB.ScanFailed)
    $isCountOk = if ($isCountComparable) { $healthA.FileCount -eq $healthB.FileCount } else { $true }
    $isHashOk = ($healthA.SampleHash -eq $healthB.SampleHash)
    $isHealthOk = $isCountOk -and $isHashOk

    if ($isHealthOk) {
        $countInfo = if ($isCountComparable) { "files=$($healthA.FileCount)" } else { "files=scanned:$($healthA.FileCount)/$($healthB.FileCount) (truncated)" }
        $okMessage = "Synchronizacja i health-check OK (A->B: $exitA, B->A: $exitB, $countInfo, sampleHash=$($healthA.SampleHash.Substring(0, 12)))."
        Write-HealthLog -Level "SUCCESS" -Message $okMessage
        Send-SyncNotification -Title "SyncDokumentacjaADRION" -Message $okMessage
    }
    else {
        $failMessage = "Rozjazd po sync: count A=$($healthA.FileCount), B=$($healthB.FileCount), truncated A=$($healthA.IsCountTruncated), B=$($healthB.IsCountTruncated); sampleHash A=$($healthA.SampleHash.Substring(0, 12)), B=$($healthB.SampleHash.Substring(0, 12))."
        Write-HealthLog -Level "FAIL" -Message $failMessage
        Send-SyncNotification -Title "SyncDokumentacjaADRION" -Message $failMessage -IsError $true
    }

    # Auto-commit Knowledge Bank po kazdym poprawnym sync.
    $autoCommitScript = "C:\Users\adiha\kb-auto-commit.ps1"
    if (Test-Path $autoCommitScript) {
        try {
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $autoCommitScript
        }
        catch {
            Write-Host "UWAGA: Auto-commit nie powiodl sie: $($_.Exception.Message)"
        }
    }
    else {
        Write-Host "UWAGA: Brak skryptu auto-commit: $autoCommitScript"
    }
}
else {
    Write-Host "UWAGA: Blad sync (A->B: $exitA, B->A: $exitB) - sprawdz log: $LOG"
    Write-HealthLog -Level "FAIL" -Message "Blad robocopy: A->B=$exitA, B->A=$exitB"
    Send-SyncNotification -Title "SyncDokumentacjaADRION" -Message "Blad synchronizacji (A->B: $exitA, B->A: $exitB). Sprawdz: $LOG" -IsError $true
}
