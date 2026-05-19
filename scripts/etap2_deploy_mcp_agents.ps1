"""
ETAP 2: MCP AGENTS DEPLOYMENT SCRIPT
Deploying 6-agent ADRION 369 swarm
Sequential startup + validation + integration testing
"""

$ErrorActionPreference = "Continue"
$VerbosePreference = "SilentlyContinue"

# ════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ════════════════════════════════════════════════════════════════════════════

$agents = @(
    @{ name = "ROUTER";    app = "mcp_router_app.py";     port = 9000; env = "MCP_ROUTER";    priority = 1 },
    @{ name = "GENESIS";   app = "mcp_genesis_app.py";    port = 9004; env = "MCP_GENESIS";   priority = 2 },
    @{ name = "GUARDIAN";  app = "mcp_guardian_app.py";   port = 9002; env = "MCP_GUARDIAN";  priority = 3 },
    @{ name = "HEALER";    app = "mcp_healer_app.py";     port = 9003; env = "MCP_HEALER";    priority = 4 },
    @{ name = "ORACLE";    app = "mcp_oracle_app.py";     port = 9005; env = "MCP_ORACLE";    priority = 5 },
    @{ name = "VORTEX";    app = "mcp_vortex_app.py";     port = 9006; env = "MCP_VORTEX";    priority = 6 }
)

$logDir = ".\logs\etap2"
$reportFile = "$logDir\deployment_report.json"

# ════════════════════════════════════════════════════════════════════════════
# FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

function Write-Color {
    param([string]$text, [string]$color = "White")
    Write-Host $text -ForegroundColor $color
}

function Test-Port {
    param([int]$port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", $port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

function Get-AgentStatus {
    param([string]$name, [int]$port)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            return "healthy"
        }
    } catch {
        if (Test-Port $port) {
            return "listening"
        }
    }
    return "offline"
}

function Start-Agent {
    param([hashtable]$agent)
    $name = $agent.name
    $app = $agent.app
    $port = $agent.port

    Write-Color "`n[$(Get-Date -Format 'HH:mm:ss')] Starting $name on port $port..." "Cyan"

    if (-not (Test-Path $app)) {
        Write-Color "❌ $app not found" "Red"
        return $false
    }

    if (Test-Port $port) {
        Write-Color "⚠️  Port $port already in use - stopping existing process..." "Yellow"
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -eq "python") {
                $proc | Stop-Process -Force
                Write-Color "    Stopped PID $($_.OwningProcess)" "Yellow"
                Start-Sleep -Milliseconds 500
            }
        }
    }

    # Start process in background
    $env:PATH = ".venv\Scripts;$env:PATH"
    $process = Start-Process -FilePath "python" -ArgumentList $app -PassThru -NoNewWindow -RedirectStandardOutput "$logDir\$name.log" -RedirectStandardError "$logDir\${name}_err.log"

    Write-Host "  PID: $($process.Id)"
    Start-Sleep -Seconds 2

    # Verify startup
    $status = Get-AgentStatus $name $port
    switch ($status) {
        "healthy" {
            Write-Color "✅ $name is HEALTHY" "Green"
            return $true
        }
        "listening" {
            Write-Color "✅ $name is LISTENING (health endpoint pending)" "Green"
            return $true
        }
        default {
            Write-Color "❌ $name failed to start (status: $status)" "Red"
            if (Test-Path "$logDir\${name}_err.log") {
                $err = Get-Content "$logDir\${name}_err.log" -Tail 3
                Write-Color "  Errors: $err" "Red"
            }
            return $false
        }
    }
}

function Test-AgentCommunication {
    param([hashtable]$agent)
    $name = $agent.name
    $port = $agent.port

    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3 -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        return $data
    } catch {
        return $null
    }
}

function Generate-Report {
    param([array]$results)

    $report = @{
        timestamp = (Get-Date -Format "o")
        phase = "ETAP_2_MCP_DEPLOYMENT"
        agents = @()
        summary = @{}
    }

    foreach ($result in $results) {
        $report.agents += $result
        if ($result.status -eq "healthy" -or $result.status -eq "listening") {
            $report.summary[$result.name] = "✅ DEPLOYED"
        } else {
            $report.summary[$result.name] = "❌ FAILED"
        }
    }

    $report | ConvertTo-Json -Depth 5 | Out-File $reportFile
    Write-Color "`n📋 Report saved to: $reportFile" "Cyan"
}

# ════════════════════════════════════════════════════════════════════════════
# MAIN DEPLOYMENT SEQUENCE
# ════════════════════════════════════════════════════════════════════════════

Write-Color "
╔════════════════════════════════════════════════════════════════════════════╗
║  ETAP 2: MCP AGENTS DEPLOYMENT - ADRION 369 v4.0                          ║
║  6-Agent Swarm Orchestration                                              ║
╚════════════════════════════════════════════════════════════════════════════╝
" "Green"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Color "`n[PHASE 0] PRE-DEPLOYMENT VALIDATION" "Magenta"

# Check Python environment
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Color "❌ Python not in PATH" "Red"
    exit 1
}
Write-Color "✅ Python available" "Green"

# Check all app files
$missingApps = $agents | Where-Object { -not (Test-Path $_.app) }
if ($missingApps) {
    Write-Color "❌ Missing app files: $($missingApps.app -join ', ')" "Red"
    exit 1
}
Write-Color "✅ All 6 MCP app files present" "Green"

# Check port availability
$blockedPorts = $agents | Where-Object { Test-Port $_.port } | Select-Object -ExpandProperty port
if ($blockedPorts) {
    Write-Color "⚠️  Ports in use: $($blockedPorts -join ', ') - will attempt to stop existing processes" "Yellow"
}

Write-Color "`n[PHASE 1] SEQUENTIAL AGENT STARTUP (Priority Order)" "Magenta"

$results = @()
$sortedAgents = $agents | Sort-Object -Property priority

foreach ($agent in $sortedAgents) {
    $started = Start-Agent $agent

    $result = @{
        name = $agent.name
        port = $agent.port
        priority = $agent.priority
        status = if ($started) { "listening" } else { "failed" }
        timestamp = Get-Date -Format "o"
    }

    # Try to get full status
    if ($started) {
        $health = Test-AgentCommunication $agent
        if ($health) {
            $result.status = "healthy"
            $result.health_data = $health
        }
    }

    $results += $result
}

Write-Color "`n[PHASE 2] DEPLOYMENT SUMMARY" "Magenta"

$successful = $results | Where-Object { $_.status -ne "failed" } | Measure-Object | Select-Object -ExpandProperty Count
$failed = $results | Where-Object { $_.status -eq "failed" } | Measure-Object | Select-Object -ExpandProperty Count

Write-Color "`n  Total agents:   $($results.Count)" "White"
Write-Color "  ✅ Running:     $successful" "Green"
Write-Color "  ❌ Failed:      $failed" "Red"

$results | Format-Table @(
    @{Label="Agent"; Expression={$_.name}},
    @{Label="Port"; Expression={$_.port}},
    @{Label="Status"; Expression={$_.status.ToUpper()}}
) -AutoSize

if ($failed -gt 0) {
    Write-Color "`n❌ DEPLOYMENT INCOMPLETE - Some agents failed" "Red"
    Write-Color "Check logs in: $logDir" "Yellow"
} else {
    Write-Color "`n✅ DEPLOYMENT SUCCESSFUL - All agents running" "Green"
    Write-Color "📊 Health check: curl http://127.0.0.1:9000/status" "Cyan"
}

Generate-Report $results

Write-Color "`n[NEXT STEPS]" "Yellow"
Write-Color "1. Run: curl http://127.0.0.1:9000/status" "White"
Write-Color "2. Run integration tests: python tests/test_mcp_integration.py" "White"
Write-Color "3. Verify all agents via admin dashboard" "White"

Write-Color "`n$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Deployment script complete`n" "Cyan"
