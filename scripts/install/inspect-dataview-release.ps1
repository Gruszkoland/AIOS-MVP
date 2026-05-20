$ErrorActionPreference = "Stop"
$r = Invoke-RestMethod -Uri "https://api.github.com/repos/blacksmithgu/obsidian-dataview/releases/latest"
Write-Host "Tag:" $r.tag_name
Write-Host "Assets:"
$r.assets | Select-Object -ExpandProperty name
