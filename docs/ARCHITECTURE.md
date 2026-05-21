<!-- markdownlint-disable -->

# Repository Architecture Overview

**Version:** 5.0 | **Updated:** 2026-05-20

---

## 1. System Overview

This repository contains **two complementary systems**:

### Subsystem A: ADRION 369 — Orchestration Layer (Python/Go)

ADRION 369 is a multi-agent AI orchestration system built on the **Trinity-EBDI 162D
decision framework**. Every autonomous decision is evaluated through three orthogonal
axes:

- **3 Perspectives** (LOGOS / ETHOS / EROS) -- mapped to Material / Intellectual / Essential
- **6 Processing Stages** (Hexagon) -- Inventory, Empathy, Process, Debate, Healing, Action
- **9 Guardian Laws** (Ethics) -- canonical definitions in `docs/GUARDIAN_LAWS_CANONICAL.json`

**Result:** 3 x 6 x 9 = **162-dimensional decision space** (the "162D" in Trinity-EBDI 162D).

The system comprises three independently deployable services and an optional MCP
microservices layer:

| Service            | Language    | Framework    | Port | Role                                    |
|--------------------|-------------|--------------|------|-----------------------------------------|
| Flask API          | Python 3.11 | Flask        | 8003 | Primary REST API, decision engine       |
| UAP Orchestrator   | Python 3.11 | Flask        | 8002 | Admin panel, agent/task management      |
| Go Vortex          | Go 1.22     | Echo v4      | 1740 | EBDI state machine, digital root oracle |
| MCP Layer (6 svcs) | Python 3.11 | Various      | 9000-9005 | Specialized microservices          |

> **For deep dive on ADRION 369 architecture, see sections below (2-14).
> For AI OS Cognitive Kernel (Rust) architecture, see [AI_OS_KERNEL_ARCHITECTURE.md](./AI_OS_KERNEL_ARCHITECTURE.md).**

### Subsystem B: AI OS Cognitive Kernel (Rust)

A deterministic real-time OS kernel designed to run LLM agents as advisory-only safety layers:

- **Kernel Plane** (no_std, deterministic, hard real-time) — scheduler, IPC router, capability enforcer
- **IPC Plane** (zero-copy ring buffers, shared memory, < 1μs latency)
- **Advisory Plane** (LLM agents, user-space, soft real-time) — Guardian evaluations, recommendations

**Crates:**
- `kernel/` (~500 lines) — core deterministic scheduler
- `agents/` (~300 lines) — Guardian trait + 9 specialist implementations
- `ipc/` (~200 lines) — zero-copy ring-buffer IPC
- `poc/scheduler-mgr` (~100 lines) — proof-of-concept orchestrator

> **See detailed architectural diagram and flow in [AI_OS_KERNEL_ARCHITECTURE.md](./AI_OS_KERNEL_ARCHITECTURE.md).**

---

## 2. High-Level Architecture (ADRION 369)

```
                         Browser / External Client
                                  |
                           Nginx (TLS termination)
                                  |
            +---------------------+---------------------+
            |                     |                     |
   Flask App Factory        UAP Orchestrator        Go Vortex
   (arbitrage/app.py)       (uap/backend/api.py)    (cmd/vortex-server/main.go)
   Port 8003                Port 8002                Port 1740
            |                     |                     |
   +--------+--------+    +------+------+        +-----+-----+
   | 5 Blueprints    |    | 6 AI        |        | EBDI      |
   | Guardian Laws   |    |   Personas  |        | Digital   |
   | Trinity Score   |    | Task CRUD   |        |   Root    |
   | Hexagon Pipeline|    | Genesis     |        | 174Hz     |
   | Circuit Breaker |    |   Record    |        |   Pulse   |
   | Rate Limiter    |    | Trust Score |        | Sentinel  |
   | LLM Canary      |    |   Heatmap   |        |   Scan    |
   +-----------------+    +-------------+        +-----------+
            |                     |                     |
            +---------------------+---------------------+
                                  |
                     Data Persistence Layer
                  SQLite (dev) / PostgreSQL (prod)
```

---

## 3. Flask Application (Port 8003)

**Entry point:** `wsgi.py` -> `arbitrage.app.create_app()`

The app factory in `arbitrage/app.py` assembles the full middleware stack and
registers five blueprints:

```
create_app()
  |
  +-- Load config: arbitrage.config.settings (Pydantic BaseSettings)
  |
  +-- Initialize CORS (restricted origins)
  |
  +-- CSRF origin check (before_request hook)
  |
  +-- Register Blueprints
  |     +-- arbitrage_bp  (arbitrage/blueprints/arbitrage_bp.py)
  |     |     Scout, Bid, Jobs, Cycle -- core arbitrage trading
  |     +-- quantum_bp    (arbitrage/blueprints/quantum_bp.py)
  |     |     Quantum decision, status, scan
  |     +-- oracle_bp     (arbitrage/blueprints/oracle_bp.py)
  |     |     Predict, scan
  |     +-- wholesale_bp  (arbitrage/blueprints/wholesale_bp.py)
  |     |     Bulk procurement scout, cycle, deals
  |     +-- payments_bp   (arbitrage/blueprints/payments_bp.py)
  |           Checkout, webhook, mass-gen, manifest
  |
  +-- /api/docs          Swagger UI (loads docs/openapi.yaml)
  +-- /api/openapi.json  OpenAPI 3.1 spec as JSON
  +-- /metrics           Prometheus text format (pool size, checkouts, uptime)
  +-- /health            Cascade check (DB + Ollama)
  +-- /health/live       Liveness probe (always 200)
  +-- /health/ready      Readiness probe (503 if DB down)
  |
  +-- Graceful shutdown  (atexit + SIGTERM -> DB pool drain)
  +-- Error handlers     (404, 500 -> JSON responses)
```

### Blueprint Input Validation

All blueprints use `safe_float()` / `safe_int()` from `arbitrage.blueprints.__init__`
instead of bare `float()` / `int()` to prevent unhandled conversion errors.

---

## 4. Decision Engine: Guardian -> Trinity -> Hexagon

Every arbitrage decision passes through three sequential evaluation stages.

### 4.1 Guardian Laws Validation (arbitrage/guardian.py)

The Guardian Laws engine validates ethical compliance. A failing check can
immediately deny a decision before any further processing.

**Canonical source of truth:** `docs/GUARDIAN_LAWS_CANONICAL.json`

| #  | Code | Canonical Name   | Severity | Veto Power | Description                                          |
|----|------|------------------|----------|------------|------------------------------------------------------|
| 1  | G1   | Unity            | MEDIUM   | No         | All actions must serve system coherence               |
| 2  | G2   | Harmony          | HIGH     | No         | Balance between competing objectives                  |
| 3  | G3   | Rhythm           | MEDIUM   | No         | Maintain consistent cadence and timing                |
| 4  | G4   | Causality        | HIGH     | No         | Every action must have a traceable, justified cause   |
| 5  | G5   | Transparency     | MEDIUM   | No         | All decisions and reasoning must be auditable         |
| 6  | G6   | Authenticity     | HIGH     | No         | Outputs must be genuine and free from deception       |
| 7  | G7   | Privacy          | CRITICAL | YES        | No external disclosure without consent                |
| 8  | G8   | Nonmaleficence   | CRITICAL | YES        | Never cause harm to users, systems, or data           |
| 9  | G9   | Sustainability   | HIGH     | No         | Operate within resource limits                        |

**Decision logic:**

```
evaluate_guardians(job, analysis, context) -> GuardianEval

  IF any CRITICAL law violated  -> instant DENY
  IF 2+ laws violated (any)     -> DENY
  ELSE                          -> APPROVE (continue to Trinity)
```

> **Note:** The implementation in `guardian.py` currently uses legacy names for some
> laws (e.g., "Truth" instead of "Harmony", "Autonomy" instead of "Privacy").
> The canonical JSON is the authoritative reference; a sync task (P1-5) is planned.

### 4.2 Trinity Score Evaluation (arbitrage/trinity.py)

Three perspectives scored independently on a 0.0-1.0 scale:

```
evaluate_trinity(job, analysis, system_resources) -> TrinityScore

  Material (Physical Resources)
    Inputs:   CPU usage, RAM availability (via psutil or injected dict)
    Method:   harmonic_mean(cpu_avail, ram_avail)
    Threshold: >= 0.30

  Intellectual (Analysis Quality)
    Inputs:   LLM score (0-10), reasoning length (fit + risks text)
    Method:   harmonic_mean(score_norm, reasoning_norm)
    Threshold: >= 0.50

  Essential (Purpose + Profitability)
    Inputs:   keyword match count, estimated profit
    Method:   geometric_mean(purpose_match, profit_norm)
    Threshold: >= 0.20

  Combined = (Material + Intellectual + Essential) / 3
    Threshold: >= 0.40

  Approved = ALL four thresholds met
```

Harmonic mean makes each perspective fail-fast: a single zero component
drives the whole score to zero.

### 4.3 Hexagon 6-Stage Pipeline (6 Processing Modes)

Every decision cycles through six sequential processing stages (the "Hexagon"), each ~30ms:

#### M1: Inventory — What do I see?
**Observe facts about the request.** Database lookup for precedents, fact extraction, state validation.
- Evaluates against: G1 (Unity), G3 (Rhythm), G5 (Transparency)
- Perspective: Material (resources available)
- Output: observed state summary (3-word facts)
- Latency: ~30ms

#### M2: Empathy — What does the user feel?
**Emotional and relational assessment.** Stakeholder impact analysis, historical context, relationship preservation.
- Evaluates against: G7 (Autonomy), G5 (Transparency)
- Perspective: Essential (purpose, harmony)
- Output: stakeholder sentiment, impact summary
- Latency: ~30ms

#### M3: Process — How to organize this?
**Decompose into subgoals. Allocate resources.** Goal decomposition, resource availability, timeline feasibility.
- Evaluates against: G1 (Unity), G3 (Rhythm), G9 (Sustainability)
- Perspective: Material (resources), Intellectual (logic)
- Output: execution plan, resource requirements
- Latency: ~30ms

#### M4: Debate — Is this safe?
**Multi-agent consensus voting.** Byzantine fault-tolerant (5/6 quorum), conflicting perspectives reconciled.
- Evaluates against: G2 (Truth), G4 (Causality), G6 (Nonmaleficence), G8 (Justice)
- Perspective: Intellectual (truth, logic)
- Output: consensus decision, voting breakdown
- Latency: ~30ms

#### M5: Healing — Are there manipulations?
**Detect adversarial/deceptive patterns.** Hidden assumption discovery, principle alignment verification.
- Evaluates against: G2 (Truth), G5 (Transparency), G6 (Nonmaleficence)
- Perspective: Intellectual (truth), Essential (integrity)
- Output: risk assessment, deception flags
- Latency: ~30ms

#### M6: Action — Execute with logging
**Commit decision to Genesis Record.** Decision hash commitment, Merkle tree chain extension.
- Evaluates against: G4 (Causality), G5 (Transparency), G8 (Justice)
- Perspective: All three (comprehensive logging)
- Output: decision hash, audit trail, timestamp
- Latency: ~30ms

**Total Hexagon latency: ~180ms (budget: <200ms)**

Each stage produces `{stage_name, analysis, recommendations, confidence_score}`.

---

## 5. Request Flow: Arbitrage Cycle

```
POST /api/arbitrage/cycle
  |
  v
Scout Agent
  +-- Fetch job listings (Apify)
  +-- Filter by criteria
  +-- Rank by priority
  |
  v
Parallel Analysis (1-N workers)
  +-- Guardian Laws check (DENY -> skip)
  +-- Trinity Score (< 0.4 combined -> skip)
  +-- Hexagon 6-stage pipeline
  |
  v
Bid Agent
  +-- Calculate bid amount (85% value x worthiness modifier)
  +-- Setup Stripe escrow
  +-- Submit bid
  |
  v
Track Agent
  +-- Monitor XRP confirmations
  +-- Check daily limits
  +-- Emit Prometheus metrics
  |
  v
Response: {summary, agent_metrics, health, timestamp}
```

---

## 5a. Complete Data Flow Diagram

```
┌─────────────┐
│   Browser   │  (User / External Client)
└──────┬──────┘
       │ HTTP/TLS
       v
┌──────────────────────────────────────┐
│   Nginx (reverse proxy + TLS)         │
└──────┬──────────────────────────────┬─┘
       │                              │
       │ :8003                        │ :8002       :1740
       v                              v             v
  ┌─────────────┐  ┌──────────────┐  ┌────────────┐
  │  Flask API  │  │   UAP Panel  │  │   Vortex   │
  │  (:8003)    │  │   (:8002)    │  │   (:1740)  │
  │             │  │              │  │            │
  │ Guardian ──┼┐ │ 6 Personas ──┼┐ │  EBDI SM   │
  │ Trinity    │├─┼─ Task CRUD  ─┼┼─┼─ 174Hz    │
  │ Hexagon    │└─┼─ Genesis ────┼┼─┼─ Sentinel │
  │ Circuit Br.│  │ TrustScore   │└─┤ Oracle    │
  │ RateLimit  │  │              │  │            │
  └──┬────┬────┘  └───────┬──────┘  └────┬───────┘
     │    │               │              │
     │    └───────────────┼──────────────┘
     │                    │
     v                    v
  ┌────────────────────────────────────┐
  │   Shared Data Layer                │
  │  ┌───────────────────────────────┐ │
  │  │ PostgreSQL (prod) / SQLite    │ │
  │  │  • agents  • tasks  • jobs   │ │
  │  │  • bids    • genesis_logs    │ │
  │  └───────────────────────────────┘ │
  │  ┌───────────────────────────────┐ │
  │  │ Cache: Redis (optional)        │ │
  │  │  • Circuit breaker state       │ │
  │  │  • Rate limit counters         │ │
  │  └───────────────────────────────┘ │
  └────────────────────────────────────┘
     │
     ├─────────────────────────────────────────┐
     │                                         │
     v                                         v
  ┌───────────────────┐            ┌──────────────────┐
  │ External Services │            │ MCP Layer        │
  │  • Ollama/OpenAI  │            │  (Ports 9000-9005)
  │  • Stripe         │            │  • Router        │
  │  • Apify          │            │  • Vortex-MCP    │
  │  • XRP Ledger     │            │  • Guardian-MCP  │
  └───────────────────┘            │  • Oracle-MCP    │
                                    │  • Genesis-MCP   │
                                    │  • Healer-MCP    │
                                    └──────────────────┘
```

---

## 6. UAP Orchestrator (Port 8002)

The Unified Admin Panel provides master orchestration for agents and tasks.

**File:** `uap/backend/api.py` (currently a monolith; refactor planned as P0-3)

```
Endpoints under /mapi/v1/:

  POST /task/delegate         Delegate work to 6 AI Personas
  GET  /agents                List all agents
  POST /agents                Create agent
  PUT  /agents/<id>           Update agent (column allowlist enforced)
  DELETE /agents/<id>         Soft delete agent
  GET  /genesis/logs          Query genesis event log
  GET  /agent/scores          Trust score heatmap (6 personas x EBDI state)
  POST /crisis/activate       Activate crisis mode
  POST /crisis/resolve        Conflict resolution
```

**Six pre-loaded AI Personas:**

| Persona    | Trust Score | Role                  |
|------------|-------------|-----------------------|
| Librarian  | 0.95        | Context analysis      |
| SAP        | 0.88        | Strategic planning    |
| Auditor    | 0.87        | Quality validation    |
| Sentinel   | 0.92        | Error monitoring      |
| Architect  | 0.90        | Design authority      |
| Healer     | 0.85        | Optimization          |

---

## 7. Go Vortex Engine (Port 1740)

The Vortex engine is written in Go with the Echo v4 framework. It manages the
EBDI emotional state machine and digital root oracle.

**File:** `cmd/vortex-server/main.go`

```
Routes:
  GET  /health              Health check (public)
  POST /decide              EBDI decision endpoint (auth required)
  GET  /status              Current EBDI state (auth required)
  POST /sentinel/scan       Security scan (auth required)
  GET  /sentinel/threats    Threat list (auth required)
  POST /oracle/predict      Digital root prediction (auth required)

Authentication: X-Vortex-Key header (HMAC comparison)
               Empty key = dev mode (all requests pass through)
```

**EBDI State Machine:**

- **Pleasure** (0.0-1.0) -- user satisfaction level
- **Arousal** (0.0-1.0) -- system activity / stress level
- **Dominance** (0.0-1.0) -- process control level
- **Depth** (0.0-1.0) -- engagement intensity

**174Hz Oscillation Tracker:** Background goroutine that monitors system resonance
and health, logging periodic health snapshots.

**Crisis trigger:** Arousal > 0.7 activates crisis mode (routes to Healer).

---

## 8. MCP Microservices Layer (Ports 9000-9005)

Six specialized microservices defined in `docker-compose.mcp-tier.yml`:

```
MCPRouter (9000)  -- Central decision arbitration, load balancing
     |
     +-- Vortex-MCP  (9001)  -- Orchestration, 174Hz monitoring
     +-- Guardian-MCP (9002)  -- Security, 9 Guardian Laws compliance
     +-- Oracle-MCP   (9003)  -- 162D routing, pattern matching
     +-- Genesis-MCP  (9004)  -- State management, RAG integration
     +-- Healer-MCP   (9005)  -- Recovery, monitoring, optimization
```

Each MCP service exposes `/health`, runs in its own container, and communicates
with others via HTTP over the `adrion-mcp-net` Docker network.

---

## 8a. Configuration & Environment Variables

All application configuration is managed through **Pydantic `BaseSettings`**
in `arbitrage/config.py`. Variables are typed, validated, and accessible via
`arbitrage.config.settings.*` throughout the application.

**Development startup:**
```bash
export OLLAMA_HOST=http://localhost:11434
export DB_URL=sqlite:///./arbitrage.db
export STRIPE_SECRET_KEY=sk_test_...
export STRIPE_PUBLISHABLE_KEY=pk_test_...
python wsgi.py  # http://localhost:8003
```

**Production startup (with .env file):**
```bash
export DB_URL=postgresql://user:pass@postgres-prod:5432/adrion
export LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=sk-or-...
waitress-serve --port=8003 wsgi:app
```

**Key environment variables:**
- `OLLAMA_HOST` — Ollama endpoint (fallback: OpenRouter if not set)
- `DB_URL` — Database connection string (SQLite or PostgreSQL)
- `LLM_PROVIDER` — `local` (Ollama) or `openrouter` (cloud)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` — Payment processing
- `APIFY_API_KEY` — Job sourcing
- `XRP_NETWORK` — `test` or `main` for XRP Ledger
- `VORTEX_AUTH_KEY` — HMAC key for Go Vortex (empty = dev mode)
- `PROMETHEUS_REGISTRY_PREFIX` — Metric namespace (default: `adrion_`)

---

## 8b. Startup and Graceful Shutdown

**On startup (`create_app()`):**
1. Load config from environment (Pydantic validation)
2. Initialize logging (JSON formatter for Loki/Grafana)
3. Create database connection pool (SQLite or PostgreSQL)
4. Initialize circuit breakers for external dependencies
5. Register all blueprints
6. Setup error handlers (404, 500 → JSON)
7. Register health check cascade
8. Emit startup log

**On shutdown (SIGTERM):**
1. Graceful drain of DB pool (`arbitrage.database.graceful_drain()`)
   - Wait up to 30s for in-flight queries to complete
   - Reject new connections
   - Close remaining connections
2. Flush logs to Loki (if configured)
3. Exit with status 0

**Example:** Kubernetes TERM signal → Flask SIGTERM handler → graceful_drain() →
Pod termination in ~30s (respects `terminationGracePeriodSeconds: 30`).

---

## 9. Support Systems

### Circuit Breaker (arbitrage/circuit_breaker.py)

Protects against cascading failures from external dependencies:
- LLM (Ollama / OpenRouter)
- Payment processor (Stripe)
- Job source (Apify)
- Blockchain (XRP)

Opens after N consecutive failures, enters half-open state after timeout.

### Rate Limiter (arbitrage/rate_limiter.py)

Sliding window rate limiting per IP. All POST endpoints must call
`is_allowed(client_ip)` before processing.

### LLM Abstraction (arbitrage/llm.py)

- **Primary:** Ollama (local inference)
- **Fallback:** OpenRouter (cloud)
- Prompt injection filter
- Canary deployment: configurable percentage of traffic to new model

### Configuration (arbitrage/config.py)

All settings managed via Pydantic `BaseSettings`. Environment variables are typed
and validated at startup. Application code uses `arbitrage.config.settings.*`,
never raw `os.getenv()`.

---

## 10. Data Persistence

### SQLite (Development)

```
arbitrage.db
  +-- agents       (id, name, role, trust_score, capability_level, skills)
  +-- tasks        (id, session_id, agent, status, progress, duration_seconds)
  +-- jobs         (id, type, value, status, priority, processed_at)
  +-- bids         (id, job_id, amount, status, created_at, expires_at)
  +-- genesis_logs (id, timestamp, agent, action, details, session_id)
```

### PostgreSQL (Production)

- Connection pooling (configurable pool size)
- Graceful drain on shutdown (`arbitrage.database.graceful_drain()`)
- Replication-ready for HA

**Critical rule:** All SQL uses parameterized queries (`?` or `%s` placeholders).
f-string SQL is forbidden.

---

## 11. Matryca 3-6-9: 162-Dimensional Decision Space

```
          LOGOS              ETHOS              EROS
        (Material)       (Intellectual)      (Essential)
            |                  |                  |
     +------+------+   +------+------+   +------+------+
     |  6 Hexagon  |   |  6 Hexagon  |   |  6 Hexagon  |
     |   Stages    |   |   Stages    |   |   Stages    |
     +------+------+   +------+------+   +------+------+
            |                  |                  |
     Each stage evaluated against 9 Guardian Laws
            |                  |                  |
     3  x   6   x   9   =   162 decision vectors
```

The Matryca ensures every decision is examined from three philosophical
perspectives (truth, goodness, creation), through six processing stages,
and validated against nine ethical laws. This produces 162 orthogonal
evaluation vectors that collectively determine whether a decision is
approved or denied.

---

## 12. Monitoring & Observability

### Prometheus Metrics (/metrics endpoint)

```
adrion_db_pool_size              gauge    -- Total connections in pool
adrion_db_pool_checked_out       gauge    -- Connections currently in use
adrion_db_pool_checkouts_total   counter  -- Total DB connection checkouts
adrion_db_pool_timeouts_total    counter  -- Total DB connection timeouts
adrion_uptime_seconds            gauge    -- Seconds since server start
```

### Logging

Structured JSON via `python-json-logger`, compatible with Loki/Grafana:

```json
{
  "timestamp": "2026-04-11T14:32:00Z",
  "level": "INFO",
  "name": "adrion.guardian",
  "message": "Guardian APPROVE: 9/9 laws passed"
}
```

### Grafana Dashboards (Port 3000)

- Agent performance (success rates, latency, trust scores)
- Guardian Laws compliance heatmap
- System health (CPU, memory, disk)

---

## 13. Infrastructure

### Docker Compose Variants

| File                             | Purpose      | Services | LLM Backend  |
|----------------------------------|--------------|----------|--------------|
| `docker-compose.yml`             | Development  | 5        | auto (local) |
| `docker-compose.prod.yml`        | Production   | 10       | auto         |
| `docker-compose.cloud.yml`       | Cloud deploy | 8        | OpenRouter   |
| `docker-compose.mcp-tier.yml`    | MCP layer    | 6        | auto         |
| `docker-compose.lmstudio.yml`    | LM Studio    | 2        | LM Studio    |

### Kubernetes

Manifests in `kubernetes/` with namespaced deployments, resource limits,
and secrets managed via `kubectl create secret` (YAML contains
`CHANGE_ME_IN_PRODUCTION` placeholders only).

---

## 14. Technology Stack

| Component        | Technology                                  |
|------------------|---------------------------------------------|
| Primary language | Python 3.11+                                |
| Secondary lang   | Go 1.22                                     |
| Web framework    | Flask (Python), Echo v4 (Go)                |
| Configuration    | Pydantic BaseSettings                       |
| Database         | SQLite (dev), PostgreSQL (prod)             |
| LLM inference    | Ollama (local), OpenRouter (cloud fallback) |
| Payments         | Stripe                                      |
| Job sourcing     | Apify                                       |
| Blockchain       | XRP Ledger                                  |
| Monitoring       | Prometheus + Grafana + Loki                 |
| Containerization | Docker, Docker Compose                      |
| Orchestration    | Kubernetes (optional)                       |
| CI/CD            | GitHub Actions (10 workflows)               |
| API docs         | OpenAPI 3.1 (docs/openapi.yaml)             |
| Linting          | ruff (Python), go vet (Go)                  |
| Type checking    | mypy (Python)                               |
| Testing          | pytest (Python), go test (Go)               |

---

## 15. Key File Reference

| File                                 | Role                                    |
|--------------------------------------|-----------------------------------------|
| `wsgi.py`                            | Production entry point                  |
| `arbitrage/app.py`                   | Flask app factory                       |
| `arbitrage/blueprints/`              | 5 route modules                         |
| `arbitrage/guardian.py`              | 9 Guardian Laws engine                  |
| `arbitrage/trinity.py`              | Trinity Score (M/I/E)                   |
| `arbitrage/hexagon.py`              | 6-stage processing pipeline             |
| `arbitrage/config.py`               | Pydantic BaseSettings                   |
| `arbitrage/database.py`             | DB layer (SQLite + PostgreSQL pool)     |
| `arbitrage/llm.py`                  | LLM abstraction (Ollama + OpenRouter)   |
| `arbitrage/circuit_breaker.py`      | Circuit breaker for external deps       |
| `arbitrage/rate_limiter.py`         | Sliding window rate limiter             |
| `uap/backend/api.py`               | UAP orchestrator (port 8002)            |
| `cmd/vortex-server/main.go`        | Go Vortex engine (port 1740)            |
| `docs/GUARDIAN_LAWS_CANONICAL.json` | Guardian Laws canonical definitions     |
| `docs/openapi.yaml`                | OpenAPI 3.1 specification               |

---

## 16. Testing Strategy

### Coverage Requirements

- **Python:** 80%+ coverage (enforced in CI via `pytest --cov-fail-under=80`)
- **Go:** 80%+ coverage (enforced via `go test -coverprofile=coverage.out`)
- **CI gate:** All tests must pass before merge to main

### Test Markers (pytest)

```python
@pytest.mark.tier0          # Critical path only (< 2min)
@pytest.mark.tier1          # Core features (< 10min)
@pytest.mark.tier2          # Integration tests (< 30min)
@pytest.mark.slow           # > 30s, conditional run
@pytest.mark.requires_db    # Needs database fixture
@pytest.mark.requires_ollama # Needs Ollama endpoint
```

**CI runs:** `pytest -m "tier0 or tier1"` (gates on PRs) + `pytest` (gates on main)

### Key Test Files

- `tests/test_guardian_*.py` — Guardian Laws validation
- `tests/test_trinity_*.py` — Trinity Score evaluation
- `tests/test_hexagon_*.py` — Hexagon 6-stage pipeline
- `tests/test_circuit_breaker.py` — External dependency protection
- `tests/test_rate_limiter.py` — Rate limit enforcement
- `uap/tests/test_api.py` — UAP orchestrator endpoints
- `mcp-servers/tests/test_*.py` — MCP microservices

### Property-Based Testing (Future: P2-2)

- **Hypothesis** library for fuzz testing
- Guardian Laws: any CRITICAL → DENY, any 2+ → DENY (invariants)
- Trinity Score: all scores ∈ [0.0, 1.0] range (invariants)

---

## 17. CI/CD Pipelines (GitHub Actions)

| Workflow                | Trigger    | Gates                            |
|-------------------------|------------|----------------------------------|
| `python-ci.yml`         | push/PR    | ruff + mypy + pytest 80% + TIER-0 |
| `go-ci.yml`             | push/PR    | go vet + test 80%                |
| `docker-ci.yml`         | push/PR    | docker build (no push)           |
| `security-ci.yml`       | push/PR    | bandit + safety + trivy          |
| `release.yml`           | tag v*.*  | validate → GHCR push            |
| `tier0-gate.yml`        | push/PR    | critical path tests only         |

**Release process:**
1. Tag: `git tag -a v4.2-p1 -m "Phase 1: security hardening"`
2. Push: `git push origin v4.2-p1`
3. GitHub Actions: validate → build → push to GHCR → create release

---
