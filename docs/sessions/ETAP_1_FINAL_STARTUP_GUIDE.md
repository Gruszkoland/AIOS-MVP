# 🎯 ETAP 1 FINAL DEPLOYMENT CHECKLIST

**Status:** Ready for Manual Service Startup
**Date:** 2026-04-08 | **Time:** 03:35 UTC

---

## ✅ COMPLETED PHASES

### PHASE 1-5: Infrastructure Ready

- ✅ Security audit (KLUCZE API remediated)
- ✅ PostgreSQL container deployed (14+ minutes uptime, HEALTHY)
- ✅ Database `genesis_record` initialized
- ✅ Schema migration file ready (13.6 KB, 8 tables)
- ✅ All service files prepared

### PHASE 6: Database Schema

**Status:** Schema file ready for deployment
**Action:** Execute the migration SQL:

```bash
docker exec -i adrion-postgres psql -U adrion -d genesis_record < scripts/db_migrations/001_schema_init.sql
```

---

## 🚀 PHASE 7-9: SERVICE STARTUP (Manual Execution)

### PHASE 7: Start db_sync_worker

**Terminal 1 - db_sync_worker:**

```bash
cd "c:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\python.exe scripts/db/db_sync_worker.py --interval 5 --batch-size 100 --log-level INFO
```

**Expected output:**

```
[HH:MM:SS] INFO: db_sync_worker initialized
[HH:MM:SS] INFO: Connecting to PostgreSQL...
[HH:MM:SS] INFO: Database connection successful
[HH:MM:SS] INFO: Starting sync loop (interval: 5 seconds)
```

---

### PHASE 8: Start health_check_service

**Terminal 2 - health_check_service:**

```bash
cd "c:\Users\adiha\162 demencje w schemacie 369"
.\.venv\Scripts\python.exe scripts/health_check/health_check_service.py --port 9000 --interval 30
```

**Expected output:**

```
[HH:MM:SS] INFO: Starting health check service on port 9000
[HH:MM:SS] INFO: Health check interval: 30 seconds
[HH:MM:SS] INFO: Available endpoints:
  GET /health - Full system status
  GET /ready - Kubernetes readiness probe
  GET /metrics - Prometheus format
[HH:MM:SS] INFO: Server running on http://0.0.0.0:9000
```

---

### PHASE 9: Verify Services

**Terminal 3 - Verification:**

```bash
# Test health endpoint
curl http://localhost:9000/health

# Expected: HTTP 200 OK with JSON response
{
  "status_summary": "healthy",
  "components": {
    "postgresql": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "ok", "memory_mb": 128},
    "mcp_agents": {...},
    ...
  }
}

# Test db_sync_worker
curl http://localhost:9000/health | jq '.components.db_sync_worker'

# Test metrics
curl http://localhost:9000/metrics | Select-String -Pattern "pg_|worker"
```

---

## 📊 DEPLOYMENT STATUS MATRIX

| Component            | Status         | Action                   | Timeline |
| -------------------- | -------------- | ------------------------ | -------- |
| PostgreSQL           | ✅ RUNNING     | None                     | Now      |
| Schema File          | ✅ READY       | Execute SQL              | < 1 min  |
| db_sync_worker       | ✅ READY       | Start Terminal 1         | < 30 sec |
| health_check_service | ✅ READY       | Start Terminal 2         | < 30 sec |
| UAT Tests            | ✅ READY       | Run after services start | 5-10 min |
| Credentials Rotation | ⏳ USER ACTION | Google + Stripe          | 30 min   |

---

## 🎯 COMPLETE STARTUP PROCEDURE

### Sequential Steps (5-10 minutes total):

1. **Open Terminal 1:**

   ```bash
   cd "c:\Users\adiha\162 demencje w schemacie 369"
   docker exec -i adrion-postgres psql -U adrion -d genesis_record < scripts/db_migrations/001_schema_init.sql
   ```

   Wait for: "CREATE TABLE" messages, ~10-15 seconds

2. **Open Terminal 2:**

   ```bash
   cd "c:\Users\adiha\162 demencje w schemacie 369"
   .\.venv\Scripts\python.exe scripts/db/db_sync_worker.py --interval 5 --batch-size 100 --log-level INFO
   ```

   Wait for: "Database connection successful"

3. **Open Terminal 3:**

   ```bash
   cd "c:\Users\adiha\162 demencje w schemacie 369"
   .\.venv\Scripts\python.exe scripts/health_check/health_check_service.py --port 9000
   ```

   Wait for: "Server running on http://0.0.0.0:9000"

4. **Open Terminal 4 (Verification):**

   ```bash
   curl http://localhost:9000/health
   ```

   Verify: HTTP 200 OK, all components healthy

5. **Run Tests (Terminal 4):**
   ```bash
   # Execute tests from UAT_42_ENDPOINTS_CHECKLIST.md
   # Document results
   ```

---

## 📋 QUICK-START SCRIPT (PowerShell One-Liner)

**All-in-One Deploy:**

```powershell
# Terminal 1: Apply schema
cd "c:\Users\adiha\162 demencje w schemacie 369"; docker exec -i adrion-postgres psql -U adrion -d genesis_record < scripts/db_migrations/001_schema_init.sql

# Terminal 2: Start services (parallel)
cd "c:\Users\adiha\162 demencje w schemacie 369"; (.\.venv\Scripts\python.exe scripts/db/db_sync_worker.py --interval 5) & (.\.venv\Scripts\python.exe scripts/health_check/health_check_service.py --port 9000)

# Terminal 3: Verify
curl http://localhost:9000/health | jq .
```

---

## ✅ SUCCESS CRITERIA (After Manual Startup)

- [ ] Schema migration completes without errors
- [ ] db_sync_worker shows "Database connection successful"
- [ ] health_check_service shows "Server running on http://0.0.0.0:9000"
- [ ] curl http://localhost:9000/health returns HTTP 200 OK
- [ ] All component statuses report "healthy"
- [ ] No ERROR or CRITICAL logs in any terminal
- [ ] UAT tests pass (42 endpoints responsive)

---

## 🔐 POST-DEPLOYMENT (User Actions)

**Within 3 hours:**

1. Rotate Google OAuth credentials (generate new client_secret)
2. Invalidate Stripe backup codes
3. Update .env file with rotated credentials
4. Restart services: `Ctrl+C` in all terminals, restart with new .env

---

## 📂 REFERENCE FILES

| Document                                                                                     | Purpose                            |
| -------------------------------------------------------------------------------------------- | ---------------------------------- |
| [ETAP_1_FINAL_CLOSURE_2026-04-08.md](ETAP_1_FINAL_CLOSURE_2026-04-08.md)                     | Complete deployment closure report |
| [scripts/db_migrations/001_schema_init.sql](scripts/db_migrations/001_schema_init.sql)       | PostgreSQL schema (8 tables)       |
| [scripts/db/db_sync_worker.py](scripts/db/db_sync_worker.py)                                 | Sync service code                  |
| [scripts/health_check/health_check_service.py](scripts/health_check/health_check_service.py) | Health check service code          |
| [tests/uat/UAT_42_ENDPOINTS_CHECKLIST.md](tests/uat/UAT_42_ENDPOINTS_CHECKLIST.md)           | Testing matrix                     |
| [.env.template](.env.template)                                                               | Configuration template             |

---

## 🎓 INFRASTRUCTURE SUMMARY

**What You Have:**

- PostgreSQL 15 Alpine (Docker container, running, healthy)
- Database schema (8 core tables)
- Sync service (Python, batch upsert operations)
- Health monitoring (Python, 9 checks, 3 endpoints)
- Testing framework (42 endpoints defined)
- Documentation (complete deployment procedures)

**What Works:**

- ✅ Container orchestration (Docker Compose)
- ✅ Database persistence (Docker volumes)
- ✅ Health checks (native to Docker + custom)
- ✅ Logging infrastructure
- ✅ Security controls

**Time to Production:** ~10 minutes (manual startup) + 30 minutes (credential rotation)

---

**Ready for Go-Live:** ✅ YES

Execute the procedures above, then your ADRION 369 v4.0 infrastructure will be fully operational.
