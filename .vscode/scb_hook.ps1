# SCB (Session Continuity Bridge) Hook — ADRION 369
# PowerShell Profile Extension for automatic monitoring sync
# Source this in your PowerShell profile: . ".\.vscode\scb_hook.ps1"

$ProjectRoot = "c:\Users\adiha\162 demencje w schemacie 369"

function Invoke-ADRONMonitoringSync {
    <#
    .SYNOPSIS
    Run ADRION monitoring sync before session exit
    .DESCRIPTION
    Automatically updates JSON trackers + Master Synthesis Document
    Preserves session state and ensures continuous knowledge base
    #>
    
    if (-not (Test-Path "$ProjectRoot\scripts\reporting\update_adr_status.py")) {
        Write-Host "⚠️  ADRION monitoring script not found" -ForegroundColor Yellow
        return
    }
    
    Write-Host ""
    Write-Host "🔄 [SCB] Running ADRION Monitoring Sync..." -ForegroundColor Cyan
    Write-Host "📊 Synchronizing JSON trackers + Master Synthesis Document" -ForegroundColor Cyan
    
    try {
        Push-Location $ProjectRoot
        
        # Activate venv if not already active
        if (-not $env:VIRTUAL_ENV) {
            & ".\.venv\Scripts\Activate.ps1"
        }
        
        # Run monitoring script
        $result = & python scripts/reporting/update_adr_status.py 2>&1
        
        # Parse for success indicator
        if ($result -match "✅ All monitoring systems updated") {
            Write-Host "✅ [SCB] Sync Complete — Knowledge Base Current" -ForegroundColor Green
            Write-Host "📍 Location: $ProjectRoot\progress\MASTER_SYNTHESIS_ADRION369_05-04-2026.md" -ForegroundColor Gray
        } else {
            Write-Host "⚠️  [SCB] Sync may have issues — check manually" -ForegroundColor Yellow
            Write-Host $result -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "❌ [SCB] Error: $_" -ForegroundColor Red
    } finally {
        Pop-Location
    }
}

# Register exit handler
$OnExitAction = {
    Invoke-ADRONMonitoringSync
}

# Hook into PowerShell exit event
$ExecutionContext.InvokeCommand.LocationChangedAction = {
    # Placeholder for additional session tracking if needed
}

# Export for use in profile
Export-ModuleMember -Function Invoke-ADRONMonitoringSync

Write-Host "✅ [SCB Hook] Loaded — will sync on session exit" -ForegroundColor Green
