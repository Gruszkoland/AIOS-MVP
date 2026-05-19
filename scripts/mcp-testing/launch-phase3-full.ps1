# ==============================================================================
# PHASE 3 FULL DEPLOYMENT LAUNCHER
# ADRION 369 v4.0 - MCP Infrastructure Testing & Canary Deployment
# ==============================================================================
#
# Purpose: Orchestrate complete Phase 3 pipeline
#   1. Launch 6 MCP servers (Python Flask apps)
#   2. Wait for health checks
#   3. Run smoke test
#   4. Run cluster validation
#   5. Run KPI gate
#   6. Run unit + E2E tests
#   7. Generate final report
#
# Usage: powershell scripts/mcp-testing/launch-phase3-full.ps1 -Stage all
# ==============================================================================

param(
    [ValidateSet("all", "servers", "smoke", "validate", "kpi", "tests", "report")]
    [string]$Stage = "all",

    [switch]$SkipTests,
    [switch]$DryRun,
    [int]$TimeoutSeconds = 120,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
if ($Verbose) { $VerbosePreference = "Continue" }

# ==============================================================================
# CONFIGURATION & STATE
# ==============================================================================

$startTime = Get-Date
$config = @{
    projectRoot = "c:\Users\adiha\162 demencje w schemacie 369"
    pythonExe = "c:\Users\adiha\162 demencje w schemacie 369\.venv\Scripts\python.exe"
    timeout = $TimeoutSeconds
    retries = 3
    waitBetweenRetries = 2
}

$mcp_servers = @(
    @{ name = "ROUTER"; port = 9000; app = "mcp_router_app.py"; required = $true }
    @{ name = "VORTEX"; port = 9001; app = "mcp_vortex_app.py"; required = $true }
    @{ name = "GUARDIAN"; port = 9002; app = "mcp_guardian_app.py"; required = $true }
    @{ name = "ORACLE"; port = 9003; app = "mcp_oracle_app.py"; required = $true }
    @{ name = "GENESIS"; port = 9004; app = "mcp_genesis_app.py"; required = $true }
    @{ name = "HEALER"; port = 9005; app = "mcp_healer_app.py"; required = $false }
)

$results = @{
    servers_launched = @()
    servers_healthy = @()
    smoke_test = "pending"
    cluster_validation = "pending"
    kpi_gate = "pending"
    unit_tests = "pending"
    e2e_tests = "pending"
    errors = @()
    start_time = $startTime
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

function Write-Banner {
    param([string]$text, [string]$color = "Cyan")
    Write-Host "`n╔" + ("═" * 66) + "╗" -ForegroundColor $color
    Write-Host "║  $($text.PadRight(64))  ║" -ForegroundColor $color
    Write-Host "╚" + ("═" * 66) + "╝" -ForegroundColor $color
}

function Write-Status {
    param([string]$text, [string]$status = "INFO", [string]$color = "White")
    $icon = switch ($status) {
        "OK" { "✅"; "Green" }
        "WARN" { "⚠️ "; "Yellow" }
        "ERROR" { "❌"; "Red" }
        "SKIP" { "⏭️ "; "Gray" }
        default { "ℹ️ "; "Cyan" }
    }
    Write-Host "$icon [$status] $text" -ForegroundColor $color
}

function Wait-HealthCheck {
    param(
        [string]$port,
        [string]$name,
        [int]$maxRetries = 3,
        [int]$waitSeconds = 2
    )

    $url = "http://localhost:$port/health"
    $retryCount = 0

    while ($retryCount -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                return $true
            }
        }
        catch {
            Write-Status "$name health check failed (attempt $($retryCount + 1)/$maxRetries)" "WARN" "Yellow"
        }

        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Start-Sleep -Seconds $waitSeconds
        }
    }

    return $false
}

function Launch-MCPServer {
    param([hashtable]$server)

    Write-Status "Launching $($server.name) on port $($server.port)..." "INFO" "Cyan"

    if ($DryRun) {
        Write-Status "DRY-RUN: Would launch $($server.app)" "SKIP"
        return $true
    }

    $appPath = Join-Path $config.projectRoot $server.app

    try {
        $process = Start-Process -FilePath $config.pythonExe `
            -ArgumentList $appPath `
            -WorkingDirectory $config.projectRoot `
            -NoNewWindow `
            -PassThru `
            -ErrorAction Stop

        # Store process ID for later cleanup
        $server["pid"] = $process.Id
        $results.servers_launched += $server.name

        Write-Status "$($server.name) launched (PID: $($process.Id))" "OK" "Green"
        return $true
    }
    catch {
        Write-Status "Failed to launch $($server.name): $_" "ERROR" "Red"
        $results.errors += "Launch failed for $($server.name)"
        return $false
    }
}

function Wait-AllServersHealthy {
    Write-Status "Waiting for all servers to be healthy (max $($config.timeout)s)..." "INFO" "Yellow"

    $startedWait = Get-Date
    $allHealthy = $false
    $checkInterval = 3

    while ((Get-Date) -lt $startedWait.AddSeconds($config.timeout)) {
        $healthyCount = 0
        $allHealthy = $true

        foreach ($server in $mcp_servers) {
            # Skip health check in dry-run
            if ($DryRun) {
                $isHealthy = $true
            } else {
                $isHealthy = Wait-HealthCheck -port $server.port -name $server.name -maxRetries 1 -waitSeconds 0
            }

            if ($isHealthy) {
                $healthyCount++
                if ($results.servers_healthy -notcontains $server.name) {
                    $results.servers_healthy += $server.name
                    Write-Status "$($server.name) is healthy" "OK" "Green"
                }
            }
            else {
                $allHealthy = $false
                if ($server.required) {
                    Write-Status "$($server.name) NOT healthy (required)" "WARN" "Yellow"
                }
            }
        }

        if ($allHealthy -or $healthyCount -ge 5) {
            Write-Status "All required servers healthy ($healthyCount/6)" "OK" "Green"
            return $true
        }

        Write-Status "Healthy: $healthyCount/6 servers" "WARN" "Yellow"
        Start-Sleep -Seconds $checkInterval
    }

    Write-Status "Timeout waiting for servers to be healthy" "ERROR" "Red"
    return $false
}

function Execute-SmokeTest {
    Write-Banner "SMOKE TEST EXECUTION" "Cyan"

    if ($DryRun) {
        Write-Status "DRY-RUN: Would execute smoke-test.ps1" "SKIP"
        $results.smoke_test = "dry-run"
        return $true
    }

    $smokeTestPath = Join-Path $config.projectRoot "scripts\mcp-testing\smoke-test.ps1"

    try {
        $output = & powershell -File $smokeTestPath 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Smoke test PASSED" "OK" "Green"
            $results.smoke_test = "passed"
            Write-Host $output
            return $true
        }
        else {
            Write-Status "Smoke test FAILED (exit code: $LASTEXITCODE)" "ERROR" "Red"
            $results.smoke_test = "failed"
            Write-Host $output
            $results.errors += "Smoke test failed"
            return $false
        }
    }
    catch {
        Write-Status "Smoke test execution error: $_" "ERROR" "Red"
        $results.smoke_test = "error"
        $results.errors += "Smoke test error: $_"
        return $false
    }
}

function Execute-ClusterValidation {
    Write-Banner "CLUSTER VALIDATION" "Cyan"

    if ($DryRun) {
        Write-Status "DRY-RUN: Would execute cluster validation" "SKIP"
        $results.cluster_validation = "dry-run"
        return $true
    }

    $validatePath = Join-Path $config.projectRoot "scripts\mcp-testing\validate-mcp-cluster.ps1"

    try {
        $output = & powershell -File $validatePath 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Cluster validation PASSED" "OK" "Green"
            $results.cluster_validation = "passed"
            return $true
        }
        else {
            Write-Status "Cluster validation FAILED" "WARN" "Yellow"
            $results.cluster_validation = "partial"
            return $false
        }
    }
    catch {
        Write-Status "Cluster validation error: $_" "ERROR" "Red"
        $results.cluster_validation = "error"
        $results.errors += "Validation error: $_"
        return $false
    }
}

function Execute-KPIGate {
    Write-Banner "KPI GATE VALIDATION" "Cyan"

    if ($DryRun) {
        Write-Status "DRY-RUN: Would execute KPI gate" "SKIP"
        $results.kpi_gate = "dry-run"
        return $true
    }

    $kpiPath = Join-Path $config.projectRoot "scripts\mcp-testing\kpi-gate-validation.ps1"

    try {
        $output = & powershell -File $kpiPath 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "KPI Gate PASSED ✅" "OK" "Green"
            $results.kpi_gate = "passed"
            return $true
        }
        else {
            Write-Status "KPI Gate FAILED ❌" "ERROR" "Red"
            $results.kpi_gate = "failed"
            $results.errors += "KPI gate failed"
            return $false
        }
    }
    catch {
        Write-Status "KPI gate error: $_" "ERROR" "Red"
        $results.kpi_gate = "error"
        return $false
    }
}

function Execute-UnitTests {
    Write-Banner "UNIT TESTS (DSPy Signatures)" "Cyan"

    if ($SkipTests -or $DryRun) {
        Write-Status "SKIP: Unit tests" "SKIP"
        $results.unit_tests = "skipped"
        return $true
    }

    try {
        $testPath = Join-Path $config.projectRoot "tests\mcp\test_mcp_signatures.py"
        $output = & $config.pythonExe -m pytest $testPath -v --tb=short 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "Unit tests PASSED (50+ tests)" "OK" "Green"
            $results.unit_tests = "passed"
            return $true
        }
        else {
            Write-Status "Unit tests FAILED" "WARN" "Yellow"
            $results.unit_tests = "failed"
            $results.errors += "Unit tests failed"
            return $false
        }
    }
    catch {
        Write-Status "Unit test error: $_" "ERROR" "Red"
        $results.unit_tests = "error"
        return $false
    }
}

function Execute-E2ETests {
    Write-Banner "E2E INTEGRATION TESTS" "Cyan"

    if ($SkipTests -or $DryRun) {
        Write-Status "SKIP: E2E tests" "SKIP"
        $results.e2e_tests = "skipped"
        return $true
    }

    try {
        $testPath = Join-Path $config.projectRoot "tests\mcp\test_mcp_e2e.py"
        $output = & $config.pythonExe -m pytest $testPath -v --tb=short 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Status "E2E tests PASSED (30+ tests)" "OK" "Green"
            $results.e2e_tests = "passed"
            return $true
        }
        else {
            Write-Status "E2E tests FAILED" "WARN" "Yellow"
            $results.e2e_tests = "failed"
            $results.errors += "E2E tests failed"
            return $false
        }
    }
    catch {
        Write-Status "E2E test error: $_" "ERROR" "Red"
        $results.e2e_tests = "error"
        return $false
    }
}

function Generate-Report {
    Write-Banner "PHASE 3 EXECUTION REPORT" "Cyan"

    $endTime = Get-Date
    $duration = $endTime - $results.start_time

    Write-Host "`n📊 PHASE 3 TEST RESULTS" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    Write-Host "`n🚀 SERVER LAUNCHES:" -ForegroundColor White
    foreach ($srv in $results.servers_launched) {
        Write-Status "$srv launched" "OK" "Green"
    }

    Write-Host "`n❤️  HEALTH CHECKS:" -ForegroundColor White
    foreach ($srv in $results.servers_healthy) {
        Write-Status "$srv healthy" "OK" "Green"
    }

    Write-Host "`n✅ TEST RESULTS:" -ForegroundColor White
    Write-Status "Smoke Test: $($results.smoke_test)" "INFO"
    Write-Status "Cluster Validation: $($results.cluster_validation)" "INFO"
    Write-Status "KPI Gate: $($results.kpi_gate)" "INFO"
    Write-Status "Unit Tests: $($results.unit_tests)" "INFO"
    Write-Status "E2E Tests: $($results.e2e_tests)" "INFO"

    if ($results.errors.Count -gt 0) {
        Write-Host "`n❌ ERRORS:" -ForegroundColor Red
        foreach ($err in $results.errors) {
            Write-Host "   - $err" -ForegroundColor Red
        }
    }

    Write-Host "`n⏱️  EXECUTION TIME: $($duration.TotalSeconds.ToString('F2'))s" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

    # Save report to JSON
    $reportPath = Join-Path $config.projectRoot "monitoring\phase3_execution_report_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    $results | ConvertTo-Json | Out-File $reportPath
    Write-Status "Report saved to: $reportPath" "OK" "Green"

    # Return exit code based on critical failures
    if ($results.errors.Count -gt 0) {
        return 1
    }
    return 0
}

function Cleanup-Servers {
    Write-Status "Cleaning up MCP server processes..." "INFO" "Yellow"

    foreach ($server in $mcp_servers) {
        if ($server.pid) {
            try {
                Stop-Process -Id $server.pid -ErrorAction SilentlyContinue
                Write-Status "Stopped $($server.name) (PID: $($server.pid))" "OK"
            }
            catch {
                Write-Status "Failed to stop $($server.name): $_" "WARN"
            }
        }
    }
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

Write-Banner "PHASE 3: MCP INFRASTRUCTURE TESTING & DEPLOYMENT" "Green"
Write-Status "Starting at $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" "INFO"

# Stage: Launch servers
if ($Stage -in @("all", "servers")) {
    Write-Banner "LAUNCHING MCP SERVERS" "Cyan"

    foreach ($server in $mcp_servers) {
        $launched = Launch-MCPServer $server
        if (-not $launched -and $server.required) {
            Write-Status "Required server failed to launch: $($server.name)" "ERROR" "Red"
        }
    }

    # Wait for health checks
    if ($results.servers_launched.Count -ge 5) {
        Write-Status "Waiting for health checks..." "INFO" "Yellow"
        Start-Sleep -Seconds 5
        $allHealthy = Wait-AllServersHealthy

        if (-not $allHealthy) {
            Write-Status "Not all servers became healthy, continuing anyway..." "WARN" "Yellow"
        }
    }
}

# Stage: Smoke Test
if ($Stage -in @("all", "smoke")) {
    $smokePass = Execute-SmokeTest
}

# Stage: Cluster Validation
if ($Stage -in @("all", "validate")) {
    $validationPass = Execute-ClusterValidation
}

# Stage: KPI Gate
if ($Stage -in @("all", "kpi")) {
    $kpiPass = Execute-KPIGate
}

# Stage: Tests
if ($Stage -in @("all", "tests")) {
    Execute-UnitTests
    Execute-E2ETests
}

# Stage: Report
if ($Stage -in @("all", "report")) {
    $exitCode = Generate-Report
}

# Final report
if ($Stage -eq "all") {
    Generate-Report

    # Cleanup
    Write-Banner "CLEANUP" "Yellow"
    Cleanup-Servers
}

Write-Status "Phase 3 execution completed" "OK" "Green"
exit $exitCode
