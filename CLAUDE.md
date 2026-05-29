# CLAUDE.md — ADRION 369 Project Control File

> **Version:** 5.1-plan | **Updated:** 2026-04-22 | **Score:** 77/100 (target: 100/100)
> **Plan:** 23 tasks in 5 waves x 4 phases | 18 agents parallel | 5 verification gates
> This file is the single source of truth for Claude Code. It is loaded at conversation start.
> **Standards & Architecture:** See [`MANIFEST.md`](MANIFEST.md) — Full coding standards,
> naming conventions, test markers, Git conventions, Guardian Laws, Trinity-EBDI framework.
> **All AI agents must read MANIFEST.md before making code changes.**

---

## 1. PROJECT IDENTITY

- **Name:** ADRION 369 — Multi-Agent AI Orchestration System
- **Language:** Python 3.11+ (primary), Go 1.22 (Vortex), JavaScript (dashboard)
- **Framework:** Flask app factory + 5 Blueprints, Echo (Go), Pydantic BaseSettings
- **Decision model:** Trinity-EBDI 162D space (3 perspectives x 6 modes x 9 laws)
- **Canonical source of truth:** `docs/GUARDIAN_LAWS_CANONICAL.json` (9 praw)
- **User language:** Polish (komunikacja), English (code comments, git commits)

## 1.1. INSTRUCTION BOUNDARY

- `CLAUDE.md`: project execution plan, quality gates, and repo-level constraints.
- `.github/copilot-instructions.md`: runtime behavior for the coding agent in VS Code.
- `docs/GUARDIAN_LAWS_CANONICAL.json`: canonical names/severities for Guardian Laws.
- `MANIFEST.md`: coding standards and architecture conventions.
- Precedence on conflicts: `docs/GUARDIAN_LAWS_CANONICAL.json` > `MANIFEST.md` > `CLAUDE.md` > `.github/copilot-instructions.md`.

## 1.2. REPOSITORY CONTEXT CONTRACT (SYNCED)

<!-- BEGIN:REPO_CONTEXT_CONTRACT -->
Przy **tworzeniu repozytorium** oraz przy **każdej naprawie/refaktorze** agent MUSI najpierw odczytać i zaktualizować plik:

- `REPO_CONTEXT_STATUS.txt` (root repo)

Jeśli plik nie istnieje, agent tworzy go przed pierwszą zmianą kodu.

Minimalna struktura pliku `REPO_CONTEXT_STATUS.txt`:

1. `REPO_GOAL` — cel i zakres repo (1-3 akapity)
2. `DEPLOYMENT_PLAN` — lista elementów do wdrożenia i kolejność
3. `CHANGELOG_LIVE` — lista dotychczasowych poprawek i zmian (append-only)
4. `CURRENT_RISKS` — top ryzyk technicznych i operacyjnych
5. `NEXT_ACTIONS` — następne kroki na najbliższą iterację
6. `LAST_VERIFIED` — data, autor, wynik walidacji

Zasady egzekucji:

- Przed edycją kodu: sprawdź obecność i aktualność `REPO_CONTEXT_STATUS.txt`.
- Po zakończeniu zadania: dopisz wpis do `CHANGELOG_LIVE` i zaktualizuj `LAST_VERIFIED`.
- Przy pracy wieloagentowej: traktuj ten plik jako SSOT dla szybkiej diagnozy stanu.
- Nie usuwaj historii wpisów; tylko dopisuj nowe rekordy.
<!-- END:REPO_CONTEXT_CONTRACT -->

Synchronizacja z `.github/copilot-instructions.md` jest automatyczna przez:

- `scripts/reporting/sync_repo_context_contract.py`
- hook pre-commit `sync-repo-context-contract`

---

## 2. RUNNING

```bash
# Dev (Flask Blueprints — the ONLY correct entry point)
python wsgi.py                          # http://localhost:8003
# or: waitress-serve --port=8003 wsgi:app

# UAP Orchestrator
python uap/backend/api.py               # http://localhost:8002

# Go Vortex
go run cmd/vortex-server/main.go        # http://localhost:1740

# Docker (dev)
docker-compose up -d                    # postgres + backend + frontend + ollama
docker-compose -f docker-compose.prod.yml up -d  # full 10-service stack
docker-compose -f docker-compose.cloud.yml up -d  # cloud (openrouter LLM)

# API Docs
open http://localhost:8003/api/docs     # Swagger UI
```

## 3. TESTING

Test policy (always):

- Always run relevant tests after each code change (module-level minimum, full suite for cross-cutting changes).
- Always persist test results in the deployed repository under `REPORTS/test-results/<YYYY-MM-DD_HH-mm-ss>_test-report.txt`.
- Prefer adding meaningful regression tests for each new function, endpoint, and decision branch.

```bash
# Python (must pass with 80%+ coverage)
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
python -m pytest uap/tests/ -q

# Go (must pass with 80%+ coverage)
go test ./... -v -coverprofile=coverage.out
go tool cover -func=coverage.out

# Linting + type checking
ruff check arbitrage/ uap/ tests/
mypy arbitrage/

# Security
bandit -r arbitrage/ -ll
safety check -r requirements-arbitrage.txt
```

## 4. ARCHITECTURE (v4.0)

```text
Browser --> Nginx (TLS) --> Flask App Factory (arbitrage/app.py)
                              |-- arbitrage_bp (9 routes: jobs, bids, scout, cycle)
                              |-- quantum_bp  (3 routes: decide, status, scan)
                              |-- oracle_bp   (2 routes: predict, scan)
                              |-- wholesale_bp(3 routes: scout, cycle, deals)
                              |-- payments_bp (4 routes: checkout, webhook, mass-gen, manifest)
                              |-- /health, /health/live, /health/ready (cascade)
                              |-- /metrics (Prometheus), /api/docs (Swagger)
                              |
                              +--> arbitrage/guardian.py (9 Guardian Laws)
                              +--> arbitrage/trinity.py  (Trinity Score: Material/Intellectual/Essential)
                              +--> arbitrage/database.py  (SQLite + PostgreSQL pool)
                              +--> arbitrage/llm.py       (Ollama -> OpenRouter fallback, canary deploy)
                              +--> arbitrage/circuit_breaker.py (LLM/Stripe/Apify/XRP)
                              +--> arbitrage/rate_limiter.py    (sliding window, per-endpoint)

UAP Orchestrator (port 8002) --> 6 AI Personas (Librarian, SAP, Auditor, Sentinel, Architect, Healer)
Go Vortex (port 1740)        --> EBDI state, digital root oracle, 174Hz pulse
MCP Layer                    --> Router:9000, Vortex:9001, Guardian:9002, Oracle:9003, Genesis:9004, Healer:9005
```

### Guardian Laws (canonical: `docs/GUARDIAN_LAWS_CANONICAL.json`)

**9 Immutable Laws** evaluated through **6 Processing Modes**:

| G# | Law | Severity | Purpose | Primary Modes |
| --- | --- | --- | --- | --- |
| G1 | Unity | MEDIUM | Collective good, system coherence | Inventory, Process, Action |
| G2 | Harmony | HIGH | Balance between competing objectives, genuine analysis | Debate, Healing, Action |
| G3 | Rhythm | MEDIUM | Sustainable pace, balance | Inventory, Process |
| G4 | Causality | HIGH | Full traceability | Debate, Action |
| G5 | Transparency | MEDIUM | Explainability, auditable | All 6 Modes |
| G6 | Authenticity | HIGH | Outputs must be genuine and free from deception | Debate, Healing, Action |
| G7 | Privacy | CRITICAL | Data and analysis local-only, no unauthorized disclosure | Empathy, Healing |
| G8 | Nonmaleficence | CRITICAL | Prevent harm to users, systems, and data | Debate, Action |
| G9 | Sustainability | HIGH | Long-term viability | Process, Action |

**6 Processing Modes** (Hexagon):

1. **Inventory** — Observe facts (3-word summaries)
2. **Empathy** — Assess emotional/relational impact
3. **Process** — Organize goals, allocate resources
4. **Debate** — Multi-agent consensus (5/6 quorum)
5. **Healing** — Detect deception/manipulation
6. **Action** — Execute + Genesis Record logging

**3 Perspectives** (Trinity):

- **Material:** Resources (CPU, RAM, energy)
- **Intellectual:** Truth (beauty, coherence, logic)
- **Essential:** Purpose (mission, unity, commons)

**Rule:** CRITICAL violation (G7/G8) = instant DENY. 2+ any violations = DENY.

---

## 5. KEY FILES (do NOT guess — read before editing)

| File                        | Role                           | Notes                                                 |
| --------------------------- | ------------------------------ | ----------------------------------------------------- |
| `wsgi.py`                   | Production entry point         | Imports `create_app()` from `arbitrage.app`           |
| `arbitrage/app.py`          | Flask app factory              | CSRF, CORS, health checks, graceful shutdown, OpenAPI |
| `arbitrage/blueprints/`     | 5 route modules                | `safe_float`/`safe_int` in `__init__.py`              |
| `arbitrage/config.py`       | Pydantic BaseSettings          | All env vars typed + validated                        |
| `arbitrage/guardian.py`     | 9 Guardian Laws engine         | `evaluate_guardians(job, analysis, context)`          |
| `arbitrage/trinity.py`      | Trinity Score engine           | `evaluate_trinity(job, analysis, resources)`          |
| `arbitrage/database.py`     | DB layer (SQLite + PG pool)    | Parameterized SQL only, `graceful_drain()`            |
| `arbitrage/llm.py`          | LLM abstraction                | Ollama-first, canary deploy, injection filter         |
| `arbitrage_server.py`       | Deprecated server              | Use `wsgi.py`; removal planned                        |
| `uap/backend/api.py`        | UAP orchestrator (2111 lines)  | Needs refactor; monolith and SQL injection risk       |
| `docs/openapi.yaml`         | OpenAPI 3.1 spec (1096 lines)  | 27 endpoints documented                               |
| `docs/COMPRESSION_GUIDE.md` | Token compression style guide  | Level 0-2 symbolic notation, 50-70% savings           |
| `pyproject.toml`            | Project metadata + tool config | pytest, coverage, ruff settings                       |

---

## 6. CRITICAL RULES

### Security

- **NEVER** hardcode secrets. Use `os.getenv()` or `arbitrage.config.settings.*`
- **ALWAYS** use parameterized SQL (`?` placeholders). NEVER f-string SQL.
- **NEVER** use `CORS(app)` without origins. Always restrict: `CORS(app, origins=[...])`
- **NEVER** commit `.env` files. Check `.gitignore` includes `.env*`
- K8s secrets use `CHANGE_ME_IN_PRODUCTION` placeholders — real values via `kubectl create secret`
- Check `docs/GUARDIAN_LAWS_CANONICAL.json` before modifying any law name/severity

### Code Quality

- **ALWAYS** read a file before editing it
- **ALWAYS** run `ruff check` after Python changes
- **ALWAYS** add type hints to new functions (return type + parameters)
- Blueprint input: use `safe_float()`/`safe_int()` from `arbitrage.blueprints`, never bare `float()`
- Rate limiting: every POST endpoint must call `is_allowed(client_ip)` or explain why not
- Coverage gate: Python >= 80%, Go >= 80% (enforced in CI)

### Architecture

- **Entry point is `wsgi.py`** → `arbitrage.app.create_app()`. NOT `arbitrage_server.py`
- New routes go in `arbitrage/blueprints/`, NOT in `arbitrage/api.py` or `arbitrage_server.py`
- Config via `arbitrage.config.settings.*`, NOT raw `os.getenv()` in app code
- Health checks: `/health` (cascade), `/health/live` (liveness), `/health/ready` (readiness)
- Logging: JSON format via `python-json-logger`. Check logs parse in Loki/Grafana

### Git Conventions

- Branch: feature/_, fix/_, chore/\*
- Commit: imperative English ("add", "fix", "remove"), max 72 chars
- PR: title under 70 chars, body with ## Summary + ## Test plan
- NEVER commit coverage artifacts, logs, or test result JSONs

---

## 7. CHECKLIST: 75/100 → 100/100

> **Stan inwentaryzacji (2026-04-11):** root=179 items, 45 .md, 10 .log, 9 .txt, 8 .ps1, 24 .py scripts, `Users/` + `O/` dirs present.
> **Matryca 3-6-9:** 3 perspektywy (Material/Intellectual/Essential) x 6 modes (Inventory/Empathy/Process/Debate/Healing/Action) x 9 praw Guardian = 162D przestrzen decyzyjna.

### PHASE 1: CRITICAL FIXES (75→85) — P0 — Branch: `fix/p0-critical`

#### P0-1: Fix SQL injection in UAP `[SECURITY-CRITICAL]`

- **Status:** `[x]` DONE — `ALLOWED_AGENT_COLUMNS` frozenset + column iteration from allowlist, not user input. See `uap/backend/blueprints/__init__.py:52` and `agents_bp.py:199`.
- **File:** `uap/backend/api.py:1396`
- **Problem:** `f"UPDATE agents SET {', '.join(fields)} WHERE id = ?"` — unsanitized column names from user input
- **Fix steps:**
  1. Read `uap/backend/api.py` lines 1380-1420 — understand the `update_agent` endpoint
  2. Define allowlist: `ALLOWED_AGENT_COLUMNS = frozenset({"name", "type", "status", "config", "priority", "description"})`
  3. Filter: `fields = {k: v for k, v in data.items() if k in ALLOWED_AGENT_COLUMNS}`
  4. Reject unknown: `if unknown := set(data) - ALLOWED_AGENT_COLUMNS: return jsonify({"error": f"Unknown fields: {unknown}"}), 400`
  5. Add test in `uap/tests/test_api.py`: attempt `{"id; DROP TABLE--": "x"}` → expect 400
- **Verification:** `grep -rn "f\".*UPDATE.*SET.*{" uap/` → 0 matches
- **Agent:** `backend-developer` | **Branch:** `fix/p0-1-sql-injection`

#### P0-2: Root cleanup v2 `[HYGIENE]`

- **Status:** `[ ]` NOT STARTED
- **Inventory (verified 2026-04-11):**
  - 45 `.md` files in root (keep: README.md, CLAUDE.md, CHANGELOG.md → move rest to `docs/sessions/`)
  - 10 `.log` files (move to `logs/`, add `*.log` to root `.gitignore`)
  - 9 `.txt` files incl. `cov_*.txt`, `temp_*.txt` (add to `.gitignore`, delete generated ones)
  - 8 `.ps1` scripts (move to `scripts/install/`)
  - 24 `.py` scripts (NOT wsgi.py/arbitrage_server.py — move to `scripts/`)
  - Dirs to remove: `Users/`, `O/` (accidental copies)
  - Dirs to review: `_temp_extract/`, `temp_deploy/`, `Phase2_Distribution_Package_Apr8_2026/`
- **Fix steps:**
  1. `mkdir -p docs/sessions scripts/install scripts/deploy scripts/tools`
  2. Move 42 session .md: `mv ETAP_*.md LM_STUDIO_*.md CREDENTIAL_*.md SESSION_*.md ELECTRON_*.md P0_*.md PLAN_*.md QUICK_START_*.md ADRION_STARTUP_GUIDE.md ADRION_CONTROL_CENTER_README.md IMPLEMENTATION_*.md INDEX_*.md REPOSITORIES_*.md SKILLS_*.md TOP_3_*.md UI_UX_*.md WORKSPACE_*.md docs/sessions/`
  3. Move 24 .py scripts: `mv copy_project_to_desktop.py credential_rotation_execute.py etap1_*.py etap2_*.py mcp_*_app.py move_hierarchy_to_desktop.py quick_start_agents.py run_*.py server.py test_lmstudio_integration.py test_mcp_ports.py verify_*.py scripts/`
  4. Move 8 .ps1: `mv *.ps1 scripts/install/`
  5. Move 10 .log: `mv *.log _*.log logs/`
  6. Delete or gitignore .txt: add `cov_*.txt`, `temp_*.txt` to `.gitignore`
  7. Remove: `rm -rf Users/ O/`
  8. Review and remove: `_temp_extract/`, `temp_deploy/`
  9. Update `.gitignore` with patterns: `*.log`, `cov_*.txt`, `_*_stderr.log`, `_*_stdout.log`
- **Verification:** `ls -1 | wc -l` → < 50 items
- **Agent:** `general-purpose` | **Branch:** `chore/p0-2-root-cleanup`

#### P0-3: UAP monolith refactor `[ARCHITECTURE]`

- **Status:** `[ ]` NOT STARTED
- **File:** `uap/backend/api.py` (2110 lines → target: 5 files x ~400 lines)
- **Target structure:**

  ```text
  uap/backend/
    api.py              (~200 lines — app factory, shared middleware, health)
    blueprints/
      __init__.py       (shared helpers: db access, auth decorator)
      tasks_bp.py       (CRUD tasks, task execution, task stats)
      agents_bp.py      (CRUD agents, agent status, agent config)
      genesis_bp.py     (Genesis Record endpoints, persona management)
      ebdi_bp.py        (EBDI state machine, digital root, decision pipeline)
      admin_bp.py       (admin dashboard, system config, diagnostics)
  ```

- **Fix steps:**
  1. Read full `uap/backend/api.py` — map all routes and their line ranges
  2. Extract shared utilities (db helpers, auth, error handlers) into `blueprints/__init__.py`
  3. Create each blueprint file, moving routes + their helper functions
  4. Update `api.py` to import and register all blueprints
  5. Run `python -m pytest uap/tests/ -q` after each extraction — must stay green
  6. Final: `wc -l uap/backend/api.py` → < 300 lines
- **Dependencies:** P0-1 must be done first (SQL injection fix moves into `agents_bp.py`)
- **Agent:** `backend-developer` | **Branch:** `refactor/p0-3-uap-blueprints`

#### P0-4: Remove Docker socket from prod `[SECURITY]`

- **Status:** `[x]` DONE — Verified `docker-compose.prod.yml` contains no `docker.sock` or `DOCKER_HOST` references.
- **File:** `docker-compose.prod.yml` — lines 56, 61, 119
- **Fix steps:**
  1. Read `docker-compose.prod.yml`
  2. Remove all `/var/run/docker.sock` volume mounts (lines 61, 119)
  3. Remove `DOCKER_HOST` env var (line 56)
  4. Add `DISABLE_DOCKER_INSPECT=true` to relevant service env
  5. Verify no other compose files mount socket (check `docker-compose.cloud.yml` — confirmed clean)
- **Verification:** `grep -r "docker.sock" docker-compose.prod.yml` → 0 matches
- **Agent:** `backend-developer` | **Branch:** `fix/p0-4-docker-socket`

#### P0-5: Rewrite ARCHITECTURE.md `[DOCS]`

- **Status:** `[ ]` NOT STARTED
- **File:** `docs/ARCHITECTURE.md`
- **Fix steps:**
  1. Read current `docs/ARCHITECTURE.md` — identify outdated sections
  2. Rewrite to reflect actual v4.0 architecture:
     - Flask App Factory + 5 Blueprints (not Aider)
     - Guardian Laws Engine (9 laws from CANONICAL.json)
     - Trinity Score (Material/Intellectual/Essential)
     - UAP Orchestrator + 6 AI Personas
     - Go Vortex (EBDI + digital root)
     - MCP Layer (6 microservices on ports 9000-9005)
     - Circuit Breaker + Rate Limiter + LLM Canary
  3. Include Matryca 3-6-9 diagram (3 perspectives x 6 aspects x 9 laws = 162D)
  4. Add data flow diagram: Browser → Nginx → Flask → Guardian → Trinity → LLM
- **Agent:** `backend-developer` | **Branch:** `docs/p0-5-architecture`

---

### PHASE 2: SECURITY HARDENING (85→90) — P1 — Branch: `feature/p1-security`

#### P1-1: Token-based CSRF `[SECURITY]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `arbitrage/app.py`, `requirements-arbitrage.txt`
- **Fix steps:**
  1. Add `Flask-WTF` to `requirements-arbitrage.txt`
  2. In `create_app()`: `CSRFProtect(app)` with `WTF_CSRF_TIME_LIMIT = 3600`
  3. Exempt API endpoints (JSON-only) via `@csrf.exempt` or `WTF_CSRF_CHECK_DEFAULT = False` for API blueprint
  4. For HTML forms (if any): ensure `{{ csrf_token() }}` in templates
  5. Alternative: double-submit cookie pattern if no server-side sessions
  6. Add test: POST without CSRF token → 400/403
- **Agent:** `backend-developer` | **Branch:** `feature/p1-1-csrf`

#### P1-2: K8s TLS with cert-manager `[INFRA]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `kubernetes/` directory
- **Fix steps:**
  1. Create `kubernetes/03-tls/cluster-issuer.yaml` (Let's Encrypt staging + prod)
  2. Add cert-manager annotations to Ingress: `cert-manager.io/cluster-issuer: letsencrypt-prod`
  3. Add `tls:` block with `secretName: adrion-tls` to Ingress spec
  4. Create `kubernetes/03-tls/certificate.yaml` for explicit cert resource
  5. Document in `docs/LOCAL_DEPLOYMENT_GUIDE.md`: cert-manager install steps
- **Agent:** `backend-developer` | **Branch:** `feature/p1-2-k8s-tls`

#### P1-3: Fix database.py type hints `[CODE-QUALITY]`

- **Status:** `[ ]` NOT STARTED
- **File:** `arbitrage/database.py`
- **Fix steps:**
  1. Read `arbitrage/database.py` — find `get_conn()` signature
  2. Change return type: `Union[sqlite3.Connection, Any]` → proper `Union[sqlite3.Connection, psycopg2.extensions.connection]`
  3. Or use Protocol: `class DBConnection(Protocol)` with `.execute()`, `.cursor()`, `.commit()`, `.close()`
  4. Run `mypy arbitrage/database.py` — must pass
- **Agent:** `python-pro` | **Branch:** `fix/p1-3-db-types`

#### P1-4: Genesis Record cleanup `[DOCS]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `Genesis Record/` directory, `Genesis Record/README.md`
- **Fix steps:**
  1. Count actual files per category (verify: 31 Core, 46 Strategy, 83 Technical — not 30/24/42)
  2. Find and remove 6 duplicate filenames
  3. Rename files to `Topic_DD-MM-YYYY.md` format (consistent naming)
  4. Update `Genesis Record/README.md` with correct stats
- **Agent:** `general-purpose` | **Branch:** `chore/p1-4-genesis-cleanup`

#### P1-5: Guardian Laws sync `[INTEGRITY]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `README.md`, `docs/GUARDIAN_LAWS_CANONICAL.json`
- **Fix steps:**
  1. Read `docs/GUARDIAN_LAWS_CANONICAL.json` — extract exact law names
  2. Search all .md files for wrong names: "Truth" → "Harmony", "Autonomy" → "Authenticity", "Justice" → "Privacy"
  3. Update every reference to match CANONICAL.json exactly
  4. Verify: `grep -rn "Truth\|Autonomy\|Justice" *.md docs/*.md` → only valid contextual uses
- **Agent:** `python-pro` | **Branch:** `fix/p1-5-laws-sync`

#### P1-6: Fix Prometheus targets `[MONITORING]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `docker-compose.prod.yml`, `monitoring/` directory
- **Fix steps:**
  1. Read `monitoring/grafana/provisioning/datasources/prometheus.yml`
  2. Add `postgres_exporter` sidecar service in `docker-compose.prod.yml`
  3. Fix Grafana scrape path in Prometheus config
  4. Verify dashboard JSON references match actual metric names
- **Agent:** `backend-developer` | **Branch:** `fix/p1-6-prometheus`

#### P1-7: Multi-stage Dockerfile `[INFRA]`

- **Status:** `[ ]` NOT STARTED
- **File:** `Dockerfile`
- **Fix steps:**
  1. Read current `Dockerfile`
  2. Rewrite as multi-stage:

     ```dockerfile
     # Stage 1: Builder
     FROM python:3.11-slim AS builder
     COPY requirements*.txt .
     RUN pip install --no-cache-dir --prefix=/install -r requirements-arbitrage.txt

     # Stage 2: Runtime
     FROM python:3.11-slim AS runtime
     COPY --from=builder /install /usr/local
     COPY arbitrage/ arbitrage/
     COPY wsgi.py .
     EXPOSE 8003
     CMD ["python", "wsgi.py"]
     ```

  3. Test: `docker build -t adrion-test .` — verify size reduction ~60%
  4. Update all other Dockerfiles that follow same pattern
- **Agent:** `backend-developer` | **Branch:** `feature/p1-7-multistage-docker`

---

### PHASE 3: QUALITY POLISH (90→95) — P2 — Branch: `feature/p2-quality`

#### P2-1: Remove UAP hardcoded mock data `[CODE-QUALITY]`

- **Status:** `[ ]` NOT STARTED
- **File:** `uap/backend/api.py` (or post-refactor: `uap/backend/blueprints/tasks_bp.py`)
- **Fix steps:**
  1. Find `get_active_tasks()` and `get_task_stats()` — replace hardcoded returns with real DB queries
  2. Use parameterized SQL (enforcing P0-1 fix)
  3. Add fallback for empty DB (return empty list, not mock data)
  4. Add tests for both populated and empty database states
- **Depends on:** P0-3 (UAP refactor)
- **Agent:** `backend-developer` | **Branch:** `fix/p2-1-uap-mock-data`

#### P2-2: Property-based testing with Hypothesis `[TESTING]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `tests/test_guardian_hypothesis.py` (new), `tests/test_trinity_hypothesis.py` (new)
- **Fix steps:**
  1. Add `hypothesis` to dev dependencies
  2. Create `tests/test_guardian_hypothesis.py`:
     - Fuzz all 9 law evaluation functions with random inputs
     - Test: CRITICAL violation always → DENY
     - Test: 2+ any violations always → DENY
     - Test: score always in [0.0, 1.0] range
  3. Create `tests/test_trinity_hypothesis.py`:
     - Fuzz Material/Intellectual/Essential score calculations
     - Test: weighted sum invariants
     - Test: edge cases (all zeros, all maxes, negative inputs)
  4. Run: `python -m pytest tests/test_*_hypothesis.py -v`
- **Agent:** `python-pro` | **Branch:** `feature/p2-2-hypothesis-tests`

#### P2-3: Update Go dependencies `[MAINTENANCE]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `go.mod`, `go.sum`
- **Fix steps:**
  1. `go get -u golang.org/x/crypto golang.org/x/net`
  2. `go mod tidy`
  3. `go test ./... -v` — must stay green
  4. Check for any breaking API changes in updated deps
- **Agent:** `backend-developer` | **Branch:** `chore/p2-3-go-deps`

#### P2-4: Rate limit wholesale_bp.handle_wholesale_scout `[SECURITY]`

- **Status:** `[ ]` NOT STARTED
- **File:** `arbitrage/blueprints/wholesale_bp.py`
- **Fix steps:**
  1. Read `wholesale_bp.py` — find `handle_wholesale_scout` route
  2. Add `is_allowed(client_ip)` check at route entry (same pattern as other POST endpoints)
  3. Add test: rapid requests → 429 Too Many Requests
- **Agent:** `backend-developer` | **Branch:** `fix/p2-4-rate-limit`

#### P2-5: Deprecation roadmap `[DOCS]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `CHANGELOG.md`, `arbitrage_server.py`
- **Fix steps:**
  1. Add deprecation notice to `CHANGELOG.md`: "arbitrage_server.py marked for removal in v5.0"
  2. Ensure `arbitrage_server.py` has `DeprecationWarning` on import
  3. Add removal date: v5.0 (planned Q3 2026)
- **Agent:** `backend-developer` | **Branch:** `chore/p2-5-deprecation`

#### P2-6: Stub deprecated server `[CLEANUP]`

- **Status:** `[ ]` NOT STARTED
- **File:** `arbitrage_server.py` (currently ~380 lines)
- **Fix steps:**
  1. Replace entire file with thin redirect stub (~30 lines):

     ```python
     """DEPRECATED: Use wsgi.py → arbitrage.app.create_app() instead.
     This file will be removed in v5.0. See CHANGELOG.md."""
     import warnings
     warnings.warn("arbitrage_server.py is deprecated. Use wsgi.py", DeprecationWarning, stacklevel=2)
     from arbitrage.app import create_app
     app = create_app()
     if __name__ == "__main__":
         app.run(port=8003)
     ```

  2. Update any references pointing to old server
- **Depends on:** P2-5 (deprecation roadmap)
- **Agent:** `backend-developer` | **Branch:** `chore/p2-6-stub-server`

---

### PHASE 4: EXCELLENCE (95→100) — P3 — Branch: `feature/p3-excellence`

#### P3-1: Contract testing `[TESTING]`

- **Status:** `[ ]` NOT STARTED
- **Fix steps:**
  1. Add `schemathesis` to dev dependencies
  2. Create `tests/contract/test_arbitrage_contract.py` — validates against `docs/openapi.yaml`
  3. Create `tests/contract/test_uap_contract.py` — validates UAP API responses
  4. Add to CI: `schemathesis run docs/openapi.yaml --base-url=http://localhost:8003`
  5. Optional: Pact broker for cross-service contracts
- **Agent:** `python-pro` | **Branch:** `feature/p3-1-contract-tests`

#### P3-2: DAST scanning with OWASP ZAP `[SECURITY]`

- **Status:** `[ ]` NOT STARTED
- **Fix steps:**
  1. Create `.github/workflows/dast-zap.yml`
  2. Use `zaproxy/action-full-scan@v0.10.0` or `zaproxy/action-api-scan`
  3. Target: running app in CI container
  4. Fail pipeline on HIGH/CRITICAL findings
  5. Add ZAP rules file: `.zap/rules.conf` (suppress known false positives)
- **Agent:** `backend-developer` | **Branch:** `feature/p3-2-dast-zap`

#### P3-3: Container image signing `[SUPPLY-CHAIN]`

- **Status:** `[ ]` NOT STARTED
- **Fix steps:**
  1. Add cosign step to `.github/workflows/release.yml`
  2. After GHCR push: `cosign sign --key cosign.key ghcr.io/$IMAGE`
  3. Store signing key as GitHub secret `COSIGN_PRIVATE_KEY`
  4. Add verification step: `cosign verify --key cosign.pub ghcr.io/$IMAGE`
  5. Document in `docs/SECURITY.md`
- **Agent:** `backend-developer` | **Branch:** `feature/p3-3-cosign`

#### P3-4: OpenTelemetry distributed tracing `[OBSERVABILITY]`

- **Status:** `[ ]` NOT STARTED
- **Files:** `arbitrage/app.py`, `uap/backend/api.py`, Go Vortex
- **Fix steps:**
  1. Add `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-flask` to deps
  2. Initialize TracerProvider in `create_app()` with OTLP exporter
  3. Add `opentelemetry-instrumentation-requests` for LLM/external calls
  4. Go Vortex: add `go.opentelemetry.io/otel` with Echo middleware
  5. Configure Jaeger/Tempo collector in `docker-compose.prod.yml`
  6. Add trace ID to JSON logs for correlation
- **Agent:** `backend-developer` | **Branch:** `feature/p3-4-otel-traces`

#### P3-5: Helm charts `[INFRA]`

- **Status:** `[ ]` NOT STARTED
- **Target:** `kubernetes/charts/adrion/`
- **Fix steps:**
  1. `helm create kubernetes/charts/adrion`
  2. Convert existing K8s YAML to templates:
     - `templates/deployment.yaml` — parameterize image, replicas, resources
     - `templates/service.yaml` — parameterize ports
     - `templates/ingress.yaml` — parameterize host, TLS
     - `templates/configmap.yaml` — from `kubernetes/02-config/`
     - `templates/secrets.yaml` — external secrets reference
  3. Create `values.yaml` with sensible defaults
  4. Create `values-prod.yaml` overlay
  5. Test: `helm lint kubernetes/charts/adrion/`
  6. Test: `helm template adrion kubernetes/charts/adrion/ | kubectl apply --dry-run=client -f -`
- **Agent:** `backend-developer` | **Branch:** `feature/p3-5-helm-charts`

---

### POST-100: SCALING (backlog)

| # | Task | Details | Priority |
| --- | --- | --- | --- |
| S1 | Infrastructure as Code | Terraform/Pulumi for cloud provisioning (AWS/GCP) | MEDIUM |
| S2 | Multi-region DR | Cross-region PostgreSQL replication, failover automation | HIGH |
| S3 | Load testing in CI | k6 benchmarks on every release, performance regression gate | MEDIUM |
| S4 | SaaS multi-tenant isolation | Per-tenant DB schemas, tenant-aware middleware | LOW |

---

## 8. EXECUTION STRATEGY — PLAN OPERACYJNY

### Zasada Matrycy 3-6-9

Kazde zadanie oceniane przez 3 perspektywy:

- **LOGOS (Prawda):** Czy naprawia faktyczny blad? Czy kod jest poprawny?
- **ETHOS (Dobro):** Czy chroni system i uzytkownikow? Czy jest etyczne?
- **EROS (Tworzenie):** Czy posuwa projekt do przodu? Czy jest eleganckie?

### Kolejnosc wykonania (dependency graph)

```text
WAVE 1 (parallel — no deps):
  P0-1 (SQL injection)  ──┐
  P0-2 (Root cleanup)     │── Can run simultaneously
  P0-4 (Docker socket)    │
  P0-5 (ARCHITECTURE.md) ->

WAVE 2 (after P0-1):
  P0-3 (UAP refactor) ── needs P0-1 fix in place first

WAVE 3 (after P0-3, parallel):
  P1-1 (CSRF)         P1-2 (K8s TLS)      P1-3 (DB types)
  P1-5 (Laws sync)    P1-6 (Prometheus)    P1-7 (Dockerfile)
  P1-4 (Genesis)

WAVE 4 (after P0-3):
  P2-1 (UAP mocks)    P2-4 (Rate limit)

WAVE 5 (parallel — no deps):
  P2-2 (Hypothesis)   P2-3 (Go deps)
  P2-5 (Deprecation) → P2-6 (Stub server)

WAVE 6 (after all above):
  P3-1 (Contract)     P3-2 (DAST)    P3-3 (Cosign)
  P3-4 (OTel)         P3-5 (Helm)
```

### Agent Assignment (5 parallel agents per wave)

**WAVE 1 — P0 Quick Wins (4 agents parallel):**

| Agent | Task | Type | Effort | Branch |
| --- | --- | --- | --- | --- |
| A1 | P0-1: SQL injection fix | backend-developer | S | `fix/p0-1-sql-injection` |
| A2 | P0-2: Root cleanup v2 | general-purpose | L | `chore/p0-2-root-cleanup` |
| A3 | P0-4: Docker socket removal | backend-developer | XS | `fix/p0-4-docker-socket` |
| A4 | P0-5: ARCHITECTURE.md rewrite | backend-developer | M | `docs/p0-5-architecture` |

**WAVE 2 — P0 Major Refactor (1 agent, focused):**

| Agent | Task | Type | Effort | Branch |
| --- | --- | --- | --- | --- |
| A1 | P0-3: UAP refactor (2110→5 files) | backend-developer | XL | `refactor/p0-3-uap-blueprints` |

**WAVE 3 — P1 Security (5 agents parallel):**

| Agent | Task | Type | Effort | Branch |
| --- | --- | --- | --- | --- |
| A1 | P1-1: CSRF + P1-2: K8s TLS | backend-developer | M+M | `feature/p1-1-csrf`, `feature/p1-2-k8s-tls` |
| A2 | P1-3: DB types + P1-5: Laws sync | python-pro | S+S | `fix/p1-3-db-types`, `fix/p1-5-laws-sync` |
| A3 | P1-4: Genesis Record cleanup | general-purpose | M | `chore/p1-4-genesis-cleanup` |
| A4 | P1-6: Prometheus + P1-7: Dockerfile | backend-developer | M+M | `fix/p1-6-prometheus`, `feature/p1-7-multistage-docker` |
| A5 | P2-1: UAP mocks + P2-4: Rate limit | backend-developer | M+S | `fix/p2-1-uap-mock-data`, `fix/p2-4-rate-limit` |

**WAVE 4 — P2 Quality (3 agents parallel):**

| Agent | Task | Type | Effort | Branch |
| --- | --- | --- | --- | --- |
| A1 | P2-2: Hypothesis tests | python-pro | M | `feature/p2-2-hypothesis-tests` |
| A2 | P2-3: Go deps | backend-developer | S | `chore/p2-3-go-deps` |
| A3 | P2-5 + P2-6: Deprecation + Stub | backend-developer | S+S | `chore/p2-5-deprecation`, `chore/p2-6-stub-server` |

**WAVE 5 — P3 Excellence (5 agents parallel):**

| Agent | Task | Type | Effort | Branch |
| --- | --- | --- | --- | --- |
| A1 | P3-1: Contract testing | python-pro | M | `feature/p3-1-contract-tests` |
| A2 | P3-2: DAST scanning | backend-developer | M | `feature/p3-2-dast-zap` |
| A3 | P3-3: Image signing | backend-developer | S | `feature/p3-3-cosign` |
| A4 | P3-4: OpenTelemetry | backend-developer | L | `feature/p3-4-otel-traces` |
| A5 | P3-5: Helm charts | backend-developer | L | `feature/p3-5-helm-charts` |

### Git Strategy

```bash
# Each task gets its own branch from main
git checkout main && git pull
git checkout -b fix/p0-1-sql-injection

# After task completion — squash merge to main
git checkout main
git merge --squash fix/p0-1-sql-injection
git commit -m "fix: sanitize SQL column names in UAP agent update endpoint"

# Phase gates — tag after each phase passes verification
git tag -a v4.1-p0 -m "Phase 0 complete: critical fixes (75→85)"
git tag -a v4.2-p1 -m "Phase 1 complete: security hardening (85→90)"
git tag -a v4.3-p2 -m "Phase 2 complete: quality polish (90→95)"
git tag -a v5.0    -m "Phase 3 complete: excellence (95→100)"
```

### Verification Gates

```bash
# === GATE 1: After Phase 0 (target: 85/100) ===
ls -1 | wc -l                                    # < 50 items in root
python -m pytest tests/ -q --tb=no               # all pass
python -m pytest uap/tests/ -q --tb=no           # all pass
grep -rn "f\".*UPDATE.*SET.*{" uap/              # 0 matches (no SQL injection)
grep -r "docker.sock" docker-compose.prod.yml    # 0 matches
wc -l uap/backend/api.py                         # < 300 lines

# === GATE 2: After Phase 1 (target: 90/100) ===
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
grep "CHANGE_ME" kubernetes/02-config/*.yaml     # only placeholders
mypy arbitrage/database.py                       # passes
docker build -t adrion-test .                    # multi-stage build succeeds
docker images adrion-test --format "{{.Size}}"   # < 200MB

# === GATE 3: After Phase 2 (target: 95/100) ===
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=85
python -m pytest tests/test_*_hypothesis.py -v   # property tests pass
go test ./... -v                                  # Go tests pass
grep -c "mock\|hardcoded" uap/backend/           # 0 in production code

# === GATE 4: After Phase 3 (target: 100/100) ===
helm lint kubernetes/charts/adrion/
schemathesis run docs/openapi.yaml --dry-run     # contract test schema valid
# ZAP scan: 0 HIGH/CRITICAL findings
# cosign verify: signature valid
```

---

## 9. KNOWN ISSUES (do NOT re-investigate)

| Issue                                   | Status      | Resolution                                   |
| --------------------------------------- | ----------- | -------------------------------------------- |
| `arbitrage_server.py` is deprecated     | KNOWN       | Use `wsgi.py` → `arbitrage.app.create_app()` |
| `.env` not in git                       | VERIFIED OK | `.gitignore` has `.env*`                     |
| Phase2_Reports (311MB clone)            | REMOVED     | `.gitignore` blocks re-add                   |
| K8s secrets = placeholders              | INTENTIONAL | Real values via `kubectl create secret`      |
| UAP `_execute_task` uses threads        | KNOWN       | Future: migrate to Celery/asyncio            |
| `conftest.py` schema has only jobs+bids | KNOWN-DEBT  | Add missing tables to `in_memory_db` fixture |

---

## 10. CI/CD PIPELINES (10 workflows)

| Workflow                  | Trigger              | Gates                             |
| ------------------------- | -------------------- | --------------------------------- |
| `python-ci.yml`           | push/PR              | ruff + mypy + pytest 80% + TIER-0 |
| `go-ci.yml`               | push/PR              | go vet + test 80%                 |
| `docker-ci.yml`           | push/PR              | docker build (no push)            |
| `security-ci.yml`         | push/PR + weekly Mon | bandit + safety + trivy           |
| `release.yml`             | tag v*.*.\*          | validate → release → GHCR push    |
| `tier0-gate.yml`          | push/PR              | critical path tests only          |
| `adr-check.yml`           | push/PR              | ADR format validation             |
| `162d-gate.yml`           | push/PR              | 162D decision space integrity     |
| `linkedin-publish.yml`    | manual               | content publishing                |
| `micro-saas-security.yml` | push/PR              | SaaS-specific security checks     |

---

## 11. DOCKER COMPOSE FILES

| File                                 | Purpose      | Services                                     | LLM Backend  |
| ------------------------------------ | ------------ | -------------------------------------------- | ------------ |
| `docker-compose.yml`                 | Dev          | postgres, backend, frontend, ollama, pgadmin | auto (local) |
| `docker-compose.prod.yml`            | Production   | 10 services + nginx TLS + monitoring stack   | auto         |
| `docker-compose.cloud.yml`           | Cloud deploy | 8 services, named volumes, no Docker socket  | openrouter   |
| `docker-compose.mcp-tier.yml`        | MCP layer    | 6 MCP microservices                          | auto         |
| `docker-compose.lmstudio.yml`        | LM Studio    | backend + LM Studio endpoint                 | lmstudio     |
| `docker-compose.k8s-integration.yml` | K8s bridge   | local services + k8s network                 | auto         |
| `docker-compose-orchestration.yml`   | Full stack   | All services orchestrated                    | auto         |
<!-- EOF -->
