param(
    [switch]$Silent,
    [ValidateSet("Both","AtoB","BtoA")]
    [string]$Direction = "Both"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PathA = "C:\Users\adiha\Desktop\Dokumentacja"
$PathB = "C:\Users\adiha\.1_Projekty\WSZYSTKIE DOKUMENTY ADRIANA"
$LogDir = "C:\Users\adiha\.1_Projekty\.sync-logs"
$LogFile = Join-Path $LogDir "sync-$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Msg, [string]$Color = "White")
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $Msg"
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
    if (-not $Silent) {
        Write-Host $line -ForegroundColor $Color
    }
}

function Invoke-RoboCopy {
    param([string]$Src, [string]$Dst, [string]$Label)
    Write-Log ">> $Label" "Cyan"
    Write-Log "   SRC: $Src" "DarkGray"
    Write-Log "   DST: $Dst" "DarkGray"
    $robArgs = @(
        $Src, $Dst,
        "/E", "/XO",
        "/DCOPY:DA", "/COPY:DAT",
        "/R:2", "/W:1", "/NP",
        "/LOG+:$LogFile"
    )
    & robocopy @robArgs | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        Write-Log "[WARN] Robocopy kod: $rc - sprawdz log!" "Yellow"
    } else {
        Write-Log "[OK] $Label - kod: $rc" "Green"
    }
}

if (-not (Test-Path $PathA)) { Write-Error "Brak folderu A: $PathA"; exit 1 }
if (-not (Test-Path $PathB)) { Write-Error "Brak folderu B: $PathB"; exit 1 }

Write-Log "=== SYNC START $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" "Magenta"

switch ($Direction) {
    "AtoB" { Invoke-RoboCopy $PathA $PathB "Desktop\Dokumentacja -> WSZYSTKIE DOKUMENTY ADRIANA" }
    "BtoA" { Invoke-RoboCopy $PathB $PathA "WSZYSTKIE DOKUMENTY ADRIANA -> Desktop\Dokumentacja" }
    "Both" {
        Invoke-RoboCopy $PathA $PathB "Desktop\Dokumentacja -> WSZYSTKIE DOKUMENTY ADRIANA"
        Invoke-RoboCopy $PathB $PathA "WSZYSTKIE DOKUMENTY ADRIANA -> Desktop\Dokumentacja"
    }
}

Write-Log "=== SYNC DONE - log: $LogFile ===" "Magenta"
if (-not $Silent) {
    Write-Host "[LOG] Zapisano: $LogFile" -ForegroundColor DarkCyan
}