<#
.SYNOPSIS
    ADRION 369 — One-Click Windows Installer
.DESCRIPTION
    Sprawdza i instaluje wszystkie wymagania, konfiguruje środowisko,
    inicjalizuje bazę danych, uruchamia cały stack i weryfikuje stan zdrowia.
    Obsługuje Windows 10/11 (PowerShell 5.1+).
.EXAMPLE
    .\scripts\install\setup-ADRION.ps1
    .\scripts\install\setup-ADRION.ps1 -SkipDocker -OfflineMode
#>
[CmdletBinding()]
param(
    [switch]$SkipDocker,
    [switch]$SkipOllama,
    [switch]$OfflineMode,
    [switch]$ForceReinstall,
    [string]$PythonVersion = "3.11",
    [string]$GoVersion     = "1.22"
)

$ErrorActionPreference = 'Stop'
$ProgressPreference    = 'SilentlyContinue'

# ── Paths ─────────────────────────────────────────────────────────────────────
$ROOT        = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$VENV        = Join-Path $ROOT ".venv"
$VENV_PY     = Join-Path $VENV "Scripts\python.exe"
$VENV_PIP    = Join-Path $VENV "Scripts\pip.exe"
$ENV_FILE    = Join-Path $ROOT ".env"
$ENV_EXAMPLE = Join-Path $ROOT ".env.example"
$LOG_DIR     = Join-Path $ROOT "logs\install"
$LOG_FILE    = Join-Path $LOG_DIR "setup-$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# ── Colors / helpers ──────────────────────────────────────────────────────────
function Write-Step  { param($n,$t,$m) Write-Host "[$n/$t] $m" -ForegroundColor Cyan   }
function Write-OK    { param($m) Write-Host "  [OK]  $m" -ForegroundColor Green  }
function Write-WARN  { param($m) Write-Host "  [!!]  $m" -ForegroundColor Yellow }
function Write-FAIL  { param($m) Write-Host "  [XX]  $m" -ForegroundColor Red    }
function Write-INFO  { param($m) Write-Host "        $m" -ForegroundColor Gray   }

function Tee-Log {
    param([string]$Msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $LOG_FILE -Value "[$ts] $Msg" -Encoding UTF8
}

function Step-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("─" * 60) -ForegroundColor DarkCyan
    Write-Host "  $Title" -ForegroundColor White
    Write-Host ("─" * 60) -ForegroundColor DarkCyan
    Tee-Log "=== $Title ==="
}

# ── Init log ──────────────────────────────────────────────────────────────────
New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
Tee-Log "ADRION 369 setup started"
Tee-Log "ROOT=$ROOT  OfflineMode=$OfflineMode  SkipDocker=$SkipDocker"

# ── Banner ────────────────────────────────────────────────────────────────────
Clear-Host
Write-Host @"

  █████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗    ██████╗  ██████╗  █████╗
 ██╔══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║    ╚════██╗██╔════╝ ██╔══██╗
 ███████║██║  ██║██████╔╝██║██║   ██║██╔██╗ ██║     █████╔╝███████╗ ╚ ════╔╝
 ██╔══██║██║  ██║██╔══██╗██║██║   ██║██║╚██╗██║    ██╔═══╝ ██╔══██╗ ██╔══██╗
 ██║  ██║██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║    ███████╗╚██████╔╝╚█████╔╝
 ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝    ╚══════╝ ╚═════╝  ╚════╝

         One-Click Installer — Windows 10/11
"@ -ForegroundColor Cyan
Write-Host "  Projekt:   162 Demencje w Schemacie 369" -ForegroundColor White
Write-Host "  Katalog:   $ROOT" -ForegroundColor DarkGray
Write-Host "  Log:       $LOG_FILE" -ForegroundColor DarkGray
Write-Host ""

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1/8 — SYSTEM REQUIREMENTS CHECK
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 1/8 — Weryfikacja środowiska"
$TOTAL_STEPS = 8
$issues = @()

# Windows version
$winVer = [System.Environment]::OSVersion.Version
if ($winVer.Major -lt 10) {
    Write-FAIL "Windows $($winVer.Major) nie jest wspierany. Wymagany Windows 10+."
    exit 1
}
Write-OK "Windows $($winVer.Major).$($winVer.Minor) (build $($winVer.Build))"
Tee-Log "Windows version: $winVer"

# PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-FAIL "PowerShell $($PSVersionTable.PSVersion) — wymagany 5.1+"
    exit 1
}
Write-OK "PowerShell $($PSVersionTable.PSVersion)"

# Admin check (optional but recommended)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-WARN "Brak uprawnień administratora — niektóre instalacje mogą wymagać UAC"
} else {
    Write-OK "Uprawnienia administratora"
}

# Disk space (min 5 GB free)
$drive = Split-Path -Qualifier $ROOT
$freeGB = (Get-PSDrive ($drive.TrimEnd(':'))).Free / 1GB
if ($freeGB -lt 5) {
    Write-WARN "Wolne miejsce: $([math]::Round($freeGB,1)) GB — zalecane 5 GB+"
    $issues += "Low disk space"
} else {
    Write-OK "Wolne miejsce: $([math]::Round($freeGB,1)) GB"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2/8 — PREREQUISITES
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 2/8 — Wymagane oprogramowanie"

function Test-Command { param($cmd) return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null }
function Install-WithWinget {
    param([string]$Id, [string]$Name)
    if (Test-Command "winget") {
        Write-INFO "Instaluję $Name przez winget..."
        Tee-Log "winget install $Id"
        winget install --id $Id --silent --accept-package-agreements --accept-source-agreements 2>&1 | Tee-Log
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("Path","User")
    } else {
        Write-WARN "winget niedostępny — zainstaluj $Name ręcznie"
        $issues += "Missing $Name"
    }
}

# Git
if (Test-Command "git") {
    $gitV = git --version 2>&1
    Write-OK "Git: $gitV"
} else {
    Write-WARN "Git nie znaleziony"
    if (-not $OfflineMode) { Install-WithWinget "Git.Git" "Git" }
    else { $issues += "Git missing" }
}

# Python 3.11+
$pyOk = $false
foreach ($pyCmd in @("python", "python3", "py")) {
    if (Test-Command $pyCmd) {
        try {
            $v = & $pyCmd --version 2>&1
            if ($v -match "Python (\d+)\.(\d+)") {
                $maj = [int]$matches[1]; $min = [int]$matches[2]
                if ($maj -ge 3 -and $min -ge 11) {
                    Write-OK "Python $v"
                    $PYTHON_CMD = $pyCmd
                    $pyOk = $true
                    break
                }
            }
        } catch {}
    }
}
if (-not $pyOk) {
    Write-WARN "Python $PythonVersion+ nie znaleziony"
    if (-not $OfflineMode) { Install-WithWinget "Python.Python.3.11" "Python 3.11" }
    else { $issues += "Python missing" }
}

# Go 1.22+
$goOk = $false
if (Test-Command "go") {
    $goV = go version 2>&1
    if ($goV -match "go(\d+)\.(\d+)") {
        $maj = [int]$matches[1]; $min = [int]$matches[2]
        if ($maj -ge 1 -and $min -ge 22) { $goOk = $true; Write-OK "Go: $goV" }
        else { Write-WARN "Go $goV — wymagany 1.22+" }
    }
}
if (-not $goOk) {
    if (-not $OfflineMode) { Install-WithWinget "GoLang.Go" "Go 1.22" }
    else { Write-WARN "Go 1.22+ nie zainstalowany (opcjonalny dla Vortex Engine)" }
}

# Docker Desktop
if (-not $SkipDocker) {
    $dockerOk = $false
    try {
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $dockerOk = $true; Write-OK "Docker Desktop: uruchomiony" }
    } catch {}
    if (-not $dockerOk) {
        Write-INFO "Uruchamiam Docker Desktop..."
        $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        if (Test-Path $dockerPath) {
            Start-Process $dockerPath
            $waited = 0
            while ($waited -lt 90) {
                Start-Sleep 5; $waited += 5
                try {
                    docker info 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        Write-OK "Docker Desktop gotowy (${waited}s)"
                        $dockerOk = $true; break
                    }
                } catch {}
            }
            if (-not $dockerOk) {
                Write-WARN "Docker Desktop nie odpowiedział w 90s — kontynuuję bez Docker"
                $issues += "Docker not responding"
            }
        } else {
            Write-WARN "Docker Desktop nie znaleziony. Pobierz z: https://www.docker.com/products/docker-desktop"
            if (-not $OfflineMode) { Install-WithWinget "Docker.DockerDesktop" "Docker Desktop" }
            $issues += "Docker missing"
        }
    }
}

# Ollama (optional for offline LLM)
if (-not $SkipOllama) {
    if (Test-Command "ollama") {
        $ollamaV = ollama version 2>&1
        Write-OK "Ollama: $ollamaV"
    } else {
        Write-WARN "Ollama nie znaleziony (offline LLM bedzie niedostepny)"
        Write-INFO "Pobierz z: https://ollama.com/download"
        if (-not $OfflineMode) { Install-WithWinget "Ollama.Ollama" "Ollama" }
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3/8 — PYTHON VIRTUAL ENVIRONMENT
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 3/8 — Python venv"

if ((Test-Path $VENV_PY) -and -not $ForceReinstall) {
    Write-OK "Virtualenv już istnieje: $VENV"
} else {
    Write-INFO "Tworzę virtualenv w $VENV ..."
    & $PYTHON_CMD -m venv $VENV 2>&1 | Tee-Log
    Write-OK "Virtualenv utworzony"
}

# Upgrade pip silently
Write-INFO "Aktualizuję pip..."
& $VENV_PY -m pip install --upgrade pip --quiet 2>&1 | Tee-Log

# Install requirements
$reqFile = Join-Path $ROOT "requirements-arbitrage.txt"
if (Test-Path $reqFile) {
    Write-INFO "Instaluję zależności Python..."
    & $VENV_PIP install -r $reqFile --quiet 2>&1 | Tee-Log
    Write-OK "Zależności Python zainstalowane"
} else {
    Write-WARN "Nie znaleziono requirements-arbitrage.txt"
    $issues += "requirements-arbitrage.txt missing"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4/8 — ENVIRONMENT CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 4/8 — Konfiguracja środowiska"

if (-not (Test-Path $ENV_FILE)) {
    if ($OfflineMode) {
        $offlineEnv = Join-Path $ROOT ".env.offline"
        if (Test-Path $offlineEnv) {
            Copy-Item $offlineEnv $ENV_FILE
            Write-OK ".env skopiowany z .env.offline (tryb offline)"
        } elseif (Test-Path $ENV_EXAMPLE) {
            Copy-Item $ENV_EXAMPLE $ENV_FILE
            Write-OK ".env skopiowany z .env.example"
        } else {
            Write-WARN ".env nie istnieje — uruchom scripts\install\setup-environment.ps1"
            $issues += ".env missing"
        }
    } else {
        # Run environment setup script
        $envSetup = Join-Path $PSScriptRoot "setup-environment.ps1"
        if (Test-Path $envSetup) {
            & $envSetup -Root $ROOT
        } elseif (Test-Path $ENV_EXAMPLE) {
            Copy-Item $ENV_EXAMPLE $ENV_FILE
            Write-OK ".env skopiowany z .env.example"
            Write-WARN "Edytuj $ENV_FILE i ustaw swoje klucze API"
        }
    }
} else {
    Write-OK ".env istnieje"
}

# Validate .env
$validateDb = Join-Path $PSScriptRoot "validate-database.ps1"
if (Test-Path $validateDb) {
    Write-INFO "Walidacja konfiguracji bazy danych..."
    & $validateDb -Root $ROOT -EnvFile $ENV_FILE -Quiet
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5/8 — DATABASE INITIALIZATION
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 5/8 — Inicjalizacja bazy danych"

Write-INFO "Inicjalizuję SQLite..."
try {
    & $VENV_PY -c "
import sys, os
sys.path.insert(0, r'$ROOT')
os.chdir(r'$ROOT')
from arbitrage.database import init_db
init_db()
print('SQLite database initialized')
" 2>&1 | Tee-Log
    Write-OK "Baza SQLite gotowa: $(Join-Path $ROOT 'arbitrage.db')"
} catch {
    Write-FAIL "Błąd inicjalizacji SQLite: $_"
    $issues += "SQLite init failed"
}

Write-INFO "Stosowanie migracji..."
try {
    $migrateScript = Join-Path $ROOT "scripts\migrate.py"
    & $VENV_PY $migrateScript up --target 999 2>&1 | Tee-Log
    Write-OK "Migracje zastosowane"
} catch {
    Write-WARN "Błąd migracji: $_"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6/8 — DOCKER STACK
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 6/8 — Docker Stack (adrion-swarm)"

if ($SkipDocker) {
    Write-WARN "Docker pominięty (parametr -SkipDocker)"
} else {
    $composeFile = Join-Path $ROOT "adrion-swarm\docker-compose.yml"
    if (Test-Path $composeFile) {
        try {
            docker info 2>&1 | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-INFO "Pobieram obrazy Docker (może chwilę potrwać)..."
                docker compose -f $composeFile pull 2>&1 | Tee-Log
                Write-INFO "Uruchamiam kontenery..."
                docker compose -f $composeFile up -d 2>&1 | Tee-Log

                # Wait for postgres health
                $waited = 0
                while ($waited -lt 30) {
                    Start-Sleep 3; $waited += 3
                    $status = docker inspect adrion-db --format='{{.State.Health.Status}}' 2>$null
                    if ($status -eq "healthy") { break }
                }
                if ($waited -ge 30) {
                    Write-WARN "PostgreSQL health check oczekuje — kontynuuję"
                } else {
                    Write-OK "PostgreSQL uruchomiony i zdrowy"
                }

                $running = docker ps --filter "name=adrion" --format "{{.Names}}" 2>$null
                $running | ForEach-Object { Write-INFO "  Kontener: $_" }
            }
        } catch {
            Write-WARN "Docker Stack błąd: $_ — kontynuuję w trybie SQLite"
            $issues += "Docker stack error"
        }
    } else {
        Write-WARN "Nie znaleziono $composeFile"
    }
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 7/8 — BUILD GO VORTEX ENGINE
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 7/8 — Kompilacja Vortex Engine (Go)"

if ($goOk) {
    try {
        Set-Location $ROOT
        $buildOutput = go build ./... 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Go build sukces"
        } else {
            Write-WARN "Go build warning: $buildOutput"
        }
    } catch {
        Write-WARN "Go build błąd: $_ — Vortex Engine niedostępny"
        $issues += "Go build failed"
    } finally {
        Set-Location $ROOT
    }
} else {
    Write-WARN "Go nie zainstalowany — Vortex Engine pominięty"
}

# ═════════════════════════════════════════════════════════════════════════════
# STEP 8/8 — HEALTH VERIFICATION
# ═════════════════════════════════════════════════════════════════════════════
Step-Header "KROK 8/8 — Weryfikacja instalacji"

$checks = @{}

# Check .env
$checks["env_file"] = Test-Path $ENV_FILE

# Check venv
$checks["venv"] = Test-Path $VENV_PY

# Check arbitrage import
try {
    & $VENV_PY -c "import arbitrage; print(arbitrage.__version__)" 2>&1 | Out-Null
    $checks["python_import"] = ($LASTEXITCODE -eq 0)
} catch {
    $checks["python_import"] = $false
}

# Check SQLite DB
$checks["sqlite_db"] = Test-Path (Join-Path $ROOT "arbitrage.db")

# Check Docker (if not skipped)
if (-not $SkipDocker) {
    try {
        docker ps --filter "name=adrion-db" --format "{{.Status}}" 2>$null | Out-Null
        $checks["docker"] = ($LASTEXITCODE -eq 0)
    } catch {
        $checks["docker"] = $false
    }
}

Write-Host ""
$allOk = $true
foreach ($check in $checks.GetEnumerator()) {
    if ($check.Value) {
        Write-OK "$($check.Key): OK"
    } else {
        Write-FAIL "$($check.Key): FAIL"
        $allOk = $false
    }
}

$elapsed = [math]::Round(((Get-Date) - (Get-Item $LOG_FILE).CreationTime).TotalSeconds)
Tee-Log "Setup completed in ${elapsed}s. Issues: $($issues.Count)"

Write-Host ""
Write-Host ("═" * 60) -ForegroundColor DarkCyan
if ($allOk -and $issues.Count -eq 0) {
    Write-Host "  INSTALACJA ZAKOŃCZONA POMYŚLNIE ($($elapsed)s)" -ForegroundColor Green
} elseif ($issues.Count -le 2) {
    Write-Host "  INSTALACJA ZAKOŃCZONA Z OSTRZEŻENIAMI ($($issues.Count))" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host "  ⚠  $_" -ForegroundColor Yellow }
} else {
    Write-Host "  INSTALACJA ZAKOŃCZONA Z BŁĘDAMI ($($issues.Count))" -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  ✗  $_" -ForegroundColor Red }
}
Write-Host ("═" * 60) -ForegroundColor DarkCyan
Write-Host ""
Write-Host "  Następny krok — uruchom system:" -ForegroundColor White
Write-Host "    .\admin.ps1 start" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Pełny log:" -ForegroundColor DarkGray
Write-Host "    $LOG_FILE" -ForegroundColor DarkGray
Write-Host ""
