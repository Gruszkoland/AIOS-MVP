# sync-obsydian-local.ps1
# One-way sync: Desktop\Dokumentacja -> Obsydian-synchronizacja dokumentow (vault)

$Source = "C:\Users\adiha\Desktop\Dokumentacja"
$Vault = "C:\Users\adiha\Desktop\Dokumentacja\Obsydian-synchronizacja dokumentów"
$Log = "C:\Users\adiha\sync-obsydian-local.log"

$ExcludeFullDirs = @(
    "C:\Users\adiha\Desktop\Dokumentacja\Obsydian-synchronizacja dokumentów",
    "C:\Users\adiha\Desktop\Dokumentacja\.1_Projekty"
)

$ExcludeDirNames = @(
    "node_modules", ".git", ".venv", "__pycache__", ".vscode",
    "dist", "build", ".next", ".nuxt", "vendor", "target", "bin", "obj"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "[$timestamp] === OBSYDIAN SYNC START ==="

Write-Host "[$timestamp] Obsidian local sync START"

$xdArgs = @()
$xdArgs += $ExcludeFullDirs
$xdArgs += $ExcludeDirNames

robocopy $Source $Vault /E /XO /FFT /R:1 /W:1 /NP /XD $xdArgs /LOG+:$Log
$exitCode = $LASTEXITCODE

$timestampEnd = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "[$timestampEnd] === OBSYDIAN SYNC END (code: $exitCode) ==="

if ($exitCode -le 7) {
    Write-Host "OBSYDIAN SYNC OK (code: $exitCode)"
} else {
    Write-Host "OBSYDIAN SYNC FAIL (code: $exitCode) - sprawdz log: $Log"
    exit $exitCode
}
