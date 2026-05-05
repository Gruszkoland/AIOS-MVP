# ADRION 369 v4.0 - Advanced AI System

## Overview

**ADRION 369 v4.0** is an elite, security-hardened autonomous execution environment based on the **Trinity-EBDI** framework. It orchestrates high-performance components across Go and Python to deliver predictive intelligence (Vortex Oracle) and real-time governance.

### Key Innovations (v4.0)

- **Go Sentinel 174Hz**: Low-latency execution monitoring and rapid-response logic in Go.
- **Python Quantum**: Advanced decision-making and pattern recognition using high-dimensional modeling.
- **162D Decision Space**: A 162-dimensional workspace for evaluating actions based on Material, Intellectual, and Essential perspectives.
- **Trinity-EBDI Engine**: Blending emotional intelligence (EBDI) with logical purity for balanced decisions.

### 🎯 Core Philosophy

- **Local-First**: All inference on your machine via Ollama (DeepSeek-Coder).
- **Privacy-Centric**: Genesis Record ensures zero data export.
- **Trinity Reasoning**: Every decision is weighted by ROI (Material), Logic (Intellectual), and Ethics (Essential).
- **Self-Healing**: Automated technical debt reduction and error recovery.

---

## Architecture

### Flask App Factory with Blueprints

The Python backend uses a Flask application factory (`arbitrage/app.py`) with five
registered blueprints:

| Blueprint      | Prefix           | Responsibility                          |
| -------------- | ---------------- | --------------------------------------- |
| `arbitrage_bp` | `/api/arbitrage` | Job scouting, analysis, bidding         |
| `quantum_bp`   | `/api/quantum`   | Quantum scan channels, circuit breakers |
| `oracle_bp`    | `/api/oracle`    | Vortex Oracle predictions               |
| `wholesale_bp` | `/api/wholesale` | Wholesale deal orchestration            |
| `payments_bp`  | `/api/payments`  | XRP tracking, Stripe integration        |

Additional top-level routes: `GET /health`, `GET /metrics` (Prometheus text format).

### Pydantic BaseSettings (`arbitrage/config.py`)

All configuration is managed through `AdrionSettings(BaseSettings)` with typed
fields, `.env` loading, and field validators. Module-level aliases preserve
backward compatibility (`from arbitrage.config import DB_PATH`).

### 9 Guardian Laws Engine (`arbitrage/guardian.py`)

Every arbitrage decision is validated against nine ethical laws in sequence:

1. **Unity** (MEDIUM) -- job aligns with system core purpose
2. **Harmony** (HIGH) -- balance between competing objectives
3. **Rhythm** (MEDIUM) -- bid pace is sustainable (daily limits)
4. **Causality** (HIGH) -- price chain is traceable and non-negative
5. **Transparency** (MEDIUM) -- all required analysis fields present
6. **Authenticity** (CRITICAL) -- analysis is genuine and non-deceptive
7. **Privacy** (CRITICAL) -- no external disclosure without consent
8. **Nonmaleficence** (CRITICAL) -- no financial harm to operator
9. **Sustainability** (HIGH) -- daily total operational cost within limit

**Decision rules:** A CRITICAL law violation triggers an instant DENY. Two or
more violations of any severity also trigger a DENY. Zero or one non-critical
violations result in APPROVE.

Canonical definitions: [`docs/GUARDIAN_LAWS_CANONICAL.json`](docs/GUARDIAN_LAWS_CANONICAL.json)

### Trinity Score Engine (`arbitrage/trinity.py`)

Three perspectives evaluate every decision in a 162-dimensional space:

- **Material** -- system resource availability (CPU/RAM via `psutil`).
  Aggregation: harmonic mean. All components must pass (fail-fast).
- **Intellectual** -- LLM analysis quality (score + reasoning).
  Aggregation: harmonic mean. Low quality blocks the entire analysis.
- **Essential** -- purpose alignment + profitability.
  Aggregation: geometric mean. Both must be high (multiplicative).

Combined score: `(material + intellectual + essential) / 3`. Approved when
`material >= 0.3`, `intellectual >= 0.5`, `essential >= 0.2`, and
`combined >= TRINITY_MIN_COMBINED`.

### MCP Layer (6 Microservices)

| Service  | Port | Role                          |
| -------- | ---- | ----------------------------- |
| Router   | 9000 | Request routing and balancing |
| Vortex   | 9001 | EBDI state management         |
| Guardian | 9002 | Law evaluation gateway        |
| Oracle   | 9003 | Predictive intelligence       |
| Genesis  | 9004 | Immutable audit log           |
| Healer   | 9005 | Self-healing and optimization |

### Go Vortex Server

Echo framework on port 1740. Provides high-speed EBDI state management, CORS
with configurable `CORS_ALLOWED_ORIGIN`, Vortex auth middleware
(`X-Vortex-Key`), and 174Hz oscillation monitoring.

### Supporting Infrastructure

- **vortex-core (Go)**: High-speed API and system telemetry.
- **quantum-oracle (Python)**: Strategic arbitrage and predictive analysis.
- **n8n-adrion**: Workflow orchestration and stream connectors.
- **Genesis Record**: Unified local storage for all decisions and logs.

---

## 🧠 The Swarm Personas

| Persona       | Role                | Primary Law              | Trigger      |
| ------------- | ------------------- | ------------------------ | ------------ |
| **LIBRARIAN** | Knowledge Archiver  | 1: Unity                 | `@librarian` |
| **SAP**       | Strategic Planner   | 2: Harmony               | `@sap`       |
| **AUDITOR**   | Quality Overseer    | 5: Transparency          | `@auditor`   |
| **SENTINEL**  | Error Guardian      | 8: Nonmaleficence        | `@sentinel`  |
| **ARCHITECT** | Design Authority    | 4: Causality             | `@architect` |
| **HEALER**    | Optimization Engine | 9: Sustainability        | `@healer`    |

---

## ⚡ Quick Start

### 1. Prerequisites

- Ollama from [ollama.com](https://ollama.com)
- Python 3.10+
- Git

### 2. Setup Ollama

```bash
# Start Ollama and download model
ollama run deepseek-coder-v2:16b
# (or use :lite for smaller systems)
```

### 3. Install Aider

```bash
pip install aider-chat
```

### 4. Start the System

**Terminal 1 (Ollama):**

```bash
ollama serve
# Ollama will run on http://localhost:11434
```

**Terminal 2 (Aider):**

```bash
# In your project directory
aider

# Or with explicit settings:
aider --model openai/deepseek-coder-v2:16b \
       --openai-api-base http://localhost:11434/v1 \
       --openai-api-key ollama
```

### 5. Invoke Personas

```
# Start with analysis
@librarian
Give me a quick summary of this project.

# Then plan
@sap
Create today's optimization plan based on the Librarian's analysis.

# Validate quality
@auditor
Review the code quality and flag any regressions.

# Emergency fix
@sentinel
We have production errors - deploy immediate fixes.

# Design review
@architect
Is this architecture aligned with our system principles?

# Continuous improvement
@healer
Run an optimization cycle on technical debt.
```

### Stream Connectors (n8n/Webhooks)

You can now connect the UGC and Resale streams to real external data sources.
Update your `.env` with:

- `UGC_SOURCE_URL`: URL to your UGC marketplace/n8n endpoint.
- `RESALE_SOURCE_URL`: URL to your resale marketplace/n8n endpoint.
- `STREAMS_CONNECTOR_TOKEN`: Optional Bearer token for authentication.

To manually trigger a data pull:

```bash
curl -X POST http://localhost:5000/api/arbitrage/streams/run
```

### Production Deployment

For production-grade deployment of the Arbitrage API (Docker + Waitress + healthcheck), see:

- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)

### Local Secret Loading (Safe)

- Non-secret static references are stored in [config/reference_constants.py](config/reference_constants.py).
- Secret values must stay in local `.env` only (never in git).
- Validate required local secrets without printing them:

```bash
python scripts/security/load_secrets.py
```

### Local Pre-Commit Secret Guard

- Install repository-local hooks path:

```powershell
./scripts/security/install-githooks.ps1
```

- Active hook: `.githooks/pre-commit`
- It blocks commits that include `.env.local` or Stripe-like secret patterns in staged changes.
- If installer reports `Git executable not found`, install Git for Windows and reopen terminal.
- If installer reports `not a git directory`, initialize repo first with `git init` in project root.

### UGC/Resale Stream Connectors (Optional)

- You can feed real UGC and resale events from n8n or marketplace webhooks.
- Set these vars in local `.env`:
  - `UGC_SOURCE_URL`
  - `RESALE_SOURCE_URL`
  - `STREAMS_CONNECTOR_TOKEN` (optional bearer token)
- Trigger ingestion manually:

```bash
curl -X POST http://localhost:8001/api/arbitrage/streams/run \
   -H "Content-Type: application/json" \
   -d '{"dry_run": false}'
```

- API status includes connector config visibility under `stream_sources`.

---

## �️ Maintenance & Self-Healing

The **ADRION 369** system includes advanced autonomous maintenance components:

### 1. Go-based Sentinel (174Hz)

The system's "immune system" implemented in Go for maximum performance.

- **Location**: `cmd/vortex-server/`
- **Function**: Real-time monitoring of system integrity, logic stress detection, and sub-millisecond response to anomalies.
- **Usage**: Automatically runs as part of the `vortex-core` stack. Monitor logs via:
  ```bash
  docker logs adrion-vortex-server
  ```

### 2. Adrion-Healer (Autonomous Optimization)

A dedicated container focused on reducing technical debt and optimizing the codebase.

- **Function**: Background analysis of code patterns, performance bottlenecks, and structural alignment with Trinity principles.
- **Status Check**:
  ```bash
  docker ps -f name=adrion-healer
  ```
- **Manual Trigger**:
  ```bash
  @healer Run optimization cycle on latest modules.
  ```

### 3. Legacy Migration

Old logic (e.g., `oracle.py`, `quantum.py`) has been moved to the `legacy/` directory to prevent interference with the new Go-based core. Always verify that high-speed logic is implemented in the `cmd/` or `internal/` Go directories.

---

## Project Structure

```
.
├── arbitrage/
│   ├── app.py                               # Flask app factory (create_app)
│   ├── config.py                            # Pydantic BaseSettings configuration
│   ├── guardian.py                           # 9 Guardian Laws Engine
│   ├── trinity.py                           # Trinity Score Engine (Material/Intellectual/Essential)
│   ├── blueprints/
│   │   ├── arbitrage_bp.py                  # Job scouting, analysis, bidding
│   │   ├── quantum_bp.py                    # Quantum scan channels
│   │   ├── oracle_bp.py                     # Vortex Oracle predictions
│   │   ├── wholesale_bp.py                  # Wholesale deal orchestration
│   │   └── payments_bp.py                   # XRP tracking, Stripe integration
│   ├── circuit_breaker.py                   # Circuit breaker (LLM/Stripe/Apify/XRP)
│   ├── database.py                          # Connection pooling (SQLite/PostgreSQL)
│   ├── metrics.py                           # Prometheus pool metrics
│   └── rate_limiter.py                      # Sliding window rate limiter
├── cmd/
│   └── vortex-server/                       # Go Vortex Server (Echo, port 1740)
├── internal/
│   ├── api/                                 # Go API handlers
│   └── quantum/                             # Go Vortex/EBDI/Oracle
├── kubernetes/
│   ├── 00-namespace/                        # Namespace definitions
│   ├── 01-storage/                          # Persistent volume claims
│   ├── 02-config/                           # ConfigMaps and secrets
│   ├── 03-postgres/                         # PostgreSQL StatefulSet
│   ├── 04-tier1/                            # Tier-1 services
│   ├── 05-core/                             # Core application pods
│   ├── 06-monitoring/                       # Prometheus, Grafana, Loki
│   ├── 07-networking/                       # Ingress and service mesh
│   └── 08-jobs/                             # CronJobs and batch tasks
├── monitoring/
│   ├── grafana/                             # Grafana dashboards and provisioning
│   ├── alerts/                              # Alerting rules
│   ├── loki/                                # Loki log aggregation config
│   ├── promtail/                            # Promtail log shipping config
│   └── prometheus.yml                       # Prometheus scrape configuration
├── scripts/
│   ├── reporting/                           # LLM KPI guards, session reports, CI gate reports
│   ├── security/                            # Secret loading, git hooks
│   ├── install/                             # One-click installer (setup-ADRION.ps1)
│   ├── monitoring/                          # Service health monitoring
│   └── backup/                              # PostgreSQL and SQLite backup scripts
├── db/
│   ├── migrations/                          # SQL migration files (001-004)
│   └── MIGRATION_GUIDE.md
├── docs/
│   ├── ARCHITECTURE.md                      # System design & data flow
│   ├── LAWS.md                              # The 9 governing laws explained
│   ├── GUARDIAN_LAWS_CANONICAL.json          # Machine-readable law definitions
│   ├── API_SCHEMA.yaml                      # OpenAPI specification
│   └── DEPLOYMENT_RUNBOOK.md                # Production deployment guide
├── config/
│   └── personas.yml                         # 6 persona definitions + system prompts
├── persona-agents/                          # Individual persona agent files
│   ├── librarian.agent.md
│   ├── sap.agent.md
│   ├── auditor.agent.md
│   ├── sentinel.agent.md
│   ├── architect.agent.md
│   └── healer.agent.md
├── .github/
│   └── workflows/                           # CI/CD (python-ci, release, security-ci)
├── tests/                                   # Python test suite (83%+ coverage)
└── README.md                                # This file
```

---

## 🚀 How It Works

### Normal Workflow

```
User Query
   ↓
LIBRARIAN (Analysis) → Context & History
   ↓
SAP (Planning) → Task Prioritization & Risk Assessment
   ↓
ARCHITECT (Optional) → Design Review & Validation
   ↓
Implementation → Code Changes
   ↓
AUDITOR (Validation) → Quality Checks & Regression Tests
   ↓
SENTINEL (Monitoring) → Error Detection & Alerts
   ↓
HEALER (Background) → Continuous Optimization & Debt Reduction
```

### Crisis Mode

```
Critical Error Detected
   ↓
SENTINEL (Immediate Response) ← < 1 second
   ↓
Deploy Hotfix
   ↓
Escalate to HEALER (if recurring)
```

---

## 🔒 Privacy & Security

### Law 7: Genesis Record

- ✅ All inference runs locally (Ollama on `localhost:11434`)
- ✅ All code stays on your machine
- ✅ All logs stored locally in `.aider/logs/`
- ✅ No external API calls to cloud services
- ❌ No credentials transmitted
- ❌ No telemetry or data collection

**Your code is yours. Period.**

---

## The Nine Guardian Laws

Canonical definitions: [`docs/GUARDIAN_LAWS_CANONICAL.json`](docs/GUARDIAN_LAWS_CANONICAL.json)

1. **G1 Unity** (MEDIUM) -- All actions must serve system coherence
2. **G2 Harmony** (HIGH) -- Balance between competing objectives
3. **G3 Rhythm** (MEDIUM) -- Maintain consistent cadence and timing of operations
4. **G4 Causality** (HIGH) -- Every action must have a traceable, justified cause
5. **G5 Transparency** (MEDIUM) -- All decisions and reasoning must be visible and auditable
6. **G6 Authenticity** (HIGH) -- Outputs must be genuine and free from deception
7. **G7 Privacy** (CRITICAL) -- No external disclosure without consent
8. **G8 Nonmaleficence** (CRITICAL) -- Never cause harm to users, systems, or data
9. **G9 Sustainability** (HIGH) -- Operate within resource limits and preserve long-term system health

**Decision rules:** A CRITICAL law violation triggers an instant DENY. Two or
more violations of any severity also trigger a DENY.

**Learn more:** See [docs/LAWS.md](docs/LAWS.md)

---

## 🔧 Configuration

### Aider Settings (`.aider/config.yml`)

```yaml
model: openai/deepseek-coder-v2:16b
openai-api-base: http://localhost:11434/v1
openai-api-key: ollama
edit-format: architect # Debate mode
stream: true # Live streaming
context-limit: 16000
auto-commits: true
```

### Persona Definitions (`config/personas.yml`)

Each persona has:

- System prompt (role, constraints, tools)
- Allowed tools (what they can do)
- Output format
- Token limits

---

## 📊 Example Session

### Terminal Output

```
user> @librarian
Analyze this project's recent history and structure.

LIBRARIAN:
📚 Historical Analysis
- Last 10 commits: Focused on refactoring, no breaking changes
- Structure: Modular architecture, 12 main modules
- Dependencies: Current versions all stable
- Technical Debt: 3 high-priority items in payment module

---

user> @sap
Based on that, create a session plan.

SAP:
📋 Today's Optimization Plan
1. [CRITICAL] Fix payment module circular dependency
2. [HIGH] Refactor auth middleware for testability
3. [MEDIUM] Document cache layer behavior
4. [LOW] Update stale dependencies

---

user> @auditor
These changes look good?

AUDITOR:
✓ Code Quality Score: 8.2/10
✓ All tests passing
✓ No regressions detected
⚠ Warning: Payment module needs test coverage boost (currently 62%)

Process continues...
```

---

## 🛠️ Common Commands

```bash
# Start everything
ollama serve &
aider

# Just check status
ollama list

# View logs
tail -f .aider/logs/session.log

# Use specific model
aider --model openai/deepseek-coder-v2:7b

# View all available models
ollama pull deepseek-coder-v2

# Kill Ollama service (if needed)
pkill ollama
```

---

## 📚 Documentation

| Document                                      | Purpose                   |
| --------------------------------------------- | ------------------------- |
| [INSTALL.md](docs/INSTALL.md)                 | Step-by-step setup guide  |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)       | System design & data flow |
| [LAWS.md](docs/LAWS.md)                       | Detailed law descriptions |
| [WORKFLOW.md](docs/WORKFLOW.md)               | How to use the personas   |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues & fixes     |

---

## 🚨 Troubleshooting

### Ollama not responding

```bash
curl http://localhost:11434/api/tags
# If fails, restart Ollama
```

### Model not found

```bash
ollama pull deepseek-coder-v2:16b
ollama list
```

### Aider slow

```yaml
# In .aider/config.yml, reduce context:
context-limit: 8000 # was 16000
```

### Out of memory

```bash
# Use smaller model
ollama run deepseek-coder-v2:lite
```

---

## 🎓 Learn More

- **Ollama**: https://ollama.com
- **Aider**: https://aider.chat
- **DeepSeek Coder**: https://github.com/deepseek-ai/deepseek-coder
- **Local AI Philosophy**: Run models on your hardware, not cloud

---

## 📈 Next Steps

1. ✅ Setup complete
2. 🚀 Start Ollama and Aider
3. 📖 Read [WORKFLOW.md](docs/WORKFLOW.md) for best practices
4. 🧪 Try your first `@librarian` query
5. 🔄 Build your workflow rhythm

---

## 📝icense & Attribution

ADRION 369 System created with:

- **Ollama** (MIT License)
- **Aider** (Apache 2.0)
- **DeepSeek-Coder** (MIT License)

---

**Version:** 4.0
**Last Updated:** April 11, 2026
**Status:** PRODUCTION-GRADE (83%+ test coverage, CI/CD gated)

**🚀 Your local AI coding army is ready to go!**
