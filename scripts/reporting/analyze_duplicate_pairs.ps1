param(
    [Parameter(Mandatory = $true)]
    [string]$RootPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$files = Get-ChildItem -LiteralPath $RootPath -File -Recurse -Force -ErrorAction SilentlyContinue
$sizeGroups = $files | Group-Object Length | Where-Object { $_.Count -gt 1 }
$pairs = @{}

foreach ($group in $sizeGroups) {
    $hashed = $group.Group | ForEach-Object {
        try {
            [PSCustomObject]@{
                Hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                Path = $_.FullName
            }
        }
        catch {
        }
    }

    foreach ($dup in ($hashed | Group-Object Hash | Where-Object { $_.Count -gt 1 })) {
        $tops = $dup.Group | ForEach-Object {
            (($_.Path.Substring($RootPath.Length).TrimStart('\\')).Split('\\')[0])
        } | Sort-Object -Unique

        if ($tops.Count -gt 1) {
            for ($i = 0; $i -lt $tops.Count; $i++) {
                for ($j = $i + 1; $j -lt $tops.Count; $j++) {
                    $key = $tops[$i] + ' <-> ' + $tops[$j]
                    if (-not $pairs.ContainsKey($key)) {
                        $pairs[$key] = 0
                    }
                    $pairs[$key]++
                }
            }
        }
    }
}

$lines = $pairs.GetEnumerator() | Sort-Object -Property Value -Descending | ForEach-Object {
    $_.Name + '|groups=' + $_.Value
}

[System.IO.File]::WriteAllLines($OutputPath, $lines, [System.Text.UTF8Encoding]::new($false))
$lines
