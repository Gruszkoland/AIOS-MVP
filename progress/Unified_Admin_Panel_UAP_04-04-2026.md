# Unified Admin Panel (UAP) — ADRION 369 v4.0

**Data Startu**: 2026-04-04
**Status**: Plan → Implementation
**Autor**: Claude Code + Master Orchestrator
**Tier**: 3 (Funkcjonalny)
**Wysiłek**: 3-4 tygodnie

---

## 1. SCOPE (5 Moduły)

### 1.1 **Control HQ**

- Trinity scores (Material, Intellectual, Essential) w real-time
- Trust Score per Agent heatmap (9 personas, 0.0-1.0 range)
- Guardian Laws status (9 laws, pass/fail per operation)
- Threat vectors (A-01 do A-12) live dashboard

### 1.2 **Agent Delegator**

- Natural Language Task Input (textarea)
- Automatic persona routing (EBDI + TSPA)
- **Dry Run Mode (DRM)** — diff preview dla destruktywnych operacji
- Execution log + stderr/stdout capture
- Manual approval button (przed destructive ops)

### 1.3 **Genesis Viewer**

- Searchable audit trail (wszystkie operacje loggowane)
- Filter: persona, timestamp, status, law violations
- Export: JSON, CSV
- Timeline visualization (decision history)

### 1.4 **Orchestrator Console**

- Crisis Mode trigger (Arousal > 0.7)
- Conflict Resolver voting UI (gdy 2+ personas sprzeczne propozycje)
- Rollback Checkpoint viewer (RBC snapshots)
- Session Continuity Bridge (SCB) snapshots

### 1.5 **Self-Healing Dashboard**

- Healer persona suggestions (tech debt, optimizations)
- Performance heatmap (CPU, RAM, DB queries)
- Trust Score recovery status (agents < 0.6)
- Action history (what Healer fixed last 24h)

---

## 2. TECHNOLOGIA

### Frontend

- **Framework**: Vanilla HTML/CSS/JS (+ Bootstrap 5 dla responsiveness)
- **Port**: 8003 (oddzielny od istniejących: 9000, 5678, 1740)
- **WebSocket**: Real-time updates (Trinity scores, EBDI PAD)

### Backend (New API Layer)

- **Port**: 8002 (`/mapi/v1/`)
- **Framework**: Flask minimal extension
- **Endpoints**: Task delegation, Genesis queries, checkpoint restore
- **Auth**: API key (simple, local-only)

### Integration Points

- PostgreSQL: Genesis Record logs + checkpoints
- Ollama: LLM for natural language → routing logic
- Existing arbitrage APIs: `/api/arbitrage/*` proxied
- WebSocket server: real-time metrics push

---

## 3. CORE WORKFLOW

```
User Input (NL Task)
    ↓
[Route via EBDI + TSPA] → Select best persona
    ↓
[Generate Plan] → MCTS graph exploration
    ↓
[DSV Validator] → Check Input→Output signature
    ↓
IF destructive_op:
    [DRM] → Show diff, ask approval
ELSE:
    [Execute immediately]
    ↓
[SAV] → Step auto-verification (Definition of Done)
    ↓
IF pass: Log to Genesis, update Trust Score (+0.05)
IF fail: Log error, TS (-0.20), propose Healer fix
    ↓
[Update Dashboard] → Real-time UI refresh
```

---

## 4. KEY FEATURES

### 4.1 Master Orchestrator Integration

- **Delegation Protocol**: `/mapi/v1/task/delegate` endpoint
- **DSPy Signature Validator**: Pre-execution Input→Output check
- **Trust Score per Agent (TSPA)**: Block if TS < 0.6
- **Conflict Resolver (CR)**: Weighted voting if 2+ personas disagree

### 4.2 Dry Run Mode (DRM)

```
POST /mapi/v1/task/simulate
{
  "task": "git reset --hard origin/main",
  "agent": "SAP",
  "dry_run": true
}
→ Response:
{
  "diff": "--- Current state\n+++ After execution",
  "affected_files": ["file1.py", "file2.go"],
  "requires_approval": true,
  "approval_token": "dXBjUVQtLTgtNDI..."
}
```

### 4.3 Genesis Viewer

- Full-text search w logu operacji
- Timeline: każda decyzja, każdy agent action, każda anomalia
- Export auditability dla compliance

### 4.4 Live EBDI Telemetry

- **Arousal** heatmap (crisis detection)
- **Pleasure/Dominance** gauge
- Per-persona PAD vectors

---

## 5. IMPLEMENTATION PHASES

### Phase 1 — Foundation (Week 1)

- [ ] API skeleton (`/mapi/v1/task/delegate`)
- [ ] Frontend HTML structure (5 modules)
- [ ] WebSocket server (real-time metrics push)
- [ ] Database schema (Genesis access, RBC snapshots)

### Phase 2 — Core Logic (Week 2)

- [ ] Natural language parsing → persona routing
- [ ] MCTS graph builder (Drafting step)
- [ ] Dry Run Mode implementation
- [ ] SAV (Step Auto-Verification) validation

### Phase 3 — Dashboards (Week 2-3)

- [ ] Control HQ visualization
- [ ] Genesis Viewer search UI
- [ ] Orchestrator Console (Crisis mode, CR voting)
- [ ] Self-Healing Dashboard (Healer suggestions)

### Phase 4 — Hardening (Week 3-4)

- [ ] Integration tests (UAP ↔ arbitrage APIs)
- [ ] Error handling + retry logic
- [ ] Rate limiting on `/mapi/v1/` endpoints
- [ ] Documentation + user guide

---

## 6. API SPECIFICATION (Draft)

### Base URL: `http://localhost:8002/mapi/v1/`

#### Task Delegation

```
POST /task/delegate
{
  "task_description": "Find all XRP arbitrage opportunities under $5",
  "agent_hint": "scout",  # optional
  "dry_run": false,
  "budget_max": 500  # optional constraints
}
→ 200 OK:
{
  "task_id": "upc-q8-42-daa",
  "status": "submitted|pending_approval|executing|completed|failed",
  "assigned_agent": "SAP",
  "trust_score": 0.85,
  "created_at": "2026-04-04T10:30:00Z",
  "result": {...}
}
```

#### Task Status

```
GET /task/{task_id}
→ Get execution status, logs, errors
```

#### Genesis Records

```
GET /genesis/logs?agent=SAP&since=2h&status=completed
→ Return filtered audit trail entries
```

#### Checkpoint Restore

```
POST /checkpoint/restore
{
  "checkpoint_id": "rbc-2026-04-04-08-15"
}
→ Git stash pop + session state restore
```

---

## 7. SECURITY & GOVERNANCE

✅ **Guardian Laws Enforced:**

- G1 (Unity) — Single source of truth (Genesis Record)
- G5 (Transparency) — All actions logged, reversible
- G7 (Privacy) — Local-only, no cloud export
- G8 (Nonmaleficence) — DRM prevents accidental destructive ops

✅ **Trust Score System:**

- TSPA < 0.6 → Agent blocked
- Success +0.05, Error −0.20
- UI shows Trust Score heatmap per persona

✅ **Rate Limiting:**

- Per-user: 100 tasks/hour
- Per-endpoint: 1000 req/min
- Burst protection: Token bucket

---

## 8. SUCCESS CRITERIA

- ✅ UAP accessible at `http://localhost:8003`
- ✅ All 5 modules functional (Control HQ, Delegator, Genesis, Console, Healer)
- ✅ Dry Run Mode working for destructive ops
- ✅ Genesis Viewer searchable (50+ test log entries)
- ✅ Real-time WebSocket telemetry (< 500ms latency)
- ✅ 95%+ Test coverage for `/mapi/v1/` endpoints
- ✅ Integration tests pass (UAP ↔ arbitrage ↔ n8n)
- ✅ User guide + API docs (OpenAPI schema)

---

## 9. NEXT STEPS

1. **Confirm scope** — Are 5 modules correct?
2. **Specify UI** — Wireframe preferences?
3. **Choose template** — Bootstrap, Tailwind, or custom?
4. **Auth strategy** — Simple API key or JWT?
5. **Deployment** — Docker Compose update needed?

**Status**: Awaiting approval to proceed with Phase 1.
