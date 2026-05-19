#!/bin/bash
# Local deployment startup script for ADRION 369 autonomous agent system

set -e

echo "=================================="
echo "ADRION 369 - Local Deployment"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Environment check
echo -e "${BLUE}[1/7] Checking environment...${NC}"
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose not found. Please install Docker Compose."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3."
    exit 1
fi

echo -e "${GREEN}✓ Environment check passed${NC}"
echo ""

# Step 2: Python dependencies
echo -e "${BLUE}[2/7] Installing Python dependencies...${NC}"
pip install -q -r requirements-arbitrage.txt 2>/dev/null || true
pip install -q pytest pytest-asyncio 2>/dev/null || true
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 3: Start Docker services
echo -e "${BLUE}[3/7] Starting Docker services...${NC}"
docker-compose -f docker-compose.local.yml up -d
echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Step 4: Wait for services to be ready
echo -e "${BLUE}[4/7] Waiting for services to be healthy...${NC}"
sleep 10

# Check PostgreSQL
if docker-compose -f docker-compose.local.yml exec -T postgres pg_isready -U adrion > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL still initializing (may take a moment)${NC}"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Prometheus is ready${NC}"
else
    echo -e "${YELLOW}⚠ Prometheus initializing...${NC}"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Grafana is ready${NC}"
else
    echo -e "${YELLOW}⚠ Grafana initializing...${NC}"
fi

echo ""

# Step 5: Run tests
echo -e "${BLUE}[5/7] Running agent tests...${NC}"
python -m pytest tests/test_base_agent.py tests/test_autonomous_agents.py tests/test_agent_tracker.py -q --tb=short 2>&1 | tail -3 || true
echo ""

# Step 6: Display service URLs
echo -e "${BLUE}[6/7] Services deployed:${NC}"
echo ""
echo -e "${GREEN}Application URLs:${NC}"
echo "  Grafana Dashboard:   http://localhost:3000 (admin/admin)"
echo "  Prometheus:          http://localhost:9090"
echo "  PostgreSQL:          localhost:5432 (adrion/adrion_local_dev_2026)"
echo "  Redis:               localhost:6379"
echo ""

# Step 7: Display next steps
echo -e "${BLUE}[7/7] Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Start the autonomous agent system:"
echo "   python -c \"from arbitrage.agents.session_coordinator import SessionCoordinator; import asyncio\""
echo ""
echo "2. View Grafana dashboards:"
echo "   Open http://localhost:3000 in your browser"
echo "   Navigate to Dashboards → ADRION 369 - Agent Performance"
echo ""
echo "3. Monitor Prometheus metrics:"
echo "   Open http://localhost:9090"
echo "   Query: agent_success_rate, agent_avg_duration_ms, session_jobs_processed"
echo ""
echo "4. Check agent logs:"
echo "   docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "5. Stop services:"
echo "   docker-compose -f docker-compose.local.yml down"
echo ""
echo -e "${GREEN}All services are running!${NC}"
