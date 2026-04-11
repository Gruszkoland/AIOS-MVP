# Local Deployment Startup Guide

**Status:** Ready to deploy (all prerequisites met)

## Prerequisites Verification ✅

- [x] Docker Desktop installed: v29.1.3
- [x] Docker Compose available: v2.40.3
- [x] Python 3.11+ available
- [x] Git repository initialized
- [x] Local compose file: `docker-compose.local.yml`
- [x] Autonomous agent system: 94 tests passing
- [x] Security fixes applied: P0-1, P0-4, P1-5
- [x] Architecture documented: v4.0 complete

## Quick Start (Windows)

### Step 1: Start Docker Desktop

```powershell
# Open Docker Desktop application (GUI)
# Or: Start-Service Docker (if installed as service)
# Wait 30-60 seconds for daemon to be ready
```

### Step 2: Verify Docker is Running

```powershell
docker ps
# Should show empty list (no containers running yet)
```

### Step 3: Start Local Stack

```powershell
cd "c:\Users\adiha\162 demencje w schemacie 369"
docker-compose -f docker-compose.local.yml up -d
```

**Expected services:**

- PostgreSQL (5432)
- Prometheus (9090)
- Grafana (3000)
- Redis (6379)

### Step 4: Verify Services

```powershell
docker-compose -f docker-compose.local.yml ps

# Expected output:
# NAME              STATUS
# adrion-postgres   Up (healthy)
# adrion-prometheus Up (healthy)
# adrion-grafana    Up (healthy)
# adrion-redis      Up (healthy)
```

### Step 5: Run Deployment Verification

```powershell
python scripts/verify-deployment.py

# Expected: 7/7 checks passed
```

### Step 6: Start Agent Session

```powershell
python scripts/run-agent-session.py --num-analyzers 4

# Expected: Session completes with metrics
```

### Step 7: Access Monitoring Dashboards

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Agent Performance Dashboard:** Pre-configured

## Troubleshooting

### Docker Daemon Not Starting

**Error:** `open //./pipe/dockerDesktopLinuxEngine: file not found`

**Solution:**

1. Open Docker Desktop application manually
2. Wait 60 seconds for WSL2 backend to initialize
3. Run `docker ps` to verify daemon is ready
4. Then run `docker-compose up -d`

### Services Not Healthy

```powershell
# Check service logs
docker-compose -f docker-compose.local.yml logs -f <service>

# Common service names:
# adrion-postgres, adrion-prometheus, adrion-grafana, adrion-redis
```

### PostgreSQL Connection Failed

```powershell
# Check PostgreSQL is accepting connections
docker-compose -f docker-compose.local.yml exec postgres pg_isready -U adrion
```

### Memory Issues

If Docker runs out of memory, increase Docker Desktop allocation:

1. Docker Desktop → Settings → Resources
2. Set Memory ≥ 8GB (recommended)
3. Set CPUs ≥ 4 cores
4. Restart Docker

## Testing & Validation

### Run Test Suite

```powershell
# Autonomous agents (52 tests)
python -m pytest tests/test_autonomous_agents.py tests/test_base_agent.py -q

# UAP API tests
python -m pytest uap/tests/test_api.py -q

# Expected: All passing
```

### Sample Agent Execution

```powershell
python -c "
from arbitrage.agents.session_coordinator import SessionCoordinator
import asyncio

async def test():
    coordinator = SessionCoordinator('test-001', num_analyzers=2)
    result = await coordinator.orchestrate(filters={}, max_duration_seconds=5)
    print(f'Status: {result[\"summary\"].get(\"status\")}')
    print(f'Jobs processed: {result[\"summary\"].get(\"jobs_processed\")}')

asyncio.run(test())
"
```

### Performance Check

```powershell
# Monitor system during agent execution
docker stats --no-stream

# Expected CPU/Memory allocation within reasonable limits
```

## Next Steps After Deployment

1. **Access Grafana Dashboard**
   - Open: http://localhost:3000
   - Explore: Agent Performance dashboard
   - Monitor: Trinity/Hexagon/Guardian metrics

2. **Run Comprehensive Tests**
   - Full test suite: `pytest tests/ -q --cov=arbitrage`
   - UAP tests: `pytest uap/tests/ -q`
   - Coverage gate: ≥80%

3. **Verify Local vs Sequential Timing**
   - Run: `python scripts/run-agent-session.py --num-analyzers 1` (baseline)
   - Run: `python scripts/run-agent-session.py --num-analyzers 4` (parallel)
   - Compare: Should see ~2-3x speedup with 4 workers

4. **Export Metrics**
   - Results saved to: `reports/local-sessions/`
   - Format: JSON with performance analysis
   - Includes: Bottleneck detection, health status

## Production Readiness Checklist

- [x] Security: SQL injection fix, credentials not in git
- [x] Architecture: v4.0 documented, decision engine complete
- [x] Testing: 52 agent tests passing, security tests added
- [x] Monitoring: Prometheus + Grafana configured
- [x] Logging: JSON structured logs, Genesis Record enabled
- [x] Deployment: Docker Compose stack provided
- [x] Documentation: LOCAL_DEPLOYMENT_GUIDE.md complete

**Status:** ✅ Ready for local deployment and performance testing

---

**For help:** See `docs/LOCAL_DEPLOYMENT_GUIDE.md` (comprehensive 500+ line guide)
