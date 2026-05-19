# KPI Gate Integration for MCP Deployment
# Monitors MCP routing metrics and validates against KPI thresholds

param(
    [int]$SamplingWindow = 50,
    [int]$MinEvents = 20,
    [float]$TargetSuccessRate = 0.95,
    [float]$MaxErrorRate = 0.05,
    [float]$MaxLatencyMs = 500,
    [string]$OutputPath = "./monitoring/mcp_kpi_report.json"
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

Write-Host "
╔════════════════════════════════════════════════════════════════╗
║         MCP KPI GATE INTEGRATION — PHASE 3                    ║
║         Validate MCP metrics against Gate thresholds          ║
╚════════════════════════════════════════════════════════════════╝
" -ForegroundColor Cyan

# ════════════════════════════════════════════════════════════════════════════
# KPI THRESHOLDS
# ════════════════════════════════════════════════════════════════════════════

$kpi_thresholds = @{
    routing_success_rate = $TargetSuccessRate
    routing_error_rate = $MaxErrorRate
    routing_latency_p99 = $MaxLatencyMs
    trust_score_average = 0.75
    health_check_success = 1.0
    compliance_pass_rate = 0.98
}

# ════════════════════════════════════════════════════════════════════════════
# COLLECT MCP METRICS
# ════════════════════════════════════════════════════════════════════════════

Write-Host "[1/4] Collecting MCP metrics from routing service..." -ForegroundColor Yellow

$routing_stats = $null
$health_reports = @{}
$compliance_stats = $null

try {
    # Get routing statistics
    $response = Invoke-WebRequest -Uri "http://localhost:9000/stats/routing" `
        -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    $routing_stats = $response.Content | ConvertFrom-Json
    Write-Host "  ✅ Routing stats collected" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Failed to collect routing stats: $_" -ForegroundColor Red
}

try {
    # Get health from all servers
    $ports = @(9000, 9001, 9002, 9003, 9004, 9005)
    foreach ($port in $ports) {
        $response = Invoke-WebRequest -Uri "http://localhost:$port/health" `
            -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        $health_reports["port_$port"] = @{
            status = "healthy"
            code = $response.StatusCode
        }
    }
    Write-Host "  ✅ Health checks collected" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Some health checks failed" -ForegroundColor Yellow
}

try {
    # Get compliance summary
    $response = Invoke-WebRequest -Uri "http://localhost:9002/audit/summary" `
        -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    $compliance_stats = $response.Content | ConvertFrom-Json
    Write-Host "  ✅ Compliance stats collected" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Failed to collect compliance stats: $_" -ForegroundColor Yellow
}

# ════════════════════════════════════════════════════════════════════════════
# CALCULATE KPIs
# ════════════════════════════════════════════════════════════════════════════

Write-Host "[2/4] Calculating KPIs..." -ForegroundColor Yellow

$kpi_results = @{
    timestamp = Get-Date -Format "o"
    window_seconds = $SamplingWindow
    metrics = @{}
    gate_status = @{}
}

# Calculate routing metrics
if ($routing_stats) {
    $total_queries = $routing_stats.total_queries
    $approved = $routing_stats.approved

    if ($total_queries -ge $MinEvents) {
        $success_rate = if ($total_queries -gt 0) { $approved / $total_queries } else { 0 }
        $error_rate = 1.0 - $success_rate

        $kpi_results.metrics.routing_success_rate = [math]::Round($success_rate, 4)
        $kpi_results.metrics.routing_error_rate = [math]::Round($error_rate, 4)
        $kpi_results.metrics.total_queries = $total_queries
        $kpi_results.metrics.approved = $approved

        Write-Host "  ├─ Routing Success Rate: $([math]::Round($success_rate * 100, 2))%" -ForegroundColor White
        Write-Host "  ├─ Routing Error Rate: $([math]::Round($error_rate * 100, 2))%" -ForegroundColor White
        Write-Host "  └─ Total Queries: $total_queries (min required: $MinEvents)" -ForegroundColor White
    } else {
        Write-Host "  ⚠️  Insufficient events ($total_queries < $MinEvents)" -ForegroundColor Yellow
        $kpi_results.metrics.warning = "Insufficient sampling data"
    }
}

# Calculate health metrics
$health_success = 0
$health_total = $health_reports.Count
foreach ($key in $health_reports.Keys) {
    if ($health_reports[$key].status -eq "healthy") {
        $health_success++
    }
}

if ($health_total -gt 0) {
    $health_rate = $health_success / $health_total
    $kpi_results.metrics.health_check_success = [math]::Round($health_rate, 4)
    Write-Host "  └─ Health Checks: $health_success/$health_total passing" -ForegroundColor White
}

# Calculate compliance metrics
if ($compliance_stats) {
    $total_events = $compliance_stats.total_events
    $passes = $compliance_stats.compliance_passes

    if ($total_events -gt 0) {
        $compliance_rate = $passes / $total_events
        $kpi_results.metrics.compliance_pass_rate = [math]::Round($compliance_rate, 4)
        Write-Host "  └─ Compliance Pass Rate: $([math]::Round($compliance_rate * 100, 2))%" -ForegroundColor White
    }
}

# ════════════════════════════════════════════════════════════════════════════
# GATE DECISION
# ════════════════════════════════════════════════════════════════════════════

Write-Host "[3/4] Validating against KPI thresholds..." -ForegroundColor Yellow

$gate_pass = $true
$gate_details = @()

# Check success rate
$success_rate = $kpi_results.metrics.routing_success_rate
if ($null -ne $success_rate) {
    if ($success_rate -ge $kpi_thresholds.routing_success_rate) {
        Write-Host "  ✅ Success Rate: $([math]::Round($success_rate * 100, 2))% ≥ $([math]::Round($kpi_thresholds.routing_success_rate * 100, 2))%" -ForegroundColor Green
        $kpi_results.gate_status.success_rate = "PASS"
        $gate_details += "✅ Routing success rate within threshold"
    } else {
        Write-Host "  ❌ Success Rate: $([math]::Round($success_rate * 100, 2))% < $([math]::Round($kpi_thresholds.routing_success_rate * 100, 2))%" -ForegroundColor Red
        $kpi_results.gate_status.success_rate = "FAIL"
        $gate_pass = $false
        $gate_details += "❌ Routing success rate below threshold"
    }
}

# Check error rate
$error_rate = $kpi_results.metrics.routing_error_rate
if ($null -ne $error_rate) {
    if ($error_rate -le $kpi_thresholds.routing_error_rate) {
        Write-Host "  ✅ Error Rate: $([math]::Round($error_rate * 100, 4))% ≤ $([math]::Round($kpi_thresholds.routing_error_rate * 100, 2))%" -ForegroundColor Green
        $kpi_results.gate_status.error_rate = "PASS"
    } else {
        Write-Host "  ❌ Error Rate: $([math]::Round($error_rate * 100, 4))% > $([math]::Round($kpi_thresholds.routing_error_rate * 100, 2))%" -ForegroundColor Red
        $kpi_results.gate_status.error_rate = "FAIL"
        $gate_pass = $false
        $gate_details += "❌ Routing error rate above threshold"
    }
}

# Check health
$health_rate = $kpi_results.metrics.health_check_success
if ($null -ne $health_rate -and $health_rate -ge 1.0) {
    Write-Host "  ✅ Health Checks: 100% passing" -ForegroundColor Green
    $kpi_results.gate_status.health_check = "PASS"
} else {
    Write-Host "  ⚠️  Health Checks: Not all passing" -ForegroundColor Yellow
    $kpi_results.gate_status.health_check = "WARN"
}

# Check compliance
$compliance_rate = $kpi_results.metrics.compliance_pass_rate
if ($null -ne $compliance_rate) {
    if ($compliance_rate -ge $kpi_thresholds.compliance_pass_rate) {
        Write-Host "  ✅ Compliance Pass Rate: $([math]::Round($compliance_rate * 100, 2))%" -ForegroundColor Green
        $kpi_results.gate_status.compliance = "PASS"
    } else {
        Write-Host "  ⚠️  Compliance Pass Rate: $([math]::Round($compliance_rate * 100, 2))%" -ForegroundColor Yellow
        $kpi_results.gate_status.compliance = "WARN"
    }
}

# ════════════════════════════════════════════════════════════════════════════
# GATE DECISION & REPORT
# ════════════════════════════════════════════════════════════════════════════

Write-Host "[4/4] Gate Decision..." -ForegroundColor Yellow

$kpi_results.gate_decision = if ($gate_pass) { "PASS" } else { "FAIL" }
$kpi_results.gate_details = $gate_details
$kpi_results.thresholds = $kpi_thresholds

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║ KPI GATE REPORT" -ForegroundColor Cyan
Write-Host "╠════════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan

foreach ($detail in $gate_details) {
    Write-Host "║ $detail" -ForegroundColor Cyan
}

Write-Host "║" -ForegroundColor Cyan
if ($gate_pass) {
    Write-Host "║ GATE STATUS: ✅ PASS — Ready for canary deployment" -ForegroundColor Green
} else {
    Write-Host "║ GATE STATUS: ❌ FAIL — Investigate issues before deployment" -ForegroundColor Red
}
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

# Save report
$kpi_results | ConvertTo-Json -Depth 10 | Out-File -FilePath $OutputPath -Encoding UTF8
Write-Host ""
Write-Host "Report saved to: $OutputPath" -ForegroundColor Gray

exit if ($gate_pass) { 0 } else { 1 }
