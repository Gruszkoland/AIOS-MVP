# 📑 ADRION 369 - QUICK STRUCTURE INDEX

## 🚀 SZYBKIE NAWIGACJA

### 📊 Raporty Skanowania

1. **JSON Report** → [`WORKSPACE_STRUCTURE_SCAN_2026-04-08.json`](WORKSPACE_STRUCTURE_SCAN_2026-04-08.json)
   - Pełne dane strukturalne w formacie maszynowym
   - Statystyki, rozmiary, kategorie

2. **Markdown Report** → [`WORKSPACE_STRUCTURE_SCAN_2026-04-08.md`](WORKSPACE_STRUCTURE_SCAN_2026-04-08.md)
   - Przejrzysty przegląd hierarchii katalogów
   - Opisy modułów, kluczowe pliki

---

## 🎯 GŁÓWNE MODUŁY (Szybkie Linki)

### Arbitrage Engine

- **Lokacja:** `arbitrage/`
- **Główny plik:** `arbitrage/main.py`
- **Orchestration:** `arbitrage/orchestrator.py`
- **Guardian Rules:** `arbitrage/guardian.py`
- **API:** `arbitrage/api.py`

### Universal Application Platform

- **Lokacja:** `uap/`
- **Backend API:** `uap/backend/api.py`
- **WebSocket:** `uap/backend/websocket_server.py`
- **K8s Integration:** `uap/backend/kubernetes_integration.py`
- **Frontend:** `uap/frontend/`
- **Desktop/Systray:** `uap/desktop/systray/uap_systray.py`

### MCP Servers

- **Lokacja:** `mcp_servers/` + Root level
- Genesis: `mcp_genesis_app.py` - Immutable audit logs
- Guardian: `mcp_guardian_app.py` - Safety enforcement
- Healer: `mcp_healer_app.py` - Self-repair
- Oracle: `mcp_oracle_app.py` - Forecasting
- Vortex: `mcp_vortex_app.py` - Stream processing
- Router: `mcp_router_app.py` - Message routing

---

## 🐳 INFRASTRUKTURA

### Docker Compose Files

| Plik                                 | Zastosowanie |
| ------------------------------------ | ------------ |
| `docker-compose.yml`                 | DEV          |
| `docker-compose.prod.yml`            | PROD         |
| `docker-compose.mcp-tier.yml`        | MCP agents   |
| `docker-compose.k8s-integration.yml` | K8s control  |
| `docker-compose.lmstudio.yml`        | Local LLM    |

### Kubernetes

- **Manifests:** `kubernetes/`
- **Core deployments:** `kubernetes/04-backend.yaml`
- **Storage:** `kubernetes/02-storage.yaml`
- **Database:** `kubernetes/03-postgres/`
- **Monitoring:** `kubernetes/06-monitoring/`
- **Ingress:** `kubernetes/06-ingress.yaml`

### Monitoring Stack

- **Prometheus:** `monitoring/prometheus.yml`
- **Loki:** `monitoring/loki/`
- **Grafana:** `monitoring/grafana/provisioning/`
- **Alerts:** `monitoring/llm_rollout_alert.json`

---

## 🧪 TESTY

**Lokacja:** `tests/`

| Kategoria  | Pliki                       |
| ---------- | --------------------------- |
| MCP Tests  | `tests/mcp/test_mcp_e2e.py` |
| UAP Tests  | `tests/uap/test_*.py`       |
| Unit Tests | `tests/test_*.py`           |
| Config     | `pytest.ini`, `conftest.py` |

---

## 📚 DOKUMENTACJA

### Core Docs

- `docs/ARCHITECTURE.md` - System architecture
- `docs/MCP_ARCHITECTURE.md` - MCP design
- `docs/LAWS.md` - 9 Guardian Laws

### Deployment

- `docs/DEPLOYMENT_RUNBOOK.md`
- `docs/KUBERNETES_QUICK_START.md`
- `ETAP_1_FINAL_REPORT.md` - Phase 1 completion
- `ETAP_2_DEPLOYMENT_FINAL_REPORT_2026-04-08.md` - Phase 2 completion

### ADR (Architecture Decision Records)

- `docs/adr/ADR-001-*.md` through `ADR-010-*.md`

---

## ⚙️ SKRYPTY AUTOMATYZACJI

**Lokacja:** `scripts/`

| Kategoria    | Przykłady                                           |
| ------------ | --------------------------------------------------- |
| Production   | `scripts/prod/start-prod.ps1`, `.../stop-prod.ps1`  |
| Installation | `scripts/install/setup-ADRION.ps1`                  |
| Testing      | `scripts/testing/start_arbitrage_api_test_port.ps1` |
| Security     | `scripts/security/validate-precommit-hook.ps1`      |
| Reporting    | `scripts/reporting/run_llm_kpi_guard_loop.ps1`      |
| MCP Testing  | `scripts/mcp-testing/smoke-test.ps1`                |

---

## 📋 KONFIGURACJA

### Environment Files

- `.env` - Current environment
- `.env.template` - Template
- `.env.local` - Local overrides
- `.env.lmstudio` - LM Studio config

### Application Config

- `config/trinity-weights.yml` - Trinity weight system
- `config/personas.yml` - Persona definitions
- `pyproject.toml` - Python metadata
- `pytest.ini` - Test configuration

---

## 🔐 SECURITY & CI/CD

### GitHub Actions

**Lokacja:** `.github/workflows/`

- `python-ci.yml` - Python testing
- `docker-ci.yml` - Docker build
- `security-ci.yml` - SAST scans
- `tier0-gate.yml` - Pre-deployment
- `jednosc-162d-gate.yml` - 162D validation

### Pre-Commit Hooks

- `.github/copilot-instructions.md` - Agent instructions
- `.pre-commit-config.yaml` - Hook configuration

---

## 📦 GENESIS RECORD (Backup & History)

**Lokacja:** `Genesis Record/`

| Folder                          | Zawartość              |
| ------------------------------- | ---------------------- |
| `02_STRATEGY_PLANS/`            | Phase 2 planning       |
| `03_TECHNICAL_SPECS/`           | v1.0 complete snapshot |
| `06_SECURITY_BACKUPS/`          | Full source backup     |
| `10_RAPORTY_DZIALANIA_SYSTEMU/` | Phase execution logs   |

---

## 🎯 QUICK START CHECKLIST

- [ ] **Backend:** `arbitrage/main.py`
- [ ] **API:** `uap/backend/api.py`
- [ ] **Frontend:** `uap/frontend/` (React)
- [ ] **Deploy:** `docker-compose.prod.yml`
- [ ] **K8s:** `kubernetes/00-namespace.yaml` start
- [ ] **Tests:** `pytest tests/`
- [ ] **Monitoring:** `monitoring/prometheus.yml`
- [ ] **Docs:** `docs/DEPLOYMENT_RUNBOOK.md`

---

## 📞 CONTACT FILES

### Deployment Reports

- `SESSION_COMPLETION_REPORT_2026-04-08.md`
- `DEPLOYMENT_SUMMARY.md`
- `ETAP_1_WORK_COMPLETION_FINAL.md`

### System Documentation

- `ADRION_STARTUP_GUIDE.md`
- `ADRION_CONTROL_CENTER_README.md`
- `STARTING_HERE.md`

---

**Generated:** 2026-04-08
**Status:** COMPLETE
**Total Items Indexed:** 40+
