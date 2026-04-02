param(
    [Parameter(Mandatory = $true)]
    [string]$CsvPath,

    [Parameter(Mandatory = $true)]
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

function Get-UniquePath {
    param(
        [string]$DesiredPath,
        [string]$SourceTag
    )

    if (-not (Test-Path -LiteralPath $DesiredPath)) {
        return $DesiredPath
    }

    $dir = Split-Path -Path $DesiredPath -Parent
    $leaf = Split-Path -Path $DesiredPath -Leaf
    $name = [System.IO.Path]::GetFileNameWithoutExtension($leaf)
    $ext = [System.IO.Path]::GetExtension($DesiredPath)
    $safeTag = ($SourceTag -replace '[^A-Za-z0-9_-]', '_')
    $stamp = Get-Date -Format 'yyyyMMddHHmmss'
    $index = 1

    while ($true) {
        $candidate = Join-Path $dir ("{0}__from_{1}_{2}_{3}{4}" -f $name, $safeTag, $stamp, $index, $ext)
        if (-not (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
        $index++
    }
}

function Move-SourceIntoTarget {
    param(
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$SourceName,
        [System.Collections.Generic.List[string]]$LogLines
    )

    if (-not (Test-Path -LiteralPath $SourcePath)) {
        $LogLines.Add("SKIP|missing_source|$SourcePath")
        return
    }

    if ($SourcePath.TrimEnd('\\') -ieq $TargetPath.TrimEnd('\\')) {
        $LogLines.Add("SKIP|already_in_place|$SourcePath")
        return
    }

    $targetParent = Split-Path -Path $TargetPath -Parent
    if (-not (Test-Path -LiteralPath $targetParent)) {
        New-Item -ItemType Directory -Path $targetParent -Force | Out-Null
        $LogLines.Add("MKDIR|$targetParent")
    }

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        Move-Item -LiteralPath $SourcePath -Destination $TargetPath
        $LogLines.Add("MOVE_DIR|$SourcePath|$TargetPath")
        return
    }

    $LogLines.Add("MERGE_DIR|$SourcePath|$TargetPath")
    $children = Get-ChildItem -LiteralPath $SourcePath -Force
    foreach ($child in $children) {
        $desired = Join-Path $TargetPath $child.Name
        if (Test-Path -LiteralPath $desired) {
            $desired = Get-UniquePath -DesiredPath $desired -SourceTag $SourceName
            $LogLines.Add("RENAME_ON_COLLISION|$($child.FullName)|$desired")
        }
        Move-Item -LiteralPath $child.FullName -Destination $desired
        $LogLines.Add("MOVE_ITEM|$($child.FullName)|$desired")
    }

    $remaining = Get-ChildItem -LiteralPath $SourcePath -Force -ErrorAction SilentlyContinue
    if (($remaining | Measure-Object).Count -eq 0) {
        Remove-Item -LiteralPath $SourcePath -Force
        $LogLines.Add("RMDIR_EMPTY|$SourcePath")
    } else {
        $LogLines.Add("KEEP_NON_EMPTY|$SourcePath")
    }
}

function Resolve-SourcePath {
    param(
        [pscustomobject]$Row
    )

    if ($Row.PSObject.Properties.Name -contains 'SourcePath' -and -not [string]::IsNullOrWhiteSpace($Row.SourcePath)) {
        return $Row.SourcePath
    }

    $parts = $Row.ProposedTargetPath -split '\\'
    $catIndex = -1
    for ($i = 0; $i -lt $parts.Length; $i++) {
        if ($parts[$i] -eq $Row.ProposedCategory) {
            $catIndex = $i
            break
        }
    }

    if ($catIndex -lt 1) {
        throw "Cannot resolve root path for row: $($Row.SourceName)"
    }

    $rootPath = ($parts[0..($catIndex - 1)] -join '\\')
    return Join-Path $rootPath $Row.SourceName
}

$rows = Import-Csv -LiteralPath $CsvPath -Delimiter ';'
$logLines = New-Object System.Collections.Generic.List[string]
$logLines.Add('RUN=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$logLines.Add('CSV=' + $CsvPath)
$logLines.Add('ROWS=' + $rows.Count)

foreach ($row in $rows) {
    $sourcePath = Resolve-SourcePath -Row $row
    Move-SourceIntoTarget -SourcePath $sourcePath -TargetPath $row.ProposedTargetPath -SourceName $row.SourceName -LogLines $logLines
}

$logLines.Add('DONE=' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
[System.IO.File]::WriteAllLines($LogPath, $logLines, [System.Text.UTF8Encoding]::new($false))
$logLines
