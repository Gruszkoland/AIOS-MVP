# generate-obsidian-indexes.ps1
# Builds INDEX.md and per-project folder maps for merged docs in Obsidian.

$docRoot = "C:\Users\adiha\Desktop\Dokumentacja"
$vaultDir = Get-ChildItem -Path $docRoot -Directory -Filter "Obsydian-synchronizacja*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $vaultDir) {
    throw "Vault directory not found under: $docRoot"
}

$mergedRoot = Join-Path $vaultDir.FullName "_PROJEKTY_SCALONE"
if (-not (Test-Path $mergedRoot)) {
    throw "Merged docs directory not found: $mergedRoot"
}

$mapsRoot = Join-Path $mergedRoot "_MAPY"
New-Item -ItemType Directory -Path $mapsRoot -Force | Out-Null

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Utf8NoBomFile {
    param(
        [string]$Path,
        [string]$Content
    )

    $parent = Split-Path -Path $Path -Parent
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Get-LinkFromMergedRoot {
    param([string]$ToPath)

    $relative = $ToPath.Substring($mergedRoot.Length).TrimStart('\\')
    return $relative.Replace('\', '/')
}

function Get-LinkFromMapsRoot {
    param([string]$ToPath)

    $relative = $ToPath.Substring($mergedRoot.Length).TrimStart('\\')
    return ('../' + $relative.Replace('\', '/'))
}

function Convert-ToSafeFileName {
    param([string]$Name)

    $safe = $Name
    foreach ($char in [System.IO.Path]::GetInvalidFileNameChars()) {
        $safe = $safe.Replace($char, '-')
    }
    return $safe
}

function Get-ProjectDocSample {
    param([string]$ProjectPath)

    $patterns = @('*.md', '*.mdx', '*.txt', '*.pdf', '*.docx', '*.gdoc')
    return Get-ChildItem -Path $ProjectPath -Recurse -File -Include $patterns -ErrorAction SilentlyContinue |
        Sort-Object FullName |
        Select-Object -First 25
}

$projectDirs = Get-ChildItem -Path $mergedRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne '_MAPY' } |
    Sort-Object Name

$projectSummaries = @()

foreach ($project in $projectDirs) {
    $projectFiles = Get-ChildItem -Path $project.FullName -Recurse -File -ErrorAction SilentlyContinue
    $fileCount = @($projectFiles).Count
    $markdownCount = @($projectFiles | Where-Object { $_.Extension -in '.md', '.mdx' }).Count
    $subdirs = Get-ChildItem -Path $project.FullName -Directory -ErrorAction SilentlyContinue | Sort-Object Name
    $sampleDocs = Get-ProjectDocSample -ProjectPath $project.FullName

    $mapName = Convert-ToSafeFileName -Name ($project.Name + ' - MAPA.md')
    $mapPath = Join-Path $mapsRoot $mapName

    $mapLines = @()
    $mapLines += '# ' + $project.Name + ' - MAPA'
    $mapLines += ''
    $mapLines += '- Project: ' + $project.Name
    $mapLines += '- Files: ' + $fileCount
    $mapLines += '- Markdown: ' + $markdownCount
    $mapLines += '- Generated: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    $mapLines += ''
    $mapLines += '## Top-Level Folders'
    $mapLines += ''

    if (@($subdirs).Count -eq 0) {
        $mapLines += '- No subfolders'
    } else {
        foreach ($dir in $subdirs) {
            $relative = Get-LinkFromMapsRoot -ToPath $dir.FullName
            $childFiles = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
            $mapLines += '- [' + $dir.Name + '](' + $relative + ') - files: ' + $childFiles
        }
    }

    $mapLines += ''
    $mapLines += '## Quick Document Sample'
    $mapLines += ''

    if (@($sampleDocs).Count -eq 0) {
        $mapLines += '- No matching docs found'
    } else {
        foreach ($doc in $sampleDocs) {
            $relative = Get-LinkFromMapsRoot -ToPath $doc.FullName
            $mapLines += '- [' + $doc.Name + '](' + $relative + ')'
        }
    }

    $mapLines += ''
    $mapLines += '## Root'
    $mapLines += ''
    $projectRelative = Get-LinkFromMapsRoot -ToPath $project.FullName
    $mapLines += '- [' + $project.Name + ' root](' + $projectRelative + ')'

    Write-Utf8NoBomFile -Path $mapPath -Content ($mapLines -join [Environment]::NewLine)

    $projectSummaries += [PSCustomObject]@{
        Name = $project.Name
        Files = $fileCount
        Markdown = $markdownCount
        MapPath = $mapPath
        ProjectPath = $project.FullName
    }
}

$indexPath = Join-Path $mergedRoot 'INDEX.md'
$indexLines = @()
$indexLines += '# INDEX - PROJEKTY SCALONE'
$indexLines += ''
$indexLines += '- Vault: ' + $vaultDir.Name
$indexLines += '- Scope: _PROJEKTY_SCALONE'
$indexLines += '- Projects: ' + @($projectSummaries).Count
$indexLines += '- Generated: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
$indexLines += ''
$indexLines += '## Navigation'
$indexLines += ''
$indexLines += '- [_MAPY](_MAPY)'
$indexLines += ''
$indexLines += '## Projects'
$indexLines += ''
$indexLines += '| Project | Files | Markdown | Map | Root |'
$indexLines += '|---|---:|---:|---|---|'

foreach ($item in ($projectSummaries | Sort-Object Files -Descending)) {
    $mapRelative = Get-LinkFromMergedRoot -ToPath $item.MapPath
    $projectRelative = Get-LinkFromMergedRoot -ToPath $item.ProjectPath
    $indexLines += '| ' + $item.Name + ' | ' + $item.Files + ' | ' + $item.Markdown + ' | [MAP](' + $mapRelative + ') | [OPEN](' + $projectRelative + ') |'
}

$indexLines += ''
$indexLines += '## Largest Projects'
$indexLines += ''
foreach ($item in ($projectSummaries | Sort-Object Files -Descending | Select-Object -First 5)) {
    $mapRelative = Get-LinkFromMergedRoot -ToPath $item.MapPath
    $indexLines += '- [' + $item.Name + '](' + $mapRelative + ') - files: ' + $item.Files + ', markdown: ' + $item.Markdown
}

Write-Utf8NoBomFile -Path $indexPath -Content ($indexLines -join [Environment]::NewLine)

Write-Host 'INDEX_PATH=' + $indexPath
Write-Host 'MAPS_ROOT=' + $mapsRoot
Write-Host 'PROJECTS=' + @($projectSummaries).Count