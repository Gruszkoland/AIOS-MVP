# ADRIAN 369 - RUNTIME CONNECTOR SETUP GUIDE

# ════════════════════════════════════════════════════════════════════════════════

# This guide walks through starting local development services: Ollama, Dashboard,

# and optional Vortex Sentinel relay.

#

# TARGET: Full End-to-End validation of oracle/quantum connectors + API endpoints

# STATUS: Created 2026-04-02 (post Ruff cleanup)

# ════════════════════════════════════════════════════════════════════════════════

## PREREQUISITE: Environment Setup

1. **Verify Python 3.11 Virtual Environment:**

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python --version  # Should be 3.11.x
   ```

2. **Verify .env.local is Configured:**
   ```bash
   # Check that .env.local exists and has template placeholders:
   cat .env.local | grep -E "STRIPE_|OLLAMA_|DASHBOARD_"
   ```

## STAGE 1: Ollama LLM Service (REQUIRED for quantum/oracle tests)

### Start Ollama Server (Terminal 1):

```powershell
# Option A: If ollama in PATH:
ollama serve

# Option B: If not in PATH, use full path (example for Windows):
C:\Users\adiha\AppData\Local\Ollama\ollama.exe serve
```

**Expected Output:**

```
Starting Ollama...
Listening on http://localhost:11434
```

**Verify Service:**

```powershell
# New terminal:
curl http://localhost:11434/api/tags -Headers @{"Content-Type"="application/json"}
# Should return: {"models":[...]}
```

### Pull LLM Model (One-time setup):

```powershell
# Terminal 2 (while Ollama server runs):
ollama pull deepseek-coder-v2:lite
# OR for more powerful model:
ollama pull deepseek-coder-v2:16b
```

**Can also override in .env.local:**

```bash
OLLAMA_MODEL=deepseek-coder-v2:lite
```

---

## STAGE 2: Dashboard Service (OPTIONAL for monitoring/validation)

### Start Dashboard (Terminal 2):

```powershell
# Activate venv if not already active:
.\.venv\Scripts\Activate.ps1

# Run dashboard flask app:
python scripts/dashboard/run.py
```

**Expected Output:**

```
WARNING: This is a development server...
Running on http://localhost:5000/
```

**Verify Dashboard:**

```powershell
curl http://localhost:5000/
# Should return HTML dashboard page
```

---

## STAGE 3: Vortex Sentinel (OPTIONAL - Go Relay)

### Option A: Disable Sentinel (Recommended for Python-only testing):

In .env.local (already set by default):

```bash
USE_SENTINEL_QUANTUM=0
```

This forces quantum_decide() to use deterministic local logic (no Go dependency).

### Option B: Enable Sentinel + Start Vortex Server:

```powershell
# Terminal 3 (requires Go 1.22+):
cd cmd/vortex-server
go run main.go
```

**Then enable in .env.local:**

```bash
USE_SENTINEL_QUANTUM=1
```

---

## STAGE 4: Full Validation

### Step 1: Verify All Connectors Are Reachable

```powershell
# In workspace root:
.\.venv\Scripts\Activate.ps1

# Check Ollama:
python -c "import requests; print(requests.get('http://localhost:11434/api/tags').json())"

# Check Quantum fallback (no external call needed - deterministic local):
python -c "from arbitrage.quantum import quantum_decide; result = quantum_decide(100, 105); print(f'Fallback OK: {result}')"

# Check Oracle:
python -c "from arbitrage.oracle import oracle_predict; result = oracle_predict([100, 101, 102, 103, 104, 105]); print(f'Fallback OK: {result}')"
```

### Step 2: Run Stripe Secrets Validation (micro-saas)

```powershell
cd micro-saas

# This checks .env.local for required Stripe secrets (will FAIL until you fill them in):
npm run check:secrets

# Expected output if secrets missing:
# Missing required secret placeholders:
# - STRIPE_LOGIN_EMAIL
# - ... (others)
```

**To make this PASS, fill in .env.local with real or test credentials:**

```bash
STRIPE_LOGIN_EMAIL=your-email@example.com
STRIPE_LOGIN_PASSWORD=YOUR_STRIPE_PASSWORD
STRIPE_BACKUP_CODE=YOUR_STRIPE_BACKUP_CODE
STRIPE_SECRET_KEY=STRIPE_SECRET_KEY_PLACEHOLDER
STRIPE_WEBHOOK_SECRET=STRIPE_WEBHOOK_SECRET_PLACEHOLDER
STRIPE_PRICE_ID_PRO=price_1ABC...
STRIPE_PRICE_ID_FOUNDING=price_1XYZ...
```

### Step 3: Run Oracle + Quantum Tests (Python)

```powershell
# In workspace root:
.\.venv\Scripts\Activate.ps1

# Run oracle & quantum tests with fallback logic:
pytest tests/test_oracle.py tests/test_quantum.py -v

# Expected: 75 tests PASS (75/75) ✓
```

### Step 4: Run Full Python Test Suite

```powershell
pytest -q
# Expected: 151 tests PASS (all ✓)
```

### Step 5: Build + Validate Next.js App

```powershell
cd micro-saas
npm run build
# Expected: ✓ Compiled successfully in ~10s
```

### Step 6: Validate Go Module (Optional)

```powershell
go test ./...
# Expected: exit 0 (no test files in packages is OK)
```

---

## QUICK REFERENCE: Service Checklist

| Service        | Port   | Command                                    | Status Check                           |
| -------------- | ------ | ------------------------------------------ | -------------------------------------- |
| **Ollama**     | :11434 | `ollama serve`                             | `curl http://localhost:11434/api/tags` |
| **Dashboard**  | :5000  | `python scripts/dashboard/run.py`          | `curl http://localhost:5000/`          |
| **Vortex**     | :1740  | `go run cmd/vortex-server/main.go`         | `curl http://localhost:1740/health`    |
| **PostgreSQL** | :5432  | `docker-compose up adrion-db` (via Docker) | `psql ...`                             |

---

## TROUBLESHOOTING

### Issue: `quantum_decide` returns empty/zero margin_pct

**Cause:** Sentinel relay active but Vortex not running.

**Fix:** Set `USE_SENTINEL_QUANTUM=0` in .env.local (uses deterministic fallback).

### Issue: `npm run check:secrets` fails

**Cause:** Missing Stripe credentials in .env.local.

**Fix:** Fill in STRIPE\_\* placeholders in .env.local (can use test values).

### Issue: Ollama service not found / import fails

**Cause:** Ollama not installed or not in PATH.

**Fix:** Install Ollama from https://ollama.ai or set full path in .env.local:

```bash
OLLAMA_API_BASE=http://localhost:11434
```

---

## VALIDATION COMMAND (ALL-IN-ONE)

After all services started (Ollama, optionally Dashboard):

```powershell
# Python validation:
.\.venv\Scripts\Activate.ps1
pytest -q && Write-Host "✓ PyTest OK"

# Next.js validation (micro-saas):
cd micro-saas
npm run check:secrets && npm run build && Write-Host "✓ Next.js OK"

# Go validation (optional):
cd ..
go test ./... && Write-Host "✓ Go OK"
```

**Expected Output:**

```
151 passed
✓ PyTest OK
✓ Compiled successfully in 10.5s
✓ Next.js OK
✓ Go OK
```

---

## PROGRESS TRACKING

| Date       | Phase                         | Status                      |
| ---------- | ----------------------------- | --------------------------- |
| 2026-04-02 | Ruff cleanup                  | ✓ Completed (63 auto-fixes) |
| 2026-04-02 | .env.local creation           | ✓ Completed                 |
| 2026-04-02 | Runtime connector setup       | ✓ Created (this document)   |
| 2026-04-02 | Service startup (user action) | ⏳ Pending user             |
| 2026-04-02 | Full validation               | ⏳ Pending user             |

---

**NEXT STEP:** User starts services per STAGE 1-4 instructions, then runs VALIDATION COMMAND.
