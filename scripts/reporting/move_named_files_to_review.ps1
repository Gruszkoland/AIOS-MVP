param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    [Parameter(Mandatory = $true)]
    [string]$FileName,

    [Parameter(Mandatory = $true)]
    [string]$ReviewFolderName,

    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$files = Get-ChildItem -LiteralPath $RootPath -Filter $FileName -File -Recurse -Force -ErrorAction SilentlyContinue
$reviewRoot = Join-Path $RootPath $ReviewFolderName
$moved = New-Object System.Collections.Generic.List[string]

foreach ($file in $files) {
    $relativeDir = $file.DirectoryName.Substring($RootPath.Length).TrimStart('\\')
    $targetDir = if ([string]::IsNullOrWhiteSpace($relativeDir)) { $reviewRoot } else { Join-Path $reviewRoot $relativeDir }
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    $targetPath = Join-Path $targetDir $file.Name
    Move-Item -LiteralPath $file.FullName -Destination $targetPath -Force
    $moved.Add($targetPath)
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('ROOT=' + $RootPath)
$lines.Add('FILE=' + $FileName)
$lines.Add('REVIEW=' + $reviewRoot)
$lines.Add('MOVED=' + $moved.Count)
$lines.Add('REMAINING=' + ((Get-ChildItem -LiteralPath $RootPath -Filter $FileName -File -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object).Count))
$lines.Add('')
$lines.Add('MOVED_PATHS')
foreach ($path in $moved) {
    $lines.Add('  ' + $path)
}

if ($OutputPath) {
    [System.IO.File]::WriteAllLines($OutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
}

$lines
