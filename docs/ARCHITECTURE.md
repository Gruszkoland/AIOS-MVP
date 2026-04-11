# ADRION 369 — Architecture & System Design

**Version:** 4.0 | **Updated:** 2026-04-11 | **Design Authority:** Backend Architecture Team

---

## 🏗️ System Overview

ADRION 369 is a multi-agent AI orchestration system built on the **Trinity-EBDI 162D decision framework**. The system makes autonomous decisions by evaluating each opportunity through:

- **3 Decision Perspectives** (Logos/Ethos/Eros) = Material/Intellectual/Essential
- **6 Processing Stages** (Hexagon) = Inventory→Empathy→Process→Debate→Healing→Action
- **9 Guardian Laws** (Ethics) = Unity, Harmony, Rhythm, Causality, Transparency, Authenticity, Privacy, Nonmaleficence, Sustainability

**Result:** 3 × 6 × 9 = 162-dimensional decision space

---

## 📐 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Client Layer: Browser → Nginx (TLS) → Single Entry Point        │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ HTTP/REST + WebSocket
         │
┌────────▼────────────────────────────────────────────────────────┐
│ API Gateway Layer: Flask App Factory (arbitrage/app.py)         │
│ • Port 8003                                                      │
│ • 5 Blueprints: arbitrage, quantum, oracle, wholesale, payments │
│ • Health checks: /health, /health/live, /health/ready           │
│ • Metrics export: /metrics (Prometheus)                         │
│ • OpenAPI docs: /api/docs (Swagger UI)                          │
└────────┬────────────────────────────────────────────────────────┘
         │
    ┌────┴───────────────────────────────────────┐
    │                                            │
    ▼                                            ▼
┌─────────────────────────┐        ┌──────────────────────────┐
│ Decision Engine         │        │ Support Systems          │
│                         │        │                          │
│ 1. Guardian Laws (9)    │        │ • Circuit Breaker        │
│    ├─ Validation check  │        │ • Rate Limiter           │
│    ├─ CRITICAL = DENY   │        │ • LLM Canary Deploy      │
│    └─ 2+ violations =   │        │ • Health Cascade         │
│       DENY              │        │                          │
│                         │        │ ┌──────────────────────┐ │
│ 2. Trinity Score (3%)   │        │ │ LLM Abstraction (llm)│ │
│    ├─ Material (wealth) │        │ │ • Ollama-first       │ │
│    ├─ Intellectual (QA) │        │ │ • OpenRouter fallback│ │
│    └─ Essential (ethics)│        │ │ • Injection filter   │ │
│                         │        │ │ • Canary validation  │ │
│ 3. Hexagon Processing   │        │ └──────────────────────┘ │
│    (6-stage pipeline)   │        │                          │
└────────┬────────────────┘        └─────────┬────────────────┘
         │                                   │
         └───────────────┬───────────────────┘
                         │
         ┌───────────────▼────────────────┐
         │ Data Persistence Layer         │
         │                                │
         │ • SQLite (dev/local)           │
         │ • PostgreSQL pool (production) │
         │ • Parameterized queries only   │
         │ • Graceful conn drain          │
         └────────────────────────────────┘
```

---

## 🔷 Flask Application Architecture

**Entry Point:** `wsgi.py` → `arbitrage.app.create_app()`

```python
create_app()
  │
  ├─ Load config from arbitrage.config.settings (Pydantic BaseSettings)
  │
  ├─ Initialize Database (arbitrage/database.py)
  │  └─ SQLite or PostgreSQL depending on environment
  │
  ├─ Register 5 Blueprints from arbitrage/blueprints/
  │  ├─ arbitrage_bp: Scout, Bid, Jobs, Cycle (arbitrage trading)
  │  ├─ quantum_bp: Quantum decision (3 routes)
  │  ├─ oracle_bp: Predict, Scan (2 routes)
  │  ├─ wholesale_bp: Bulk procurement (3 routes)
  │  └─ payments_bp: Checkout, Webhook, Manifest (4 routes)
  │
  ├─ Attach Middleware Stack
  │  ├─ CORS (restricted origins)
  │  ├─ Authentication (API key header)
  │  ├─ Rate Limiter (sliding window per endpoint)
  │  ├─ Circuit Breaker (LLM/Stripe/Apify/XRP)
  │  └─ Health cascade (/health aggregates all dependencies)
  │
  └─ Return Flask app for WSGI server
```

### Blueprint Input Validation

**Critical Rule:** Use `safe_float()`/`safe_int()` from `arbitrage.blueprints.__init__` — NEVER bare `float()`.

```python
# ❌ WRONG
value = float(request.json.get("value"))

# ✅ CORRECT
from arbitrage.blueprints import safe_float
value = safe_float(request.json.get("value"), default=0.0)
```

---

## 🧠 Decision Engine: Trinity-Hexagon-Guardian

### Step 1: Guardian Laws Validation (Immediate DENY if violated)

```python
# arbitrage/guardian.py: evaluate_guardians(job, analysis, context)

9 Laws (Source of Truth: docs/GUARDIAN_LAWS_CANONICAL.json):
  1. Unity (MEDIUM)
  2. Harmony (HIGH)
  3. Rhythm (MEDIUM)
  4. Causality (HIGH)
  5. Transparency (MEDIUM)
  6. Authenticity (HIGH)
  7. Privacy (CRITICAL) ← Veto power
  8. Nonmaleficence (CRITICAL) ← Veto power
  9. Sustainability (HIGH)

Logic:
  • If ANY CRITICAL law violated → INSTANT DENY
  • If 2+ laws violated → DENY
  • Otherwise → Continue to Trinity
```

### Step 2: Trinity Score Evaluation (0.0-1.0)

```python
# arbitrage/trinity.py: evaluate_trinity(job, analysis, resources)

Three perspectives evaluated in parallel:

Material (Physical Resources)
  • Cash flow
  • Inventory constraints
  • Logistics feasibility
  Score: 0.0-1.0

Intellectual (Quality/Analysis)
  • Technical soundness
  • Data quality
  • Model confidence
  Score: 0.0-1.0

Essential (Ethical/Strategic)
  • Alignment with values
  • Long-term sustainability
  • Impact on stakeholders
  Score: 0.0-1.0

Overall Trinity Score = (M + I + E) / 3
  Threshold: >= 0.4 to proceed
```

### Step 3: Hexagon 6-Stage Pipeline (Sequential)

```python
# arbitrage/hexagon.py: HexagonProcessor.process(trinity_scores)

Six processing stages run in order:

1. INVENTORY STAGE
   └─ Current state assessment
      • Market data ingestion
      • Portfolio analysis
      • Constraint mapping

2. EMPATHY STAGE
   └─ Stakeholder consideration
      • Customer impact
      • Team availability
      • Market sentiment

3. PROCESS STAGE
   └─ Workflow validation
      • Can existing processes handle?
      • Do we need new procedures?
      • Resource allocation

4. DEBATE STAGE
   └─ Multi-perspective discussion
      • Pro arguments
      • Con arguments
      • Risk assessment

5. HEALING STAGE
   └─ Optimization
      • Cost reduction
      • Quality improvement
      • Technical debt addressing

6. ACTION STAGE
   └─ Execution planning
      • Actionable steps
      • Timeline
      • Success metrics

Each stage produces: {stage_name, analysis, recommendations, confidence_score}
Score aggregated for next step
```

---

## 🎯 Request Flow: Arbitrage Cycle Example

```
User POST /api/arbitrage/cycle
       │
       ▼
Scout Agent (Scout-001)
  ├─ Fetch jobs from Apify
  ├─ Filter by criteria
  ├─ Rank by priority
  └─ Output: 15 job opportunities
       │
       ▼
Parallel Analyze Agents (1-N workers, configurable)
  ├─ Each job → Trinity evaluation
  ├─ Each job → Hexagon processing
  ├─ Each job → Guardian validation
  ├─ Skip if: Trinity < 0.4 or Guardian DENY
  └─ Output: Worthy jobs with decision_reason
       │
       ▼
Bid Agent (Bid-001)
  ├─ For each worthy job:
  │  ├─ Calculate bid amount (85% value × worthiness modifier)
  │  ├─ Setup Stripe escrow
  │  └─ Submit bid
  └─ Output: Created bids
       │
       ▼
Track Agent (Track-001)
  ├─ Monitor XRP confirmations
  ├─ Check daily limits
  ├─ Detect bottlenecks
  └─ Emit Prometheus metrics
       │
       ▼
Response to Client
  └─ {
       summary: {jobs_processed, jobs_worthy, bids_created, parallel_factor},
       agent_metrics: {scout-001, analyze-001..N, bid-001, track-001},
       health: {status, bottlenecks},
       timestamp
     }
```

---

## 📦 UAP Orchestrator (Port 8002)

**Unified Admin Panel** — Master orchestration API for agents & tasks.

```
arbitrage/app.py (Flask, primary)
     ↓
uap/backend/api.py (Flask, auxiliary on 8002)
     │
     ├─ /mapi/v1/task/delegate {task_description, agent_hint}
     │  └─ Delegate work to 6 AI Personas
     │
     ├─ /mapi/v1/agents/* (CRUD)
     │  ├─ GET /agents → Fetch all agents
     │  ├─ POST /agents → Create agent
     │  ├─ PUT /agents/<id> → Update agent (SANITIZED: P0-1 fix)
     │  └─ DELETE /agents/<id> → Soft delete
     │
     ├─ /mapi/v1/genesis/* (Event logging)
     │  ├─ GET /logs → Query genesis events
     │  └─ GET /logs?agent=SAP&since=1h → Filtered logs
     │
     ├─ /mapi/v1/agent/scores (Trust scoring)
     │  └─ Heatmap: 6 personas × trust_score × EBDI state
     │
     └─ /mapi/v1/crisis/* (Crisis management)
        ├─ POST /activate → Activate crisis mode
        └─ POST /resolve → Conflict resolution

Six Personas (Pre-loaded):
  • Librarian (0.95, Context analysis)
  • SAP (0.88, Strategic planning)
  • Auditor (0.87, Quality validation)
  • Sentinel (0.92, Error monitoring)
  • Architect (0.90, Design authority)
  • Healer (0.85, Optimization)
```

---

## 🔴 Go Vortex (Port 1740)

**Digital Root Oracle** — EBDI state machine + 174Hz resonance.

```go
// cmd/vortex-server/main.go

EBDI State Machine:
  ├─ Pleasure (0.0-1.0) — User satisfaction
  ├─ Arousal (0.0-1.0) — System activity/stress
  ├─ Dominance (0.0-1.0) — Process control level
  └─ Depth (0.0-1.0) — Engagement intensity

Digital Root Oracle:
  ├─ 174Hz resonance pulse
  ├─ Phase tracking
  └─ System harmonics alignment

Crisis Detection:
  IF Arousal > 0.7 → ACTIVATE crisis mode (HEALER-MCP)
```

---

## 🔌 MCP Microservices (Ports 9000-9005)

**Machine Control Protocol** — 6 independent microservices for specialized tasks.

```
┌──────────────────────────────────────────┐
│ MCPRouter (Port 9000)                    │
│ - Central routing with trust score       │
│ - Load balancing across 5 MCPs           │
│ - Request/response middleware            │
└──────────────────────────────────────────┘
         │      │      │      │      │
    ┌────┴──┬───┴──┬───┴──┬───┴──┬───┴──┐
    │       │      │      │      │      │
    ▼       ▼      ▼      ▼      ▼      ▼
   9001   9002   9003   9004   9005
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│VRTX │ │GARD │ │ORAC │ │GEN  │ │HEAL │
│-----├─│-----├─│-----├─│-----├─│-----│
│Orch │ │Sec  │ │Rout │ │Mem  │ │Recov
│Exec │ │Law  │ │Pred │ │Audit│ │Optim
│Safe │ │Val  │ │Scan │ │Evt  │ │Heal
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘
```

Each MCP server:

- **Listens on unique port**
- **Exposes `/health` endpoint**
- **Thread-safe with timeouts**
- **Logs to stdout (Loki scrapes via Promtail)**

---

## 💾 Data Persistence

### SQLite (Development)

```
arbitrage.db
  ├─ agents (id, name, role, trust_score, capability_level, skills)
  ├─ tasks (id, session_id, agent, status, progress, duration_seconds)
  ├─ jobs (id, type, value, status, priority, processed_at)
  ├─ bids (id, job_id, amount, status, created_at, expires_at)
  └─ genesis_logs (id, timestamp, agent, action, details, session_id)
```

### PostgreSQL (Production)

- **Connection pooling** (configurable)
- **Parameterized queries** (zero f-string SQL)
- **Graceful drain** on shutdown
- **Replication-ready** for HA

**Critical Rule:** Always use placeholders `?` or `%s` depending on dialect, NEVER f-strings.

```python
# ❌ WRONG — SQL injection risk
db.execute(f"SELECT * FROM jobs WHERE id = {job_id}")

# ✅ CORRECT — Parameterized
db.execute("SELECT * FROM jobs WHERE id = ?", [job_id])
```

---

## 🛡️ Security Strategy

### Guardian Laws: Immediate Enforcement

```python
if evaluate_guardians(job, analysis, context)["denied"]:
    return {"error": "DENIED by Guardian Laws", "reason": "..."}
```

**CRITICAL Laws (instant veto):**

- Law 7: Privacy
- Law 8: Nonmaleficence

### Circuit Breaker: Dependency Resilience

```python
@circuit_breaker(name="llm_circuit", threshold=5, timeout=60)
def call_llm(prompt):
    return llm.chat(prompt)
```

Monitors:

- LLM (Ollama/OpenRouter)
- Payment processor (Stripe)
- Job source (Apify)
- Blockchain (XRP)

### Rate Limiting: Per-Endpoint Protection

```python
def is_allowed(client_ip: str) -> bool:
    # Sliding window: 100 requests per hour per IP
    return rate_limiter.check(client_ip)
```

All POST endpoints enforce rate limiting.

### LLM Canary: Gradual Rollout

```python
if random() < canary_percentage:
    # 5% traffic → new OpenRouter model
    llm_model = "new_model"
else:
    # 95% traffic → current stable model
    llm_model = "stable_model"
```

### CORS + Origin Validation

```python
CORS(app, origins=["http://localhost:8003", "https://api.adrion.io"])

@app.before_request
def _check_csrf():
    if request.method in ("POST", "PUT", "DELETE"):
        origin = request.headers.get("Origin")
        if origin not in ALLOWED_ORIGINS:
            return {"error": "Origin not allowed"}, 403
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics (Port 9090)

Exported from `/metrics` endpoint:

```
# Counters
agent_tasks_completed{agent_id="scout-001"}
agent_tasks_failed{agent_id="analyze-001"}

# Histograms
agent_avg_duration_ms{agent_id="bid-001"}
session_complete_duration_ms

# Gauges
agent_success_rate{agent_id="track-001"}
session_parallel_factor
system_health{status="healthy|warning|critical"}
```

### Grafana Dashboards (Port 3000)

Pre-configured dashboards:

- **Agent Performance:** Success rates, latency, trust scores
- **Hexagon Pipeline:** Stage duration, bottleneck detection
- **Guardian Laws:** Law compliance rates, violation heatmap
- **System Health:** CPU, memory, disk usage

### Loki Logs (Port 3100)

**Log format:** Structured JSON (via `python-json-logger`)

```json
{
  "timestamp": "2026-04-11T14:32:00Z",
  "level": "INFO",
  "service": "adrion.arbitrage",
  "message": "Job processed successfully",
  "job_id": "job-12345",
  "agent_id": "analyze-001",
  "duration_ms": 245
}
```

All logs queryable in Grafana via Loki datasource.

---

## 🧪 Testing Strategy

### Unit Tests (80% coverage minimum)

```bash
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
```

Critical modules:

- `arbitrage/guardian.py` — 9 laws validation
- `arbitrage/trinity.py` — 3-perspective scoring
- `arbitrage/hexagon.py` — 6-stage pipeline
- `arbitrage/circuit_breaker.py` — Failure handling

### Integration Tests

```bash
# End-to-end: scout → analyze → bid → track
pytest tests/test_autonomous_agents.py -v

# API endpoints
pytest tests/test_api_integration.py -v

# UAP orchestrator
pytest uap/tests/test_api.py -v
```

### Go Tests (80% coverage minimum)

```bash
go test ./... -v -coverprofile=coverage.out
go tool cover -func=coverage.out
```

---

## 🚀 Deployment

### Docker Compose (Local)

```bash
docker-compose up -d
# Services: PostgreSQL, Prometheus, Grafana, Redis
```

### Docker Compose (Production)

```bash
docker-compose -f docker-compose.prod.yml up -d
# 10 services + Nginx TLS + monitoring stack
```

### Kubernetes (Cloud)

```bash
kubectl apply -f kubernetes/
# Namespaced deployments with resource limits
# Secrets via external-secrets-operator
```

---

## 📈 Matryca 3-6-9 Visualization

```
                    DECISION SPACE (162D)
                              │
                    ┌─────────┼─────────┐
                    │         │         │
              LOGOS │     ETHOS│    EROS│
           (Logos)  │    (Ethos) (Eros)
             │      │         │         │
      ┌──────┼──────┼─────┬───┼────┬────┼──────┐
      │      │      │     │   │    │    │      │
      ▼      ▼      ▼     ▼   ▼    ▼    ▼      ▼
    [6 Hexagon Stages] × [9 Guardian Laws]

    Result: 3 perspectives × 6 stages × 9 laws = 162 decision vectors
```

Each decision gets scored across all 162 dimensions for comprehensive evaluation.

---

## 📚 References

- **Guardian Laws:** `docs/GUARDIAN_LAWS_CANONICAL.json`
- **Configuration:** `arbitrage/config.py` (Pydantic BaseSettings)
- **Entry Point:** `wsgi.py` → `arbitrage.app.create_app()`
- **API Docs:** `http://localhost:8003/api/docs` (Swagger UI)
- **Local Deployment:** `docs/LOCAL_DEPLOYMENT_GUIDE.md`

---

**ADRION 369 — Autonomous Decision-making with Real-time Integration & Orchestration Nexus**

_Last Updated: 2026-04-11 | Architecture Version: 4.0 | Maintained by Backend Architecture Team_
