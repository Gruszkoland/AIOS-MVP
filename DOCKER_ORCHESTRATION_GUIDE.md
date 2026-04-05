# 🚀 ADRION 369 — Complete Docker Orchestration Guide (162D)

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Production-Ready

---

## 📋 Overview

This document covers the **Complete Docker Orchestration Stack** for ADRION 369 (162D system).
It includes **12 integrated services** that work together seamlessly:

| Tier        | Service       | Role                         | Status |
| ----------- | ------------- | ---------------------------- | ------ |
| **Core**    | PostgreSQL    | Genesis Record database      | ✅     |
| **Core**    | N8N           | Workflow orchestration (SAP) | ✅     |
| **Core**    | Ollama        | Local LLM engine (Privacy)   | ✅     |
| **Core**    | Vortex        | 174Hz harmonic engine        | ✅     |
| **App**     | ADRION API    | Main arbitrage engine        | ✅     |
| **App**     | Healer        | Self-healing daemon          | ✅     |
| **Support** | Loki          | Log aggregation              | ✅     |
| **Support** | Promtail      | Log shipping                 | ✅     |
| **Support** | Alert Handler | Slack/PagerDuty webhooks     | ✅     |
| **Support** | Grafana       | Monitoring dashboard         | ✅     |
| **Support** | Prometheus    | Metrics collection           | ✅     |
| **Ingress** | Nginx         | Reverse proxy & TLS          | ✅     |

---

## 🎯 Quick Start

### Option 1: Full Stack (Production)

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369

# Edit .env with your credentials
nano .env

# Start all services
docker-compose -f docker-compose-orchestration.yml up -d

# Verify status
docker-compose -f docker-compose-orchestration.yml ps

# Check logs
docker-compose -f docker-compose-orchestration.yml logs -f
```

### Option 2: Development Only

```bash
# Minimal stack (no monitoring, no backup)
docker-compose -f docker-compose.yml up -d
```

### Option 3: Staging (with monitoring)

```bash
# Production-like but with dev credentials
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📁 Directory Structure

Ensure these directories exist before starting:

```bash
mkdir -p data/{postgres,loki,promtail,ollama,n8n,grafana,prometheus}
mkdir -p monitoring/{loki,promtail,grafana/{dashboards,provisioning/{alerting,dashboards,datasources}}}
mkdir -p scripts/{db,monitoring,backups}
mkdir -p config/nginx/{certs,ssl}
mkdir -p backups logs
```

Create if missing:

```bash
# PostgreSQL initialization script
touch scripts/db/init-postgres.sql

# Loki config
touch monitoring/loki/local-config.yaml

# Promtail config
touch monitoring/promtail/config.yaml

# Prometheus config
touch monitoring/prometheus.yml

# Nginx config (if customizing)
touch config/nginx/nginx.conf
```

---

## 🔧 Prerequisites

### System Requirements

- **Docker Desktop** (or Docker Engine + Docker Compose v2.20+)
- **Disk Space:** 50GB minimum (for data/ollama with models)
- **RAM:** 16GB recommended (8GB minimum)
- **CPU:** 4 cores recommended

### Windows-Specific (WSL2)

```powershell
# Ensure WSL2 backend is enabled for Docker Desktop
docker version

# Expected: Client API version should match Server API
```

### Environment File (.env)

Create or update `.env` with:

```env
# ═════════════════════════════════════════════════════════════════
# CORE CONFIGURATION
# ═════════════════════════════════════════════════════════════════

ENVIRONMENT=production
PROJECT_NAME=ADRION 369
VERSION=1.0.0

# ═════════════════════════════════════════════════════════════════
# DATABASE
# ═════════════════════════════════════════════════════════════════

POSTGRES_USER=adrion
POSTGRES_PASSWORD=your_secure_password_here_CHANGE_THIS
POSTGRES_DB=genesis_record

# ═════════════════════════════════════════════════════════════════
# SECURITY
# ═════════════════════════════════════════════════════════════════

UAP_API_KEY=your-secret-api-key-change-this
JWT_SECRET=your-jwt-secret-change-this-to-random-32-chars
DRM_HMAC_SECRET=your-drm-secret-change-this

# ═════════════════════════════════════════════════════════════════
# N8N ORCHESTRATOR
# ═════════════════════════════════════════════════════════════════

N8N_ADMIN_USER=admin
N8N_ADMIN_PASSWORD=your-n8n-password-change-this
N8N_ENCRYPTION_KEY=your-n8n-encryption-key-random-32-chars

# ═════════════════════════════════════════════════════════════════
# GRAFANA MONITORING
# ═════════════════════════════════════════════════════════════════

GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your-grafana-password-change-this
GRAFANA_ALERT_WEBHOOK_URL=

# ═════════════════════════════════════════════════════════════════
# ALERT HANDLERS (Slack/PagerDuty)
# ═════════════════════════════════════════════════════════════════

SLACK_WEBHOOK_URL=
PAGERDUTY_KEY=

# ═════════════════════════════════════════════════════════════════
# LLM CONFIGURATION
# ═════════════════════════════════════════════════════════════════

LLM_BACKEND=ollama
LLM_MODEL=deepseek-coder-v2:16b
OLLAMA_NUM_PARALLEL=4
OLLAMA_NUM_GPU=1

# ═════════════════════════════════════════════════════════════════
# GPU SUPPORT (Optional, requires NVIDIA)
# ═════════════════════════════════════════════════════════════════

NVIDIA_GPU_COUNT=1
NVIDIA_DEVICE_ID=0

# ═════════════════════════════════════════════════════════════════
# NGINX
# ═════════════════════════════════════════════════════════════════

NGINX_HOST=localhost
NGINX_PORT=80
```

---

## 🚀 Startup Sequence

Services initialize in this exact order (guaranteed by `depends_on`):

### Phase 1: Infrastructure (Parallel)

```
1. postgres:15-alpine                    (start)
   ↓ waits for healthcheck
2. loki:3.1.1                            (start)
   ↓ waits for healthcheck
3. ollama:latest                          (start)
   ↓ waits for healthcheck
4. alert-handler:Dockerfile              (start)
   ↓ waits for healthcheck
```

### Phase 2: Services Depending on Phase 1

```
5. promtail:3.1.1                        (depends_on: loki healthy)
6. n8n:latest                            (depends_on: postgres healthy)
7. vortex-engine:Dockerfile.vortex       (depends_on: postgres healthy)
8. adrion-healer:Dockerfile.healer       (depends_on: postgres healthy)
```

### Phase 3: Application Services

```
9. adrion-api:Dockerfile                 (depends_on: ollama healthy)
10. adrion-backup:Dockerfile.backup      (depends_on: alert-handler healthy)
11. grafana:11.1.4                       (depends_on: loki, alert-handler healthy)
12. prometheus:v2.51.0                   (no deps, auto-start)
```

### Phase 4: Ingress

```
13. adrion-nginx:1.27-alpine             (depends_on: all APIs healthy)
    ↓ Now reverse-proxies all services
```

**Total startup time:** ~3-5 minutes (depending on Ollama model loading)

---

## 🎮 Common Commands

### View Status

```bash
# All services
docker-compose -f docker-compose-orchestration.yml ps

# Specific service
docker-compose -f docker-compose-orchestration.yml ps grafana

# Verbose with logs
docker-compose -f docker-compose-orchestration.yml logs --follow
```

### Manage Specific Service

```bash
# Restart a service
docker-compose -f docker-compose-orchestration.yml restart n8n

# View logs for service
docker-compose -f docker-compose-orchestration.yml logs -f vortex-engine --tail 100

# Execute command in container
docker-compose -f docker-compose-orchestration.yml exec postgres psql -U adrion -d genesis_record
```

### Database Management

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose-orchestration.yml exec postgres psql -U adrion -d genesis_record

# Backup database
docker-compose -f docker-compose-orchestration.yml exec postgres pg_dump -U adrion genesis_record > backup.sql

# Restore database
docker-compose -f docker-compose-orchestration.yml exec -T postgres psql -U adrion genesis_record < backup.sql
```

### View Container Metrics (Real-time)

```bash
# Watch resource usage
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

---

## 🌐 Access Points

Once all services are healthy:

| Service           | URL                    | Credentials         |
| ----------------- | ---------------------- | ------------------- |
| **Grafana**       | http://localhost:3000  | admin / (from .env) |
| **Prometheus**    | http://localhost:9090  | None (read-only)    |
| **N8N**           | http://localhost:5678  | admin / (from .env) |
| **Loki**          | http://localhost:3100  | API only (no UI)    |
| **ADRION API**    | http://localhost:8001  | X-API-Key header    |
| **Vortex Engine** | http://localhost:1740  | Internal only       |
| **Ollama**        | http://localhost:11434 | API only            |
| **Nginx**         | http://localhost:80    | Reverse proxy       |

---

## 🔍 Health Checks

Verify all services are healthy:

```bash
# Check service health via docker
curl http://localhost:3000/api/health               # Grafana
curl http://localhost:9090/-/ready                   # Prometheus
curl http://localhost:5678/healthz                   # N8N
curl http://localhost:3100/ready                     # Loki
curl http://localhost:11434/api/tags                 # Ollama
curl http://localhost:8090/health                    # Alert Handler
curl http://localhost:1740/health                    # Vortex
curl http://localhost:8001/api/arbitrage/status      # ADRION API
```

If any returns error, check logs:

```bash
docker-compose -f docker-compose-orchestration.yml logs <service_name>
```

---

## 🛑 Shutdown

### Graceful Shutdown (recommended)

```bash
# Stop all services (data persists)
docker-compose -f docker-compose-orchestration.yml down

# Output: Stopping adrion-nginx ... done
#         Stopping grafana ... done
#         ...
```

### Complete Cleanup

```bash
# Remove all volumes (WARNING: data loss)
docker-compose -f docker-compose-orchestration.yml down -v

# Remove all containers, volumes, and networks
docker-compose -f docker-compose-orchestration.yml down -v --remove-orphans
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# View detailed logs
docker-compose -f docker-compose-orchestration.yml logs --timestamps

# Check specific service
docker-compose -f docker-compose-orchestration.yml logs postgres | tail -50

# Verify Docker resources
docker system df
```

### Database Connection Errors

```bash
# Test PostgreSQL connectivity
docker-compose -f docker-compose-orchestration.yml exec postgres pg_isready -U adrion

# Check PostgreSQL logs
docker-compose -f docker-compose-orchestration.yml logs postgres
```

### Ollama GPUNot Recognized

```bash
# Check if nvidia-docker is installed
which nvidia-docker

# Verify GPU in container
docker-compose -f docker-compose-orchestration.yml exec ollama nvidia-smi

# If not found, run CPU-only (default fallback works)
```

### Network Issues Between Containers

```bash
# Test inter-container connectivity
docker-compose -f docker-compose-orchestration.yml exec n8n ping postgres

# Check network
docker network ls
docker network inspect adrion-backend
```

---

## 📊 Monitoring & Observability

### View Real-time Logs (Loki)

```bash
# Query logs via Grafana
# 1. Open http://localhost:3000
# 2. Menu > Explore > Select Loki data source
# 3. Query example: {service="adrion-api"}
```

### Custom Dashboards

```bash
# Create in Grafana: http://localhost:3000/d/new
# Data source: Loki (logs), Prometheus (metrics)

# Pre-built dashboards in:
# ./monitoring/grafana/dashboards/
```

### Alert Configuration

```bash
# Edit Grafana alerts:
# http://localhost:3000 > Alerts > Alert Rules

# Test alert delivery:
curl -X POST http://localhost:8090/alert/test?severity=warning
```

---

## 🔄 Updating Services

### Update Single Service

```bash
# Pull latest image
docker-compose -f docker-compose-orchestration.yml pull grafana

# Restart service
docker-compose -f docker-compose-orchestration.yml up -d grafana

# View new logs
docker-compose -f docker-compose-orchestration.yml logs -f grafana
```

### Update All Services

```bash
# Pull all images
docker-compose -f docker-compose-orchestration.yml pull

# Recreate all containers
docker-compose -f docker-compose-orchestration.yml up -d

# Verify all healthy
docker-compose -f docker-compose-orchestration.yml ps
```

---

## 📝 Guardian Laws Compliance

This orchestration stack implements all 9 Guardian Laws:

| Law                     | Implementation                                | Evidence                           |
| ----------------------- | --------------------------------------------- | ---------------------------------- |
| **G1 — Unity**          | Single compose file, coordinated startup      | `depends_on` order maintained      |
| **G2 — Harmony**        | Services communicate via predefined channels  | Network policies in docker-compose |
| **G3 — Rhythm**         | 174Hz Vortex engine maintains pulse           | `VORTEX_PULSE_HZ=174` env var      |
| **G4 — Causality**      | Audit trails via Loki                         | All container stdout → Loki        |
| **G5 — Transparency**   | Full observability (Grafana + Prometheus)     | Metrics on all services            |
| **G6 — Authenticity**   | JWT + API keys + mAPI authentication          | Security env vars in .env          |
| **G7 — Privacy**        | Local-first LLM (Ollama), no external APIs    | `LLM_BACKEND=ollama` default       |
| **G8 — Nonmaleficence** | Safe error handling, graceful degradation     | Health checks on all services      |
| **G9 — Sustainability** | Efficient resources, local-first architecture | CPU/memory limits on each service  |

---

## 🏆 Production Hardening Checklist

- [ ] Update all passwords in `.env` to secure values
- [ ] Configure Slack/PagerDuty webhooks
- [ ] Enable TLS in Nginx (copy certs to `config/nginx/certs/`)
- [ ] Set up Prometheus alerting rules (if needed)
- [ ] Create Grafana dashboards for KPIs
- [ ] Configure log retention (Loki retention_deletes_enabled)
- [ ] Test backup/restore workflow
- [ ] Document custom alert rules
- [ ] Set up external log shipping (if required)
- [ ] Implement secret management (Vault/AWS Secrets Manager)

---

## 📚 Additional Resources

- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [Grafana Documentation](https://grafana.com/docs)
- [Prometheus Queries](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Loki LogQL](https://grafana.com/docs/loki/latest/logql/)
- [N8N Documentation](https://docs.n8n.io)

---

**Author:** ADRION 369 Architect Persona  
**Date:** 2026-04-05  
**Version:** 1.0-PRODUCTION-READY
