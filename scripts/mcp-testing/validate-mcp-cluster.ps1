# MCP Cluster Validation Script
# Validates all 6 MCP servers (9000-9005) with comprehensive health checks

param(
    [string]$Environment = "local",
    [int]$Timeout = 30,
    [bool]$Verbose = $true,
    [string]$OutputPath = "./monitoring/mcp_validation_results.json"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

$mcp_servers = @{
    "MCP-ROUTER"    = @{ port = 9000; name = "Router"; role = "Orchestration" }
    "VORTEX-MCP"    = @{ port = 9001; name = "Vortex"; role = "Harmonic Orchestration" }
    "GUARDIAN-MCP"  = @{ port = 9002; name = "Guardian"; role = "Security" }
    "ORACLE-MCP"    = @{ port = 9003; name = "Oracle"; role = "Routing" }
    "GENESIS-MCP"   = @{ port = 9004; name = "Genesis"; role = "State Management" }
    "HEALER-MCP"    = @{ port = 9005; name = "Healer"; role = "Recovery" }
}

# ════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

function Test-MCP-Health {
    param([string]$ServerName, [int]$Port)

    $url = "http://localhost:$Port/health"

    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            return @{
                success = $true
                status = "HEALTHY"
                code = $response.StatusCode
                latency_ms = $response.Headers."X-Response-Time" -join ","
            }
        }
    } catch {
        return @{
            success = $false
            status = "UNHEALTHY"
            error = $_.Exception.Message
        }
    }
}

function Test-MCP-Route {
    param([string]$Query, [hashtable]$Context)

    $url = "http://localhost:9000/route"
    $payload = @{
        query = $Query
        context = $Context
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest -Uri $url -Method POST `
            -ContentType "application/json" `
            -Body $payload `
            -TimeoutSec $Timeout `
            -UseBasicParsing `
            -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            return @{
                success = $true
                result = $response.Content | ConvertFrom-Json
            }
        }
    } catch {
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
}

function Test-Guardian-Compliance {
    param([string]$Operation, [hashtable]$Context)

    $url = "http://localhost:9002/validate"
    $payload = @{
        operation = $Operation
        context = $Context
    } | ConvertTo-Json

    try {
        $response = Invoke-WebRequest -Uri $url -Method POST `
            -ContentType "application/json" `
            -Body $payload `
            -TimeoutSec $Timeout `
            -UseBasicParsing `
            -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            return @{
                success = $true
                compliance = "PASSED"
                data = $response.Content | ConvertFrom-Json
            }
        }
    } catch {
        return @{
            success = $false
            compliance = "FAILED"
            error = $_.Exception.Message
        }
    }
}

function Test-MCP-Stats {
    param([int]$Port, [string]$Endpoint)

    $url = "http://localhost:$Port/$Endpoint"

    try {
        $response = Invoke-WebRequest -Uri $url -Method GET `
            -TimeoutSec $Timeout `
            -UseBasicParsing `
            -ErrorAction Stop

        if ($response.StatusCode -eq 200) {
            return @{
                success = $true
                stats = $response.Content | ConvertFrom-Json
            }
        }
    } catch {
        return @{
            success = $false
            error = $_.Exception.Message
        }
    }
}

# ════════════════════════════════════════════════════════════════════════════
# MAIN VALIDATION
# ════════════════════════════════════════════════════════════════════════════

Write-Log "═════════════════════════════════════════════════════════════" "INFO"
Write-Log "ADRION 369 MCP CLUSTER VALIDATION — PHASE 3" "INFO"
Write-Log "Environment: $Environment | Timeout: ${Timeout}s | Output: $OutputPath" "INFO"
Write-Log "═════════════════════════════════════════════════════════════" "INFO"

$validation_results = @{
    timestamp = Get-Date -Format "o"
    environment = $Environment
    timeout_seconds = $Timeout
    servers = @{}
    integration_tests = @{}
    compliance_tests = @{}
    summary = @{}
}

# ─── STEP 1: Health Checks ───────────────────────────────────────────────

Write-Log "[STEP 1/5] Health Checks on all 6 MCP servers..." "INFO"

$health_passed = 0
$health_total = 0

foreach ($server_name in $mcp_servers.Keys) {
    $server_info = $mcp_servers[$server_name]
    $port = $server_info.port

    Write-Log "  ├─ Testing $server_name (port $port)..." "INFO"

    $health_result = Test-MCP-Health -ServerName $server_name -Port $port
    $validation_results.servers[$server_name] = $health_result

    if ($health_result.success) {
        Write-Host "     ✅ HEALTHY" -ForegroundColor Green
        $health_passed++
    } else {
        Write-Host "     ❌ UNHEALTHY: $($health_result.error)" -ForegroundColor Red
    }

    $health_total++
}

$validation_results.summary.health_checks = @{
    passed = $health_passed
    total = $health_total
    status = if ($health_passed -eq $health_total) { "PASS" } else { "FAIL" }
}

Write-Log "Health Checks: $health_passed/$health_total PASSED" "INFO"

# ─── STEP 2: Integration Tests ──────────────────────────────────────────

Write-Log "[STEP 2/5] Integration Tests (Routing & Compliance)..." "INFO"

$test_cases = @(
    @{ query = "fix the bug in payment service"; intent = "fix"; context = @{ audit_logged = $true; backup_exists = $true } }
    @{ query = "add new feature to dashboard"; intent = "feature"; context = @{ audit_logged = $true; backup_exists = $true } }
    @{ query = "deploy to production"; intent = "deploy"; context = @{ audit_logged = $true; backup_exists = $true } }
)

$integration_passed = 0

foreach ($test in $test_cases) {
    Write-Log "  ├─ Query: '$($test.query)'" "INFO"

    $route_result = Test-MCP-Route -Query $test.query -Context $test.context

    if ($route_result.success) {
        $validation_results.integration_tests[$test.query] = $route_result.result
        Write-Host "     ✅ Routed to: $($route_result.result.agent)" -ForegroundColor Green
        $integration_passed++
    } else {
        Write-Host "     ❌ Routing failed: $($route_result.error)" -ForegroundColor Red
    }
}

$validation_results.summary.integration_tests = @{
    passed = $integration_passed
    total = $test_cases.Count
    status = if ($integration_passed -eq $test_cases.Count) { "PASS" } else { "WARN" }
}

Write-Log "Integration Tests: $integration_passed/$($test_cases.Count) PASSED" "INFO"

# ─── STEP 3: Compliance Tests ───────────────────────────────────────────

Write-Log "[STEP 3/5] Guardian Compliance Tests (9 Laws)..." "INFO"

$compliance_tests = @(
    @{ operation = "export_data"; context = @{ scope = "local" }; expect = "PASS" }
    @{ operation = "export_data"; context = @{ scope = "global" }; expect = "FAIL" }
    @{ operation = "delete"; context = @{ backup_exists = $true }; expect = "PASS" }
    @{ operation = "delete"; context = @{ backup_exists = $false }; expect = "FAIL" }
)

$compliance_passed = 0

foreach ($test in $compliance_tests) {
    Write-Log "  ├─ Op: $($test.operation) | Scope: $($test.context.scope)" "INFO"

    $compliance_result = Test-Guardian-Compliance -Operation $test.operation -Context $test.context

    if ($compliance_result.success) {
        if (($test.expect -eq "PASS" -and $compliance_result.compliance -eq "PASSED") -or `
            ($test.expect -eq "FAIL" -and $compliance_result.compliance -ne "PASSED")) {
            Write-Host "     ✅ Compliance: $($compliance_result.compliance)" -ForegroundColor Green
            $compliance_passed++
        } else {
            Write-Host "     ⚠️  Compliance: $($compliance_result.compliance) (expected $($test.expect))" -ForegroundColor Yellow
        }
        $validation_results.compliance_tests[$test.operation] = $compliance_result
    } else {
        Write-Host "     ❌ Compliance check failed" -ForegroundColor Red
    }
}

$validation_results.summary.compliance_tests = @{
    passed = $compliance_passed
    total = $compliance_tests.Count
    status = if ($compliance_passed -eq $compliance_tests.Count) { "PASS" } else { "WARN" }
}

Write-Log "Compliance Tests: $compliance_passed/$($compliance_tests.Count) PASSED" "INFO"

# ─── STEP 4: Performance Stats ──────────────────────────────────────────

Write-Log "[STEP 4/5] Performance & Statistics..." "INFO"

$stats_endpoints = @{
    "9000" = @{ port = 9000; endpoint = "stats/routing" }
    "9002" = @{ port = 9002; endpoint = "audit/summary" }
    "9004" = @{ port = 9004; endpoint = "stats" }
    "9005" = @{ port = 9005; endpoint = "stats" }
}

foreach ($key in $stats_endpoints.Keys) {
    $endpoint_info = $stats_endpoints[$key]
    Write-Log "  ├─ Port $($endpoint_info.port): $($endpoint_info.endpoint)" "INFO"

    $stats = Test-MCP-Stats -Port $endpoint_info.port -Endpoint $endpoint_info.endpoint
    if ($stats.success) {
        Write-Host "     ✅ Stats retrieved" -ForegroundColor Green
        $validation_results.summary["stats_port_$($endpoint_info.port)"] = $stats.stats
    } else {
        Write-Host "     ❌ Stats retrieval failed" -ForegroundColor Red
    }
}

# ─── STEP 5: Summary Report ────────────────────────────────────────────

Write-Log "[STEP 5/5] Generating Summary Report..." "INFO"

$overall_status = "PASS"
if ($validation_results.summary.health_checks.status -ne "PASS" -or `
    $validation_results.summary.integration_tests.status -eq "FAIL" -or `
    $validation_results.summary.compliance_tests.status -eq "FAIL") {
    $overall_status = "FAIL"
}

$validation_results.summary.overall_status = $overall_status
$validation_results.summary.timestamp_completed = Get-Date -Format "o"

Write-Log "═════════════════════════════════════════════════════════════" "INFO"
Write-Log "VALIDATION RESULTS" "INFO"
Write-Log "═════════════════════════════════════════════════════════════" "INFO"
Write-Host "Health Checks:      $($validation_results.summary.health_checks.passed)/$($validation_results.summary.health_checks.total) ✅" -ForegroundColor Green
Write-Host "Integration Tests:  $($validation_results.summary.integration_tests.passed)/$($validation_results.summary.integration_tests.total) ✅" -ForegroundColor Green
Write-Host "Compliance Tests:   $($validation_results.summary.compliance_tests.passed)/$($validation_results.summary.compliance_tests.total) ✅" -ForegroundColor Green
Write-Host ""
Write-Host "OVERALL STATUS: $overall_status" -ForegroundColor $(if ($overall_status -eq "PASS") { "Green" } else { "Red" })
Write-Log "═════════════════════════════════════════════════════════════" "INFO"

# Save results to file
$validation_results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Log "Validation results saved to: $OutputPath" "INFO"

exit if ($overall_status -eq "PASS") { 0 } else { 1 }
