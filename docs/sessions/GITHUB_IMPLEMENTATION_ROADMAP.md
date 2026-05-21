# ADRION 369 — GitHub Implementation Roadmap

## PHASE 0: Pre-Launch Verification (2-3 dni)

### Checklist
- [ ] Zsynchronizować Guardian Laws: 11 (kod) vs 9 (CLAUDE.md) — update CANONICAL.json + CLAUDE.md
- [ ] Weryfikacja: PARP_Wniosek_PL_v2.md z v2_complete folder — czy zawiera wszystkie wymagane sekcje?
- [ ] Potwierdzić struktura GitHub:
  - [ ] `main` branch = current state
  - [ ] `master` branch = release branch (za CLAUDE.md)
  - [ ] `.github/workflows/` = 10 CI/CD pipelines zdefiniowane (python-ci, go-ci, docker-ci, security-ci, etc.)
- [ ] Weryfikacja `.gitignore`: czy blokuje `*.log`, `cov_*.txt`, `.env*`, `Phase2_Reports/`?
- [ ] Potwierdzić GitHub Secrets skonfigurowane:
  - [ ] `CHANGE_ME_IN_PRODUCTION` placeholders w K8s (jeśli wdrażacie)
  - [ ] LLM credentials: `OLLAMA_URL`, `OPENROUTER_API_KEY` (jeśli potrzebne)

---

## PHASE 1: WAVE 1 — P0 Critical Fixes (parallel, 1 week)

**Goal:** 75 → 85 (root cleanup, SQL injection, Docker socket, docs)

### P0-1: Fix SQL injection in UAP ✅ (ALREADY DONE?)
- [ ] Verify `uap/backend/blueprints/__init__.py:52` — `ALLOWED_AGENT_COLUMNS` frozenset
- [ ] Verify `uap/backend/blueprints/agents_bp.py:199` — column filtering
- [ ] PR: `fix/p0-1-sql-injection` → merge to main

### P0-2: Root cleanup v2
- [ ] Create branch: `chore/p0-2-root-cleanup`
- [ ] Move 42 .md files → `docs/sessions/`
- [ ] Move 24 .py scripts → `scripts/`
- [ ] Move 8 .ps1 → `scripts/install/`
- [ ] Move 10 .log → `logs/`
- [ ] Delete: `Users/`, `O/`, `_temp_extract/`, `temp_deploy/`
- [ ] Update `.gitignore`: add `*.log`, `cov_*.txt`, `_*_stderr.log`
- [ ] PR: `chore/p0-2-root-cleanup` → merge to main

### P0-4: Remove Docker socket from prod
- [ ] Verify `docker-compose.prod.yml` — 0 `/var/run/docker.sock` mounts
- [ ] Verify `docker-compose.cloud.yml` — clean
- [ ] PR: `fix/p0-4-docker-socket` → merge to main

### P0-5: Rewrite ARCHITECTURE.md
- [ ] Update `docs/ARCHITECTURE.md`:
  - [ ] Add v4.0 overview (Flask App Factory + 5 Blueprints)
  - [ ] Add Guardian Laws Engine (9 or 11? TBD)
  - [ ] Add Trinity Score (Material/Intellectual/Essential)
  - [ ] Add UAP Orchestrator + 6 Personas
  - [ ] Add Go Vortex (EBDI + digital root)
  - [ ] Add MCP Layer (6 microservices, ports 9000-9005)
  - [ ] Add Matryca 3-6-9 diagram + data flow
- [ ] PR: `docs/p0-5-architecture` → merge to main

---

## PHASE 2: WAVE 2 — P0-3 UAP Refactor (focused, 1-2 weeks)

**Goal:** Monolith 2110 lines → 5 files × 400 lines each

### P0-3: UAP blueprints extraction
- [ ] Create branch: `refactor/p0-3-uap-blueprints`
- [ ] Read `uap/backend/api.py` — map all 2110 lines to routes
- [ ] Create structure:
  ```
  uap/backend/
    api.py (~200 lines)
    blueprints/
      __init__.py (shared: db, auth, errors)
      tasks_bp.py (CRUD + execution)
      agents_bp.py (CRUD + config)
      genesis_bp.py (Genesis Record)
      ebdi_bp.py (EBDI state machine)
      admin_bp.py (diagnostics)
  ```
- [ ] Extract shared utilities → `blueprints/__init__.py`
- [ ] Create each blueprint file
- [ ] Update `api.py` to register blueprints
- [ ] Test: `python -m pytest uap/tests/ -q` → green
- [ ] Final: `wc -l uap/backend/api.py` < 300
- [ ] PR: `refactor/p0-3-uap-blueprints` → merge to main

**Verification Gate (nach P0-3):**
```bash
ls -1 | wc -l                                     # < 50 items in root
python -m pytest tests/ -q --tb=no                # pass
grep -rn "f\".*UPDATE.*SET.*{" uap/               # 0 matches
grep -r "docker.sock" docker-compose.prod.yml     # 0 matches
wc -l uap/backend/api.py                          # < 300 lines
```

---

## PHASE 3: WAVE 3-4 — P1-P2 Security & Quality (parallel, 2 weeks)

**Goal:** 85 → 95 (security, testing, deprecation)

### P1: Security Hardening

#### P1-1: Token-based CSRF
- [ ] Branch: `feature/p1-1-csrf`
- [ ] Add `Flask-WTF` to `requirements-arbitrage.txt`
- [ ] Update `arbitrage/app.py` — `CSRFProtect(app)` with `WTF_CSRF_TIME_LIMIT=3600`
- [ ] Exempt API endpoints: `@csrf.exempt` or `WTF_CSRF_CHECK_DEFAULT=False`
- [ ] Test: POST without CSRF token → 400/403
- [ ] PR → merge

#### P1-2: K8s TLS with cert-manager
- [ ] Branch: `feature/p1-2-k8s-tls`
- [ ] Create `kubernetes/03-tls/cluster-issuer.yaml`
- [ ] Add cert-manager annotations to Ingress
- [ ] Create `kubernetes/03-tls/certificate.yaml`
- [ ] Document: `docs/LOCAL_DEPLOYMENT_GUIDE.md`
- [ ] PR → merge

#### P1-3: Database type hints
- [ ] Branch: `fix/p1-3-db-types`
- [ ] Update `arbitrage/database.py` — proper type hints for `get_conn()`
- [ ] Option: use `Protocol` for DB connection abstraction
- [ ] Verify: `mypy arbitrage/database.py` passes
- [ ] PR → merge

#### P1-4: Genesis Record cleanup
- [ ] Branch: `chore/p1-4-genesis-cleanup`
- [ ] Count actual files per category (verify stats)
- [ ] Find and remove 6 duplicate filenames
- [ ] Rename to `Topic_DD-MM-YYYY.md` format
- [ ] Update `Genesis Record/README.md`
- [ ] PR → merge

#### P1-5: Guardian Laws sync
- [ ] Branch: `fix/p1-5-laws-sync`
- [ ] Read `docs/GUARDIAN_LAWS_CANONICAL.json` — extract exact names
- [ ] Find wrong names in .md files (e.g., "Truth" → "Harmony")
- [ ] Verify: `grep -rn "Truth\|Autonomy\|Justice" *.md docs/*.md` → only contextual
- [ ] PR → merge

#### P1-6: Fix Prometheus targets
- [ ] Branch: `fix/p1-6-prometheus`
- [ ] Add `postgres_exporter` sidecar in `docker-compose.prod.yml`
- [ ] Fix Grafana scrape paths
- [ ] Verify dashboard JSON matches metric names
- [ ] PR → merge

#### P1-7: Multi-stage Dockerfile
- [ ] Branch: `feature/p1-7-multistage-docker`
- [ ] Rewrite `Dockerfile` with builder + runtime stages
- [ ] Test build: `docker build -t adrion-test .` → size < 200MB
- [ ] Update other Dockerfiles
- [ ] PR → merge

### P2: Quality Polish

#### P2-1: Remove UAP mock data
- [ ] Branch: `fix/p2-1-uap-mock-data`
- [ ] Replace hardcoded returns in `get_active_tasks()`, `get_task_stats()`
- [ ] Use parameterized SQL (enforce P0-1 fix)
- [ ] Test: empty DB → empty list (not mocks)
- [ ] PR → merge

#### P2-2: Hypothesis property-based tests
- [ ] Branch: `feature/p2-2-hypothesis-tests`
- [ ] Add `hypothesis` to dev deps
- [ ] Create `tests/test_guardian_hypothesis.py` — fuzz all laws
- [ ] Create `tests/test_trinity_hypothesis.py` — fuzz Trinity scores
- [ ] Run: `python -m pytest tests/test_*_hypothesis.py -v`
- [ ] PR → merge

#### P2-3: Update Go dependencies
- [ ] Branch: `chore/p2-3-go-deps`
- [ ] `go get -u golang.org/x/crypto golang.org/x/net`
- [ ] `go mod tidy`
- [ ] `go test ./... -v` → green
- [ ] PR → merge

#### P2-4: Rate limit wholesale_bp
- [ ] Branch: `fix/p2-4-rate-limit`
- [ ] Add `is_allowed(client_ip)` check in `handle_wholesale_scout`
- [ ] Test: rapid requests → 429
- [ ] PR → merge

#### P2-5: Deprecation roadmap
- [ ] Branch: `chore/p2-5-deprecation`
- [ ] Add notice to `CHANGELOG.md`: "arbitrage_server.py removed in v5.0"
- [ ] Ensure `arbitrage_server.py` has `DeprecationWarning`
- [ ] PR → merge

#### P2-6: Stub deprecated server
- [ ] Branch: `chore/p2-6-stub-server`
- [ ] Replace `arbitrage_server.py` with ~30-line stub
- [ ] Import from `arbitrage.app.create_app()`
- [ ] PR → merge

---

## PHASE 4: WAVE 5 — P3 Excellence (2 weeks)

**Goal:** 95 → 100 (testing, security scanning, observability)

### P3-1: Contract testing
- [ ] Branch: `feature/p3-1-contract-tests`
- [ ] Add `schemathesis` to dev deps
- [ ] Create `tests/contract/test_arbitrage_contract.py`
- [ ] Create `tests/contract/test_uap_contract.py`
- [ ] Run: `schemathesis run docs/openapi.yaml --base-url=http://localhost:8003`
- [ ] PR → merge

### P3-2: DAST scanning with OWASP ZAP
- [ ] Branch: `feature/p3-2-dast-zap`
- [ ] Create `.github/workflows/dast-zap.yml`
- [ ] Use `zaproxy/action-full-scan@v0.10.0`
- [ ] Fail on HIGH/CRITICAL findings
- [ ] Create `.zap/rules.conf` (suppress false positives)
- [ ] PR → merge

### P3-3: Container image signing
- [ ] Branch: `feature/p3-3-cosign`
- [ ] Add cosign step to `.github/workflows/release.yml`
- [ ] Generate key pair, store in GitHub secrets
- [ ] Verify: `cosign verify --key cosign.pub ghcr.io/$IMAGE`
- [ ] Document in `docs/SECURITY.md`
- [ ] PR → merge

### P3-4: OpenTelemetry distributed tracing
- [ ] Branch: `feature/p3-4-otel-traces`
- [ ] Add OTel deps: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-flask`
- [ ] Initialize TracerProvider in `create_app()`
- [ ] Configure Jaeger/Tempo collector in `docker-compose.prod.yml`
- [ ] Add trace ID to JSON logs
- [ ] PR → merge

### P3-5: Helm charts
- [ ] Branch: `feature/p3-5-helm-charts`
- [ ] `helm create kubernetes/charts/adrion/`
- [ ] Convert K8s YAML to templates:
  - [ ] `templates/deployment.yaml`
  - [ ] `templates/service.yaml`
  - [ ] `templates/ingress.yaml`
  - [ ] `templates/configmap.yaml`
  - [ ] `templates/secrets.yaml`
- [ ] Create `values.yaml` + `values-prod.yaml`
- [ ] Test: `helm lint kubernetes/charts/adrion/`
- [ ] PR → merge

---

## Final Verification Gate (POST-100)

```bash
# All tests pass with 80%+ coverage
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
go test ./... -v -coverprofile=coverage.out

# No regressions
ruff check arbitrage/ uap/ tests/
mypy arbitrage/

# No security issues
bandit -r arbitrage/ -ll
safety check -r requirements-arbitrage.txt

# Docker builds correctly
docker build -t adrion:latest . && docker images adrion:latest --format "{{.Size}}"

# Git tags mark phases
git tag -a v4.1-p0 -m "Phase 0 complete: critical fixes (75→85)"
git tag -a v4.2-p1 -m "Phase 1 complete: security hardening (85→90)"
git tag -a v4.3-p2 -m "Phase 2 complete: quality polish (90→95)"
git tag -a v5.0    -m "Phase 3 complete: excellence (95→100)"

# Push tags
git push origin v4.1-p0 v4.2-p1 v4.3-p2 v5.0
```

---

## GitHub Actions Workflows (TBD — Create if missing)

| Workflow | File | Trigger | Gates |
|----------|------|---------|-------|
| Python CI | `.github/workflows/python-ci.yml` | push/PR | ruff + mypy + pytest 80% + TIER-0 |
| Go CI | `.github/workflows/go-ci.yml` | push/PR | go vet + test 80% |
| Docker CI | `.github/workflows/docker-ci.yml` | push/PR | docker build (no push) |
| Security CI | `.github/workflows/security-ci.yml` | push/PR + weekly | bandit + safety + trivy |
| Release | `.github/workflows/release.yml` | tag v*.*.* | validate → release → GHCR push |

---

## Timeline

| Phase | Tasks | Duration | ETA |
|-------|-------|----------|-----|
| **P0** | P0-1,2,4,5 | 1 week | 2026-05-27 |
| **P0-3** | UAP refactor | 1-2 weeks | 2026-06-10 |
| **P1-P2** | Security + Quality | 2 weeks | 2026-06-24 |
| **P3** | Excellence | 2 weeks | 2026-07-08 |
| **POST** | Helm, OTel, Cosign | 1 week | 2026-07-15 |

**Target:** v5.0 ready for PARP submission = **2026-07-15**

---

## Notes for GitHub

- Use **squash merge** for all PRs (clean history)
- Tag every phase with version bump
- Keep CLAUDE.md in sync — it's the source of truth
- Binary: "status quo" (free tier) vs. "post-PARP" (Azure/Vertex/GitLab)
