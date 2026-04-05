# MCP ARCHITECTURE — ADRION 369 v4.0

**Version:** 1.0 | **Date:** 2026-04-05 | **Status:** Architecture Design

---

## 📐 Overview

ADRION 369 MCP (Model Context Protocol) infrastructure provides **declarative routing** across the **162D decision space** through 5 specialized MCP servers. Each server implements DSPy-style signatures (Input → Output) and operates within the **Trinity-EBDI framework** (Material, Intellectual, Essential perspectives).

### Architecture Pillars

1. **Deklaratywne Potoki (DSPy Logic)** — Precyzyjne sygnatury dla każdego agenta
2. **162D Decision Space** — $ 3 \times 6 \times 9 = 162 $ wymiarów (Perspective × Agent × Guardian Law)
3. **9 Guardian Laws** — Hard veto na każdym kroku (non-negotiable compliance)
4. **Trust Score per Agent (TSPA)** — Dynamic gating (TS < 0.6 → escalate to Arbiter)
5. **Local-First Genesis Record** — Zero data export, RAG-based session continuity

---

## 🏗️ MCP Server Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (Aider, Copilot)            │
└────────────────────┬────────────────────────────────────────┘
                     │ DSPy Input Signatures
                     ↓
    ┌────────────────────────────────────────────────────┐
    │            ROUTING LAYER (Gating System)           │
    │  • Trust Score validation (TSPA)                   │
    │  • Crisis Mode detection (EBDI Arousal > 0.7)     │
    │  • Conflict resolution (CR voting)                 │
    └────────┬──────────┬──────────┬──────────┬──────────┘
             │          │          │          │
        ┌────▼─┐   ┌────▼─┐  ┌────▼─┐  ┌────▼─┐  ┌────▼──┐
        │VORTEX│   │GUARD.│  │ORACLE│  │GENESIS│  │HEALER│
        │ MCP  │   │ MCP  │  │ MCP  │  │ MCP   │  │ MCP  │
        └────┬─┘   └────┬─┘  └────┬─┘  └────┬──┘  └────┬──┘
             │          │          │         │          │
    ┌────────┴──────────┴──────────┴─────────┴──────────┴──────┐
    │         PERSISTENCE LAYER (Genesis Record + RAG)        │
    │  • Session state (PostgreSQL)                           │
    │  • Decision logs (append-only)                          │
    │  • Rollback checkpoints (git-based)                     │
    └─────────────────────────────────────────────────────────┘
```

---

## 📋 MCP Server Specifications

### 1️⃣ **VORTEX-MCP** — Harmonic Orchestration (174Hz)

**Rola:** Docker API gateway, health monitoring, canary deployment gates

**DSPy Signature:**

```
class VortexOrchestration(dspy.Signature):
    """Coordinate 174Hz harmonic system execution"""
    service_name: str = dspy.InputField()
    action: str = dspy.InputField(desc="start|stop|escalate|rollback")
    constraints: dict = dspy.InputField(desc="EBDI PAD thresholds, timeout")
    
    execution_result: dict = dspy.OutputField()
    telemetry: dict = dspy.OutputField(desc="latency, resource usage")
    compliance_check: bool = dspy.OutputField(desc="✅ within 9 Guardian Laws")
```

**Endpoints:**
- `POST /vortex/health` — System telemetry
- `POST /vortex/deploy` — Managed deployment with canary gates
- `POST /vortex/rollback` — Atomic rollback to last checkpoint

**Integration Points:**
- Docker Compose orchestrator
- Prometheus metrics
- Grafana dashboards

---

### 2️⃣ **GUARDIAN-MCP** — Policy Enforcement (9 Laws)

**Rola:** Validator for all operations against Guardian Laws, audit logging

**DSPy Signature:**

```
class GuardianValidation(dspy.Signature):
    """Validate action compliance with 9 Guardian Laws"""
    action_description: str = dspy.InputField()
    agent_requesting: str = dspy.InputField()
    context: dict = dspy.InputField()
    
    is_compliant: bool = dspy.OutputField()
    violated_laws: list = dspy.OutputField(desc="G1-G9 indices if any")
    remediation: str = dspy.OutputField(desc="corrective action")
    audit_entry: dict = dspy.OutputField()
```

**9 Guardian Laws:**
1. **G1 — Unity** (Spójność systemu)
2. **G2 — Harmony** (Brak konfliktów wewnętrznych)
3. **G3 — Rhythm** (Ciągłość czasowa)
4. **G4 — Causality** (Przyczynowość logiczna)
5. **G5 — Transparency** (Pełna obserwowalność)
6. **G6 — Authenticity** (Brak manipulacji)
7. **G7 — Privacy** (Local-first, zero export)
8. **G8 — Nonmaleficence** (Brak szkody)
9. **G9 — Sustainability** (Długotrwałość)

**Endpoints:**
- `POST /guardian/validate` — Pre-execution validation
- `GET /guardian/audit-log` — Compliance history
- `POST /guardian/override-request` — Escalation to Arbiter

---

### 3️⃣ **ORACLE-MCP** — 162D Decision Making

**Rola:** Route decisions through 162D space, LLM integration, pattern matching

**DSPy Signature:**

```
class Oracle162DRouting(dspy.Signature):
    """Route decision through 162D space (3×6×9 grid)"""
    decision_prompt: str = dspy.InputField()
    perspective: str = dspy.InputField(desc="Material|Intellectual|Essential")
    agent_pool: list = dspy.InputField(desc="candidate agents")
    
    selected_agent: str = dspy.OutputField()
    reasoning: str = dspy.OutputField(desc="why this agent + perspective")
    confidence: float = dspy.OutputField(desc="0.0-1.0")
    fallback_agents: list = dspy.OutputField()
```

**The 162D Space:**

```
Material Perspective (3 dims):
  • ROI efficiency
  • Resource cost
  • Execution speed

Intellectual Perspective (3 dims):
  • Algorithm purity
  • Logical consistency
  • Proof validity

Essential Perspective (3 dims):
  • Guardian Law alignment
  • Ethical correctness
  • Sustainability

× 6 Agents (LIBRARIAN, SAP, AUDITOR, SENTINEL, ARCHITECT, HEALER)
× 9 Guardian Laws (G1-G9)
= 3 × 2 × 3 × 6 × 9 = 162D
```

**Endpoints:**
- `POST /oracle/route` — Intelligent agent selection
- `POST /oracle/rank-agents` — Trust Score-weighted ranking
- `GET /oracle/decision-history` — Audit trail

---

### 4️⃣ **GENESIS-MCP** — Record Management & RAG

**Rola:** Session persistence, decision logs, RAG-based context retrieval

**DSPy Signature:**

```
class GenesisRecordPersistence(dspy.Signature):
    """Manage session state and decision archival"""
    session_id: str = dspy.InputField()
    event_type: str = dspy.InputField(desc="decision|checkpoint|error|audit")
    payload: dict = dspy.InputField()
    
    record_id: str = dspy.OutputField()
    archived: bool = dspy.OutputField()
    rag_indexed: bool = dspy.OutputField()
```

**Storage Structure:**

```
Genesis Record/
├── 10_RAPORTY_DZIALANIA_SYSTEMU/
│   ├── PLAN/Topic_DD-MM-YYYY.md
│   ├── PROGRESS/Topic_DD-MM-YYYY.md
│   └── REPORTS/Topic_DD-MM-YYYY.md
├── session-states/
│   └── {session_id}.json (checkpoint)
├── decision-logs/
│   └── {date}.jsonl (append-only)
└── rag-index/
    └── embeddings.pkl (vector store)
```

**Endpoints:**
- `POST /genesis/checkpoint` — Save session state
- `POST /genesis/log-decision` — Append decision to log
- `GET /genesis/rag-retrieve` — Query historical context
- `POST /genesis/rollback` — Restore from checkpoint

---

### 5️⃣ **HEALER-MCP** — Autonomous Recovery

**Rola:** Automated error Detection, self-healing, metric monitoring, alerts

**DSPy Signature:**

```
class HealerAutoRecovery(dspy.Signature):
    """Detect anomalies and trigger self-healing"""
    telemetry: dict = dspy.InputField(desc="EBDI PAD, metrics, logs")
    alert_config: dict = dspy.InputField()
    
    anomaly_detected: bool = dspy.OutputField()
    severity: str = dspy.OutputField(desc="info|warning|critical")
    proposed_action: str = dspy.OutputField()
    executed: bool = dspy.OutputField()
    result: dict = dspy.OutputField()
```

**Recovery Actions:**
- **Automatic:** Log rotation, cache clear, connection reset (severity ≤ warning)
- **Manual:** User approval required (severity = critical)
- **Rollback:** Atomic git commit revert (destructive operations)

**Endpoints:**
- `GET /healer/health` — Current system health
- `POST /healer/analyze` — Anomaly detection
- `POST /healer/execute-recovery` — Trigger healing action
- `GET /healer/recovery-history` — Audit trail

---

## 🔄 Operational Flow (KROK 1-5 LOOP)

### KROK 1: Sensing & Routing (MoE Gating)

1. Odbierz bodziec od użytkownika/systemu
2. **Telemetria EBDI live (TEL)** — Sprawdź PAD każdego agenta
3. If `Arousal > 0.7` → Crisis Mode → SENTINEL escalation
4. **Trust Score per Agent (TSPA)** — Validacja TS >= 0.6
5. Route do ORACLE-MCP dla 162D selection

### KROK 2: Graph-of-Thoughts & Speculative Drafting

1. ORACLE-MCP generuje wstępne rozwiązania (parallel exploration)
2. **Conflict Resolver (CR)** — Multiple agents → TS-weighted voting
3. **Dry Run Mode (DRM)** — Destructive ops require user approval (diff preview)

### KROK 3: Self-Correction (STaR + SimPO)

1. AUDITOR-MCP conducts internal audit
2. Verify logical correctness (backward rationalization)
3. HEALER-MCP checks agent health (EBDI baseline)

### KROK 4: Action & Genesis Record

1. Execute solution (file writes, terminal commands)
2. Update `progress/<TOPIC>.md` (append-only)
3. Genesis Record entry (9-point micro-summary)
4. Update Trust Score: Success +0.05, Error −0.20

### KROK 5: Structured Output

1. Mini-spis technicznych akcji
2. Decyzja katalityczna (forced binary choice)
3. Mierzalny efekt

---

## 🛡️ 10 Mechanizmy Bezpieczeństwa

| # | Mechanizm | Trigger | Akcja |
|---|-----------|---------|-------|
| 1 | **TSPA** | TS < 0.6 | Blokada, eskalacja do Arbitra |
| 2 | **SAV** | Koniec kroku | Walidacja Definition of Done |
| 3 | **RBC** | Co 5 kroków / destrukcja | `git stash` + snapshot |
| 4 | **SCB** | Start/koniec sesji | Export/import RAG |
| 5 | **CWM** | Kontekst > 80% | Recursive Summarization |
| 6 | **CR** | Sprzeczne decyzje | TS-weighted voting |
| 7 | **DSV** | Przed egzekucją | Input→Output validation |
| 8 | **DRM** | Destruktywne ops | Diff bez zapisu → akceptacja |
| 9 | **TEL** | Routing | Alarm Arousal > 0.7 |
| 10 | **PHM** | Audyt | Identity Reset po >3 odchyleniach |

---

## 📍 Deployment Topology

### Local (DEV)

```yaml
mcp-servers:
  vortex-mcp: localhost:9000
  guardian-mcp: localhost:9001
  oracle-mcp: localhost:9002
  genesis-mcp: localhost:9003
  healer-mcp: localhost:9004

routing:
  primary: localhost:9100 (aggregator)
  fallback: direct per-server
```

### Docker (PROD)

```yaml
services:
  vortex-mcp:
    image: adrion-vortex-mcp:latest
    ports: ["9000:9000"]
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
      - LOG_LEVEL=info

  guardian-mcp:
    image: adrion-guardian-mcp:latest
    ports: ["9001:9001"]
    volumes:
      - ./Genesis\ Record:/app/genesis
      - ./docs/guardian-laws.yaml:/app/config/laws.yaml

  oracle-mcp:
    image: adrion-oracle-mcp:latest
    ports: ["9002:9002"]
    environment:
      - OLLAMA_API_BASE=http://ollama:11434
      - VECTORDB_PATH=/app/vectors

  genesis-mcp:
    image: adrion-genesis-mcp:latest
    ports: ["9003:9003"]
    environment:
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/genesis

  healer-mcp:
    image: adrion-healer-mcp:latest
    ports: ["9004:9004"]
    environment:
      - PROMETHEUS_URL=http://prometheus:9090
      - ALERT_WEBHOOK=http://alert-handler:5000/alert
```

---

## 📋 Integration Checklist

- [ ] MCP SDK (mcp-python) installed
- [ ] 5 server directories created
- [ ] DSPy signatures implemented per server
- [ ] Docker tier `06-mcp-servers` added
- [ ] E2E tests passing (Aider CLI invocation)
- [ ] Genesis Record linked
- [ ] KPI Dashboard updated
- [ ] Production rollout checklist approved

---

**Next:** Faza 2 — Implementacja 5 MCP Servers
