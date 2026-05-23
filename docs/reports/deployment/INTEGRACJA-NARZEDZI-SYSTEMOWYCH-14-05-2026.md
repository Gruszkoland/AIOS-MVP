# 🔧 ANALIZA NARZĘDZI SYSTEMOWYCH — Integracja z ADRION 369

**Data:** 14.05.2026  
**Źródło:** 3 dokumenty z Desktop/WDROŻENIE w Copilot  
**Cel:** Mapowanie narzędzi systemowych do architektury 33 agentów (32 Gems + Chronos)  

---

## 📊 PRZEGLĄD NARZĘDZI (7 total)

### Tier 1: EXECUTION LAYER (CLI & Terminal)

| Tool | Role | Status | Integration Point |
|------|------|--------|-------------------|
| **Warp** | Structured CLI blocks | ✅ READY | Arbitrage API (8001) → Shell commands |
| **PowerToys** | OS-level triggers | ✅ READY | Vortex Engine (8003) → System hooks |
| **Raycast** | macOS automation | ✅ READY | Alert-Handler → Quick actions |

**Funkcjonalność:** Zamiast czytać chaotyczne logi, agent odpytuje Warp o strukturalne bloki (stdout/stderr/exit_code) — drastycznie zmniejsza halucynacje.

**Problem:** Dotychczas brak natywnego integrowania tego w arbitrage_server.py. Narzędy są „na boku" — mogą być wezwane, ale nie są automatyzowane w pipeline.

---

### Tier 2: BROWSER ISOLATION (Workspace Separation)

| Tool | Role | Status | Integration Point |
|------|------|--------|-------------------|
| **Zen Browser** | Profile-based isolation | ✅ READY | MCP: oracle.py (web scraping) |
| **Arc Browser** | Spaces for segmentation | ✅ READY | MCP: router.py (task distribution) |

**Funkcjonalność:** Każdy agent pracuje w hermetycznym profilu — żaden cookie spill, wszystkie sesje niezależne.

**Problem:** Przeglądarki to UI-driven — trudne do automatyzacji dla headless agentów. Potrzebna warstwa „browser remote protocol" (np. Playwright, Puppeteer).

---

### Tier 3: SYSTEM SANITIZATION (State Cleanup)

| Tool | Role | Status | Integration Point |
|------|------|--------|-------------------|
| **Revo Uninstaller** | Deep OS cleanup | ✅ READY | Adrion-Backup (scheduled) |

**Funkcjonalność:** Po cyklu testowym, Revo przywraca OS do czystego stanu (brak registry pollution, ghost files).

**Problem:** Windows-specific, nie obsługiwane na Linux/Mac. W dockerized environment (ADRION 369) mniej istotne (kontenery są izolowane).

---

### Tier 4: P2P DATA TRANSFER

| Tool | Role | Status | Integration Point |
|------|------|--------|-------------------|
| **Blip** | Wireless P2P file transfer | ✅ READY | Backend API (8002) → Mobile nodes |

**Funkcjonalność:** Agent na telefonie wysyła dane do lokalnego węzła bez chmury (niskie opóźnienia, prywatność).

**Problem:** Niche use-case. Obecny ADRION stack nie ma mobilnych agentów. Byłoby istotne w przyszłej ekspansji.

---

## 🧩 MAPOWANIE DO ADRION 369 ARCHITECTURE

### Current State (12 Docker Services)

```
┌─ PostgreSQL (genesis_record)
│
├─ Loki + Promtail (log aggregation)
├─ Ollama (LLM engine)
├─ n8n (workflows)
│
├─ Vortex-Engine (174Hz orchestration)
├─ Adrion-Healer (self-healing)
│
├─ Arbitrage API (8001)
├─ Backend API (8002)
├─ Alert-Handler
├─ Adrion-Backup
│
├─ Nginx (ingress)
├─ Grafana (dashboards)
└─ Prometheus (metrics)
```

### Proposed Integration Points (Tools)

```
EXECUTION LAYER (Tier 2)
├─ Warp Integration:
│  └─ Arbitrage API (8001) —[spawn CLI]→ Warp Blocks
│     Problem: Current shell invocations use subprocess.run()
│     Fix: Implement structured block parser (JSON wrapper around Warp)
│
├─ PowerToys Integration:
│  └─ Vortex-Engine (8003) —[hook into]→ PowerToys plugins
│     Problem: Vortex runs in Docker (isolated)
│     Fix: Mount /dev/input or use D-Bus on Linux, WinRM on Windows
│
└─ Raycast Integration:
   └─ Alert-Handler —[trigger]→ Raycast quick actions
      Problem: macOS-only, requires Raycast daemon
      Fix: Abstract to shell command, make OS-agnostic

BROWSER TIER (Tier 3)
├─ Zen Browser + Arc:
│  └─ MCP: oracle.py (web scraping) + router.py
│     Problem: Headless execution requires browser remote protocol
│     Fix: Replace with Playwright/Selenium library
│
CLEANUP TIER (Tier 4)
├─ Revo Uninstaller:
│  └─ Adrion-Backup (scheduled cleanup)
│     Problem: Windows-specific, Docker containers don't need it
│     Fix: Implement Docker-native cleanup (prune volumes, clear cache)

P2P TIER (Tier 5)
└─ Blip Transfer:
   └─ Backend API (8002) —[P2P]→ Mobile node (future)
      Problem: Not currently implemented
      Fix: Add optional P2P module when mobile agents planned
```

---

## 🚨 CRITICAL GAPS (vs. Current State)

### Gap 1: Warp Integration NOT AUTOMATED

**Current:** `arbitrage/app.py` spawns shells with `subprocess.Popen()`

```python
# Current (bad):
proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE)
stdout, stderr = proc.communicate()  # Raw text string
# Problem: LLM hallucinates, misparses results
```

**Needed:**

```python
# Proposed (good):
warp = WarpBlockAPI()  # Structured block query
result = warp.execute_and_parse(cmd)
# Returns: {"exit_code": 0, "stdout": {...}, "stderr": {...}}
```

**Impact:** BLOCKING for reliable agent → system execution chain.

---

### Gap 2: Browser Isolation (No Headless Protocol)

**Current:** `mcp/oracle.py` scrapes web using... ? (Not visible in TEST_REPORT)

**Needed:**
- Playwright / Puppeteer wrapper
- Per-agent browser context (Profile A ≠ Profile B)
- Cookie isolation
- Screenshot capability for vision-based agents

**Impact:** HIGH for web-dependent agents (SEO, e-commerce, market analysis gems).

---

### Gap 3: PowerToys Hooks (Docker Environment)

**Current:** Vortex runs in Docker → no access to host Windows GUI

**Solutions:**
- Option A: Mount host D-Bus (Linux) / WinRM (Windows)
- Option B: Abstract to shell scripts (less powerful, but portable)
- Option C: Skip for containerized version, implement for "Agent on Desktop" mode

**Impact:** MEDIUM — orchestration works without it, but loses OS-level automation.

---

### Gap 4: Revo Cleanup (Irrelevant for Docker)

**Current:** Not needed in containerized environment

**Alternative:** Native Docker cleanup

```bash
docker system prune -a --volumes  # Remove unused containers/images/volumes
docker container prune --filter "until=24h"  # Clean up 1d+ old containers
```

**Impact:** LOW (nice-to-have, not critical).

---

### Gap 5: Blip P2P (Future)

**Current:** No mobile agents

**Needed when:** Expanding to phone/IoT tier

**Impact:** VERY LOW (not in current roadmap).

---

## 🎯 REMEDIATION ROADMAP

### Phase 1: IMMEDIATE (Today/Tomorrow)

**Priority 1A: Warp Integration**

Create: `arbitrage/execution/warp_shell.py`

```python
import json
import subprocess

class WarpBlockExecutor:
    """Structured CLI execution for LLM-safe parsing."""
    
    def execute(self, cmd: str) -> dict:
        """Execute and return structured result."""
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.split('\n'),
            "stderr": proc.stderr.split('\n'),
            "success": proc.returncode == 0
        }

# Usage in Arbitrage API:
executor = WarpBlockExecutor()
result = executor.execute("docker ps")
# Returns structured JSON for LLM to parse reliably
```

**Effort:** 2 hours  
**Blocker:** None — self-contained module

---

**Priority 1B: Abstract Browser Layer**

Create: `arbitrage/execution/browser_manager.py`

```python
from playwright.async_api import async_playwright

class BrowserPool:
    """Isolated browser contexts per agent."""
    
    async def new_context(self, agent_id: str):
        """Create isolated context (no cookie spill)."""
        browser = await self.playwright.chromium.launch()
        context = await browser.new_context(
            proxy={"server": f"socks5://localhost:9050+{agent_id}"}
        )
        return context

# Usage: Each gem gets isolated browser
context_a = await pool.new_context("MPG")
context_b = await pool.new_context("SEO")
# No cookie collision
```

**Effort:** 4 hours  
**Blocker:** Install playwright — `pip install playwright`

---

### Phase 2: SHORT-TERM (This Week)

**Priority 2A: PowerToys Abstraction**

Create: `arbitrage/execution/system_hooks.py`

```python
import platform
import subprocess

class SystemAutomation:
    """Platform-agnostic OS automation."""
    
    def run_quick_action(self, action: str, params: dict):
        """Abstract layer for OS automation."""
        if platform.system() == "Windows":
            # Use PowerToys via WinRM
            self._run_powertoys_action(action, params)
        elif platform.system() == "Darwin":
            # Use Raycast applescript
            self._run_raycast_action(action, params)
        else:
            # Linux: use dbus
            self._run_dbus_action(action, params)
```

**Effort:** 6 hours  
**Blocker:** Requires host access (not available in pure Docker).

---

**Priority 2B: Guardian Laws Extension**

Add to `arbitrage/guardian.py`:

```python
# New Law: G12_ToolIntegrity
class G12_ToolIntegrity:
    """Verify external tool execution safety."""
    
    def evaluate(self, tool_name: str, params: dict) -> bool:
        """Check if tool invocation is safe."""
        # Whitelist: allow only known tools
        whitelist = ["Warp", "Playwright", "n8n", "Ollama"]
        
        if tool_name not in whitelist:
            return False  # DENY unknown tools
        
        # Validate params (no injection attacks)
        if self._has_injection_pattern(params):
            return False  # DENY
        
        return True  # APPROVE
```

**Effort:** 3 hours  
**Blocker:** None — extends existing framework.

---

### Phase 3: MEDIUM-TERM (2-3 weeks)

**Priority 3: Testing & Integration**

Create: `tests/test_system_integration.py`

```python
@pytest.mark.asyncio
async def test_warp_shell_execution():
    """Verify structured CLI execution."""
    executor = WarpBlockExecutor()
    result = executor.execute("echo 'test'")
    assert result["exit_code"] == 0
    assert result["success"] is True

@pytest.mark.asyncio
async def test_browser_isolation():
    """Verify no cookie spill between agents."""
    pool = BrowserPool()
    ctx_a = await pool.new_context("MPG")
    ctx_b = await pool.new_context("SEO")
    # Set cookie in A
    await ctx_a.goto("http://example.com")
    # Verify B doesn't see it
    cookies_b = await ctx_b.context.cookies()
    assert len(cookies_b) == 0
```

**Effort:** 8 hours  
**Blocker:** None — can run in parallel with development.

---

## 📋 INTEGRACJA Z ISTNIEJĄCYM PLANEM

### Current Deployment Plan (14.05.2026)

| Phase | Status | Tools Needed |
|-------|--------|-------------|
| **Phase 1: Pre-check** | ✅ DONE | None |
| **Phase 2: Docker Build** | ⏳ PENDING | Warp integration |
| **Phase 3: Smoke Tests** | ⏳ PENDING | Warp for structured output |
| **Phase 4: Integration Tests** | ⏳ PENDING | Browser manager for oracle tests |

### Modified Timeline

```
TODAY (14.05)
  ✅ Complete ADRION 369 analysis & deployment plan
  ⏳ Start Phase 1 Docker deployment
  ⏳ Parallel: Implement Warp integration (2h)

TOMORROW (15.05)
  ✅ Deploy Docker stack (45-60 min)
  ✅ Run smoke tests (8/8 target)
  ⏳ Implement browser manager (4h)
  ⏳ Test with oracle.py

THIS WEEK (15-17.05)
  ✅ ROPE 2.0 gap remediation (OUTPUT_SPEC, INPUT_SCHEMA)
  ⏳ Add G12_ToolIntegrity to Guardian Laws
  ⏳ System hooks abstraction (PowerToys/Raycast)
  ⏳ Unit + integration tests

NEXT WEEK (18-21.05)
  🚀 Production deployment
  🌍 Multi-region setup
```

---

## 💡 3 PROPOZYCJE WDRAŻANIA

### Opcja A: Minimal Integration (Fast Track)

**Co wdrażamy:** Warp + basic browser isolation  
**Czas:** 6-8 godzin  
**Koszt:** Niska złożoność, brak zmian w core loop  
**Wynik:** Arbitrage API może bezpiecznie wywoływać CLI i web scraping

```python
# Arbitrage API + Warp + Playwright
# Nadal 12 Docker services, ale z lepszymi "rękami" do systemu
```

---

### Opcja B: Full Integration (Recommended)

**Co wdrażamy:** Warp + Browser manager + PowerToys abstraction + G12_ToolIntegrity  
**Czas:** 15-20 godzin  
**Koszt:** Średnia złożoność, wymaga testów  
**Wynik:** Wielomodalny system agentowy z pełną izolacją i bezpieczeństwem

```python
# ADRION 369 z OS-level capabilities
# 33 agenty mogą manipulować systemem w hermetycznych piaskach
```

---

### Opcja C: Roadmap-Only (Recommendation + Future)

**Co wdrażamy:** Roadmap + placeholder modules  
**Czas:** 4-5 godzin  
**Koszt:** Minimalna, przygotowuje grunt  
**Wynik:** Czysty kod, gotowy do implementacji, brak ryzyka

```python
# Struktura kodu już na miejscu
# Zespół może rozwijać incrementally
```

---

## 🔐 SECURITY IMPLICATIONS

### Tool Integrity (Guardian Laws Extension)

**Nowe ryzyka:**
- Agent może wezwać nieznanym narzędziem → RCE (Remote Code Execution)
- Warp commands mogą mieć injection attacks
- Browser context może być skażona złośliwym skryptem

**Mitygacja:**
- ✅ G12_ToolIntegrity (whitelist)
- ✅ Input validation (regex + AST parsing)
- ✅ Sandbox execution (ulimit, seccomp)
- ✅ Genesis logging (all tool invocations recorded)

**CVC Implications:**
- Tool invocation failures → YELLOW state
- Injection attempts → ORANGE state
- Tool crash/timeout → RED state (escalate to human)

---

## 📊 METRICS (Post-Implementation)

| Metrika | Baseline | Target |
|---------|----------|--------|
| CLI execution reliability | ~70% | >95% (structured parsing) |
| Browser isolation (cookie spill) | N/A | 0% |
| Tool invocation latency | — | <500ms (via cache) |
| Security violations (G12) | 0 | 0 (detection + block) |

---

## ✅ CHECKLIST WDRAŻANIA

### Pre-Implementation

- [ ] Review wszystkich 3 dokumentów z Desktop/WDROŻENIE w Copilot
- [ ] Zatwierdzić architekturę integracji
- [ ] Zarezerwować 20h czasu developerskiego
- [ ] Przygotować testowe VM/container do eksperymentów

### Implementation (Faza 1)

- [ ] Warp integration module (warp_shell.py)
- [ ] Unit tests dla Warp (execution, exit codes, output parsing)
- [ ] Integration test z Arbitrage API
- [ ] Deployment na staging

### Implementation (Faza 2)

- [ ] Browser manager (Playwright + context pooling)
- [ ] Cookie isolation tests
- [ ] Vision-based agent tests (PDF visual mode)
- [ ] Performance benchmarks

### Implementation (Faza 3)

- [ ] PowerToys abstraction (Windows) + Raycast (macOS)
- [ ] G12_ToolIntegrity law
- [ ] Updated Genesis Record logging
- [ ] Updated CVC state machine

### Post-Implementation

- [ ] Full smoke tests (8/8 + tool execution)
- [ ] Load testing (100+ concurrent tool calls)
- [ ] Security audit (OWASP Top 10 + custom rules)
- [ ] Documentation update

---

## 🎯 DECISION POINT

**Pytanie kierunkowe:**

Którą opcję wybrać?

- **Opcja A (Fast):** Jeśli pilna produkcja w 2-3 dni
- **Opcja B (Full):** Jeśli chcesz solidnych fundamentów (rekomendowany)
- **Opcja C (Roadmap):** Jeśli czas do następnego sprintu

**Moja rekomendacja:** **Opcja B (Full Integration)** — koszt 15-20h to inwestycja, która fundamentalnie podnosi capabilities ADRION 369 i przygotowuje go na przyszłą ekspansję (mobile, IoT, multi-region).

---

**Przygotował:** Autonomous Analysis Agent  
**Data:** 14.05.2026 16:20 UTC  
**Status:** 📋 READY FOR DECISION

**Pliki powiązane:**
- [ADRION-369-Deployment-Plan-14-05-2026.md](./ADRION-369-Deployment-Plan-14-05-2026.md)
- [Desktop/WDROŻENIE w Copilot/Raport_*.md](c:\Users\adiha\Desktop\WDROŻENIE w Copilot)
