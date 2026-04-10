<#
═══════════════════════════════════════════════════════════════════════════════
  LM STUDIO SETUP & LAUNCHER — ADRIAN 369 Local LLM Deployment
═══════════════════════════════════════════════════════════════════════════════

Usage:
  .\setup_lmstudio_win.ps1          # Full setup
  .\setup_lmstudio_win.ps1 -Quick   # Quick start (assumes LM Studio installed)
  .\setup_lmstudio_win.ps1 -Check   # just verify setup

─────────────────────────────────────────────────────────────────────────────#>

param(
    [switch]$Quick,
    [switch]$Check,
    [string]$Model = \"neural-chat\",
    [string]$LMStudioPath = \".\",
    [int]$Port = 1234
)

$ErrorActionPreference = \"Stop\"

# ═══ Colors for Output ═══
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }

# ═══ Phase 1: Verify Prerequisites ═══
Write-Info \"═════════════════════════════════════════════════════════════\"
Write-Info \"  LM STUDIO SETUP — ADRIAN 369\"
Write-Info \"═════════════════════════════════════════════════════════════\"

Write-Info \"\\n[1/5] Checking Python environment...\"
if (-Not (Test-Path \".\\\.venv\\\Scripts\\\python.exe\")) {
    Write-Error \"❌ Python venv not found. Run: python -m venv .venv\"
    exit 1
}
Write-Success \"✅ Python venv found\"

Write-Info \"\\n[2/5] Checking LM Studio installation...\"
$LMStudioProcesses = Get-Process lm-studio -ErrorAction SilentlyContinue
if ($LMStudioProcesses) {
    Write-Success \"✅ LM Studio is running (PID: $($LMStudioProcesses.Id))\"
} else {
    Write-Info \"⚠️  LM Studio is not running\"
    Write-Info \"   Download from: https://lmstudio.ai/\"
    Write-Info \"   Then run: lm-studio\"
    if (-Not $Quick) {
        Read-Host \"   Press Enter to continue...\"
    }
}

# ═══ Phase 2: Test LM Studio Server ═══
Write-Info \"\\n[3/5] Testing LM Studio API (http://localhost:$Port)...\"
try {
    $Response = Invoke-WebRequest -Uri \"http://localhost:$Port/v1/models\" -TimeoutSec 5 -ErrorAction Stop
    $Models = ($Response.Content | ConvertFrom-Json).data
    Write-Success \"✅ LM Studio API is responding\"
    Write-Info \"   Loaded models: $($Models | Select-Object -ExpandProperty id | Join-String -Separator ', ')\"

    # Find the target model
    $LoadedModel = $Models | Where-Object { $_.id -like \"*$Model*\" } | Select-Object -First 1
    if ($LoadedModel) {
        Write-Success \"   ✅ Model '$($LoadedModel.id)' is loaded\"
    } else {
        Write-Info \"   ⚠️  '$Model' not currently loaded\"
        Write-Info \"   Available: $(($Models | Select-Object -ExpandProperty id) -join ', ')\"
    }
} catch {
    Write-Error \"❌ Cannot connect to LM Studio at http://localhost:$Port\"
    Write-Error \"   Error: $($_.Exception.Message)\"
    Write-Info \"\\n   Solution:\"
    Write-Info \"   1. Download LM Studio: https://lmstudio.ai/\"
    Write-Info \"   2. Launch LM Studio desktop app\"
    Write-Info \"   3. Load a model (Settings → Local Server → Select & Load)\"
    Write-Info \"   4. Verify: http://localhost:$Port/v1/models\"
    if (-Not $Check) {
        Read-Host \"   Press Enter to continue anyway...\"
    } else {
        exit 1
    }
}

# ═══ Phase 3: Setup .env Configuration ═══
Write-Info \"\\n[4/5] Configuring .env for LM Studio...\"

if (Test-Path \".\\\.env.lmstudio\") {
    Write-Success \"✅ .env.lmstudio template found\"
} else {
    Write-Info \"Creating .env.lmstudio...\"
    @\"
LLM_BACKEND=lmstudio
LMSTUDIO_URL=http://localhost:$Port
LMSTUDIO_MODEL=$Model
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=deepseek:7b
DB_ENGINE=sqlite
DB_PATH=./arbitrage.db
\" | Out-File -FilePath \".env.lmstudio\" -Encoding UTF8 -Force
    Write-Success \"✅ Created .env.lmstudio\"
}

# Check if .env.local exists
if (Test-Path \".\\\.env\") {
    Write-Info \"   .env already exists (not overwriting)\"
} else {
    Write-Info \"   Creating .env from .env.lmstudio...\"
    Copy-Item -Path \".\\\.env.lmstudio\" -Destination \".\\\.env\" -Force
    Write-Success \"✅ Copied to .env\"
}

# ═══ Phase 4: Verify Dependencies ═══
Write-Info \"\\n[5/5] Verifying Python dependencies...\"
.\\\.venv\\\Scripts\\\pip.exe install -q openai requests 2>$null
Write-Success \"✅ Python dependencies ready\"

# ═══ Final Status ═══
Write-Info \"\\n═════════════════════════════════════════════════════════════\"
Write-Success \"✅ LM STUDIO SETUP COMPLETE\"
Write-Info \"═════════════════════════════════════════════════════════════\"

Write-Info \"\\n📋 Next Steps:\"
Write-Info \"   1. Ensure LM Studio is running: lm-studio\"
Write-Info \"   2. Load a model in LM Studio (Settings → Local Server)\"
Write-Info \"   3. Start ADRIAN 369:\"
Write-Info \"\\n      .\\\.venv\\\Scripts\\\Activate.ps1\"
Write-Info \"      python arbitrage_server.py\"
Write-Info \"\\n   4. Open Dashboard: http://localhost:5000\"
Write-Info \"   5. Verify LLM Backend shows: lmstudio\"

Write-Info \"\\n📊 Version Info:\"
$PythonVer = &.\\\.venv\\\Scripts\\\python.exe --version 2>&1
Write-Info \"   Python: $PythonVer\"
Write-Info \"   LM Studio: http://localhost:$Port\"
Write-Info \"   Model: $Model\"

Write-Info \"\\n💡 Troubleshooting:\"
Write-Info \"   • 'Connection refused': Start LM Studio desktop app\"
Write-Info \"   • 'Model not loaded': Click 'Load' in LM Studio UI\"
Write-Info \"   • 'Out of memory': Use smaller model (mistral:7b)\"
Write-Info \"   • 'Slow responses': Check GPU in LM Studio Settings\"

Write-Info \"\\n📚 Documentation: LM_STUDIO_INTEGRATION.md\"
Write-Info \"═════════════════════════════════════════════════════════════\\n\"

# ═══ Optional: Start Services ═══
if (-Not $Check) {
    $Start = Read-Host \"Start ADRIAN 369 services now? (y/n)\"
    if ($Start -eq \"y\") {
        Write-Info \"\\nStarting Arbitrage Server...\"
        .\\\.venv\\\Scripts\\\Activate.ps1
        python arbitrage_server.py
    }
}
