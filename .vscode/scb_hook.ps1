# SCB (Session Continuity Bridge) Hook - ADRION 369
# PowerShell Profile Extension for automatic monitoring sync
# Simple version (no try/catch to avoid PS parsing issues)

$ProjectRoot = "c:\Users\adiha\162 demencje w schemacie 369"

function Invoke-ADRONMonitoringSync {
    param()
    
    $ScriptPath = "$ProjectRoot\scripts\reporting\update_adr_status.py"
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "Warning: ADRION monitoring script not found" -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "[SCB] Running ADRION Monitoring Sync..." -ForegroundColor Cyan
    
    Push-Location $ProjectRoot -ErrorAction SilentlyContinue
    
    # Activate venv if not active
    if (-not $env:VIRTUAL_ENV) {
        & ".\.venv\Scripts\Activate.ps1" -ErrorAction SilentlyContinue
    }
    
    # Run monitoring script
    python scripts/reporting/update_adr_status.py
    
    Pop-Location -ErrorAction SilentlyContinue
}

Write-Host "[SCB Hook] Loaded - monitoring available" -ForegroundColor Green

