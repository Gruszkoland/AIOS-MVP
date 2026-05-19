<#
.SYNOPSIS
    Kopiuje brakujace pliki z Historie Zycia do Pictures na podstawie raportu weryfikacji.

.DESCRIPTION
    Czyta raport Weryfikacja_Historie_Zycia_Do_Obrazy_*.txt, wyciaga liste brakujacych plikow
    (linie SRC= lub NAME=), lokalizuje je w folderze SOURCE i kopiuje do $TargetSubfolder.
    Nie nadpisuje plikow juz istniejacych w miejscu docelowym.
    Dla formatu NAME= przeszukuje SOURCE rekurencyjnie po nazwie pliku.

.PARAMETER ReportPath
    Sciezka do pliku raportu TXT.

.PARAMETER TargetSubfolder
    Folder docelowy. Domyslnie: C:\Users\adiha\Pictures\Historie_Braki_2026-04-02

.PARAMETER DryRun
    Jesli ustawiony -- tylko pokazuje co bylby skopiowane, bez faktycznego kopiowania.

.EXAMPLE
    .\copy_missing_historie_to_pictures.ps1 -DryRun
    .\copy_missing_historie_to_pictures.ps1
#>
param(
    [string]$ReportPath = 'C:\Users\adiha\162 demencje w schemacie 369\Genesis Record\10_RAPORTY_DZIALANIA_SYSTEMU\REPORTS\Weryfikacja_Historie_Zycia_Do_Obrazy_02-04-2026.txt',
    [string]$TargetSubfolder = 'C:\Users\adiha\Pictures\Historie_Braki_2026-04-02',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ReportPath)) {
    Write-Error "Raport nie istnieje: $ReportPath"
    exit 1
}

$reportLines = Get-Content -LiteralPath $ReportPath -Encoding UTF8

# Odczytaj SOURCE= z raportu
$sourceRoot = $null
foreach ($line in $reportLines) {
    if ($line -match '^SOURCE=(.+)$') {
        $sourceRoot = $Matches[1].Trim()
        break
    }
}

# Zbierz lista plikow do skopiowania
# Format SRC=: bezposrednia sciezka
# Format NAME=: tylko nazwa -- szukamy w SOURCE
$srcLines = $reportLines | Where-Object { $_.TrimStart().StartsWith('SRC=') } |
    ForEach-Object { $_.TrimStart().Substring(4).Trim() } | Select-Object -Unique

$nameLines = @()
if ($srcLines.Count -eq 0) {
    # Fallback: NAME= format
    $nameLines = $reportLines | Where-Object { $_ -match '^NAME=([^|]+)' } |
        ForEach-Object { $Matches[1].Trim() } | Select-Object -Unique
}

$total = $srcLines.Count + $nameLines.Count
$copied  = 0
$skipped = 0
$failed  = 0
$notFound = 0

Write-Output "REPORT=$ReportPath"
Write-Output "SOURCE_ROOT=$sourceRoot"
Write-Output "TARGET=$TargetSubfolder"
Write-Output "MISSING_FILES=$total"
Write-Output "DRY_RUN=$($DryRun.IsPresent)"
Write-Output ""

if (-not $DryRun) {
    if (-not (Test-Path -LiteralPath $TargetSubfolder)) {
        New-Item -ItemType Directory -Path $TargetSubfolder -Force | Out-Null
    }
}

# Kopie dla formatu SRC= (pelna sciezka)
foreach ($srcPath in $srcLines) {
    if (-not (Test-Path -LiteralPath $srcPath)) {
        Write-Warning "SKIP_NOT_FOUND: $srcPath"
        $notFound++
        continue
    }

    $fileName = [System.IO.Path]::GetFileName($srcPath)
    $dstPath  = [System.IO.Path]::Combine($TargetSubfolder, $fileName)

    if (Test-Path -LiteralPath $dstPath) {
        Write-Output "ALREADY_EXISTS: $fileName"
        $skipped++
        continue
    }

    if ($DryRun) {
        Write-Output "WOULD_COPY: $srcPath -> $dstPath"
        $copied++
    } else {
        try {
            Copy-Item -LiteralPath $srcPath -Destination $dstPath
            Write-Output "COPIED: $fileName"
            $copied++
        } catch {
            Write-Warning "FAILED: $srcPath - $_"
            $failed++
        }
    }
}

# Kopie dla formatu NAME= (wyszukiwanie w SOURCE)
if ($nameLines.Count -gt 0 -and $sourceRoot) {
    Write-Output "Wyszukiwanie $($nameLines.Count) plikow w: $sourceRoot"
    $srcIndex = @{}
    Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force -ErrorAction SilentlyContinue |
        ForEach-Object { $srcIndex[$_.Name.ToLowerInvariant()] = $_.FullName }

    foreach ($name in $nameLines) {
        $key = $name.ToLowerInvariant()
        if (-not $srcIndex.ContainsKey($key)) {
            Write-Warning "NOT_IN_SOURCE: $name"
            $notFound++
            continue
        }

        $srcPath  = $srcIndex[$key]
        $dstPath  = [System.IO.Path]::Combine($TargetSubfolder, $name)

        if (Test-Path -LiteralPath $dstPath) {
            Write-Output "ALREADY_EXISTS: $name"
            $skipped++
            continue
        }

        if ($DryRun) {
            Write-Output "WOULD_COPY: $srcPath -> $dstPath"
            $copied++
        } else {
            try {
                Copy-Item -LiteralPath $srcPath -Destination $dstPath
                Write-Output "COPIED: $name"
                $copied++
            } catch {
                Write-Warning "FAILED: $name - $_"
                $failed++
            }
        }
    }
}

Write-Output ""
Write-Output "=== SUMMARY ==="
Write-Output "TOTAL=$total"
Write-Output "COPIED=$copied"
Write-Output "SKIPPED=$skipped"
Write-Output "NOT_FOUND=$notFound"
Write-Output "FAILED=$failed"

if ($failed -gt 0) { exit 2 }
exit 0

