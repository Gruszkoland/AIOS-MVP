# Changelog — ADRION 369

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
versioning based on [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Version note:** Semantic version (CHANGELOG) is the authoritative release identifier.
> The marketing label "v4.0" in README refers to the product generation, not the code release.
> Mapping: `v4.0 product` = `1.x.x semantic`. Do not conflate the two.

---

## [1.2.0] — 2026-05-06

### Security

- **`uap/backend/api.py`** — `UAP_API_KEY` guard now triggers `sys.exit(1)` for any environment that is not explicitly `ENVIRONMENT=development|dev|test|testing`. Previously only blocked on `ENVIRONMENT=production` (opt-in). Now blocks by default, opt-out requires explicit dev env declaration.
- **`uap/backend/auth.py`** — `JWT_SECRET` default guard applies same logic: `sys.exit(1)` unless `ENVIRONMENT` is a recognised dev/test value. Removed duplicate `import logging` anti-pattern; uses single `_AUTH_LOGGER`.

### Fixed

- **Guardian Laws: weighted violation scoring** — replaced binary `DENY_THRESHOLD=2` with weighted system (`CRITICAL=10, HIGH=2, MEDIUM=1, deny_if weight >= 4`). Prevents false DENY on 2× low-severity MEDIUM violations (e.g. Unity + Rhythm = weight 2 → APPROVE). Two HIGH violations (weight 4) correctly deny.
- **Guardian Law G7 (Autonomy) severity** — corrected from `HIGH` to `CRITICAL`, aligned with `docs/GUARDIAN_LAWS_CANONICAL.json` (G7 = Privacy = CRITICAL).
- **Guardian Law G8 (Justice) severity** — corrected from `MEDIUM` to `CRITICAL`, aligned with canonical G8 = Nonmaleficence = CRITICAL.
- **`GUARDIAN_LAWS_CANONICAL.json`** — updated to v2.0: added `severity` field to all 9 laws, added `weight_map` and `deny_weighted_threshold` fields; added `runtime_name` for backward-compat mapping.
- **`arbitrage/pipeline_unified.py`** — replaced deprecated `datetime.utcnow()` with `datetime.now(timezone.utc)`.
- **`pyproject.toml`** — `fail_under` raised from `65` → `80` to match `--cov-fail-under=80` in CI workflow (was inconsistent).

### Deprecated

- **`Dockerfile.genesis-mcp`, `Dockerfile.guardian-mcp`, `Dockerfile.healer-mcp`, `Dockerfile.mcp-router`, `Dockerfile.oracle-mcp`, `Dockerfile.vortex-mcp`** — replaced by unified `Dockerfile.mcp-tier` with `--build-arg APP=<entrypoint> --build-arg PORT=<port>`. Old files retain deprecation header; will be removed in v5.0.

### Changed

- **`backups/` and `memories/`** — added to `.gitignore`, untracked from git index. Runtime state must not be versioned.
- **Coverage gate** — `pyproject.toml fail_under` unified at 80 (was 65, CI was already at 80).
- **README** — Guardian Laws decision rules updated to reflect weighted system. Coverage claim updated from "83%+" to "80%+ gate enforced by CI".

---

## [1.1.0] - 2026-04-05

### Added

- **UAP tests CI step** — `pytest uap/tests/ -v` added as separate step in `python-ci.yml` with env vars `UAP_API_KEY`, `ENVIRONMENT`, `JWT_SECRET`
- **GUARDIAN_LAWS_CANONICAL.json** (`docs/`) — single-source canonical definition of all 9 Guardian Laws (G1–G9)

### Changed

- **Coverage gate unified** — `--cov-fail-under` raised from 37 → 65 in `.github/workflows/release.yml` (aligned with `python-ci.yml` and `pyproject.toml`)
- **Resource limits** added to all major services in `docker-compose.prod.yml` (`deploy.resources.limits`): adrion-api (512m/0.5cpu), adrion-uap (512m/0.5cpu), adrion-dashboard (256m/0.25cpu), loki (512m/0.5cpu), grafana (512m/0.5cpu), adrion-nginx (128m/0.25cpu)
- **Pre-commit hook cross-platform** — `powershell.exe` call in `.githooks/pre-commit` wrapped in shell detection (powershell.exe → pwsh → warning fallback)

### Security

- **Bandit SAST** — `continue-on-error: false` made explicit in `security-ci.yml` to ensure hard block on findings
- **Safety dependency check** — `continue-on-error: false` made explicit in `security-ci.yml`

### Fixed

- **`.gitignore`** — added `monitoring/*.jsonl`, `monitoring/*_history*.jsonl`, `monitoring/*_test*.json`, `.runtime/`, `*.pid` to prevent runtime data from being committed

---

## [Unreleased]

### Deprecated

- **`arbitrage_server.py`** — replaced with thin redirect stub (~20 lines). Use `wsgi.py` → `arbitrage.app.create_app()`. Will be **removed in v5.0** (planned Q3 2026).

### Security

- Added startup `logger.warning` in `uap/backend/api.py` when `UAP_API_KEY` env var is not set (insecure default key "local-dev-key-123")
- Added startup `logger.warning` in `uap/backend/auth.py` when `JWT_SECRET` env var is not set (insecure default)

### Fixed

- Removed duplicated `_SlidingWindowRateLimiter` class from `arbitrage/api.py` — now uses `quantum_limiter` from `arbitrage/rate_limiter.py` (single source of truth)
- Removed orphaned `import collections` from `arbitrage/api.py` after class removal

### Changed

- Coverage gate raised from `fail_under = 37` → `65` in `pyproject.toml`
- Coverage gate raised from `--cov-fail-under=37` → `65` in `.github/workflows/python-ci.yml`
- Added `mypy` type-checking step to `python-ci.yml` CI workflow
- Added `mypy` pre-commit hook to `.pre-commit-config.yaml` (scoped to `arbitrage/` module)

---

## [1.0.0] — 2026-04-04

### Added

- **Core Arbitrage Engine** — Scout → Analyze → Bid pipeline (Fiverr/Upwork, Apify integration)
- **Quantum Module** (`arbitrage/quantum.py`) — Łukasiewicz 3-value logic, Autopojeza self-reset
- **Vortex Oracle** (`arbitrage/oracle.py`) — Fibonacci retracement + Enneagram prediction
- **Wholesale Pipeline** (`arbitrage/wholesale_orchestrator.py`) — B2B full Singularity Run
- **Mass Generator** (`arbitrage/mass_generator.py`) — Bulk manifest for Next.js ISR
- **Stripe Payments** (`arbitrage/payments.py`) — Checkout + webhook with HMAC verification
- **Circuit Breaker** (`arbitrage/circuit_breaker.py`) — Exponential backoff, CLOSED/OPEN/HALF_OPEN
- **Rate Limiter** (`arbitrage/rate_limiter.py`) — Per-endpoint, per-IP sliding-window, 5 named instances
- **LLM Layer** (`arbitrage/llm.py`) — Ollama↔OpenRouter fallback, canary rollout, KPI gate, injection detection
- **Autopilot** (`arbitrage/autopilot.py`) — Background scheduler for automated cycles
- **PostgreSQL connection pool** (`arbitrage/database.py`) — psycopg2 pool with graceful drain
- **Prometheus metrics** (`arbitrage/metrics.py`) — Optional prometheus_client gauges/histograms
- **HTTP API Server** (`arbitrage/api.py`) — 20+ endpoints, stdlib HTTPServer, port 8001
- **Unified Admin Panel** (`uap/`) — Flask API port 8002, JWT+RBAC auth, MCTS planner, WebSocket server
- **Harmonia Dashboard** (`harmonia-dashboard/`) — Lead pipeline, RAG memory, VERA scoring, ChromaDB
- **Micro-SaaS** (`micro-saas/`) — Next.js 15, pdf-parse, Stripe, Resend
- **ADRION Swarm** (`adrion-swarm/`) — Docker Compose: Ollama, n8n, PostgreSQL stack
- **Docker production stack** — `docker-compose.prod.yml` with Grafana/Loki/Promtail monitoring
- **Pre-commit hooks** — Ruff, go-fmt, go-vet, trailing-whitespace, secret detection, no-commit-to-main
- **Genesis Record** — PLAN/PROGRESS/REPORTS audit trail, Session Continuity Bridge (SCB)
- **162D Decision Space** — 3×6×9 Trinity-EBDI framework, 9 Guardian Laws
- **9 Personas** — Librarian, SAP, Auditor, Sentinel, Architect, Healer, Amplifier, BoosterLever, Chronos
- **JEDNOSC 162D** — Knowledge graph + RAG classification of 162 documents
- **Test suite** — 23 test files: unit, integration, guardrails, LLM, rate limiter, circuit breaker
- **LLM KPI Guard Loop** — PowerShell monitor, canary rollout promotion/rollback, alert history
- **XRP Tracker** (`arbitrage/xrp.py`, `xrp_tracker.py`) — Progress toward XRP target snapshots

### Infrastructure

- Python 3.11, Ruff linting, pytest + pytest-cov
- Go 1.21+ (`go.mod`) for Vortex engine skeleton
- Makefile with `test`, `lint`, `build`, `docker-build`, `dev`, `install` targets
