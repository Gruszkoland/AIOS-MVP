# ADRION 369 v2.0 - Advanced AI System

## Overview

**ADRION 369 v2.0** is an elite, security-hardened autonomous execution environment based on the **Trinity-EBDI** framework. It orchestrates high-performance components across Go and Python to deliver predictive intelligence (Vortex Oracle) and real-time governance.

### 🚀 Key Innovations (v2.0)

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

## 🏗️ Architecture

- **vortex-core (Go)**: High-speed API and system telemetry.
- **quantum-oracle (Python)**: Strategic arbitrage and predictive analysis.
- **n8n-adrion**: Workflow orchestration and stream connectors.
- **Genesis Record**: Unified local storage for all decisions and logs.

---

## 🧠 The Swarm Personas

| Persona       | Role                | Law                      | Trigger      |
| ------------- | ------------------- | ------------------------ | ------------ |
| **LIBRARIAN** | Knowledge Archiver  | 1: Historical Continuity | `@librarian` |
| **SAP**       | Strategic Planner   | 2: Strategic Coherence   | `@sap`       |
| **AUDITOR**   | Quality Overseer    | 3: Non-Regression        | `@auditor`   |
| **SENTINEL**  | Error Guardian      | 4: Rapid Response        | `@sentinel`  |
| **ARCHITECT** | Design Authority    | 5: Unified Design        | `@architect` |
| **HEALER**    | Optimization Engine | 6: Continuous Healing    | `@healer`    |

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

## �📁 Project Structure

```
.
├── .github/
│   └── copilot-instructions.md          # Global system instructions
├── .vscode/
│   ├── settings.json                    # VS Code configuration
│   └── tasks.json                       # Aider launcher tasks
├── .aider/
│   ├── config.yml                       # Aider + Ollama configuration
│   └── logs/                            # Genesis Record (session logs)
├── config/
│   └── personas.yml                     # 6 persona definitions + system prompts
├── persona-agents/                      # Individual persona agent files
│   ├── librarian.agent.md
│   ├── sap.agent.md
│   ├── auditor.agent.md
│   ├── sentinel.agent.md
│   ├── architect.agent.md
│   └── healer.agent.md
├── docs/
│   ├── INSTALL.md                       # Installation & setup guide
│   ├── ARCHITECTURE.md                  # System design & data flow
│   ├── LAWS.md                          # The 9 governing laws explained
│   ├── WORKFLOW.md                      # How to use the personas
│   └── TROUBLESHOOTING.md               # Common issues & fixes
└── README.md                            # This file
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

## ⚖️ The Nine Governing Laws

1. **Historical Continuity** - Never erase institutional knowledge
2. **Strategic Coherence** - All actions align with long-term goals
3. **Non-Regression** - No change degrades existing functionality
4. **Rapid Response** - Errors demand sub-second intervention
5. **Unified Design** - All components follow shared principles
6. **Continuous Healing** - System grows more resilient over time
7. **Privacy Protection** - Genesis Record: local-only logging
8. **Transparency in Reasoning** - Every decision is explained
9. **Fail-Safe Defaults** - When uncertain, be conservative

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

**Version:** 1.0  
**Last Updated:** March 29, 2026  
**Status:** ✅ READY FOR DEPLOYMENT

**🚀 Your local AI coding army is ready to go!**
