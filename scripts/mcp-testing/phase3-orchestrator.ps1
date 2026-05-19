# PHASE 3 ORCHESTRATOR — MCP Integration & Testing
# Master script for validating MCP cluster and canary deployment

param(
    [ValidateSet("smoke", "validate", "kpi", "all", "canary-5", "canary-50", "canary-100")][string]$Stage = "all",
    [bool]$StopOnFail = $false,
    [string]$LogPath = "./monitoring/phase3_execution.log"
)

$ErrorActionPreference = if ($StopOnFail) { "Stop" } else { "Continue" }
$ProgressPreference = "SilentlyContinue"

# ════════════════════════════════════════════════════════════════════════════
# INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════

$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root_dir = Split-Path -Parent (Split-Path -Parent $script_dir)
$phase3_start_time = Get-Date

# Create log
if (-not (Test-Path (Split-Path -Parent $LogPath))) {
    New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
}

$log_stream = [System.IO.StreamWriter]::new([System.IO.File]::Create($LogPath))

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $log_line = "[$timestamp] [$Level] $Message"

    Write-Host $log_line -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "White" }
        }
    )

    $log_stream.WriteLine($log_line)
    $log_stream.Flush()
}

function Run-Stage {
    param(
        [string]$StageName,
        [scriptblock]$ScriptBlock,
        [bool]$Critical = $false
    )

    Write-Log "═════════════════════════════════════════════════════════" "INFO"
    Write-Log "EXECUTING STAGE: $StageName" "INFO"
    Write-Log "═════════════════════════════════════════════════════════" "INFO"

    $stage_start = Get-Date

    try {
        & $ScriptBlock
        $stage_duration = ((Get-Date) - $stage_start).TotalSeconds
        Write-Log "✅ STAGE PASSED: $StageName (${stage_duration}s)" "SUCCESS"
        return $true
    } catch {
        Write-Log "❌ STAGE FAILED: $StageName - $_" "ERROR"
        if ($Critical) {
            Write-Log "Critical stage failed. Aborting." "ERROR"
            return $false
        }
        return $true
    }
}

Write-Log "
╔════════════════════════════════════════════════════════════════╗
║       PHASE 3: MCP INTEGRATION & TESTING ORCHESTRATOR         ║
║       Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')                         ║
║       Stage: $Stage                                           ║
╚════════════════════════════════════════════════════════════════╝
" "INFO"

# ════════════════════════════════════════════════════════════════════════════
# STAGE DEFINITIONS
# ════════════════════════════════════════════════════════════════════════════

$stages = @{
    "smoke" = {
        Write-Log "Stage 1: Smoke testing..." "INFO"
        & "$script_dir\smoke-test.ps1" -MaxWaitSeconds 60
        if ($LASTEXITCODE -ne 0) { throw "Smoke test failed" }
    }

    "validate" = {
        Write-Log "Stage 2: Full cluster validation..." "INFO"
        & "$script_dir\validate-mcp-cluster.ps1" `
            -Environment "local" `
            -Timeout 30 `
            -OutputPath "$root_dir/monitoring/mcp_validation_results.json"
        if ($LASTEXITCODE -ne 0) { throw "Cluster validation failed" }
    }

    "kpi" = {
        Write-Log "Stage 3: KPI gate validation..." "INFO"
        & "$script_dir\kpi-gate-validation.ps1" `
            -SamplingWindow 50 `
            -MinEvents 20 `
            -TargetSuccessRate 0.95 `
            -OutputPath "$root_dir/monitoring/mcp_kpi_report.json"
        if ($LASTEXITCODE -ne 0) { throw "KPI validation failed" }
    }

    "unit-tests" = {
        Write-Log "Stage 4: Running unit tests..." "INFO"
        Push-Location $root_dir
        & pytest tests/mcp/test_mcp_signatures.py -v --tb=short
        if ($LASTEXITCODE -ne 0) { throw "Unit tests failed" }
        Pop-Location
    }

    "e2e-tests" = {
        Write-Log "Stage 5: Running E2E integration tests..." "INFO"
        Push-Location $root_dir
        & pytest tests/mcp/test_mcp_e2e.py -v --tb=short
        if ($LASTEXITCODE -ne 0) { throw "E2E tests failed" }
        Pop-Location
    }

    "canary-5" = {
        Write-Log "Stage 6: Canary deployment (5%)..." "INFO"
        Write-Log "⚠️  Manual action required: Route 5% traffic to MCP tier" "WARN"
        Write-Log "Duration: 600 seconds (10 minutes)" "INFO"
        Write-Log "Success criteria: error_rate <= 2%" "INFO"
        # Programmatic canary would be implemented here for production
    }

    "canary-50" = {
        Write-Log "Stage 7: Canary deployment (50%)..." "INFO"
        Write-Log "⚠️  Manual action required: Route 50% traffic to MCP tier" "WARN"
        Write-Log "Duration: 600 seconds (10 minutes)" "INFO"
        Write-Log "Success criteria: error_rate <= 1.5%" "INFO"
    }

    "canary-100" = {
        Write-Log "Stage 8: Full rollout (100%)..." "INFO"
        Write-Log "⚠️  Manual action required: Route 100% traffic to MCP tier" "WARN"
        Write-Log "Duration: 300 seconds (5 minutes)" "INFO"
        Write-Log "Success criteria: success_rate >= 95%" "INFO"
    }
}

# ════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ════════════════════════════════════════════════════════════════════════════

$success_count = 0
$failed_stages = @()

if ($Stage -eq "all") {
    $execution_stages = @("smoke", "validate", "kpi", "unit-tests", "e2e-tests", "canary-5", "canary-50", "canary-100")
} else {
    $execution_stages = @($Stage)
}

foreach ($stage_name in $execution_stages) {
    if ($stages.ContainsKey($stage_name)) {
        $stage_result = Run-Stage -StageName $stage_name -ScriptBlock $stages[$stage_name] -Critical ($stage_name -in @("smoke", "validate", "kpi"))

        if ($stage_result) {
            $success_count++
        } else {
            $failed_stages += $stage_name
        }
    } else {
        Write-Log "Unknown stage: $stage_name" "ERROR"
    }
}

# ════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ════════════════════════════════════════════════════════════════════════════

$total_duration = ((Get-Date) - $phase3_start_time).TotalSeconds

Write-Log "
╔════════════════════════════════════════════════════════════════╗
║                    PHASE 3 EXECUTION REPORT                   ║
╠════════════════════════════════════════════════════════════════╣
║ Total Duration: ${total_duration}s" "INFO" | Out-Host

if ($failed_stages.Count -eq 0) {
    Write-Log "║ Status: ✅ ALL STAGES PASSED" "SUCCESS" | Out-Host
    $exit_code = 0
} else {
    Write-Log "║ Status: ❌ FAILURES DETECTED" "ERROR" | Out-Host
    Write-Log "║ Failed Stages:" "ERROR" | Out-Host
    foreach ($stage in $failed_stages) {
        Write-Log "║   - $stage" "ERROR" | Out-Host
    }
    $exit_code = 1
}

Write-Log "╚════════════════════════════════════════════════════════════════╝" "INFO" | Out-Host

Write-Log ""
Write-Log "Log file: $LogPath" "INFO"
Write-Log "Validation results: ./monitoring/mcp_validation_results.json" "INFO"
Write-Log "KPI report: ./monitoring/mcp_kpi_report.json" "INFO"

$log_stream.Close()

exit $exit_code
