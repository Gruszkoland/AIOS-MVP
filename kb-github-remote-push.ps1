param(
    [Parameter(Mandatory = $true)]
    [string]$RemoteUrl
)

$ErrorActionPreference = "Stop"
$repoPath = "C:\Users\adiha\Desktop\Dokumentacja\ADRION-KNOWLEDGE-BANK"

if (-not (Test-Path (Join-Path $repoPath ".git"))) {
    throw "Brak repo git w: $repoPath"
}

$existingOrigin = git -C $repoPath remote | Where-Object { $_ -eq "origin" }
if ($existingOrigin) {
    git -C $repoPath remote set-url origin $RemoteUrl
    Write-Host "Zaktualizowano origin -> $RemoteUrl"
} else {
    git -C $repoPath remote add origin $RemoteUrl
    Write-Host "Dodano origin -> $RemoteUrl"
}

git -C $repoPath push -u origin master
Write-Host "Push zakonczony sukcesem."
