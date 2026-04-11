# 🚀 ETAP 1: COMPLETE DEPLOYMENT GUIDE

**Status:** Ready for Execution
**Components:** PostgreSQL + db_sync_worker + health_check_service + UAT
**Prerequisites:** Docker Desktop must be running
**Timeline:** ~10-15 minutes

---

## ⚠️ CURRENT BLOCKER

**Docker Desktop is not running** - Required to start PostgreSQL container.

### Quick Fix

1. **Start Docker Desktop:**
   - Windows: Click Desktop shortcut or `C:\Program Files\Docker\Docker\Docker Desktop.exe`
   - Or: Open PowerShell and run:

   ```powershell
   Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
   # Wait 30-60 seconds for initialization
   ```

2. **Verify Docker is ready:**
   ```powershell
   docker ps
   docker-compose --version
   ```

---

## 📋 ETAP 1 EXECUTION STEPS

### Phase 1: PostgreSQL Initialization (5 minutes)

```powershell
cd "c:\Users\adiha\162 demencje w schemacie 369"

# Step 1: Start PostgreSQL container
Write-Host "▶️  Starting PostgreSQL..." -ForegroundColor Cyan
docker-compose up -d postgres

# Step 2: Wait for health check
Start-Sleep -Seconds 5
docker ps --filter "name=adrion-postgres" --format "table {{.Names}}\t{{.Status}}"

# Step 3: Verify connection
docker exec adrion-postgres pg_isready -U adrion -d genesis_record
```

**Expected Output:**

```
adrion-postgres   Up 10 seconds (healthy)
accepting connections
```

### Phase 2: Apply Database Schema (2 minutes)

```powershell
# Step 1: Check migration file exists
Test-Path "scripts/db_migrations/001_schema_init.sql"  # Should be True

# Step 2: Apply migration
$sqlFile = Get-Content "scripts/db_migrations/001_schema_init.sql" -Raw
docker exec -i adrion-postgres psql -U adrion -d genesis_record << EOF
$sqlFile
EOF

# Step 3: Verify tables created
docker exec adrion-postgres psql -U adrion -d genesis_record -c "\dt"
```

**Expected Output:**

```
          List of relations
 Schema |       Name       | Type  |  Owner
--------+------------------+-------+--------
 public | agents           | table | adrion
 public | api_keys         | table | adrion
 public | audit_log        | table | adrion
 public | checkpoints      | table | adrion
 public | events           | table | adrion
 public | performance_metrics | table | adrion
 public | sessions         | table | adrion
 public | tasks            | table | adrion
(8 rows)
```

### Phase 3: Start Background Services (3 minutes)

**Terminal 1: db_sync_worker**

```powershell
cd "c:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\python.exe scripts/db/db_sync_worker.py `
  --interval 5 `
  --batch-size 100 `
  --log-level INFO

# Expected output:
# [2026-04-08 15:30:00] INFO: db_sync_worker initialized
# [2026-04-08 15:30:00] INFO: Connecting to PostgreSQL...
# [2026-04-08 15:30:01] INFO: Database connection successful
```

**Terminal 2: health_check_service**

```powershell
cd "c:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\python.exe scripts/health_check/health_check_service.py `
  --port 9000 `
  --interval 30

# Expected output:
# [2026-04-08 15:31:00] INFO: Starting health check service on port 9000
# [2026-04-08 15:31:00] INFO: Endpoints available at:
#   /health - Full system status
#   /ready - Kubernetes readiness probe
#   /metrics - Prometheus format
```

### Phase 4: Verification (3 minutes)

**Terminal 3: Run verification commands**

```powershell
# Check database health
curl -s http://localhost:9000/health | jq '.postgres'

# Check all services
curl -s http://localhost:9000/health | jq '.summary'

# Get metrics
curl -s http://localhost:9000/metrics | Select-String -Pattern "pg_|redis_" | Select-Object -First 10

# Test sync worker logs
Get-Content logs/db_sync_worker.log -Tail 10 -Wait
```

---

## 📃 TEST MATRIX (UAT 42 Endpoints)

**Location:** `tests/uat/UAT_42_ENDPOINTS_CHECKLIST.md`

After services are running, execute:

```powershell
# Run health endpoint test
$headers = @{"X-API-Key" = "local-dev-key-123"}
$response = Invoke-WebRequest -Uri "http://localhost:9000/health" -Headers $headers

# Expected: 200 OK with JSON body
$response.StatusCode -eq 200  # Should be True
$response.Content | ConvertFrom-Json | Select-Object status_summary
```

---

## 🔍 MONITORING DURING EXECUTION

### PostgreSQL Logs

```powershell
docker-compose logs -f postgres | Select-Object -Last 20
```

### Application Logs

```powershell
Get-Content "logs/db_sync_worker.log" -Wait -Tail 5
Get-Content "logs/health_check_service.log" -Wait -Tail 5
```

### Container Status

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## ✅ SUCCESS CRITERIA (Go-Live Checklist)

- [ ] PostgreSQL container running and healthy
- [ ] 8 database tables created (verified via `\dt`)
- [ ] db_sync_worker connected to database
- [ ] health_check_service running on port 9000
- [ ] `/health` endpoint returns 200 OK
- [ ] `/metrics` endpoint shows all services
- [ ] All 42 endpoints tested (UAT checklist)
- [ ] No critical errors in logs

---

## 🛑 TROUBLESHOOTING

### Issue: "Cannot connect to Docker daemon"

**Solution:** Start Docker Desktop first

```powershell
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Start-Sleep -Seconds 60
docker ps  # Verify connection
```

### Issue: "Port 5432 already in use"

**Solution:** Stop existing container

```powershell
docker-compose down
# Wait 5 seconds
docker-compose up -d postgres
```

### Issue: "psql: command not found"

**Solution:** Use docker exec instead of local psql

```powershell
# Instead of: psql -U adrion -d genesis_record
# Use: docker exec adrion-postgres psql -U adrion -d genesis_record
```

### Issue: "db_sync_worker: ModuleNotFoundError"

**Solution:** Activate virtual environment

```powershell
cd "c:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\Activate.ps1
pip install psycopg2-binary click asyncio  # If needed
```

---

## 📁 FILES CREATED THIS SESSION

| File                                                                                         | Purpose                     | Status   |
| -------------------------------------------------------------------------------------------- | --------------------------- | -------- |
| [scripts/db_migrations/001_schema_init.sql](scripts/db_migrations/001_schema_init.sql)       | PostgreSQL schema           | ✅ Ready |
| [scripts/db/db_sync_worker.py](scripts/db/db_sync_worker.py)                                 | RAM→DB sync daemon          | ✅ Ready |
| [scripts/health_check/health_check_service.py](scripts/health_check/health_check_service.py) | System health monitoring    | ✅ Ready |
| [tests/uat/UAT_42_ENDPOINTS_CHECKLIST.md](tests/uat/UAT_42_ENDPOINTS_CHECKLIST.md)           | Testing matrix              | ✅ Ready |
| [docs/SSL_CERTIFICATE_DEPLOYMENT.md](docs/SSL_CERTIFICATE_DEPLOYMENT.md)                     | HTTPS setup guide           | ✅ Ready |
| [.env.template](.env.template)                                                               | Secrets template            | ✅ Ready |
| [ETAP_1_DEPLOY.ps1](ETAP_1_DEPLOY.ps1)                                                       | Automated deployment script | ✅ Ready |

---

## 🔐 SECURITY HANDOFF

**Completed (This Session):**

- ✅ KLUCZE API files moved to Genesis Record/06_SECURITY_BACKUPS
- ✅ stripe_backup_code.txt secured
- ✅ SECURITY_INCIDENT_REPORT_2026-04-08.md generated
- ✅ Git history scan (no secrets found)

**User Action Required:**

- ⏳ Rotate Google OAuth secrets (client_secret refresh)
- ⏳ Invalidate Stripe backup codes
- ⏳ Update `.env` with new credentials

---

## 📊 CHECKPOINT SUMMARY

**PHASES COMPLETED (This Session):**

1. ✅ **PHASE 1 - SECURITY:** Exposed API keys secured
2. ✅ **PHASE 2 - SCHEMA:** PostgreSQL schema created (8 tables, indexes, roles)
3. ✅ **PHASE 3 - SYNC:** db_sync_worker ready (batch upsert, health checks)
4. ✅ **PHASE 4 - HEALTH:** health_check_service ready (9 checks, 3 endpoints)
5. ✅ **PHASE 5 - UAT:** Test matrix created (42 endpoints across 6 MCP servers)
6. ✅ **PHASE 6 - SSL:** HTTPS deployment guide documentation (Let's Encrypt + Nginx)

**STAT**US: All ETAP 1 files generated, awaiting Docker startup and execution.

---

## 🎯 NEXT: Execution Timeline

1. **Immediate (Today):**
   - [ ] Start Docker Desktop
   - [ ] Execute Phase 1-2 (PostgreSQL + Schema)
   - [ ] Verify with `docker ps` + `\dt` commands

2. **30 minutes later:**
   - [ ] Execute Phase 3-4 (Start services)
   - [ ] Test endpoints via `curl /health`

3. **1 hour total:**
   - [ ] Execute Phase 5 (UAT tests)
   - [ ] Document results in UAT_42_ENDPOINTS_CHECKLIST.md

4. **Credential rotation (parallel):**
   - [ ] User rotates Google credentials
   - [ ] User invalidates Stripe codes
   - [ ] Update `.env` file

---

**ETAP 1 Ready for Go-Live** ✅
**All infrastructure files generated and committed**
**Awaiting: Docker Desktop + Manual credential rotation**
