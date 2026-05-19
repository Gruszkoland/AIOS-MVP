param(
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$userRoot = 'C:\Users\adiha'
$driveDir = Get-ChildItem -LiteralPath $userRoot -Directory | Where-Object { $_.Name -like 'M*' -and $_.Name -match 'dysk' } | Select-Object -First 1
$srcDir = Get-ChildItem -LiteralPath $driveDir.FullName -Directory | Where-Object { $_.Name -like 'Historie*' } | Select-Object -First 1
$dstDir = 'C:\Users\adiha\Pictures'
$excludeReview = '\\_review_ThumbsDb_2026-04-02\\'

$srcAll = Get-ChildItem -LiteralPath $srcDir.FullName -File -Recurse -Force -ErrorAction SilentlyContinue
$src = $srcAll | Where-Object { $_.FullName -notmatch $excludeReview }
$dst = Get-ChildItem -LiteralPath $dstDir -File -Recurse -Force -ErrorAction SilentlyContinue

$srcHashCount = @{}
$dstHashCount = @{}
$srcExamplePath = @{}

foreach ($f in $src) {
    try {
        $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
        if (-not $srcHashCount.ContainsKey($h)) {
            $srcHashCount[$h] = 0
            $srcExamplePath[$h] = $f.FullName
        }
        $srcHashCount[$h]++
    }
    catch {
    }
}

foreach ($f in $dst) {
    try {
        $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
        if (-not $dstHashCount.ContainsKey($h)) {
            $dstHashCount[$h] = 0
        }
        $dstHashCount[$h]++
    }
    catch {
    }
}

$missing = New-Object System.Collections.Generic.List[object]
foreach ($h in $srcHashCount.Keys) {
    $need = $srcHashCount[$h]
    $have = 0
    if ($dstHashCount.ContainsKey($h)) {
        $have = $dstHashCount[$h]
    }
    if ($have -lt $need) {
        $missing.Add([PSCustomObject]@{
            Hash = $h
            Need = $need
            Have = $have
            Missing = ($need - $have)
            Example = $srcExamplePath[$h]
        })
    }
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('SOURCE=' + $srcDir.FullName)
$lines.Add('TARGET=' + $dstDir)
$lines.Add('SOURCE_FILES_ALL=' + $srcAll.Count)
$lines.Add('SOURCE_FILES_EXCL_REVIEW=' + $src.Count)
$lines.Add('TARGET_FILES=' + $dst.Count)
$lines.Add('SOURCE_UNIQUE_HASHES=' + $srcHashCount.Keys.Count)
$lines.Add('TARGET_UNIQUE_HASHES=' + $dstHashCount.Keys.Count)
$lines.Add('MISSING_HASH_GROUPS=' + $missing.Count)
$lines.Add('MISSING_FILE_INSTANCES=' + (($missing | Measure-Object Missing -Sum).Sum))
$lines.Add('STATUS=' + ($(if ($missing.Count -eq 0) { 'OK_ALL_PRESENT' } else { 'MISSING_DETECTED' })))
$lines.Add('')
$lines.Add('TOP_MISSING')
foreach ($m in ($missing | Sort-Object Missing -Descending | Select-Object -First 30)) {
    $lines.Add('HASH=' + $m.Hash + '|need=' + $m.Need + '|have=' + $m.Have + '|missing=' + $m.Missing)
    $lines.Add('  SRC=' + $m.Example)
}

[System.IO.File]::WriteAllLines($OutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
$lines
