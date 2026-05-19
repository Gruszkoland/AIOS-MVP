# ADRION 369 — Deployment Runbook

**Version:** 1.0.0
**Target environment:** Docker Compose (local / VPS) → Kubernetes (future)

---

## Pre-Deployment Checklist (5 min)

Run this before every production deployment:

```bash
# 1. All tests passing
python -m pytest tests/ --cov=arbitrage --cov-fail-under=37 \
  -m "not e2e and not runtime" -q

# 2. Linting clean
python -m ruff check arbitrage/ tests/ --select=E,F,W --ignore=E501

# 3. Go builds and tests
go vet ./...
go test -v ./...

# 4. Coverage gate (Go 80%+)
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep ^total

# 5. No uncommitted changes
git status  # should be clean

# 6. Migration status reviewed
python scripts/migrate.py list
```

Checklist gates:
- [ ] Python coverage ≥ 37%
- [ ] Go coverage ≥ 80%
- [ ] Ruff reports 0 errors
- [ ] No pending migrations overlooked
- [ ] `git status` is clean (or PR is merged)

---

## Deployment Steps (10 min)

### Step 1: Tag the release

```bash
# Confirm current version
cat VERSION

# Create a semver tag
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions `release.yml` will automatically:
- Re-run all tests and lint
- Create a GitHub Release with auto-generated release notes
- Build Docker images (tagged with version + `latest`)

### Step 2: Deploy to staging

```bash
# Pull latest images
docker-compose -f adrion-swarm/docker-compose.yml pull

# Restart stack in detached mode
docker-compose -f adrion-swarm/docker-compose.yml up -d --remove-orphans

# Wait for health checks
docker-compose -f adrion-swarm/docker-compose.yml ps
```

### Step 3: Apply database migrations

```bash
# SQLite (local dev)
python scripts/migrate.py up --target 999

# PostgreSQL (prod — env vars set)
DB_ENGINE=postgres DB_URL=postgresql://adrion:pass@localhost:5432/genesis_record \
  python scripts/migrate.py list

DB_ENGINE=postgres DB_URL=postgresql://adrion:pass@localhost:5432/genesis_record \
  python scripts/migrate.py up --target 999
```

### Step 4: Smoke tests

```bash
# Arbitrage API
curl -s http://localhost:8001/api/arbitrage/status | python -m json.tool

# Vortex Engine
curl -s http://localhost:1740/health | python -m json.tool

# Quantum decision (basic call)
curl -s -X POST http://localhost:8001/api/arbitrage/quantum/decide \
  -H "Content-Type: application/json" \
  -d '{"price_wholesale": 100, "price_retail": 150, "channel_id": "AUDIO_PREMIUM"}' \
  | python -m json.tool

# n8n UI (manual check)
echo "Open http://localhost:5678 and verify workflows are active"
```

---

## Post-Deployment Validation (5 min)

```bash
# 1. All containers healthy
docker ps --filter "name=adrion" --format "table {{.Names}}\t{{.Status}}"

# 2. Logs clean (no errors in last 50 lines)
docker logs adrion-vortex --tail=50 | grep -i error || echo "Clean"
docker logs adrion-healer --tail=50 | grep -i error || echo "Clean"

# 3. DB connection pool initialized (PostgreSQL only)
docker logs adrion-healer | grep "PostgreSQL connection pool"

# 4. Migration tracking table intact
python scripts/migrate.py list
```

---

## Rollback Procedure (< 5 min)

### Application rollback

```bash
# Stop running containers
docker-compose -f adrion-swarm/docker-compose.yml stop

# Pull and start previous image version
# (Edit docker-compose.yml tag from 1.0.0 to 0.x.x first, or use image pinning)
docker-compose -f adrion-swarm/docker-compose.yml up -d

# Smoke test
curl http://localhost:8001/api/arbitrage/status
```

### Database rollback

```bash
# Roll back last migration
python scripts/migrate.py list   # identify last applied version N
python scripts/migrate.py down --target <N-1>

# Verify
python scripts/migrate.py list
```

### Full restore from backup

See `docs/DISASTER_RECOVERY.md` for full DB restore procedure.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_ENGINE` | `sqlite` | `sqlite` or `postgres` |
| `DB_PATH` | `arbitrage.db` | SQLite file path |
| `DB_URL` | _(empty)_ | PostgreSQL DSN |
| `QUANTUM_RATE_LIMIT_MAX` | `30` | Quantum endpoint: max requests per window |
| `QUANTUM_RATE_LIMIT_WINDOW_SECONDS` | `60` | Quantum endpoint: window in seconds |
| `SCOUT_RATE_LIMIT_MAX` | `10` | Scout endpoint: max requests per window |
| `CYCLE_RATE_LIMIT_MAX` | `5` | Cycle endpoint: max requests per window |
| `ORACLE_RATE_LIMIT_MAX` | `20` | Oracle scan: max requests per window |
| `MASS_GEN_RATE_LIMIT_MAX` | `3` | Mass-generate: max requests per window |
| `RETENTION_DAYS` | `7` | Backup retention window in days |

---

## Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `adrion-db` not healthy | postgres_data corrupt | Restore from backup |
| 429 on all endpoints | Rate limit too aggressive | Increase `*_RATE_LIMIT_MAX` env vars |
| `Circuit 'llm' is OPEN` | LLM service down | `llm_breaker.reset()` or restart Ollama |
| Migration fails | Schema drift | Run `python scripts/migrate.py list` to diagnose |
| Go coverage < 80% | New code without tests | Add tests before tagging release |

---

## Release Checklist Summary

```
PRE:
  [ ] pytest gate (37%+) passes
  [ ] ruff clean
  [ ] go test passes, coverage 80%+
  [ ] migrations reviewed

DEPLOY:
  [ ] git tag v<VERSION> && git push origin v<VERSION>
  [ ] GitHub Actions release created
  [ ] docker-compose pull + up
  [ ] migrations applied

POST:
  [ ] smoke tests pass
  [ ] logs clean
  [ ] backup created
```
