# ADRION 369 Extension - Comprehensive Button Testing Guide

**Date**: 2026-04-05
**Extension Version**: 1.0.0 (Post-Fix)
**Total Buttons**: 42 (Kubernetes + Deployment + Debugging + Testing + Core + Protocols + Models + Gates)

---

## 📋 Test Categories & Expected Behavior

### Category 1: 🐳 Kubernetes Operations (8 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 1.1 | 📊 List Pods | `kubectl get pods -n adrion` → Pod list | ⏳ TEST |
| 1.2 | 🔗 List Services | `kubectl get svc -n adrion` → Service list | ⏳ TEST |
| 1.3 | 📈 HPA Status | `kubectl get hpa -n adrion` → HPA status | ⏳ TEST |
| 1.4 | 📝 Backend Logs (Live) | Live kubectl logs (curl: Ctrl+C to stop) | ⏳ TEST |
| 1.5 | 🔀 Port Forward Backend | Port forward 8002 → Local access | ⏳ TEST |
| 1.6 | 🔀 Port Forward Frontend | Port forward 8003 → Local access | ⏳ TEST |
| 1.7 | 🗄️ Query Database | psql query → COUNT(*) FROM tasks | ⏳ TEST |
| 1.8 | 🔄 Restart Backend Pods | kubectl delete pod → Auto-restart | ⏳ TEST |

---

### Category 2: 📊 Deployment & Scaling (5 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 2.1 | 🚀 Deploy All | `kubectl apply -f kubernetes/` → All created/configured | ⏳ TEST |
| 2.2 | 📋 Backend Status | `kubectl describe deployment` → Full details | ⏳ TEST |
| 2.3 | 📈 Scale Backend (5) | `kubectl scale --replicas=5` → 5 running | ⏳ TEST |
| 2.4 | 🔄 Restart Deployment | `kubectl rollout restart` → Pods restarting | ⏳ TEST |
| 2.5 | ⚠️ Recent Events | `kubectl get events` → Last 20 events | ⏳ TEST |

---

### Category 3: 🔍 Debugging (4 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 3.1 | 💻 Node Resources | `kubectl top nodes` → CPU/Memory usage | ⏳ TEST |
| 3.2 | 📦 Pod Resources | `kubectl top pod` → Pod metrics | ⏳ TEST |
| 3.3 | 🖥️ Node Details | `kubectl describe node` → Full node spec | ⏳ TEST |
| 3.4 | 💾 Storage Status | `kubectl get pvc` → PVC info | ⏳ TEST |

---

### Category 4: ⚙️ Cluster Info (4 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 4.1 | ℹ️ Cluster Info | `kubectl cluster-info` → API server URL | ⏳ TEST |
| 4.2 | 🌐 Nodes | `kubectl get nodes` → Node list | ⏳ TEST |
| 4.3 | 📂 Namespaces | `kubectl get ns` → Namespace list | ⏳ TEST |
| 4.4 | 📌 K8s Version | `kubectl version` → Version info | ⏳ TEST |

---

### Category 5: 🧪 Testing (2 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 5.1 | ✅ Test Backend API | curl HTTP 200 + JSON status | ⏳ TEST |
| 5.2 | ✅ Test Frontend | curl HTTP 200 + HTML dashboard | ⏳ TEST |

---

### Category 6: Core Operations (4 buttons)

| # | Button | Expected Output | Status |
|----|--------|-----------------|--------|
| 6.1 | 🚀 Start Ollama Server | Ollama server listening on 11434 | ⏳ TEST |
| 6.2 | 🤖 Start Aider | Aider CLI interactive mode | ⏳ TEST |
| 6.3 | ✅ Check System Status | System health check output | ⏳ TEST |
| 6.4 | Start Arbitrage API | Task: ADRION: Start Arbitrage API Test Port | ⏳ TEST |

---

### Category 7: Protocols (5 buttons)

| # | Button | Expected Task | Status |
|----|--------|-----------------|--------|
| 7.1 | 🛡️ Audit Security | ADRION: /audit - Audyt Bezpieczeństwa | ⏳ TEST |
| 7.2 | 💰 Boost ROI | ADRION: /boost - Dźwignie ROI | ⏳ TEST |
| 7.3 | 🔧 Self-Heal | ADRION: /heal - Samonaprawa | ⏳ TEST |
| 7.4 | 🔄 Sync Chronos | ADRION: /sync - Synchronizacja Chronos | ⏳ TEST |
| 7.5 | Predeploy A-11 | Task: ADRION: Predeploy A-11 Validation | ⏳ TEST |

---

### Category 8: Models & LLM Rollout (4 buttons)

| # | Button | Expected Task | Status |
|----|--------|-----------------|--------|
| 8.1 | LLM Ops Dashboard | Task: ADRION: Show LLM Ops Dashboard | ⏳ TEST |
| 8.2 | Promote Canary +5% | Task: ADRION: Promote LLM Canary 5% | ⏳ TEST |
| 8.3 | Emergency Disable | Task: ADRION: Disable LLM Canary | ⏳ TEST |
| 8.4 | 📊 List Models | Task: 📊 Show Ollama Models | ⏳ TEST |

---

### Category 9: Critical Gates (2 buttons)

| # | Button | Expected Task | Status |
|----|--------|-----------------|--------|
| 9.1 | Release Gate | Task: ADRION: Local Release Gate (A-11 + Reports) | ⏳ TEST |
| 9.2 | KPI Guard (15m) | Task: ADRION: Monitor LLM KPI Gate (15m) | ⏳ TEST |

---

## 🧪 How to Run Tests

### Before Starting:
```bash
# Make sure K8s is running
kubectl cluster-info

# Make sure backend is running
kubectl port-forward svc/uap-backend 8002:8002 -n adrion &
kubectl port-forward svc/uap-frontend 8003:8003 -n adrion &
```

### Test Pattern:

1. **Click button in Extension**
2. **Terminal opens** (or reuses existing)
3. **Command executes**
4. **Verify output matches "Expected Output"**
5. **Note status: ✅ PASS or ❌ FAIL**

---

## Testing Instructions

### 🐳 Kubernetes Tests (1.1 - 1.8)

**1.1 List Pods:**
- Click "📊 List Pods"
- Should show: Pod list with STATUS (Running, Pending, etc.)
- ✅ PASS if: All pods shown with names and status

**1.2 List Services:**
- Click "🔗 List Services"
- Should show: ClusterIP services
- ✅ PASS if: uap-backend, uap-frontend, postgres in list

**1.3 HPA Status:**
- Click "📈 HPA Status"
- Should show: TARGETS (CPU %), MINPODS, MAXPODS, REPLICAS
- ✅ PASS if: Shows HPA targets for backend and frontend

**1.4 Backend Logs (Live):**
- Click "📝 Backend Logs (Live)"
- Should stream logs in real-time
- ✅ PASS if: Logs appear continuously (press Ctrl+C to stop)

**1.5 Port Forward Backend:**
- Click "🔀 Port Forward Backend"
- Should show: "Forwarding from 127.0.0.1:8002 -> 8002"
- ✅ PASS if: Port 8002 becomes accessible (test with curl)

**1.6 Port Forward Frontend:**
- Click "🔀 Port Forward Frontend"
- Should show: "Forwarding from 127.0.0.1:8003 -> 8003"
- ✅ PASS if: Port 8003 becomes accessible

**1.7 Query Database:**
- Click "🗄️ Query Database"
- Should show: "count" with number (e.g., 0)
- ✅ PASS if: Returns count result without errors

**1.8 Restart Backend Pods:**
- Click "🔄 Restart Backend Pods"
- Should show: Pods being deleted
- ✅ PASS if: K8s automatically recreates pods (check with "List Pods")

---

### 📊 Deployment & Scaling Tests (2.1 - 2.5)

**2.1 Deploy All:**
- Click "🚀 Deploy All"
- Should show: Resources being created/updated
- ✅ PASS if: No errors, resources configured

**2.2 Backend Status:**
- Click "📋 Backend Status"
- Should show: Full deployment description
- ✅ PASS if: Shows replicas, image, conditions

**2.3 Scale Backend (5):**
- Click "📈 Scale Backend (5 replicas)"
- Should show: deployment.apps/uap-backend scaled
- ✅ PASS if: Check with "List Pods" → 5 backend pods after 30s

**2.4 Restart Deployment:**
- Click "🔄 Restart Backend Deployment"
- Should show: rollout restart initiated
- ✅ PASS if: Pods restart (check logs)

**2.5 Recent Events:**
- Click "⚠️ Recent Events"
- Should show: Last 20 K8s events
- ✅ PASS if: Events displayed with timestamps

---

### 🔍 Debugging Tests (3.1 - 3.4)

**3.1 Node Resources:**
- Click "💻 Node Resources"
- Should show: Node CPU and Memory usage
- ✅ PASS if: docker-desktop shows usage (%)

**3.2 Pod Resources:**
- Click "📦 Pod Resources"
- Should show: Each pod's CPU and Memory
- ✅ PASS if: Shows metrics for all 6 pods

**3.3 Node Details:**
- Click "🖥️ Node Details"
- Should show: Full docker-desktop node spec
- ✅ PASS if: Shows capacities, addresses, conditions

**3.4 Storage Status:**
- Click "💾 Storage Status"
- Should show: PVC information
- ✅ PASS if: Shows postgres-pvc with 50Gi capacity

---

### ⚙️ Cluster Info Tests (4.1 - 4.4)

**4.1 Cluster Info:**
- Click "ℹ️ Cluster Info"
- Should show: Control plane URL and DNS
- ✅ PASS if: Shows https://127.0.0.1:6443

**4.2 Nodes:**
- Click "🌐 Nodes"
- Should show: docker-desktop node with Ready status
- ✅ PASS if: Shows 1 Ready node

**4.3 Namespaces:**
- Click "📂 Namespaces"
- Should show: All namespaces including "adrion"
- ✅ PASS if: adrion namespace visible

**4.4 K8s Version:**
- Click "📌 K8s Version"
- Should show: Client and Server versions
- ✅ PASS if: Shows v1.27+ version

---

### 🧪 Testing Tests (5.1 - 5.2)

**5.1 Test Backend API:**
- Click "✅ Test Backend API"
- Should return: HTTP 200 + JSON (status, agents_online, uptime_seconds)
- ✅ PASS if: JSON response with status: "ok"

**5.2 Test Frontend:**
- Click "✅ Test Frontend"
- Should return: HTTP 200 + HTML dashboard
- ✅ PASS if: HTML contains "ADRION 369"

---

### Core Operations Tests (6.1 - 6.4)

**6.1 Start Ollama:**
- Click "🚀 Start Ollama Server"
- Should start: Ollama daemon
- ✅ PASS if: "Ollama is running" or "listening on"

**6.2 Start Aider:**
- Click "🤖 Start Aider (Swarm Mode)"
- Should start: Aider CLI interactive mode
- ✅ PASS if: Aider prompt appears (type "exit" to quit)

**6.3 Check System Status:**
- Click "✅ Check System Status"
- Should show: System health check
- ✅ PASS if: "System OK" appears

**6.4 Start Arbitrage API:**
- Click "Start Arbitrage API"
- Should run: Task "ADRION: Start Arbitrage API Test Port"
- ✅ PASS if: "API server ready on port 8011"

---

### Protocols Tests (7.1 - 7.5)

**7.1 Audit Security:**
- Click "🛡️ Audit Security"
- Should run: ADRION: /audit task
- ✅ PASS if: Aider opens with audit message

**7.2 Boost ROI:**
- Click "💰 Boost ROI (Levers)"
- Should run: ADRION: /boost task
- ✅ PASS if: Aider opens with boost analysis

**7.3 Self-Heal:**
- Click "🔧 Self-Heal System"
- Should run: ADRION: /heal task
- ✅ PASS if: Aider opens with healing suggestions

**7.4 Sync Chronos:**
- Click "🔄 Sync Chronos"
- Should run: ADRION: /sync task
- ✅ PASS if: Aider opens with sync message (background)

**7.5 Predeploy A-11:**
- Click "Predeploy A-11"
- Should run: ADRION: Predeploy A-11 Validation
- ⚠️ EXPECTED: May fail if arbitrage API not running
- ✅ PASS if: Either validation passes OR shows "Start API first"

---

### Models & LLM Tests (8.1 - 8.4)

**8.1 LLM Ops Dashboard:**
- Click "LLM Ops Dashboard"
- Should run: ADRION: Show LLM Ops Dashboard
- ✅ PASS if: Dashboard output appears

**8.2 Promote Canary +5%:**
- Click "Promote Canary +5%"
- Should run: ADRION: Promote LLM Canary 5%
- ✅ PASS if: Promotion logic executes

**8.3 Emergency Disable:**
- Click "Emergency Disable LLM"
- Should run: ADRION: Disable LLM Canary
- ✅ PASS if: Canary disabled (script runs)

**8.4 List Models:**
- Click "📊 List Models"
- Should show: Ollama models
- ✅ PASS if: Shows installed models

---

### Critical Gates Tests (9.1 - 9.2)

**9.1 Release Gate:**
- Click "Local Release Gate (A-11)"
- Should run: ADRION: Local Release Gate (A-11 + Reports)
- ✅ PASS if: Gate validation runs (may take 1-2 min)

**9.2 KPI Guard (15m):**
- Click "Start KPI Guard (15m)"
- Should run: ADRION: Monitor LLM KPI Gate (15m)
- ✅ PASS if: KPI monitoring starts (runs in background)

---

## 📊 Test Summary Template

**After running all tests, fill this in:**

```
KUBERNETES TESTS:       ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ (8/8)
DEPLOYMENT TESTS:       ✅ ✅ ✅ ✅ ✅ (5/5)
DEBUGGING TESTS:        ✅ ✅ ✅ ✅ (4/4)
CLUSTER INFO TESTS:     ✅ ✅ ✅ ✅ (4/4)
TESTING TESTS:          ✅ ✅ (2/2)
CORE OPERATIONS TESTS:  ✅ ✅ ✅ ⚠️ (3/4 - A-11 needs API)
PROTOCOLS TESTS:        ✅ ✅ ✅ ✅ ⚠️ (4/5 - A-11 needs API)
MODEL/LLM TESTS:        ✅ ✅ ✅ ✅ (4/4)
CRITICAL GATES TESTS:   ⏳ ⏳ (0/2 - Optional advanced)

TOTAL: 34/41 PASSING (83%)
EXPECTED: Many passes + A-11 warnings (normal, needs setup)
```

---

## 🎯 Quick Test (5 minutes)

If you want to quickly verify extension works:

```
1. Click "📊 List Pods"         → Should show 6 running pods
2. Click "✅ Test Backend API" → Should show JSON
3. Click "✅ Test Frontend"     → Should show HTML
4. Click "💻 Node Resources"    → Should show CPU/Memory
5. Click "ℹ️ Cluster Info"      → Should show 127.0.0.1:6443
```

If all 5 pass → **Extension is working correctly!** ✅

---

**Status**: Ready for Testing
**Date**: 2026-04-05
**Total Tests**: 42 buttons
**Estimated Time**: 30-60 minutes (full suite) or 5 minutes (quick test)
