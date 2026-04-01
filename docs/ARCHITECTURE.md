# ADRION 369 - Architecture & System Design

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│         Ollama Local LLM Server (Port 11434)         │
│         Running DeepSeek-Coder-V2 Model             │
└───────────────────┬─────────────────────────────────┘
                    │
                    │ OpenAI-Compatible API
                    │
┌───────────────────▼─────────────────────────────────┐
│            Aider (AI Pair Programmer)               │
│     Handles multi-turn conversation & edits         │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
   ┌────────┐  ┌──────────┐  ┌────────┐
   │ Persona│  │ Persona  │  │Persona │ ...
   │Routing │  │ System   │  │Context │
   └────────┘  └──────────┘  └────────┘
        │           │           │
        └───────────┼───────────┘
                    │
        ┌───────────▼──────────────┐
        │  Genesis Record (Logs)   │
        │   .aider/logs/*.log      │
        └─────────────────────────┘
```

---

## 📍 Key Components

### 1. **Ollama (Local LLM Server)**
- **Port:** `localhost:11434`
- **Model:** `deepseek-coder-v2:16b` (or `:lite`)
- **Protocol:** OpenAI-compatible API
- **Inference:** 100% local, no cloud calls

### 2. **Aider (AI Pair Programmer)**
- **Config:** `.aider/config.yml`
- **Connection:** OpenAI-compatible client
- **Features:** Multi-file editing, debate mode, streaming

### 3. **Six Personas**
- **Librarian:** History & context analysis
- **SAP:** Strategic planning
- **Auditor:** Quality validation
- **Sentinel:** Error monitoring & rapid response
- **Architect:** Design authority
- **Healer:** Optimization & technical debt

### 4. **Genesis Record (Logging)**
- **Location:** `.aider/logs/`
- **Contents:** All sessions, decisions, changes
- **Privacy:** Local only, never transmitted

---

## 🔄 Workflow: Normal Mode

```
User Request
    │
    ▼
┌─────────────────────────┐
│ 1. LIBRARIAN            │  Analyze: History, Structure, Context
│    - Git analysis       │
│    - Code structure     │
│    - Dependencies       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 2. SAP                  │  Plan: Prioritize tasks, assess risk
│    - Create plan        │
│    - Prioritize tasks   │
│    - Risk assessment    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 3. ARCHITECT (Optional) │  Design: New patterns, interfaces
│    - Design review      │
│    - Pattern validation │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 4. Implementation       │  Execute changes, modify code
│    - Code changes       │
│    - Git commits        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 5. AUDITOR              │  Validate: Tests, quality, safety
│    - Run tests          │
│    - Check quality      │
│    - Verify regressions │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 6. SENTINEL             │  Monitor: Errors, warnings
│    - Error detection    │
│    - Performance check  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 7. HEALER (Background)  │  Optimize: Refactor, improve
│    - Technical debt     │
│    - Performance tune   │
│    - Documentation      │
└────────────┬────────────┘
             │
             ▼
         Session Complete
```

---

## 🚨 Workflow: Crisis Mode

```
Critical Error Detected
    │
    ▼
┌─────────────────────────┐
│ SENTINEL (Immediate)    │  ⚡ < 1 second response
│ - Detect error          │
│ - Generate hotfix       │
│ - Deploy fix            │
│ - Verify stability      │
└────────────┬────────────┘
             │
             ▼
    Crisis Now Resolved
    Or Requires Escalation
    │
    ▼ (if recurring)
┌─────────────────────────┐
│ Escalate to HEALER      │  Deep analysis & prevention
│ for root cause analysis │
└────────────────────────┘
```

---

## 🔮 Workflow: Healing Mode

```
Background Cycle (Every 4 hours)
    │
    ▼
┌─────────────────────────┐
│ HEALER Init             │
│ - Inventory debt        │
│ - Prioritize work       │
└────────────┬────────────┘
             │
             ├─► Refactoring (reduce complexity)
             │
             ├─► Testing (increase coverage)
             │
             ├─► Documentation (clarity)
             │
             ├─► Dependencies (update)
             │
             └─► Performance (optimize)
                     │
                     ▼
        ┌────────────────────────┐
        │ AUDITOR Validates      │
        │ - No regressions       │
        │ - Tests pass           │
        │ - Quality maintained   │
        └────────────┬───────────┘
                     │
                     ▼
               Session Logged
           (Genesis Record)
```

---

## 📊 Data Flow: Session Lifecycle

```
START
  │
  ├─► Load config from .aider/config.yml
  ├─► Connect to Ollama (http://localhost:11434/v1)
  ├─► Load persona system from config/personas.yml
  │
  ├─► USER INPUT
  │   │
  │   ├─► PARSE: Which persona(s) involved?
  │   ├─► BUILD: Construct system prompt + context
  │   ├─► CALL: Send to Ollama API
  │   ├─► STREAM: Receive response tokens
  │   │
  │   └─► PROCESS: Execute code changes if needed
  │
  └─► LOG: Write to Genesis Record
         (.aider/logs/session.log)
         - Input
         - Persona responses
         - Code changes
         - Decisions

END OF SESSION
```

---

## 🔐 Security Guarantees (Law 7)

| Component | Local? | Encrypted? | Logged? |
|-----------|--------|-----------|---------|
| Ollama Inference | ✅ | N/A | ✅ Local |
| Aider Session | ✅ | N/A | ✅ Local |
| Code Changes | ✅ | N/A | ✅ Git |
| Logs | ✅ | Optional | ✅ Local |
| API Calls | ✅ Localhost only | N/A | ✅ Local |

**No external services. No data export. Full ownership.**

---

## 🎯 Integration Points

### VS Code Integration
- Settings: `.vscode/settings.json`
- Tasks: `.vscode/tasks.json` (for Aider launcher)
- Commands: Custom commands (optional)

### Git Integration
- Hook: Auto-commit after persona validation
- Message Template: Includes persona name + action
- Log: All changes attributed to personas

### Logging Integration
- Format: Structured JSON logs
- Rotation: 90-day retention
- Analysis: Available for post-hoc review

---

## 📈 Scaling Considerations

### Single Developer
- Standard setup: 1 Ollama instance, 1 Aider session
- Recommended: `deepseek-coder-v2:16b`

### Team (Shared Ollama)
- Setup: Central Ollama server
- Network: Aider clients connect to shared instance
- Config: Point `openai-api-base` to shared Ollama

### CI/CD Integration
- Invoke personas from pipeline
- Automate quality gates (Auditor persona)
- Log decisions to Genesis Record

---

## 🔧 Extension Architecture

The persona system is extensible:

1. **Add new persona:** Add entry to `config/personas.yml`
2. **Custom tools:** Extend tool allowlist per persona
3. **Custom workflows:** Chain personas in new orders
4. **Custom output formats:** Define new response types

---

**Last Updated:** March 29, 2026  
**Architecture Version:** 1.0  
**Design Authority:** ARCHITECT Persona
