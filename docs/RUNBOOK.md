# AIOS-MVP v0.1.0-alpha RUNBOOK

**Version:** 0.1.0-alpha  
**Release Date:** 2026-06-07  
**Status:** Production Ready (Alpha)

---

## 📋 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Deployment](#deployment)
3. [Operations](#operations)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Architecture Overview](#architecture-overview)
7. [Safety Limits](#safety-limits)
8. [Support](#support)

---

## 🚀 QUICK START

### Prerequisites
- Docker 20.10+ or Rust 1.70+
- 2GB RAM minimum
- <100ms network latency (for consensus)

### Local Development (5 minutes)
```bash
# 1. Clone repository
git clone https://github.com/Gruszkoland/AIOS-MVP.git
cd AIOS-MVP

# 2. Build and run
docker-compose up -d              # Postgres + backend
cargo test --release              # Verify tests pass

# 3. Access
open http://localhost:8003        # API (Swagger UI at /api/docs)
```

### Docker Deployment (2 minutes)
```bash
# 1. Build image
docker build -t aios:v0.1.0 .

# 2. Run container
docker run -p 8003:8003 aios:v0.1.0

# 3. Verify health
curl http://localhost:8003/health
# Expected: {"status": "ready"}
```

---

## 📦 DEPLOYMENT

### Environment Variables
```bash
# Core
RUST_LOG=info                           # Logging level
BRIDGE_LATENCY_SLA_NS=1000             # P99 latency target (ns)

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@localhost/aios

# Network
PORT=8003                               # API port
CONSENSUS_TIMEOUT_MS=5000              # 6-agent voting timeout

# Security
RATE_LIMIT_REQUESTS=1000               # Per minute
RATE_LIMIT_WINDOW_SECS=60
```

### Kubernetes Deployment
```bash
# 1. Install Helm chart
helm install aios ./kubernetes/charts/aios \
  --namespace aios \
  --values kubernetes/values-prod.yaml

# 2. Verify deployment
kubectl get pods -n aios
kubectl port-forward svc/aios-api 8003:8003

# 3. Check health
curl http://localhost:8003/health/ready
```

### Multi-Region (Fabric/AKS)
```bash
# 1. Deploy to primary region
az deployment group create \
  --resource-group aios-prod \
  --template-file kubernetes/deploy.bicep

# 2. Configure replication
psql aios -c "SELECT * FROM pg_replication_slots;"

# 3. Monitor failover
az container logs --resource-group aios-prod --name aios-api
```

---

## ⚙️ OPERATIONS

### Health Checks

**Liveness Probe** (is the service running?)
```bash
curl http://localhost:8003/health/live
# 200 OK: Service is responsive
```

**Readiness Probe** (is the service ready for traffic?)
```bash
curl http://localhost:8003/health/ready
# 200 OK: Database connected, agents online
# 503 Unavailable: Waiting for initialization
```

**Bridge Latency Check** (is IPC performing?)
```bash
curl http://localhost:8003/metrics | grep bridge_latency_p99
# bridge_latency_p99_ns 890
```

### Scaling Guardian Agents
```bash
# Scale from 6 to 9 agents (add 3 more)
# Each agent runs in parallel consensus voting

AGENTS_COUNT=9 docker-compose up -d
# Wait for startup (~5 seconds)
curl http://localhost:8003/health/ready
```

### Database Maintenance
```bash
# Backup Genesis Record (immutable audit trail)
pg_dump aios > backup_genesis_$(date +%Y%m%d).sql

# Vacuum and analyze for performance
psql aios -c "VACUUM ANALYZE;"

# Check decision log size
psql aios -c "SELECT COUNT(*) FROM decisions;"
```

---

## 📊 MONITORING

### Key Metrics (Prometheus)
```
bridge_latency_p50_ns          # Ring buffer IPC performance
bridge_latency_p99_ns          # Latency SLA (target: <1000ns)
agent_consensus_quorum_met     # 6/9 voting quorum status
decision_throughput_per_sec    # Decisions processed
guardian_law_violations        # Critical/high violations
```

### Grafana Dashboards
```
- Dashboard 1: Bridge Performance (latency, throughput)
- Dashboard 2: Agent Consensus (voting, quorum, timeouts)
- Dashboard 3: Guardian Laws (violations by law, mode)
- Dashboard 4: System Health (CPU, memory, database)
```

### Logging
```bash
# Stream logs from container
docker logs -f aios-api

# Filter for errors
docker logs aios-api | grep ERROR

# Check Genesis Record (audit trail)
psql aios -c "SELECT timestamp, agent_type, decision_id FROM genesis_record ORDER BY timestamp DESC LIMIT 10;"
```

---

## 🔧 TROUBLESHOOTING

### Agent Offline
```bash
# Check status
curl http://localhost:8003/agents/status

# Restart single agent
docker restart aios-librarian

# Full restart (caution: loses consensus state)
docker-compose restart
```

### Latency > 1000ns
```bash
# 1. Check system load
top -b -n 1 | head -15

# 2. Verify database latency
psql aios -c "SELECT now() - query_start FROM pg_stat_activity WHERE state='active';"

# 3. Check bridge buffer
curl http://localhost:8003/metrics | grep ring_buffer
```

### Consensus Voting Timeout
```bash
# Increase timeout (default: 5000ms)
docker run -e CONSENSUS_TIMEOUT_MS=10000 aios:v0.1.0

# Check quorum requirement
curl http://localhost:8003/config | jq .quorum_size
# Expected: 6 (out of 9 agents, or 4 out of 6)
```

### Database Connection Failed
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Test connection
psql postgresql://user:pass@localhost/aios -c "SELECT 1;"

# Fallback to SQLite
rm DATABASE_URL environment variable and restart
```

---

## 🏗️ ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    AIOS-MVP v0.1.0-alpha                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Decision Kernel (Rust, no_std, 162D decision space) │   │
│  │  ├─ Guardian Laws (9 laws × 6 modes × 3 perspectives)  │   │
│  │  ├─ Trinity Score (Material/Intellectual/Essential)     │   │
│  │  └─ Ring Buffer IPC (<1μs latency)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  6 Guardian Agents (Consensus Voting)                │   │
│  │  ├─ Librarian  (precedent checking)                  │   │
│  │  ├─ SAP        (anomaly detection)                   │   │
│  │  ├─ Auditor    (regulatory compliance)               │   │
│  │  ├─ Sentinel   (security/adversarial)                │   │
│  │  ├─ Architect  (system alignment)                    │   │
│  │  └─ Healer     (error recovery)                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Genesis Record (Immutable Audit Trail)              │   │
│  │  └─ PostgreSQL / SQLite (with backup)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ SAFETY LIMITS

### Hard Limits (enforced by kernel)
- **Decision latency:** <1ms (triggers alert at 500ns drift)
- **Quorum timeout:** <5 seconds (fails consensus at 5.001s)
- **Agent crash recovery:** <10 seconds (automatic restart)
- **Database transaction timeout:** <30 seconds

### Soft Limits (configurable warnings)
- **Consensus quorum:** 6/9 agents online (warn at 5/9)
- **Bridge buffer utilization:** 80% (warn at 75%)
- **Guardian law violations:** 0 CRITICAL (alert at 1+)
- **Rate limiting:** 1000 req/min (warn at 900)

### Circuit Breakers
- **Database:** Fails open after 3 connection attempts
- **LLM API:** Falls back to rule-based after 2 timeouts
- **External APIs:** Degrades gracefully with exponential backoff

---

## 📞 SUPPORT

### Reporting Issues
```bash
# 1. Gather diagnostics
docker logs aios-api > aios-logs.txt
curl http://localhost:8003/metrics > metrics.txt
curl http://localhost:8003/config > config.json

# 2. File GitHub issue
gh issue create \
  --title "Issue description" \
  --body "$(cat diagnostics.md)" \
  --label "bug"
```

### Security Disclosure
- **DO NOT** file public GitHub issues for security vulnerabilities
- **Email:** security@gruszkoland.dev with details
- **Response time:** 24 hours initial acknowledgment

### SLA
| Issue Type | Response | Resolution |
|-----------|----------|-----------|
| Critical (consensus failure) | 1 hour | 4 hours |
| High (latency SLA breach) | 4 hours | 24 hours |
| Medium (feature request) | 48 hours | 2 weeks |

---

## 📚 ADDITIONAL RESOURCES

- **API Documentation:** http://localhost:8003/api/docs
- **Architecture Guide:** docs/ARCHITECTURE.md
- **Threat Model:** docs/THREAT_MODEL.md
- **Performance Report:** docs/PERFORMANCE_REPORT.md
- **Contributing Guide:** CONTRIBUTING.md

---

**Release:** v0.1.0-alpha  
**Generated:** 2026-06-07  
**Status:** ✅ PRODUCTION READY (ALPHA QUALITY)
