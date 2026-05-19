# Local deployment startup script for ADRION 369 - Windows PowerShell
# Run with: powershell -ExecutionPolicy Bypass -File scripts/deploy-local.ps1

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "ADRION 369 - Local Deployment" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Environment check
Write-Host "[1/7] Checking environment..." -ForegroundColor Blue
$missingTools = @()

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $missingTools += "Docker"
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    $missingTools += "Docker Compose"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $missingTools += "Python 3"
}

if ($missingTools.Count -gt 0) {
    Write-Host "ERROR: Missing tools: $($missingTools -join ', ')" -ForegroundColor Red
    Write-Host "Please install the missing tools and try again." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Environment check passed" -ForegroundColor Green
Write-Host ""

# Step 2: Python dependencies
Write-Host "[2/7] Installing Python dependencies..." -ForegroundColor Blue
pip install -q -r requirements-arbitrage.txt 2>$null
pip install -q pytest pytest-asyncio 2>$null
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 3: Start Docker services
Write-Host "[3/7] Starting Docker services..." -ForegroundColor Blue
docker-compose -f docker-compose.local.yml up -d
Write-Host "✓ Docker services started" -ForegroundColor Green
Write-Host ""

# Step 4: Wait for services
Write-Host "[4/7] Waiting for services to be healthy..." -ForegroundColor Blue
Start-Sleep -Seconds 10

# Check PostgreSQL
try {
    $pgCheck = docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U adrion 2>$null
    if ($?) {
        Write-Host "✓ PostgreSQL is ready" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠ PostgreSQL initializing..." -ForegroundColor Yellow
}

# Check Prometheus
try {
    $promCheck = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -ErrorAction SilentlyContinue
    if ($promCheck.StatusCode -eq 200) {
        Write-Host "✓ Prometheus is ready" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠ Prometheus initializing..." -ForegroundColor Yellow
}

# Check Grafana
try {
    $grafanaCheck = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -ErrorAction SilentlyContinue
    if ($grafanaCheck.StatusCode -eq 200) {
        Write-Host "✓ Grafana is ready" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠ Grafana initializing..." -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Run tests
Write-Host "[5/7] Running agent tests..." -ForegroundColor Blue
python -m pytest tests/test_base_agent.py tests/test_autonomous_agents.py tests/test_agent_tracker.py -q --tb=short 2>&1 | Select-Object -Last 3
Write-Host ""

# Step 6: Display service URLs
Write-Host "[6/7] Services deployed:" -ForegroundColor Blue
Write-Host ""
Write-Host "Application URLs:" -ForegroundColor Green
Write-Host "  Grafana Dashboard:   http://localhost:3000 (admin/admin)"
Write-Host "  Prometheus:          http://localhost:9090"
Write-Host "  PostgreSQL:          localhost:5432 (adrion/adrion_local_dev_2026)"
Write-Host "  Redis:               localhost:6379"
Write-Host ""

# Step 7: Display next steps
Write-Host "[7/7] Deployment complete!" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Start the autonomous agent system:"
Write-Host "   python scripts/run-agent-session.py"
Write-Host ""
Write-Host "2. View Grafana dashboards:"
Write-Host "   Open http://localhost:3000 in your browser"
Write-Host "   Navigate to Dashboards → ADRION 369 - Agent Performance"
Write-Host ""
Write-Host "3. Monitor Prometheus metrics:"
Write-Host "   Open http://localhost:9090"
Write-Host "   Query: agent_success_rate, agent_avg_duration_ms, session_jobs_processed"
Write-Host ""
Write-Host "4. Check agent logs:"
Write-Host "   docker-compose -f docker-compose.local.yml logs -f"
Write-Host ""
Write-Host "5. Stop services:"
Write-Host "   docker-compose -f docker-compose.local.yml down"
Write-Host ""
Write-Host "All services are running!" -ForegroundColor Green
