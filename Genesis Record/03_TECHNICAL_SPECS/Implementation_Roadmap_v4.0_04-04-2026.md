# ADRION 369 Technical Implementation Roadmap (v4.0)

**Wersja:** 4.0
**Data:** 2026-04-04
**Status:** Plan zatwierdzony | Gotowy do implementacji

---

## Context

**Problem Statement:**

ADRION 369 is an advanced multi-agent AI orchestration system with Trinity-EBDI framework and 162D decision space. Currently at production-alpha maturity (v2.0) with critical quality gaps:

- Go Vortex engine: only 6 functions, 5 stubbed (IsMaterialFlow hardcoded `true`, EBDI unmeasured)
- Test coverage: 25% Python, 0% Go (despite Go CI workflow expecting tests)
- Database: no connection pooling, no migration system, raw SQL embedded in code
- CI/CD: 6 workflows but no enforcement of linting or security standards
- Rate limiting: per-IP only, no per-endpoint or circuit breaker patterns
- Observability: basic logging, no distributed tracing, no dashboards

**Intended Outcome:**

Elevate ADRION 369 to production-grade reliability (target: 80-90% test coverage, enterprise-grade monitoring, scalable database layer, security-hardened API) across 4 tiers over 12 weeks.

---

## Solution Overview

### Tier 1: Foundation & Stabilization (Weeks 1–3)

- ✅ Complete Go Vortex: implement 5 stubbed functions + add 45 unit tests (80% coverage)
- ✅ Expand Python tests: raise coverage from 25% → 60% across arbitrage/ modules
- ✅ Database infrastructure: add connection pooling + migration framework scaffold
- ✅ Docker hardening: add health checks, restart policies, logging standardization

### Tier 2: Testing & CI/CD Enforcement (Weeks 4–6)

- ✅ Pre-commit hooks: ruff, black, mypy, gofmt, golangci-lint enforced at commit time
- ✅ CI/CD workflows: add linting, type checking, security scans (bandit, trivy, safety)
- ✅ Coverage gates: fail build if coverage drops (Go 80%, Python 60%)
- ✅ Test infrastructure: add conftest.py, fixtures, coverage reporting

### Tier 3: Database Scaling & Persistence (Weeks 7–9)

- ✅ Connection pool production-ready: metrics, monitoring, graceful drain
- ✅ Migration system: versioned schema deployments with rollback support
- ✅ Backup & recovery: daily incremental backups + disaster recovery procedures

### Tier 4: Advanced Monitoring & Hardening (Weeks 10–12)

- ✅ Rate limiting & circuit breakers: per-endpoint thresholds, exponential backoff
- ✅ Observability: OpenTelemetry + distributed tracing (Jaeger/Tempo), structured logging
- ✅ API documentation: OpenAPI/Swagger schemas, interactive docs
- ✅ Release automation: semantic versioning, deployment runbook, rollback procedures

---

## TIER 1 DETAILED IMPLEMENTATION

### TIER 1.1: Go Vortex Engine Completion

**Goal:** Implement all stubbed functions and establish 80% test coverage baseline.

**Critical Files to Modify:**

- `/internal/quantum/oracle.go` (lines 58–62): Replace `IsMaterialFlow()` hardcoded `true`
- `/internal/quantum/vortex.go` (lines 30–48): Add EBDI tracking beyond Health metric
- `/internal/api/handlers.go` (lines 81–119): Add 162D decision space JSON logging
- `/cmd/vortex-server/main.go`: Seed EBDI baseline on startup

**New Files to Create:**

1. **`/internal/quantum/vortex_test.go`** (15 test cases)
   - TestDigitalRoot: verify 3-6-9 encoding for [1,4,2,8,5,7,3]
   - TestCalculateMarketResonanceStates: affirmation/superposition/negation boundaries
   - TestTriggerSelfHealing: EBDI reset + health recovery
   - TestStartOscillation: ticker fires every Pulse147Hz, callback invoked
   - (+ 11 more edge case tests)

2. **`/internal/quantum/oracle_test.go`** (12 test cases)
   - TestPredictTrendBullish: history [1,2,4,3,5] → StateTrue
   - TestIsMaterialFlow: validate hexad pattern matching (1-4-2-8-5-7)
     - Include: exact match, duplicate match, pattern not found
   - TestGetFrequency: state → 528/417/396/174 Hz mapping
   - (+ 9 more tests)

3. **`/internal/api/handlers_test.go`** (18 test cases)
   - TestPostDecideValidInput: 200 response with DecisionState JSON
   - TestPostDecideRateLimitExceeded: 429 response after threshold
   - TestSentinelScan: threat vector detection + filtering
   - TestHealthCheckStatusCode: 200 + operational status
   - (+ 14 more tests covering edge cases, error scenarios)

4. **`/cmd/vortex-server/main_test.go`**
   - TestMainServer: verify router initialization, middleware stack
   - TestMainStartup: check port binding (1740)

**Acceptance Criteria:**

- `go test -v ./... -cover` shows 80%+ coverage
- All 45 tests pass deterministically
- IsMaterialFlow() correctly identifies hexad sequences (include tolerance for duplicates)
- EBDI state decays exponentially with 5-min half-life

---

### TIER 1.2: Python Test Expansion

**Goal:** Raise arbitrage/ coverage from 25% → 60% with 150+ new assertions.

**Analysis Required (First):**

- Audit which 14 of 23 arbitrage/ modules are untested
- Identify cyclomatic complexity hotspots (use radon or similar)
- Baseline report: `/scripts/reporting/coverage_baseline.json`

**New Test Files to Create:**

1. **`/tests/test_amplifier.py`** (5–8 functions)
   - boost_signal(), validate_threshold(), compose_message(), publish_achievement()

2. **`/tests/test_config.py`** (config loading, env override validation)
   - test_db_engine_fallback, test_api_key_from_env, test_port_override

3. **`/tests/test_executor.py`** (mock Upwork/Fiverr APIs)
   - test_submit_bid(), test_bid_acceptance(), test_error_handling

4. **`/tests/test_llm.py`** (mock LLM backends)
   - test_openai_completion(), test_anthropic_message(), test_openrouter_fallback()

5. **`/tests/test_scout.py`** + **`/tests/test_bidder.py`** (arbitrage core logic)

**Shared Test Infrastructure (New File):**

**`/tests/conftest.py`** — Pytest fixtures:

```python
@pytest.fixture
def mock_db():
    """In-memory SQLite for testing."""
    conn = sqlite3.connect(':memory:')
    init_db(conn)
    yield conn
    conn.close()

@pytest.fixture
def mock_llm_client():
    """Mocked LLM with predefined responses."""
    # Return MagicMock configured for different models

@pytest.fixture
def temp_arbitrage_dir(tmp_path):
    """Temporary directory for config/cache files."""
    return tmp_path
```

**`/tests/fixtures/mock_jobs.json`** — Sample data (Upwork/Fiverr job postings)

**Acceptance Criteria:**

- `pytest --cov=arbitrage --cov-report=term-missing` shows 60%+ coverage
- At least 150 new assertions
- conftest.py provides 5+ reusable fixtures
- All 10 test files pass in < 30 seconds

---

### TIER 1.3: Database Layer Hardening

**Goal:** Add connection pooling framework + migration system scaffold (not yet deployed to production).

**Files to Modify:**

**`/arbitrage/database.py`** (add pool support)

- Current: `def get_conn()` creates new connection each call
- New: Add `init_pool()` call on app startup for PostgreSQL
- New: Add `get_pooled_conn()` that checks out from pool
- New: Add `return_conn()` for pool release
- Use `psycopg2.pool.SimpleConnectionPool` for PostgreSQL
- SQLite: keep simple (no pooling needed for dev)

Example structure:

```python
_pool = None

def init_pool(db_url, min_conn=2, max_conn=10):
    global _pool
    _pool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn, db_url)

def get_pooled_conn():
    if _pool is None:
        return get_conn()  # Fallback to non-pooled
    return _pool.getconn()

def return_conn(conn):
    if _pool is not None:
        _pool.putconn(conn)
```

**`/arbitrage/config.py`** (add validation)

- Add DB_URL format validation: `postgresql://user:pass@host:port/dbname`
- Add timeout + retry parameters: `DB_CONN_TIMEOUT=10, DB_CONN_RETRIES=3`
- Read from env vars with sensible defaults

**Files to Create:**

**`/db/migrations/001_initial_schema.sql`**

- Extract all `CREATE TABLE IF NOT EXISTS` statements from database.py
- Include indexes: idx_deals_channel, idx_alerts_deal, idx_payment_events_type
- Add timestamps: created_at, updated_at to all tables

**`/db/migrations/002_add_indexes.sql`**

- Add composite indexes: (platform, status), (scouted_at, margin)
- Add EXPLAIN ANALYZE baseline for critical queries

**`/scripts/migrate.py`** (migration runner)

```python
def migrate(target_version, direction='up'):
    """Apply or rollback migrations up to target_version."""
    # Load migration files in order
    # Track applied migrations in DB table: migrations_applied
    # Execute SQL, log to Genesis Record
```

**Acceptance Criteria:**

- `pool.init_pool()` succeeds for PostgreSQL + SQLite fallback
- Migrations can be applied: `python scripts/migrate.py --target 002 --direction up`
- Migrations can be rolled back: `python scripts/migrate.py --target 001 --direction down`
- Can detect applied migrations from DB state

---

### TIER 1.4: Docker Infrastructure Hardening

**Goal:** Add reliability patterns to dev stack (adrion-swarm).

**File to Modify: `/adrion-swarm/docker-compose.yml`**

For each service, add:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:PORT/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
restart: unless-stopped
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

Specific changes:

- **postgres**: healthcheck via `pg_isready`
- **n8n**: healthcheck via `curl http://localhost:5678/api/v1/status`
- **vortex-engine**: healthcheck via `curl http://localhost:1740/health`
- **adrion-healer**: healthcheck via checking process existence (no exposed port)

Update `depends_on`:

```yaml
depends_on:
  postgres:
    condition: service_healthy  # Wait for health before starting
```

**Acceptance Criteria:**

- `docker-compose up -d` and all services pass health checks within 60s
- Service auto-restarts if container exits
- Logs are rotated (max 10MB, keep 3 files)

---

## TIER 2, 3, 4 OVERVIEW

(For full details, see original Roadmap document in Genesis Record)

### Tier 2: Pre-Commit Hooks & CI/CD Enforcement
- Ruff, mypy, gofmt, golangci-lint
- Security scans (bandit, trivy, safety)
- Coverage gates (Go 80%, Python 60%)

### Tier 3: Database Production Readiness
- Connection pooling metrics
- Migration system with rollback
- Daily backups + disaster recovery

### Tier 4: Advanced Monitoring & Hardening
- Rate limiting & circuit breakers per-endpoint
- OpenTelemetry + Jaeger distributed tracing
- Release automation (semantic versioning)
- Production deployment runbook

---

## SUCCESS METRICS & GATES

| Tier | Component | Target | Gate |
|------|-----------|--------|------|
| 1 | Go coverage | 80% | `go test -cover ./...` blocks merge if < 80% |
| 1 | Python coverage | 60% | `pytest --cov-fail-under=60` blocks merge |
| 1 | DB pool | 1 load test passing | Load test completes in < 5 seconds |
| 2 | Pre-commit hooks | 100% adoption | All developers using git hooks |
| 2 | Linting | 0 failures | ruff/mypy block commits |
| 2 | Security scans | 0 HIGH/CRITICAL | Trivy/Bandit block merge |
| 3 | Pool metrics | Exported | Prometheus scrape succeeds |
| 3 | Migrations | Bidirectional | Rollback test passes |
| 4 | Rate limiting | Per-endpoint | 429 response after threshold |
| 4 | Tracing | 95% sampled | Jaeger shows 95% of requests |
| 4 | Documentation | 100% | All public functions documented |

---

## EFFORT & TIMELINE

### Person-Days per Tier (1 FTE estimate):

- **Tier 1:** 20 days (Go 8 + Python 6 + DB 4 + Docker 2)
  - Weeks 1–3: Implementation + initial integration

- **Tier 2:** 10 days (Pre-commit 3 + CI/CD 4 + Infrastructure 3)
  - Weeks 4–6: Enforcement + automation

- **Tier 3:** 10 days (Pool 4 + Migrations 3 + Backups 3)
  - Weeks 7–9: Production hardening

- **Tier 4:** 16 days (Rate limiting 5 + Observability 4 + Docs 4 + Release 3)
  - Weeks 10–12: Advanced features + documentation

**Total: ~56 person-days | Timeline: 12 weeks (1 FTE) or 4 weeks (3–4 FTE parallel)**

---

## ASSUMPTIONS

- Python 3.11+, Go 1.22, Docker 24+
- PostgreSQL 15+ (or SQLite for dev)
- Ollama running locally for LLM inference
- GitHub Actions available for CI/CD
- 1 FTE available for implementation (56 person-days) or 3–4 FTE parallel (4 weeks)

---

**Status:** ✅ Ready for Tier 1 execution | Waiting for approval
