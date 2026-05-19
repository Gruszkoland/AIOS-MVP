# Skrypt czyszczenia zbędnych elementów
# Uruchom jako Administrator!

param(
    [ValidateSet("phase1", "phase2", "phase3", "phase4", "all")]
    [string]$Phase = "phase1"
)

# Kolory output
$colors = @{
    success = "Green"
    warning = "Yellow"
    error = "Red"
    info = "Cyan"
}

function Write-Status($msg, $type = "info") {
    Write-Host "[$((Get-Date).ToString('HH:mm:ss'))] $msg" -ForegroundColor $colors[$type]
}

# Sprawdzenie admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Status "Uruchom jako Administrator!" "error"
    exit 1
}

Write-Status "=== CZYSZCZENIE ZBEDNYCH ELEMENTÓW ===" "info"
Write-Status "Phase: $Phase" "info"

# ==========================
# FAZA 1 - Temp Files
# ==========================
function Clean-Phase1 {
    Write-Status "Faza 1: Czyszczenie plików tymczasowych" "info"
    
    $paths = @(
        "C:\Users\adiha\AppData\Local\Temp\*",
        "C:\Windows\Temp\*",
        "C:\Windows\Prefetch\*"
    )
    
    foreach ($path in $paths) {
        Write-Status "Czyszczę: $path" "info"
        try {
            Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "✓ Usunięto: $path" "success"
        } catch {
            Write-Status "⚠ Błąd przy: $path" "warning"
        }
    }
    
    # Clear Recycle Bin
    Write-Status "Czyszczę Recycle Bin..." "info"
    Clear-RecycleBin -Force -Confirm:$false -ErrorAction SilentlyContinue
    Write-Status "✓ Recycle Bin wyczyszczony" "success"
}

# ==========================
# FAZA 2 - Dev Tools Cache
# ==========================
function Clean-Phase2 {
    Write-Status "Faza 2: Czyszczenie cache narzędzi dev" "info"
    
    # VS Code Cache
    Write-Status "Czyszczę VS Code cache..." "info"
    $vscodeCache = @(
        "C:\Users\adiha\AppData\Roaming\Code\Cache",
        "C:\Users\adiha\AppData\Roaming\Code\CachedExtensionVSIXs",
        "C:\Users\adiha\AppData\Roaming\Code\Crashpad",
        "C:\Users\adiha\AppData\Roaming\Code\DawnGraphiteCache",
        "C:\Users\adiha\AppData\Roaming\Code\DawnWebGPUCache"
    )
    
    foreach ($path in $vscodeCache) {
        if (Test-Path $path) {
            Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "✓ Wyczyszczony: $path" "success"
        }
    }
    
    # npm cache
    Write-Status "Czyszczę npm cache..." "info"
    try {
        npm cache clean --force --silent
        Write-Status "✓ npm cache wyczyszczony" "success"
    } catch {
        Write-Status "⚠ npm niedostępny" "warning"
    }
    
    # pip cache
    Write-Status "Czyszczę pip cache..." "info"
    try {
        pip cache purge
        Write-Status "✓ pip cache wyczyszczony" "success"
    } catch {
        Write-Status "⚠ pip niedostępny" "warning"
    }
    
    # Docker system prune
    Write-Status "Docker system prune..." "warning"
    Write-Status "Upewnij się, że Docker Desktop jest zamknięty!" "warning"
    Write-Host "Czy kontynuować? (T/N): " -NoNewline
    $response = Read-Host
    if ($response -eq "T") {
        try {
            docker system prune -a -f
            docker volume prune -f
            Write-Status "✓ Docker oczyszczony" "success"
        } catch {
            Write-Status "⚠ Docker niedostępny lub zamknięty" "warning"
        }
    }
}

# ==========================
# FAZA 3 - AI Models (DANGEROUS)
# ==========================
function Clean-Phase3 {
    Write-Status "Faza 3: Usuwanie modeli AI" "warning"
    Write-Status "⚠️ UWAGA: To usunie pobrane modele LLM!" "warning"
    Write-Host "Modele można pobrać ponownie, ale zajmie to czas i transfer." 
    Write-Host "Czy rzeczywiście chcesz kontynuować? (T/N): " -NoNewline
    $response = Read-Host
    
    if ($response -eq "T") {
        # Ollama
        if (Test-Path "C:\Users\adiha\.ollama") {
            Write-Status "Usuwam .ollama..." "warning"
            Remove-Item "C:\Users\adiha\.ollama" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "✓ .ollama usunięty" "success"
        }
        
        # LMStudio
        if (Test-Path "C:\Users\adiha\.lmstudio") {
            Write-Status "Usuwam .lmstudio..." "warning"
            Remove-Item "C:\Users\adiha\.lmstudio" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "✓ .lmstudio usunięty" "success"
        }
    } else {
        Write-Status "Pominięto fazę 3" "info"
    }
}

# ==========================
# FAZA 4 - Deep Cleaning
# ==========================
function Clean-Phase4 {
    Write-Status "Faza 4: Głębokie czyszczenie" "info"
    
    $paths = @(
        @{path = "C:\Users\adiha\ntuser.dat.LOG*"; desc = "Registry logs"},
        @{path = "C:\Users\adiha\Cookies"; desc = "Browser cookies"},
        @{path = "C:\Users\adiha\Recent"; desc = "Recent files"},
        @{path = "C:\Users\adiha\.cache"; desc = "General cache"}
    )
    
    foreach ($item in $paths) {
        if (Test-Path $item.path) {
            Write-Status "Usuwam: $($item.desc)" "info"
            Remove-Item $item.path -Recurse -Force -ErrorAction SilentlyContinue
            Write-Status "✓ Usunięty: $($item.desc)" "success"
        }
    }
}

# ==========================
# ANALIZA ROZMIARÓW
# ==========================
function Show-Sizes {
    Write-Status "Analiza rozmiaru po czyszczeniu:" "info"
    Write-Host ""
    
    $checkPaths = @(
        "C:\Users\adiha\AppData\Local\Temp",
        "C:\Users\adiha\AppData\Roaming\Code\Cache",
        "C:\Users\adiha\.ollama",
        "C:\Users\adiha\.lmstudio"
    )
    
    foreach ($path in $checkPaths) {
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB
            Write-Host "  $path : $([math]::Round($size, 2)) GB" -ForegroundColor Cyan
        } else {
            Write-Host "  $path : 0 GB (wyczyszczony)" -ForegroundColor Green
        }
    }
}

# ==========================
# MAIN EXECUTION
# ==========================

switch ($Phase) {
    "phase1" { Clean-Phase1 }
    "phase2" { 
        Clean-Phase1
        Clean-Phase2 
    }
    "phase3" { 
        Clean-Phase1
        Clean-Phase2
        Clean-Phase3 
    }
    "phase4" { 
        Clean-Phase1
        Clean-Phase2
        Clean-Phase3
        Clean-Phase4 
    }
    "all" { 
        Clean-Phase1
        Clean-Phase2
        Clean-Phase3
        Clean-Phase4 
    }
}

Write-Host ""
Show-Sizes

Write-Status "=== CZYSZCZENIE UKOŃCZONE ===" "success"
Write-Status "Pamiętaj: Restart może być wymagany dla pełnych zmian" "info"
