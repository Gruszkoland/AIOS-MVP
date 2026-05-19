# MCP Smoke Test Script
# Quick validation of MCP cluster readiness for deployment

param(
    [int]$MaxWaitSeconds = 60,
    [bool]$StopOnFail = $false
)

$ErrorActionPreference = if ($StopOnFail) { "Stop" } else { "Continue" }
$ProgressPreference = "SilentlyContinue"

Write-Host "
╔════════════════════════════════════════════════════════════════╗
║           MCP CLUSTER SMOKE TEST — PHASE 3                    ║
║           Quick validation before canary deployment           ║
╚════════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════════════════

$test_config = @{
    timeout              = 15
    retries              = 3
    wait_between_retries = 2
}

$tests = @(
    @{
        name          = "Router Health"
        url           = "http://localhost:9000/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    },
    @{
        name          = "Vortex Health"
        url           = "http://localhost:9001/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    },
    @{
        name          = "Guardian Health"
        url           = "http://localhost:9002/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    },
    @{
        name          = "Oracle Health"
        url           = "http://localhost:9003/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    },
    @{
        name          = "Genesis Health"
        url           = "http://localhost:9004/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    },
    @{
        name          = "Healer Health"
        url           = "http://localhost:9005/health"
        method        = "GET"
        expected_code = 200
        critical      = $true
    }
)

# ════════════════════════════════════════════════════════════════════════════
# SMOKE TEST EXECUTION
# ════════════════════════════════════════════════════════════════════════════

$passed = 0
$failed = 0
$critical_failed = 0

foreach ($test in $tests) {
    Write-Host "Testing: $($test.name)..." -NoNewline -ForegroundColor White

    $retry_count = 0
    $success = $false

    while ($retry_count -lt $test_config.retries -and -not $success) {
        try {
            $response = Invoke-WebRequest -Uri $test.url `
                -Method $test.method `
                -TimeoutSec $test_config.timeout `
                -UseBasicParsing `
                -ErrorAction Stop

            if ($response.StatusCode -eq $test.expected_code) {
                $success = $true
                Write-Host " ✅ PASS" -ForegroundColor Green
                $passed++
            }
        }
        catch {
            $retry_count++
            if ($retry_count -lt $test_config.retries) {
                Write-Host "." -NoNewline
                Start-Sleep -Seconds $test_config.wait_between_retries
            }
        }
    }

    if (-not $success) {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        $failed++
        if ($test.critical) {
            $critical_failed++
        }
    }
}

# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ SMOKE TEST RESULTS" -ForegroundColor Cyan
Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ Passed:  $passed/$($tests.Count)" -ForegroundColor Cyan
Write-Host "║ Failed:  $failed/$($tests.Count)" -ForegroundColor Cyan
Write-Host "║ Critical Failed: $critical_failed" -ForegroundColor Cyan

if ($critical_failed -eq 0 -and $passed -eq $tests.Count) {
    Write-Host "║ STATUS:  ✅ ALL TESTS PASSED" -ForegroundColor Green
    $exit_code = 0
}
elseif ($critical_failed -eq 0) {
    Write-Host "║ STATUS:  ⚠️  SOME TESTS FAILED (non-critical)" -ForegroundColor Yellow
    $exit_code = 1
}
else {
    Write-Host "║ STATUS:  ❌ CRITICAL FAILURES" -ForegroundColor Red
    $exit_code = 2
}

Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Next steps
if ($exit_code -eq 0) {
    Write-Host "✅ Cluster is ready for testing. Next steps:" -ForegroundColor Green
    Write-Host "   1. Run full validation: .\scripts\mcp-testing\validate-mcp-cluster.ps1" -ForegroundColor Gray
    Write-Host "   2. Execute integration tests: pytest tests/mcp/ -v" -ForegroundColor Gray
    Write-Host "   3. Deploy canary: 5% traffic" -ForegroundColor Gray
}

exit $exit_code
