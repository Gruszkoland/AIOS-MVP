param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$dirs = Get-ChildItem -LiteralPath $RootPath -Directory -Recurse -Force -ErrorAction SilentlyContinue
$files = Get-ChildItem -LiteralPath $RootPath -File -Recurse -Force -ErrorAction SilentlyContinue
$topDirs = Get-ChildItem -LiteralPath $RootPath -Directory -Force -ErrorAction SilentlyContinue

$dupDirNames = $dirs | Group-Object Name | Where-Object { $_.Count -gt 1 } | Sort-Object Count -Descending, Name
$dupFileNames = $files | Group-Object Name | Where-Object { $_.Count -gt 1 } | Sort-Object Count -Descending, Name
$sizeGroups = $files | Group-Object Length | Where-Object { $_.Count -gt 1 }
$dupFiles = New-Object System.Collections.Generic.List[object]

foreach ($group in $sizeGroups) {
    $hashed = $group.Group | ForEach-Object {
        try {
            [PSCustomObject]@{
                Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                Path = $_.FullName
                Length = $_.Length
                Name = $_.Name
            }
        }
        catch {
        }
    }

    foreach ($hashGroup in ($hashed | Group-Object Hash | Where-Object { $_.Count -gt 1 })) {
        $dupFiles.Add([PSCustomObject]@{
            Hash = $hashGroup.Name
            Count = $hashGroup.Count
            Size = ($hashGroup.Group | Select-Object -First 1).Length
            Paths = ($hashGroup.Group | Sort-Object Path | Select-Object -ExpandProperty Path)
        })
    }
}

$signatures = foreach ($dir in $topDirs) {
    $entries = Get-ChildItem -LiteralPath $dir.FullName -File -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $_.FullName.Substring($dir.FullName.Length).TrimStart('\\') + '|' + $_.Length
    }
    $joined = ($entries | Sort-Object) -join "`n"
    $signature = if ([string]::IsNullOrEmpty($joined)) {
        'EMPTY'
    }
    else {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($joined)
        $stream = [System.IO.MemoryStream]::new($bytes)
        try {
            (Get-FileHash -InputStream $stream -Algorithm SHA256).Hash
        }
        finally {
            $stream.Dispose()
        }
    }

    [PSCustomObject]@{
        Name = $dir.Name
        Path = $dir.FullName
        FileCount = ($entries | Measure-Object).Count
        Signature = $signature
    }
}

$dupFolderSigs = $signatures | Group-Object Signature | Where-Object { $_.Count -gt 1 -and $_.Name -ne 'EMPTY' } | Sort-Object Count -Descending, Name

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ROOT=' + $RootPath)
$lines.Add('DIR_COUNT=' + $dirs.Count)
$lines.Add('FILE_COUNT=' + $files.Count)
$lines.Add('TOP_LEVEL_DIR_COUNT=' + $topDirs.Count)
$lines.Add('DUP_DIR_NAME_GROUPS=' + $dupDirNames.Count)
$lines.Add('DUP_FILE_NAME_GROUPS=' + $dupFileNames.Count)
$lines.Add('DUP_FILE_NAME_INSTANCES=' + (($dupFileNames | Measure-Object Count -Sum).Sum))
$lines.Add('DUP_FILE_GROUPS=' + $dupFiles.Count)
$lines.Add('DUP_FILE_INSTANCES=' + (($dupFiles | Measure-Object Count -Sum).Sum))
$lines.Add('DUP_FOLDER_SIGNATURE_GROUPS=' + $dupFolderSigs.Count)
$lines.Add('')
$lines.Add('TOP_LEVEL_DIRS')
foreach ($dir in $topDirs) {
    $lines.Add('  ' + $dir.Name)
}
$lines.Add('')
$lines.Add('TOP_DUPLICATE_DIRECTORY_NAMES')
foreach ($item in ($dupDirNames | Select-Object -First 30)) {
    $lines.Add('[' + $item.Count + 'x] ' + $item.Name)
    foreach ($path in ($item.Group | Select-Object -First 8 -ExpandProperty FullName)) {
        $lines.Add('  ' + $path)
    }
}
$lines.Add('')
$lines.Add('TOP_DUPLICATE_FILE_NAMES')
foreach ($item in ($dupFileNames | Select-Object -First 40)) {
    $lines.Add('[' + $item.Count + 'x] ' + $item.Name)
    foreach ($path in ($item.Group | Select-Object -First 8 -ExpandProperty FullName)) {
        $lines.Add('  ' + $path)
    }
}
$lines.Add('')
$lines.Add('TOP_DUPLICATE_FILE_GROUPS')
foreach ($item in ($dupFiles | Sort-Object Count, Size -Descending | Select-Object -First 40)) {
    $lines.Add('[' + $item.Count + 'x | ' + $item.Size + ' bytes] ' + $item.Hash)
    foreach ($path in ($item.Paths | Select-Object -First 8)) {
        $lines.Add('  ' + $path)
    }
}
$lines.Add('')
$lines.Add('DUPLICATE_FOLDER_SIGNATURES')
foreach ($group in $dupFolderSigs) {
    $lines.Add('[' + $group.Count + 'x] ' + $group.Name)
    foreach ($item in $group.Group) {
        $lines.Add('  ' + $item.Path + ' | files=' + $item.FileCount)
    }
}

[System.IO.File]::WriteAllLines($OutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
$lines
