# ⚡ QUICK START GUIDE — ADRION 369 DEPLOYMENT

**Szybki start w 15 minut** | Pełny wdrażanie w 30h

---

## 🎯 SUPER SHORT VERSION (5 MIN)

```bash
# 1. Aktivuj environment
cd "C:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\Activate.ps1

# 2. Build Docker
docker build -t adrion-api:latest .
docker build -f Dockerfile.genesis-mcp -t genesis-mcp:latest .
docker build -f Dockerfile.mcp-router -t mcp-router:latest .

# 3. Start stack
docker compose -f docker-compose.prod.yml up -d

# 4. Check health
curl http://localhost:9000/health
curl http://localhost:9004/health

# 5. Run tests
pytest tests/ -v --tb=short

# 6. View results
Start-Process ".\htmlcov\index.html"
```

**Status:** ✅ Ready to go!

---

## 📋 EXECUTION CHECKLIST (30h Deployment)

### DAY 1 — Setup & Testing (12h)

- [ ] **08:00** — Prep environment (1h)

  ```bash
  # Activate Python, verify imports
  .\.venv\Scripts\Activate.ps1
  pytest --version
  docker --version
  ```

- [ ] **09:00** — Build Docker images (2h)

  ```bash
  # Build 7 images in parallel
  docker build -t adrion-api:latest .
  docker build -f Dockerfile.genesis-mcp -t genesis-mcp:latest .
  docker build -f Dockerfile.guardian-mcp -t guardian-mcp:latest .
  docker build -f Dockerfile.mcp-router -t mcp-router:latest .
  ```

- [ ] **11:00** — Start stack (0.5h)

  ```bash
  docker compose -f docker-compose.prod.yml up -d
  docker compose ps  # Check all healthy
  ```

- [ ] **11:30** — Health checks (1h)

  ```bash
  curl http://localhost:9000/health
  curl http://localhost:9004/health
  curl http://localhost:8001/api/arbitrage/status
  ```

- [ ] **12:30** — Run tests (3h)

  ```bash
  pytest tests/ -v --tb=short --cov=arbitrage,uap,mcp_servers
  ```

- [ ] **15:30** — Review results (4h)
  ```bash
  # Analyze failures, prepare P0 fixes
  pytest tests/ --json-report --json-report-file=results.json
  python scripts/analyze_failures.py results.json
  ```

### DAY 2 — P0 Fixes (16h)

- [ ] **08:00** — Genesis endpoints (6h)
  - Implement `/events`, `/state`, `/history`, `/replay`
  - Test each endpoint
  - Expected result: 5/5 endpoints working ✅

- [ ] **14:00** — Performance optimization (8h)
  - Profile MCP latency
  - Add caching + async I/O
  - Target: <200ms all endpoints
  - Test: Latency should drop 10x

- [ ] **22:00** — Test coverage push (12h)
  - Add 60+ unit tests
  - Add 30+ integration tests
  - Target: 80%+ coverage
  - Expected: Arbitrage 80%, UAP 75%, MCP 70%

### DAY 2 (Cont.) — Validation (4h)

- [ ] **10:00** — Regression testing

  ```bash
  pytest tests/ -v --json-report
  # Expected: 90%+ success (up from 30%)
  ```

- [ ] **11:30** — Final checks

  ```bash
  # Run pre-deployment checklist
  powershell -File scripts/final_deployment_checklist.ps1
  ```

- [ ] **12:30** — Approve deployment
  ```bash
  # If all green:
  Write-Host "✅ APPROVED FOR PRODUCTION"
  ```

---

## 🔗 KEY FILES REFERENCE

| Dokument           | Link                                                                       | Cel                      |
| ------------------ | -------------------------------------------------------------------------- | ------------------------ |
| **Pełna Analiza**  | [PEŁNA_ANALIZA_ADRION369_20260408.md](PEŁNA_ANALIZA_ADRION369_20260408.md) | Architektura + status    |
| **Plan Wdrażania** | [PLAN_WDRAŻANIA_PHASE1_20260408.md](PLAN_WDRAŻANIA_PHASE1_20260408.md)     | Krok po kroku instrukcje |
| **Docker Compose** | [docker-compose.prod.yml](docker-compose.prod.yml)                         | Prod stack config        |
| **Testy**          | [pytest.ini](pytest.ini)                                                   | Test runner config       |
| **Konfiguracja**   | [config/personas.yml](config/personas.yml)                                 | Agent personalities      |

---

## ⚡ POWER COMMANDS

### Diagnostic Commands

```bash
# Check all services
docker compose ps

# View logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs -f adrion-api

# Check network
docker network ls
docker network inspect adrion_default

# Check volumes
docker volume ls

# Health check all MCP agents
@("9000","9001","9002","9003","9004","9005") | ForEach-Object {
    $port = $_
    Write-Host -NoNewline "Port $port: "
    curl -s http://localhost:$port/health | Select-String -Quiet '"status"' ? "✅" : "❌"
}
```

### Test Commands

```bash
# Run specific test file
pytest tests/test_trinity.py -v

# Run specific test class
pytest tests/test_trinity.py::TestTrinity -v

# Run specific test function
pytest tests/test_trinity.py::TestTrinity::test_material_score -v

# Run with coverage
pytest tests/ --cov=arbitrage --cov-report=html

# Run only fast tests (skip slow)
pytest tests/ -m "not slow" -v

# Run smoke tests only
pytest tests/ -m smoke -v

# Debug mode (stop on first failure)
pytest tests/ -x -v

# Verbose output
pytest tests/ -vv --tb=long

# Show print statements
pytest tests/ -v -s
```

### Docker Commands

```bash
# Build single image
docker build -t adrion-api:latest .

# Build specific Dockerfile
docker build -f Dockerfile.genesis-mcp -t genesis-mcp:latest .

# Start services
docker compose up -d

# Stop services (keep containers)
docker compose stop

# Stop and remove containers
docker compose down

# Remove volumes too (careful!)
docker compose down -v

# Restart service
docker compose restart adrion-api

# View resource usage
docker stats

# Prune unused images
docker image prune -a

# Prune unused containers
docker container prune
```

---

## 🚨 QUICK TROUBLESHOOTING

### "Tests not working"

```bash
# 1. Verify Ollama running
docker ps | grep -i ollama

# 2. Check Ollama health
curl http://localhost:11434/api/health

# 3. Restart all services
docker compose down
docker compose up -d

# 4. Re-run tests
pytest tests/ -v --tb=short
```

### "MCP endpoints slow"

```bash
# 1. Check Ollama CPU/memory
docker stats

# 2. Reduce load
# Edit .env: set LLM_BACKEND=offline (no actual LLM calls)

# 3. Restart MCP services
docker compose restart mcp-router mcp-genesis
```

### "Database connection error"

```bash
# 1. Check Postgres
docker compose logs postgres

# 2. Verify credentials in .env
cat .env | grep DB_

# 3. Reset database
docker compose exec postgres psql -U postgres -c "DROP DATABASE adrion; CREATE DATABASE adrion;"

# 4. Re-run migrations
python scripts/db/migrate.py
```

### "Docker build fails"

```bash
# 1. Clear docker cache
docker builder prune

# 2. Build with no cache
docker build --no-cache -t adrion-api:latest .

# 3. Check Dockerfile syntax
docker build --dry-run -t adrion-api:latest .

# 4. View build logs
docker buildx build --progress=plain -t adrion-api:latest .
```

---

## 🎯 SUCCESS CRITERIA

### Before Fixes

- [ ] Tests: 30% ❌
- [ ] Coverage: 35% ❌
- [ ] Latency: 2.3s ❌
- [ ] Genesis: 1/5 endpoints ❌
- [ ] Compliance: 78% 🟡

### After Fixes (Target)

- [ ] Tests: 90%+ ✅
- [ ] Coverage: 80%+ ✅
- [ ] Latency: <200ms ✅
- [ ] Genesis: 5/5 endpoints ✅
- [ ] Compliance: 95%+ ✅

**SUCCESS = All after-fix criteria met**

---

## 📞 EMERGENCY CONTACTS

If something breaks:

1. **Check logs first:**

   ```bash
   docker compose logs -f --tail=100
   ```

2. **Restart services:**

   ```bash
   docker compose restart
   ```

3. **Last resort - rollback:**

   ```bash
   docker compose down
   git checkout main
   docker compose up -d
   ```

4. **Nuclear option - restore from backup:**
   ```bash
   # Restore from Genesis Record
   cp "Genesis Record\06_SECURITY_BACKUPS\docker-compose.prod.yml" .
   docker compose up -d
   ```

---

## 📊 ESTIMATED EFFORT

| Task                     | Time     | Priority |
| ------------------------ | -------- | -------- |
| Setup environment        | 1h       | P0       |
| Docker build             | 2h       | P0       |
| Test suite run           | 3h       | P0       |
| Genesis implementation   | 6h       | P0       |
| Performance optimization | 8h       | P0       |
| Test coverage push       | 12h      | P0       |
| Final validation         | 2h       | P0       |
| **TOTAL**                | **~34h** | —        |

**Estimated window:** Dzień 1 (8h) + Dzień 2 (20h) + Contingency (6h)

---

## ✅ GO/NO-GO DECISION

**Ready to deploy if:**

- ✅ All 90%+ tests passing
- ✅ Coverage 80%+
- ✅ Genesis all 5 endpoints
- ✅ MCP latency <200ms
- ✅ Compliance >90%
- ✅ Pre-deployment checklist passed

**Status:** ⏳ Pending P0 fixes

---

**PREPARED BY:** ADRION 369 Master Orchestrator
**DATE:** 2026-04-08
**VERSION:** 1.0-QUICK-START
**NEXT STEPS:** Execute PLAN_WDRAŻANIA_PHASE1_20260408.md

🚀 **Gotowy do implementacji!**
