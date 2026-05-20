# ShieldOS Local Setup Guide — ADRION 369

Version: 1.0 | Updated: 2026-05-20 | Target: 5-minute local setup

---

## Overview

ShieldOS is the hermetic enclave layer for ADRION 369. It provides:

- Zero-trust API key separation (per-service keys, never shared)
- Isolated Docker network (`adrion-hermetic`) with no host socket access
- All 6 MCP servers (ports 9000-9005) for AI orchestration
- PostgreSQL 15 + Redis 7 infrastructure with health checks
- LocalStack for AWS service simulation (no real AWS calls in dev)
- Hermetic verification tool with score 0-100

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python3 --version` |
| Docker | 24.0+ | `docker --version` |
| Docker Compose | v2 plugin | `docker compose version` |
| Go | 1.22+ (optional) | `go version` |

Notes:
- No `sudo` required. Add your user to the `docker` group on Linux: `sudo usermod -aG docker $USER`
- Windows: Docker Desktop 4.28+ with WSL2 backend recommended
- Go is optional. It is only needed to build the Vortex binary locally.

---

## Quick Start (5 minutes)

### Step 1: Clone and enter project

```bash
git clone https://github.com/Gruszkoland/adrion-369.git
cd adrion-369
```

### Step 2: Run ShieldOS setup

```bash
python scripts/setup_shieldos_local.py
```

This script:
- Validates Python 3.11+, Docker, and Docker Compose
- Creates `.env` from `.env.example` (with CHANGE_ME placeholders)
- Starts PostgreSQL and Redis containers (idempotent)
- Writes `.mcp.json` for Claude Code MCP server discovery
- Updates `.vscode/settings.json` with MCP server URLs
- Runs smoke tests against all services
- Prints a hermetic score

Expected output:

```
==============================================================
  ShieldOS Local Setup — Summary
==============================================================
  Status:           COMPLETE
  Hermetic Score:   95/100
  Steps OK:         7
  Steps Warn:       0
  Steps Failed:     0
  Audit Log:        logs/shieldos_setup_20260520_....jsonl

  MCP Servers:      0/6 accessible
    [--] mcp-router          http://localhost:9000/health
    [--] vortex-mcp          http://localhost:9001/health
    ...
  (MCP servers not accessible yet — start them in Step 4)

  Next steps:
  1. Fill in CHANGE_ME values in .env
  2. python scripts/verify_shieldos_hermetic.py
  3. docker compose -f docker-compose.local.yml up -d
  4. http://localhost:8003  (Flask API)
  5. http://localhost:9000/health (MCP Router)
==============================================================
```

### Step 3: Fill in required secrets

Edit `.env` — find and replace all `CHANGE_ME` placeholders:

```bash
# Required minimum for local dev
POSTGRES_PASSWORD=your_local_password
UAP_API_KEY=local-dev-key-at-least-32-chars
JWT_SECRET=local-dev-jwt-at-least-32-chars00
DRM_HMAC_SECRET=local-dev-drm-at-least-32-chars
```

Secrets you can leave empty for local dev (offline mode):
- `OPENROUTER_API_KEY` — LLM falls back to `mock` mode
- `APIFY_API_TOKEN` — scraping is disabled
- `STRIPE_*` — payment routes are disabled

### Step 4: Start all services

Infrastructure only (fast, recommended for development):

```bash
docker compose -f docker-compose.local.yml up -d postgres redis
```

Full stack with MCP servers and monitoring:

```bash
docker compose -f docker-compose.local.yml up -d
```

Check service status:

```bash
docker compose -f docker-compose.local.yml ps
docker compose -f docker-compose.local.yml logs -f mcp-router
```

### Step 5: Start the Flask API

```bash
python wsgi.py
# http://localhost:8003
```

Or with the UAP orchestrator:

```bash
python wsgi.py &
python uap/backend/api.py
# Flask: http://localhost:8003
# UAP:   http://localhost:8002
```

### Step 6: Verify hermetic posture

```bash
python scripts/verify_shieldos_hermetic.py
```

Target score: 90+. The script exits with code 0 on success.

To enforce a minimum score threshold:

```bash
python scripts/verify_shieldos_hermetic.py --min-score 85
```

---

## Service Map

| Service | Port | Health URL | Description |
|---------|------|-----------|-------------|
| Flask API | 8003 | `http://localhost:8003/health` | Main application |
| UAP Orchestrator | 8002 | `http://localhost:8002/health` | AI persona manager |
| MCP Router | 9000 | `http://localhost:9000/health` | Central arbitration |
| Vortex MCP | 9001 | `http://localhost:9001/health` | 174Hz orchestration |
| Guardian MCP | 9002 | `http://localhost:9002/health` | Security + 9 Laws |
| Oracle MCP | 9003 | `http://localhost:9003/health` | 162D routing |
| Genesis MCP | 9004 | `http://localhost:9004/health` | State + RAG |
| Healer MCP | 9005 | `http://localhost:9005/health` | Recovery monitoring |
| PostgreSQL | 5432 | `docker exec adrion-postgres pg_isready -U adrion` | Primary database |
| Redis | 6379 | `docker exec adrion-redis redis-cli ping` | Cache + inter-agent |
| LocalStack | 4566 | `http://localhost:4566/_localstack/health` | AWS simulation |
| Prometheus | 9090 | `http://localhost:9090/-/healthy` | Metrics |
| Grafana | 3000 | `http://localhost:3000/api/health` | Dashboards |

---

## Architecture (local dev)

```
┌─────────────────────────────────────────────────────────────┐
│  Browser / VS Code / curl                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (port-mapped)
┌──────────────────────────▼──────────────────────────────────┐
│  adrion-hermetic (Docker bridge 172.28.0.0/24)              │
│                                                             │
│  Flask :8003 ──► Guardian Laws ──► Trinity Score            │
│       │                │                                    │
│       ▼                ▼                                    │
│  UAP :8002    PostgreSQL :5432   Redis :6379                 │
│                                                             │
│  MCP Router :9000                                           │
│    ├── Vortex :9001   (174Hz, EBDI state)                   │
│    ├── Guardian :9002 (9 Laws enforcement)                  │
│    ├── Oracle :9003   (162D decision routing)               │
│    ├── Genesis :9004  (RAG, session state)                  │
│    └── Healer :9005   (auto-recovery)                       │
│                                                             │
│  LocalStack :4566 (S3, SQS, SecretsManager)                 │
│  Prometheus :9090 / Grafana :3000                           │
└─────────────────────────────────────────────────────────────┘
  NO docker.sock | NO DOCKER_HOST | Per-service API keys
```

---

## Idempotency

The setup script is safe to run multiple times:

```bash
# First run: creates .env, starts containers, writes .mcp.json
python scripts/setup_shieldos_local.py

# Second run: skips unchanged steps, detects running containers
python scripts/setup_shieldos_local.py
# Output: [SKIP] generate_env: .env already exists
# Output: [SKIP] write_mcp_config: .mcp.json unchanged
```

Force re-create `.env`:

```bash
python scripts/setup_shieldos_local.py --force-env
```

Skip container startup (containers already running):

```bash
python scripts/setup_shieldos_local.py --skip-containers
```

---

## Verification Checklist

Run after initial setup to confirm everything works:

```bash
# 1. Hermetic score >= 90
python scripts/verify_shieldos_hermetic.py

# 2. PostgreSQL accessible
docker exec adrion-postgres pg_isready -U adrion

# 3. Redis accessible
docker exec adrion-redis redis-cli ping
# Expected: PONG

# 4. Flask API health
curl http://localhost:8003/health
# Expected: {"status": "healthy", ...}

# 5. MCP Router health (if started)
curl http://localhost:9000/health

# 6. Python tests pass
python -m pytest tests/ -q --tb=short

# 7. No docker.sock mounts anywhere
grep -r "docker.sock" docker-compose.local.yml
# Expected: no output
```

---

## Troubleshooting

### "Docker daemon not accessible"

Linux:
```bash
sudo usermod -aG docker $USER
newgrp docker
docker info
```

Windows: Ensure Docker Desktop is running with WSL2 integration enabled.

### "Port already in use"

Find and stop the conflicting process:

```bash
# Linux/Mac
lsof -ti :5432 | xargs kill -9

# Windows (PowerShell)
netstat -ano | findstr :5432
Stop-Process -Id <PID>
```

Or change the port mapping in `docker-compose.local.yml`:
```yaml
ports:
  - "5433:5432"  # Use 5433 on host instead
```

Then update `POSTGRES_PORT=5433` in `.env`.

### ".env.example not found"

You are not in the project root. Navigate to the project root:
```bash
cd /path/to/adrion-369
python scripts/setup_shieldos_local.py
```

### "MCP servers not accessible"

MCP servers are not started by default with `--skip-containers`. Start the full stack:
```bash
docker compose -f docker-compose.local.yml up -d
```

First start triggers Docker image builds which take 2-5 minutes.

### "Hermetic score below threshold"

Check the violations report:
```bash
python scripts/verify_shieldos_hermetic.py
```

Common fixes:
- `docker.sock mount` violation: Remove `/var/run/docker.sock` volumes from compose files
- `DOCKER_HOST env` violation: Remove `DOCKER_HOST` from environment sections
- `telemetry_disabled` violation: Add `TELEMETRY_ENABLED: "false"` to service env blocks
- `api_key_isolation` violation: Add per-service API key env vars (see docker-compose.local.yml for examples)

### MCP server build failures

MCP servers require their Dockerfiles:
```bash
ls Dockerfile.mcp-router Dockerfile.guardian-mcp Dockerfile.oracle-mcp \
   Dockerfile.genesis-mcp Dockerfile.healer-mcp
```

If any are missing, build the infrastructure-only subset:
```bash
docker compose -f docker-compose.local.yml up -d postgres redis localstack
```

### Containers restart in a loop

Check logs for the failing container:
```bash
docker compose -f docker-compose.local.yml logs --tail=50 mcp-router
```

Common causes:
- `.env` has invalid values (DB connection string incorrect)
- Port conflict with another service
- Missing volume directories

---

## Resetting the Environment

Stop all services and remove volumes (full reset):

```bash
docker compose -f docker-compose.local.yml down -v
```

Remove only containers (keep data volumes):

```bash
docker compose -f docker-compose.local.yml down
```

Restart with fresh state:

```bash
docker compose -f docker-compose.local.yml up -d
```

---

## CI Integration

The ShieldOS CI script runs automatically on:
- Push to `setup/**` branches
- Manual workflow dispatch (`Actions` > `ShieldOS Local Setup Validation`)

To run CI checks locally:

```bash
bash scripts/setup_shieldos_ci.sh
```

To see the hermetic report as JSON (for CI integration):

```bash
python scripts/verify_shieldos_hermetic.py --json | python -m json.tool
python scripts/setup_shieldos_local.py --json
```

---

## Security Notes

- `.env` is in `.gitignore` — never committed
- All CHANGE_ME placeholders must be replaced before staging or production use
- `docker.sock` mounts are forbidden by ShieldOS (checked by `verify_shieldos_hermetic.py`)
- Per-service API keys prevent lateral movement between MCP servers
- `TELEMETRY_ENABLED: "false"` prevents external analytics calls in dev
- Real secrets are managed via `kubectl create secret` in Kubernetes (not in code)

---

## Related Documentation

- `CLAUDE.md` — Project control file and task backlog
- `docs/ARCHITECTURE.md` — Full v4.0 architecture
- `docs/GUARDIAN_LAWS_CANONICAL.json` — 9 Guardian Laws
- `docker-compose.local.yml` — Local dev compose (this setup)
- `docker-compose.prod.yml` — Production compose
- `kubernetes/` — Kubernetes manifests
