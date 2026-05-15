# 🚀 PLAN WDROŻENIA — ADRION 369 Orchestration Stack

**Data opracowania:** 14.05.2026  
**Autor:** Autonomous Deployment Agent  
**Status:** 📋 ZAPLANOWANE  
**Priorytet:** 🔴 KRYTYCZNY — Infrastructure Deployment  

---

## 📊 EXECUTIVE SUMMARY

| Metrika | Wartość |
|---------|---------|
| **Komponenty do wdrożenia** | 12 usług Docker |
| **Liczba baz danych** | 1 PostgreSQL + 3 media (Loki, Ollama, Promtail) |
| **Porty sieciowe** | 11 portów (80, 443, 5432, 3000, 5678, 8000-8003, 11434, 3100, 9090) |
| **Szacunkowy czas** | 45-60 minut (w tym health checks) |
| **Zależności** | Docker Desktop, Docker Compose v2.0+, 16GB RAM min. |
| **Krytyczne komponenty** | PostgreSQL (root dependency), n8n, Ollama, Nginx Ingress |

---

## 🎯 CEL WDROŻENIA

Uruchomić kompletny stos ADRION 369 z 12 usługami w środowisku lokalnym/staging:

```
┌─────────────────────────────────────────────────────────┐
│         ADRION 369 ORCHESTRATION STACK (12 usług)       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TIER 0 (Foundation)                                    │
│    └─ PostgreSQL:5432 (genesis_record)                 │
│                                                         │
│  TIER 1 (Observability)                                │
│    ├─ Loki:3100 (logs)                                 │
│    ├─ Promtail (log shipper)                           │
│    └─ Grafana:3000 (dashboards)                        │
│                                                         │
│  TIER 2 (Core Engines)                                 │
│    ├─ Ollama:11434 (LLM)                               │
│    ├─ n8n:5678 (workflows)                             │
│    ├─ Vortex:8003 (orchestration @174Hz)               │
│    └─ Adrion-Healer (self-healing daemon)              │
│                                                         │
│  TIER 3 (APIs & Services)                              │
│    ├─ Arbitrage API:8001                               │
│    ├─ Backend API:8002                                 │
│    ├─ Alert Handler (webhooks)                         │
│    └─ Backup Automation                                │
│                                                         │
│  TIER 4 (Ingress)                                      │
│    └─ Nginx Reverse Proxy (80, 443)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Wymagane cechy

✅ Obsługa 32 Gems + Chronos (#33 meta-guardian)  
✅ Guardian Laws v11 enforcement  
✅ Genesis Record hash chain  
✅ CVC (Cumulative Violation Counter) state machine  
✅ LTM (Long-Term Memory) with K0 restoration  
✅ TSPA baseline scores  
✅ Prometheus metrics collection  
✅ Real-time Grafana dashboards (7 panels)  
✅ Alerting rules (11 alerts)  

---

## 📋 KOMPONENTY DO WDROŻENIA

### Tier 0: Database Foundation (MUST BE FIRST)

| # | Usługa | Image | Port | Health Check | Wnętrze |
|---|--------|-------|------|--------------|---------|
| 1 | **PostgreSQL** | `postgres:15-alpine` | 5432 | `pg_isready` | SQL init scripts |

**Krytyczność:** 🔴 BLOCKING — wszystkie inne usługi zależą od PostgreSQL

---

### Tier 1: Log Infrastructure

| # | Usługa | Image | Port | Health Check | Timeout |
|---|--------|-------|------|--------------|---------|
| 2 | **Loki** | `grafana/loki:3.1.1` | 3100 | `GET /ready` | 20s start_period |
| 3 | **Promtail** | `grafana/promtail:3.1.1` | — | — | Bind to docker.sock |

---

### Tier 2: Core Engines

| # | Usługa | Image | Port | Depends On | Notes |
|---|--------|-------|------|-----------|-------|
| 4 | **Ollama** | `ollama/ollama:latest` | 11434 | Standalone | GPU support (OLLAMA_NUM_GPU) |
| 5 | **n8n** | Custom build | 5678 | PostgreSQL | Workflow orchestration (SAP) |
| 6 | **Vortex-Engine** | Custom build | 8003 | PostgreSQL | 174Hz harmonic orchestration |
| 7 | **Adrion-Healer** | Custom build | — | PostgreSQL | Self-healing daemon (background) |

---

### Tier 3: APIs & Services

| # | Usługa | Image | Port | Depends On | Role |
|---|--------|-------|------|-----------|------|
| 8 | **Arbitrage API** | Custom build | 8001 | PostgreSQL | Main arbitrage engine |
| 9 | **Backend API** | Custom build | 8002 | PostgreSQL | Support services |
| 10 | **Alert-Handler** | Custom Dockerfile | — | — | Slack/PagerDuty webhooks |
| 11 | **Adrion-Backup** | Custom Dockerfile | — | Alert-Handler | Backup automation |

---

### Tier 4: Ingress & Monitoring

| # | Usługa | Image | Port | Depends On | Role |
|---|--------|-------|------|-----------|------|
| 12 | **Nginx** | `nginx:alpine` | 80, 443 | All APIs | Reverse proxy ingress |
| 13 | **Grafana** | `grafana/grafana:latest` | 3000 | Loki, Alert-Handler | Dashboards + alerting |
| 14 | **Prometheus** | `prom/prometheus:latest` | 9090 | — | Metrics collection |

---

## 🔧 PROCEDURE WDROŻENIA

### FAZA 1: Pre-Deployment Verification (15 min)

**Cel:** Weryfikacja środowiska i gotowości do wdrożenia

#### ✅ Step 1.1 — Walidacja środowiska

```bash
# Sprawdź wersje
docker --version          # powinno być 24.0.0+
docker-compose --version  # powinno być v2.0.0+
git --version            # powinno być 2.30+

# Sprawdź dostępną pamięć (min. 16GB)
wmic OS get totalvisiblememorylength /format:list | findstr "^Value" | for /f "tokens=2 delims==" %a in ('findstr "^Value"') do @echo %a

# Sprawdź wolne miejsce (min. 50GB)
wmic logicaldisk where name="C:" get freespace /format:list
```

**Oczekiwany rezultat:**

```
Docker version 24.0.0 or higher ✅
Docker Compose v2.0.0 or higher ✅
Total Memory ≥ 16GB ✅
Free Disk ≥ 50GB ✅
```

#### ✅ Step 1.2 — Konfiguracja zmiennych środowiskowych

```bash
cd "C:\Users\adiha\.1_Projekty\162 demencje w schemacie 369"

# Skopiuj .env.template → .env
cp .env.template .env

# Edytuj .env z następującymi wartościami OBOWIĄZKOWE:
# POSTGRES_USER=adrion
# POSTGRES_PASSWORD=<generate-secure-password>  🔐
# POSTGRES_DB=genesis_record
# ENV=staging  (LUB production, jeśli wdrażasz na prod)
# LOG_LEVEL=INFO
# AUDIT_DB_PATH=/var/log/audit.db
# API_KEY_SALT=<generate-32-char-hex>  🔐
```

**⚠️ WAŻNE:** Nigdy nie commituj `.env` do Git — zawiera sekrety!

#### ✅ Step 1.3 — Health Check Networks

```bash
# Sprawdź że portów nie zajmują inne procesy
netstat -ano | findstr ":5432"   # PostgreSQL
netstat -ano | findstr ":3100"   # Loki
netstat -ano | findstr ":5678"   # n8n
netstat -ano | findstr ":8001"   # Arbitrage API
netstat -ano | findstr ":8003"   # Vortex
netstat -ano | findstr ":11434"  # Ollama
netstat -ano | findstr ":3000"   # Grafana
netstat -ano | findstr ":9090"   # Prometheus
```

**Oczekiwany rezultat:**  
Brak procesu na żadnym z portów — wszystkie porty wolne ✅

#### ✅ Step 1.4 — Backup danych (jeśli istnieją)

```bash
# Jeśli PostgreSQL już istnieje, zrób backup
docker exec adrion-postgres pg_dump -U adrion genesis_record \
  > backup_genesis_$(date +%Y%m%d_%H%M%S).sql
```

---

### FAZA 2: Docker Compose Initialization (30 min)

**Cel:** Uruchomić stos usług w zdefiniowanej kolejności

#### ✅ Step 2.1 — Build custom images

```bash
# Przejdź do folderu głównego
cd "C:\Users\adiha\.1_Projekty\162 demencje w schemacie 369"

# Build images (jeśli dockerfile'y nie są prebuilded)
docker-compose -f docker-compose-orchestration.yml build --parallel
```

**Oczekiwany rezultat:**

```
Building n8n ... done
Building vortex-engine ... done
Building adrion-healer ... done
Building arbitrage-api ... done
Building backend-api ... done
Building alert-handler ... done
Building adrion-backup ... done
Building nginx-ingress ... done

8 images built successfully ✅
```

#### ✅ Step 2.2 — Start Docker Compose stack

```bash
# Start wszystkich 12+ usług w tle (-d = detached)
docker-compose -f docker-compose-orchestration.yml up -d

# Pokaż status kontenerów
docker-compose -f docker-compose-orchestration.yml ps
```

**Oczekiwany rezultat:**

```
NAME                  STATUS              PORTS
adrion-postgres       Up (healthy)        5432
adrion-loki           Up (healthy)        3100
adrion-promtail       Up                  -
adrion-ollama         Up                  11434
adrion-n8n            Up (healthy)        5678
vortex-engine         Up (healthy)        8003
adrion-healer         Up                  -
arbitrage-api         Up (healthy)        8001
backend-api           Up (healthy)        8002
alert-handler         Up                  -
adrion-backup         Up                  -
adrion-nginx          Up                  80, 443
grafana-adrion        Up (healthy)        3000
prometheus-adrion     Up (healthy)        9090

STATUS: All 12+ containers running ✅
```

#### ✅ Step 2.3 — Wait for health checks (10 min)

```bash
# Monitoruj health status
docker-compose -f docker-compose-orchestration.yml ps --format="{{.Name}}\t{{.Status}}"

# Lub sprawdzaj logi po kolei
docker-compose -f docker-compose-orchestration.yml logs -f postgres
docker-compose -f docker-compose-orchestration.yml logs -f loki
docker-compose -f docker-compose-orchestration.yml logs -f n8n
```

**Czekaj aż:**

- ✅ PostgreSQL: `(healthy)` — ~40s
- ✅ Loki: `(healthy)` — ~20s
- ✅ n8n: `(healthy)` — ~60s
- ✅ Grafana: `(healthy)` — ~30s

**⏱️ KRYTYCZE:** Start Period dla PostgreSQL to **40 sekund** — czekaj cierpliwie!

---

### FAZA 3: Smoke Tests & Verification (10 min)

**Cel:** Potwierdzić że wszystkie usługi odpowiadają poprawnie

#### ✅ Step 3.1 — Health checks na każdej usłudze

```bash
# PostgreSQL
psql -h localhost -U adrion -d genesis_record -c "SELECT 1;"
# Oczekiwane: 1 row (connection successful)

# Loki
curl http://localhost:3100/ready
# Oczekiwane: 200 OK

# Ollama
curl http://localhost:11434/api/tags
# Oczekiwane: {"models": []}

# n8n
curl http://localhost:5678/healthz
# Oczekiwane: 200 OK

# Arbitrage API
curl http://localhost:8001/health
# Oczekiwane: {"status": "healthy"}

# Vortex Engine
curl http://localhost:8003/status
# Oczekiwane: {"status": "running", "frequency": "174Hz"}

# Grafana
curl http://localhost:3000/api/health
# Oczekiwane: {"commit": "...", "database": "ok"}

# Prometheus
curl http://localhost:9090/-/healthy
# Oczekiwane: Prometheus is healthy.
```

**Oczekiwany rezultat:** Wszystkie endpointy zwracają 200 OK ✅

#### ✅ Step 3.2 — Run smoke test suite

```bash
# Z folderu głównego
cd "C:\Users\adiha\.1_Projekty\162 demencje w schemacie 369"

# Uruchom smoke tests
python scripts/smoke-test.py

# Lub z Powershell
python -m pytest tests/smoke_tests.py -v --tb=short
```

**Oczekiwany rezultat:**

```
Test 1: ADRION 369 Health Check ✅ PASS
Test 2: Guardian Checkpoint ✅ PASS
Test 3: CVC Status ✅ PASS
Test 4: LTM Profile ✅ PASS
Test 5: Genesis Record Integrity ✅ PASS
Test 6: Prometheus Metrics ✅ PASS
Test 7: n8n Health Check ✅ PASS
Test 8: Docker Compose Services ✅ PASS

SUMMARY: 8/8 PASS ✅
```

#### ✅ Step 3.3 — Verify data persistence

```bash
# Sprawdź czy PostgreSQL ma danych
docker exec adrion-postgres psql -U adrion -d genesis_record -c "
  SELECT tablename FROM pg_tables WHERE schemaname='public';
"

# Sprawdź czy Genesis Records istnieją
docker exec adrion-postgres psql -U adrion -d genesis_record -c "
  SELECT COUNT(*) FROM genesis_records;
"

# Sprawdź czy Loki zbiera logi
curl -s 'http://localhost:3100/loki/api/v1/query?query={job="adrion"}' | head -20
```

**Oczekiwany rezultat:** Tablice mają dane, Genesis Records → N records found ✅

---

### FAZA 4: Integration Tests & Validation (15 min)

**Cel:** Walidować integrację między komponentami

#### ✅ Step 4.1 — API Integration Test

```bash
# Test Arbitrage → Vortex → n8n loop
curl -X POST http://localhost:8001/api/mcp/invoke/router \
  -H "Content-Type: application/json" \
  -d '{
    "cmd": "invoke_workflow",
    "flags": ["SYS:DEBUG"],
    "params": {
      "workflow_id": "test-orchestration",
      "payload": {"test": "data"}
    }
  }'

# Oczekiwana odpowiedź:
# {
#   "status": "approved",
#   "approval_source": "guardian_checkpoint",
#   "cvc_state": "GREEN",
#   "genesis_record": "hash_xxx",
#   "timestamp": "2026-05-14T14:30:00Z"
# }
```

#### ✅ Step 4.2 — Guardian Laws Checkpoint

```bash
# Test Guardian Laws v11 evaluation
curl -X POST http://localhost:8001/api/mcp/guardian/checkpoint \
  -H "Content-Type: application/json" \
  -d '{
    "job": "smoke-test",
    "analysis": "Integration test payload",
    "context": {"component": "vortex-engine"},
    "flags": []
  }'

# Oczekiwana odpowiedź:
# {
#   "approval": true,
#   "compliance": {"G1": "OK", "G2": "OK", ...},
#   "laws_evaluated": 11,
#   "violations": []
# }
```

#### ✅ Step 4.3 — Metrics Collection

```bash
# Pobierz Prometheus metrics
curl http://localhost:9090/api/v1/targets

# Pokaż active alerts
curl http://localhost:9090/api/v1/rules | grep -i alert

# Pokaż current metric values
curl 'http://localhost:9090/api/v1/query?query=up'
```

**Oczekiwany rezultat:**

```
All targets UP ✅
Alerting rules loaded ✅
11 alert rules active ✅
```

#### ✅ Step 4.4 — Grafana Dashboard Access

```bash
# Otwórz w przeglądarce
curl -I http://localhost:3000/api/health
# Oczekiwane: 200 OK

# Zaloguj się: admin / admin
# Dashboards dostępne:
#   • CVC Timeline
#   • CVC State Gauge
#   • Guardian Laws Heatmap
#   • Genesis Record Throughput
#   • TSPA Score Distribution
#   • LTM Activity Log
#   • Critical Violations Alert
```

---

## 🗂️ KOMPONENTY DO WERYFIKACJI

### Bazy danych & Media

| Component | Path | Size | Health Check |
|-----------|------|------|--------------|
| PostgreSQL Data | `postgres_data/` | ~500MB | `SELECT 1` |
| Loki Data | `loki_data/` | ~100MB | `GET /ready` |
| Loki WAL | `loki_wal/` | ~50MB | Check `.wl` files |
| Promtail Positions | `promtail_positions/` | ~5MB | Check timestamps |
| Ollama Models | `ollama_data/` | ~10GB+ | `GET /api/tags` |

### Environment Variables (obowiązkowe)

```bash
# Database
POSTGRES_USER=adrion
POSTGRES_PASSWORD=<SECURE>  🔐
POSTGRES_DB=genesis_record

# Application
ENV=staging  (LUB production)
LOG_LEVEL=INFO
AUDIT_DB_PATH=/var/log/audit.db

# Security
API_KEY_SALT=<32-char-hex>  🔐
JWT_SECRET=<32-char-hex>    🔐
ENCRYPTION_KEY=<32-char-hex> 🔐

# Ollama
OLLAMA_NUM_PARALLEL=4
OLLAMA_NUM_GPU=1  (jeśli masz GPU)

# n8n
N8N_ENCRYPTION_KEY=<32-char-hex> 🔐
N8N_USER_MANAGEMENT_JWT_SECRET=<32-char-hex> 🔐
```

---

## 📊 MACIERZ RYZYKA I MITYGACJA

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|-------------------|-------|----------|
| PostgreSQL health check timeout | 🟡 MEDIUM | 🔴 CRITICAL | Zwiększ `start_period` do 60s, zwolnij Docker resources |
| Port conflict (80, 443, 5432) | 🟡 MEDIUM | 🔴 CRITICAL | `netstat` check w Step 1.3, kill conflicting processes |
| Insufficient memory (< 16GB) | 🟠 LOW | 🟡 HIGH | Sprawdzić RAM w Step 1.1, zmniejszyć container limits |
| Ollama model pull stuck | 🟠 LOW | 🟡 HIGH | Timeout 5min, pull models ręcznie: `ollama pull llama2` |
| n8n initialization slow | 🟠 LOW | 🟡 HIGH | Czekać 90s, monitor: `docker logs adrion-n8n` |
| Secrets leakage (.env) | 🟡 MEDIUM | 🔴 CRITICAL | `.env` w .gitignore, rotate passwords po deployment |
| Network isolation issues | 🟢 LOW | 🟡 HIGH | Test curl commands w Step 3.1, check docker network |

---

## ✅ CHECKLIST WDROŻENIA

### Pre-Deployment

- [ ] Walidacja Docker Desktop version (24.0.0+)
- [ ] Walidacja Docker Compose version (v2.0.0+)
- [ ] Sprawdzenie dostępnej pamięci (min. 16GB)
- [ ] Sprawdzenie wolnego miejsca dysku (min. 50GB)
- [ ] Brak konfliktów portów (netstat check)
- [ ] Przygotowanie .env z bezpiecznymi hasłami 🔐
- [ ] Backup istniejących danych (jeśli applicable)
- [ ] Review docker-compose-orchestration.yml

### Deployment Phase 1

- [ ] Build custom Docker images
- [ ] Start Docker Compose stack (`up -d`)
- [ ] Monitorowanie health status (log monitoring)
- [ ] Czekanie na postgresql (40s+ start_period)
- [ ] Czekanie na loki (20s+ start_period)
- [ ] Czekanie na n8n (60s+ start_period)

### Deployment Phase 2

- [ ] Health checks na wszystkich 14 endpoints
- [ ] PostgreSQL connectivity test (`psql`)
- [ ] Loki readiness test (`GET /ready`)
- [ ] n8n healthz test (`GET /healthz`)
- [ ] Ollama tags test (`GET /api/tags`)
- [ ] Arbitrage API health test (`GET /health`)
- [ ] Vortex status test (`GET /status`)
- [ ] Grafana API test (`GET /api/health`)
- [ ] Prometheus healthiness test (`GET /-/healthy`)

### Deployment Phase 3

- [ ] Run smoke test suite (8 tests, all PASS)
- [ ] Verify data persistence in PostgreSQL
- [ ] Verify Loki log collection
- [ ] Verify Genesis Records created
- [ ] API Integration test (POST /invoke)
- [ ] Guardian Laws checkpoint (POST /checkpoint)
- [ ] Metrics collection verification
- [ ] Grafana dashboard accessibility

### Post-Deployment

- [ ] Document deployment time & metrics
- [ ] Set monitoring alerts in Grafana
- [ ] Create runbook dla common issues
- [ ] Backup configuration (.env, docker-compose files)
- [ ] Notify team of deployment completion
- [ ] Schedule follow-up health check (T+1h, T+4h, T+24h)

### Production Hardening (jeśli applicable)

- [ ] Enable SSL/TLS certificates (nginx)
- [ ] Configure authentication (n8n, Grafana, Prometheus)
- [ ] Setup log rotation policy (Loki, Promtail)
- [ ] Configure backup retention (PostgreSQL backups)
- [ ] Setup PagerDuty / Slack integrations (Alert Handler)
- [ ] Performance tuning (PostgreSQL shared_buffers, Ollama GPU allocation)

---

## 🎯 SUCCESS CRITERIA

✅ **Wszystkie 14 kontenerów uruchomione i zdrowe**

```bash
docker-compose ps | grep -c "Up"  # Powinno być: 14
```

✅ **Wszystkie health checks PASS**

```bash
curl http://localhost:8001/health && \
curl http://localhost:5678/healthz && \
curl http://localhost:3000/api/health
# Wszystkie 200 OK
```

✅ **Smoke test suite 8/8 PASS**

```bash
python scripts/smoke-test.py  # 0 FAILURES
```

✅ **PostgreSQL zawiera dane**

```bash
docker exec adrion-postgres psql -U adrion -d genesis_record -c "SELECT COUNT(*) FROM genesis_records;"
# Result: N rows (N > 0)
```

✅ **Grafana dostępna z 7 dashboards**

```bash
curl http://localhost:3000/api/dashboards/db | grep -c "dashboard"
# Result: 7+ dashboards
```

✅ **Prometheus scraping 13+ metrics**

```bash
curl 'http://localhost:9090/api/v1/query?query=up' | grep -c "job"
# Result: 13+ metric families
```

---

## 📞 TROUBLESHOOTING

### Problem: PostgreSQL health check timeout

**Symptom:** `postgres: (unhealthy) - [WinError 10061]`

**Fix:**

```bash
# Zwiększ start_period
docker-compose down
# Edit docker-compose-orchestration.yml: start_period: 60s (zmień z 40s)
docker-compose up -d postgres
docker-compose ps postgres  # Wait 60s
```

### Problem: Port already in use

**Symptom:** `bind: address already in use [:]:5432`

**Fix:**

```bash
# Znajdź proces zajmujący port
netstat -ano | findstr ":5432"
# Kill proces: taskkill /PID <PID> /F
# Lub zmień port w docker-compose (5432:5433)
```

### Problem: Insufficient memory

**Symptom:** Kontener crash-uje po starcie, Out of Memory logs

**Fix:**

```bash
# Zmniejsz resource limits w docker-compose-orchestration.yml:
# deploy:
#   resources:
#     limits:
#       memory: 256m  (zmienić z 512m)
```

### Problem: n8n slow startup

**Symptom:** n8n still starting after 5 min

**Fix:**

```bash
docker logs adrion-n8n | tail -50  # Sprawdź logi
# Czekaj 90-120 sekund (first-time initialization)
# Jeśli dalej problem, restart: docker-compose restart n8n
```

---

## 📈 POST-DEPLOYMENT MONITORING

### Day 1 (T+4h)

- [ ] CPU usage < 80%
- [ ] Memory usage < 75%
- [ ] No critical alerts in Grafana
- [ ] All services in `(healthy)` state
- [ ] Log volume ingestion ~100MB/hour

### Day 2 (T+24h)

- [ ] Database size < expected threshold
- [ ] No anomalies in TSPA scores
- [ ] Genesis Records continuously appended
- [ ] Backup automation working (check logs)
- [ ] CVC state = GREEN (no violations)

### Week 1 (T+7d)

- [ ] Database size growth linear
- [ ] All 11 Guardian Laws evaluating correctly
- [ ] Prometheus retention policy working
- [ ] Grafana dashboards responsive
- [ ] Alerting rules triggered correctly

---

## 📝 NOTES & ASSUMPTIONS

1. **Docker Desktop** zainstalowany na Windows (with WSL2 backend)
2. **Network configuration:** All services on `adrion-backend` bridge network
3. **Volume persistence:** Dane przechowywane w named volumes (nie bind mounts)
4. **Logging driver:** json-file (max-size: 20m, max-file: 5)
5. **Restart policy:** `unless-stopped` (auto-restart po Docker daemon restart)
6. **Time sync:** System clock zsynchronizowany (Genesis Record hashes wymagają timestampów)

---

**Raport wdrażania:** [Deployment Report](./ADRION-369-Deployment-Report-14-05-2026.md) (created post-deployment)

**Ostatnia aktualizacja:** 14.05.2026 15:45 UTC

---

*Plan przygotowany przez Autonomous Deployment Agent na podstawie TEST_REPORT.md (2026-05-12) i aktualnej struktury projektu.*
