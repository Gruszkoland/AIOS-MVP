# dedupe-obsydian-content.ps1
# Deduplicate merged project docs by file content hash.
# Keeps first file and deletes duplicate copies.

$docRoot = "C:\Users\adiha\Desktop\Dokumentacja"
$vaultDir = Get-ChildItem -Path $docRoot -Directory -Filter "Obsydian-synchronizacja*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $vaultDir) {
    throw "Brak katalogu vaultu rozpoczynajacego sie od: Obsydian-synchronizacja"
}

$Root = Join-Path $vaultDir.FullName "_PROJEKTY_SCALONE"
$Log = "C:\Users\adiha\dedupe-obsydian-content.log"

if (-not (Test-Path $Root)) {
    throw "Brak katalogu do deduplikacji: $Root"
}

$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "[$ts] === DEDUPE START ==="

$files = Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue | Sort-Object FullName
$seen = @{}
$processed = 0
$deleted = 0
$errors = 0

foreach ($file in $files) {
    $processed++

    try {
        $hash = (Get-FileHash -Path $file.FullName -Algorithm SHA256 -ErrorAction Stop).Hash

        if ($seen.ContainsKey($hash)) {
            $relative = $file.FullName.Substring($Root.Length).TrimStart('\\')
            Remove-Item -LiteralPath $file.FullName -Force
            $deleted++
            Add-Content -Path $Log -Value "DELETED_DUPLICATE|$relative|hash=$hash|kept=$($seen[$hash])"
        }
        else {
            $seen[$hash] = $file.FullName
        }
    }
    catch {
        $errors++
        Add-Content -Path $Log -Value "ERROR|$($file.FullName)|$($_.Exception.Message)"
    }
}

$tsEnd = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $Log -Value "[$tsEnd] === DEDUPE END | processed=$processed | deleted=$deleted | errors=$errors | unique=$($seen.Count) ==="

Write-Host "DEDUPE_DONE processed=$processed deleted=$deleted errors=$errors unique=$($seen.Count)"
Write-Host "ROOT=$Root"
Write-Host "LOG=$Log"
