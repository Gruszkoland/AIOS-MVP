$ErrorActionPreference = "Stop"

$pluginDir = "C:\Users\adiha\Desktop\Dokumentacja\ADRION-KNOWLEDGE-BANK\.obsidian\plugins\dataview"
New-Item -ItemType Directory -Force -Path $pluginDir | Out-Null

$release = Invoke-RestMethod -Uri "https://api.github.com/repos/blacksmithgu/obsidian-dataview/releases/latest"
$requiredAssets = @("main.js", "manifest.json", "styles.css")
foreach ($name in $requiredAssets) {
    $asset = $release.assets | Where-Object { $_.name -eq $name } | Select-Object -First 1
    if (-not $asset) {
        throw "Nie znaleziono assetu: $name"
    }

    $outPath = Join-Path $pluginDir $name
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $outPath
}

Write-Host "Dataview zainstalowany w: $pluginDir"
Get-ChildItem $pluginDir | Select-Object Name
