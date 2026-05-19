$ErrorActionPreference = "Stop"

$repoPath = "C:\Users\adiha\Desktop\Dokumentacja\ADRION-KNOWLEDGE-BANK"
if (-not (Test-Path (Join-Path $repoPath ".git"))) {
    Write-Host "Brak repo git w: $repoPath"
    exit 0
}

# Stage first, then check if anything changed.
git -C $repoPath add -A | Out-Null
$changes = git -C $repoPath status --porcelain
if (-not $changes) {
    Write-Host "Brak zmian do commita."
    exit 0
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$msg = "auto: sync $stamp"
git -C $repoPath commit -m $msg | Out-Null

# Push only if origin exists; keep run resilient when remote is not yet configured.
$hasOrigin = git -C $repoPath remote | Where-Object { $_ -eq "origin" }
if ($hasOrigin) {
    git -C $repoPath push -u origin master | Out-Null
    Write-Host "Auto-commit + push OK: $msg"
} else {
    Write-Host "Auto-commit OK (bez push, brak origin): $msg"
}
