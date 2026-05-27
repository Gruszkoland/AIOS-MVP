# 🏗️ ADRION 369 v4.0 — PROJECT MANIFEST & ARCHITECTURAL GUIDELINES

> **Single Source of Truth for AI Orchestrators, Copilots, and Development Teams**
> **Version:** 5.0 | **Updated:** 2026-04-22 | **Status:** Core Standards Locked

---

## 1️⃣ WARSTWA TECHNOLOGICZNA (The Stack)

### Primary Language & Runtime

- **Language:** Python 3.11+ (primary), Go 1.22 (Vortex), JavaScript/TypeScript (Dashboard)
- **Python Runtime:** CPython 3.11+
- **Package Manager (Python):** pip via `requirements-*.txt` or Poetry (future)
- **Package Manager (Go):** Go modules (`go.mod`, `go.sum`)

### Web Frameworks

- **Python Backend:** Flask 3.1.0+ with App Factory Pattern (`arbitrage/app.py`)
- **Go Microservice:** Echo v4.11.4 (HTTP router, minimal overhead)
- **Frontend:** React/Vue (dashboard in `/frontend`), PWA-ready

### Database & ORM

- **Primary:** PostgreSQL 13+ (production)
- **Development:** SQLite (local)
- **Connection Pool:** SQLAlchemy 2.0.21 + psycopg2-binary
- **Query Builder:** SQLAlchemy ORM
- **Migrations:** Custom scripts in `/db/migrations/`

### Configuration Management

- **Pattern:** Pydantic `BaseSettings` (`arbitrage/config.py`)
- **Environment Variables:** `.env` file (NEVER committed)
- **Secret Management:** Use `config.AdrionSettings()` for all configs
- **Type Validation:** All config values must have Pydantic field validators

### AI/ML & NLP Stack

- **Local LLM Runtime:** Ollama (default: DeepSeek-Coder, configurable)
- **LLM Fallback:** OpenRouter API (canary deploy, circuit-breaker)
- **Embeddings:** sentence-transformers 2.2.2
- **Vector Search:** hnswlib 0.7.0 (HNSW algorithm, no DB dependency)
- **Numerical Compute:** NumPy 1.24.3, SciPy 1.11.3

### Message Queue & APIs

- **HTTP Server:** Flask + Waitress (WSGI)
- **RESTful API Docs:** OpenAPI/Swagger (auto-generated from Blueprints)
- **Documentation File:** `docs/openapi.yaml` (static, checked into repo)

### Monitoring & Observability

- **Metrics:** Prometheus text format (endpoint: `GET /metrics`)
- **Logging:** structlog 23.1.0 (structured, JSON-compatible)
- **Health Checks:** Cascading health endpoints (`/health`, `/health/live`, `/health/ready`)

### Testing & Quality Assurance

- **Unit Tests:** pytest 7.4+, pytest-cov 4.1+, pytest-asyncio
- **Linting:** Ruff 0.1+ (E, F, W, I rules; ignore E501)
- **Code Formatting:** Black 23.11+ (line length: 100)
- **Type Checking:** MyPy 1.6+ (strict mode)
- **Security Scanning:** Bandit (low threshold: `-ll`), Safety (dependencies)

---

## 2️⃣ WARSTWA ARCHITEKTONICZNA (The Blueprint)

### Application Structure

```
arbitrage/
├── app.py                 # App Factory; registers 5 blueprints + top-level routes
├── blueprints/            # 5 Flask Blueprints (each with dedicated prefix)
│   ├── arbitrage_bp.py    # /api/arbitrage (jobs, bids, scout, cycle)
│   ├── quantum_bp.py      # /api/quantum (decide, status, scan)
│   ├── oracle_bp.py       # /api/oracle (predict, scan)
│   ├── wholesale_bp.py    # /api/wholesale (scout, cycle, deals)
│   └── payments_bp.py     # /api/payments (checkout, webhook, mass-gen, manifest)
├── agents/                # AI Personas (6 agents: Librarian, SAP, Auditor, Sentinel, Architect, Healer)
├── crews/                 # Multi-agent workflows (CrewAI-compatible)
├── config.py              # Pydantic BaseSettings + validators
├── database.py            # SQLAlchemy models & session management
├── guardian.py            # 9 Guardian Laws Engine (G1–G9 enforcement)
├── trinity.py             # Trinity Score (Material/Intellectual/Essential)
├── llm.py                 # Ollama client + OpenRouter fallback
├── oracle.py              # Vortex Oracle predictions
├── circuit_breaker.py     # Rate limiting + failover (LLM, Stripe, Apify, XRP)
├── rate_limiter.py        # Sliding-window rate limiter (per endpoint)
├── rag_integration.py     # RAG pipeline (retrieval + generation)
├── quantum.py             # Quantum scan channels
├── hexagon.py             # Hexagonal architecture helpers
├── metrics.py             # Prometheus metrics
└── __init__.py            # Module init
```

### Architectural Pattern

- **Style:** Clean Architecture (Hexagonal) + Domain-Driven Design (DDD)
- **Separation of Concerns:**
  - **Domain Layer:** `guardian.py`, `trinity.py`, `oracle.py` (pure logic, NO I/O)
  - **Application Layer:** Blueprints (orchestration of domain + repositories)
  - **Infrastructure Layer:** `database.py`, `llm.py`, `config.py` (external integrations)
  - **API Layer:** Flask Blueprints (HTTP handlers, request/response serialization)

### Data Flow

1. **HTTP Request** → Flask Blueprint
2. **Route Handler** → Validate & deserialize input (Pydantic)
3. **Business Logic** → Call domain services (`guardian`, `trinity`, `oracle`)
4. **Database/External** → Repository pattern via SQLAlchemy ORM
5. **Response Serialization** → JSON (via Pydantic model.model_dump())

### Coupling Rules

- ✅ **Services can call Services** (horizontal)
- ✅ **Blueprints can call Services** (vertical, inbound)
- ❌ **Services cannot call Blueprints** (no circular dependency)
- ❌ **Database queries in Blueprints** (use repository layer)
- ❌ **LLM calls in HTTP handlers** (use a Service wrapper)

### Multi-Service Architecture

```
nginx (TLS) → Flask:8003 (arbitrage, quantum, oracle, wholesale, payments)
            → UAP:8002 (6 AI Personas)
            → Vortex:1740 (Go, 174Hz pulse, digital root oracle)
            → MCP Layer:9000–9005 (Router, Vortex, Guardian, Oracle, Genesis, Healer)
```

---

## 3️⃣ WARSTWA STANDARDÓW KODU (Code Quality)

### Naming Conventions

| Context | Convention | Example |
|---------|-----------|---------|
| **Python Functions** | `snake_case` | `analyze_job()`, `calculate_trinity_score()` |
| **Python Classes** | `PascalCase` | `GuardianLawsEngine`, `TrinityScore` |
| **Python Constants** | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS`, `TRINITY_MIN_COMBINED` |
| **Database Columns** | `lower_snake_case` | `created_at`, `job_id`, `guardian_score` |
| **Flask Routes** | `kebab-case` (URL)| `/api/arbitrage/jobs`, `/api/oracle/predict` |
| **Environment Variables** | `UPPER_SNAKE_CASE` | `DATABASE_URL`, `OLLAMA_API_BASE` |
| **Go Functions** | `PascalCase` (exported) | `GetVortexState()`, `CalculateDigitalRoot()` |
| **Go Constants** | `PascalCase` | `VortexPulseHz` |
| **File Names** | `snake_case.py` | `guardian.py`, `circuit_breaker.py` |

### Clean Code Standards

#### Function Length & Complexity

- **Max lines per function:** 30 lines (excluding tests)
- **Max arguments:** 3 positional + kwargs
- **Max nesting:** 2 levels (if-else, for, try-except)
- **Cyclomatic complexity:** ≤ 10 (use tools: `radon cc`)

#### Comments & Documentation

- ✅ **Required:** JSDoc/docstring for all public functions
- ✅ **Required:** Type hints on all function parameters and returns
- ✅ **Required:** Pydantic model docstrings (one-liner minimum)
- ❌ **Discouraged:** Inline comments (code should be self-documenting)
- 🔄 **When explaining WHY (not WHAT):** Use inline comments sparingly

**Example (correct):**

```python
def calculate_trinity_score(
    material_score: float,
    intellectual_score: float,
    essential_score: float,
) -> float:
    """
    Compute combined Trinity Score from three perspectives.

    Aggregation:
    - Material & Intellectual: harmonic mean
    - Essential: geometric mean
    - Final: arithmetic mean of all three

    Args:
        material_score: System resource availability (0–1).
        intellectual_score: LLM analysis quality (0–1).
        essential_score: Purpose alignment + profitability (0–1).

    Returns:
        Combined score (0–1). Approved when >= TRINITY_MIN_COMBINED.

    Raises:
        ValueError: If any score is not in [0, 1].
    """
    if not all(0 <= s <= 1 for s in [material_score, intellectual_score, essential_score]):
        raise ValueError("All scores must be in [0, 1]")

    # Material & Intellectual use harmonic mean (fail-fast)
    harmonic = 2 / (1/material_score + 1/intellectual_score) if material_score > 0 and intellectual_score > 0 else 0

    # Essential uses geometric mean
    geometric = (essential_score) ** (1/1)  # Simplified for 1 factor

    # Final: arithmetic mean
    return (harmonic + geometric) / 2
```

### Type Annotations & Typing

- ✅ **All function signatures** must include type hints
- ✅ **All class attributes** must have type hints
- ✅ **Use `Union`, `Optional`, `TypeVar`** for complex types
- ✅ **Prefer `from typing import …`** over `typing.X`
- ❌ **NEVER use `any`** — use `Unknown` instead
- ✅ **Pydantic models** must validate all input types

**Example (correct):**

```python
from typing import Optional, Union
from pydantic import BaseModel, Field

class JobAnalysisInput(BaseModel):
    job_id: str
    title: str
    salary_range: tuple[float, float] = Field(..., description="Min/max salary")
    priority: Optional[int] = None

def analyze_job(job: JobAnalysisInput) -> dict[str, Union[float, str]]:
    """Analyze a job posting."""
    return {"score": 0.85, "status": "approved"}
```

### Error Handling

- ✅ **Use custom exceptions** in `arbitrage/exceptions.py`
- ✅ **Try-catch in async/I/O** (LLM calls, database queries, API calls)
- ✅ **Raise meaningful errors** with context messages
- ✅ **Log before raising** (use structlog)
- ❌ **Bare `except:`** — always specify exception type

**Example (correct):**

```python
import structlog
from arbitrage.exceptions import LLMTimeoutError, DatabaseError

logger = structlog.get_logger()

def query_llm(prompt: str, timeout: int = 30) -> str:
    """Query Ollama LLM."""
    try:
        response = ollama_client.generate(prompt, timeout=timeout)
        return response.text
    except requests.Timeout as e:
        logger.error("llm_timeout", prompt_length=len(prompt), timeout=timeout)
        raise LLMTimeoutError(f"LLM did not respond within {timeout}s") from e
    except Exception as e:
        logger.exception("llm_error", prompt_length=len(prompt))
        raise LLMError(f"LLM error: {str(e)}") from e
```

### Async & Concurrency

- ✅ **Use `asyncio`** for I/O-bound operations (API calls, DB queries)
- ✅ **Mark async functions** with `async def`
- ✅ **Await all coroutines** (no fire-and-forget without explicit `asyncio.create_task()`)
- ✅ **Use `asyncio.gather()`** for parallel tasks
- ❌ **Blocking calls in async** (use `loop.run_in_executor()`)

### Imports Organization

```python
# Standard library
import json
import asyncio
from typing import Optional

# Third-party
import flask
import pydantic
import sqlalchemy

# Local
from arbitrage.config import AdrionSettings
from arbitrage.guardian import GuardianLawsEngine
from arbitrage.database import get_db_session
```

---

## 4️⃣ WARSTWA JAKOŚCI I TESTÓW (Quality Assurance)

### Test Strategy & Hierarchy

```
                Unit Tests (Fast, No I/O)
                     ↓
            Integration Tests (Database, LLM mocked)
                     ↓
              E2E Tests (Full stack, live DB)
```

### Test Markers (pytest)

| Marker | Scope | Speed | External | Usage |
|--------|-------|-------|----------|-------|
| `@pytest.mark.unit` | Single function | <100ms | None | Happy path, errors |
| `@pytest.mark.smoke` | Critical paths | <1s | None | Sanity checks |
| `@pytest.mark.integration` | Multiple modules | 1–5s | DB, LLM | Mocked external calls |
| `@pytest.mark.e2e` | Full pipeline | 5–30s | Live DB | Real orchestration |
| `@pytest.mark.guardian` | Guardian Laws | 1–5s | None | Law compliance |
| `@pytest.mark.ragas` | RAG evaluation | 30–60s | LLM | RAG quality metrics |
| `@pytest.mark.tier0` | Critical (NEVER skip) | <5s | None | Core system integrity |
| `@pytest.mark.crisis` | Crisis mode tests | Variable | None | Failover, resilience |

### Running Tests

```bash
# All tests (unit only, default)
python -m pytest tests/ -v --cov=arbitrage --cov-fail-under=80

# Unit + integration (skip e2e)
python -m pytest tests/ -v -m "not e2e"

# Only Guardian Laws compliance
python -m pytest tests/ -v -m "guardian"

# Only TIER 0 critical tests
python -m pytest tests/ -v -m "tier0"

# Coverage HTML report
python -m pytest tests/ --cov=arbitrage --cov-report=html
```

### Test File Structure

```
tests/
├── unit/
│   ├── test_guardian.py          # Guardian Laws validation
│   ├── test_trinity.py           # Trinity Score calculation
│   ├── test_oracle.py            # Oracle predictions
│   ├── test_circuit_breaker.py   # Rate limiting logic
│   └── ...
├── integration/
│   ├── test_blueprint_arbitrage.py  # Blueprint routes
│   ├── test_database_queries.py     # DB operations
│   └── ...
├── e2e/
│   ├── test_end_to_end_pipeline.py
│   └── ...
├── conftest.py                   # Shared fixtures
└── mcp/                          # MCP server tests (separate)
```

### Test Minimum Coverage

- **Overall:** ≥80% (enforced by pytest config)
- **Services (`arbitrage/*.py`):** ≥85%
- **Blueprints:** ≥75% (UI routes less critical)
- **Guardian & Trinity:** 100% (critical domain logic)

### Code Quality Gates (Pre-commit)

```bash
# 1. Lint (Ruff)
ruff check arbitrage/ uap/ tests/ --ignore=E501

# 2. Format (Black)
black --check arbitrage/ uap/ tests/

# 3. Type check (MyPy)
mypy arbitrage/ --strict

# 4. Security (Bandit)
bandit -r arbitrage/ -ll

# 5. Dependencies (Safety)
safety check -r requirements-arbitrage.txt

# 6. Tests (Pytest)
pytest tests/ -q --cov=arbitrage --cov-fail-under=80
```

---

## 5️⃣ WARSTWA OPERACYJNA I GIT (Operations & CI/CD)

### Git Workflow

- **Model:** Trunk-Based Development (short-lived feature branches)
- **Main branch:** Protected, requires PR + 1 approval
- **Branch naming:** `feature/xyz`, `fix/bug-description`, `docs/update-readme`
- **PR naming:** Use title, reference issue (e.g., `#123`)

### Commit Message Format (Conventional Commits)

```
<type>(<scope>): <subject> (<issue>)

<body>

<footer>
```

**Types:**

| Type | Usage |
|------|-------|
| `feat` | New feature (API route, service, config) |
| `fix` | Bug fix (corrects logic, error handling) |
| `refactor` | Code restructuring (no feature/bug change) |
| `test` | Add/update tests |
| `docs` | Documentation only |
| `chore` | Deps, tooling, config (no code logic) |
| `perf` | Performance optimization |
| `security` | Security fix or hardening |

**Examples:**

```
feat(guardian): add G7 privacy law enforcement (#456)

- Prevent external API calls without consent flag
- Log all privacy violations to audit trail
- Add Guardian Law metrics

docs(readme): update deployment instructions (#789)

fix(llm): handle ollama timeout gracefully

Adds circuit breaker fallback to OpenRouter.

Fixes #234

refactor(database): extract session management to factory

perf(trinity): optimize harmonic mean calculation
```

### CI/CD Pipeline

- **Trigger:** Every PR to `main`, every commit to `main`
- **Steps:**
  1. Lint (Ruff, Black)
  2. Type check (MyPy)
  3. Unit tests (pytest, 80% coverage)
  4. Security scan (Bandit, Safety)
  5. Build Docker image
  6. Deploy (if on `main`)

### Release Versioning (SemVer)

- **Format:** `MAJOR.MINOR.PATCH`
- **File:** `VERSION` (root)
- **Changelog:** `CHANGELOG.md` (Keep a Changelog format)
- **Tag:** Git annotated tags (`v1.2.3`)

---

## 6️⃣ WARSTWA BEZPIECZEŃSTWA (Security & Performance)

### Secret Management

- ✅ **Use environment variables** (`.env` never committed)
- ✅ **Validate with Pydantic** (type checking + required field checking)
- ✅ **Rotate secrets** monthly (database credentials, API keys)
- ✅ **Audit logs** for sensitive operations (payments, privacy-related)
- ❌ **NEVER hardcode** secrets in code or config files

**Example (.env):**

```
DATABASE_URL=postgresql://user:pass@localhost:5432/adrion_dev
OLLAMA_API_BASE=http://localhost:11434
OPENROUTER_API_KEY=sk-...
JWT_SECRET=<random-32-char-string>
```

### Data Protection

- ✅ **TLS for all external communication** (HTTPS, encrypted WebSocket)
- ✅ **Hash sensitive data** (passwords, tokens) with bcrypt/argon2
- ✅ **Encrypt PII at rest** (database columns with sensitive data)
- ✅ **Log anonymization** (never log full credit cards, SSNs)
- ✅ **Compliance:** GDPR (consent, right to be forgotten)

### Performance Optimization

- ✅ **Database indexes** on frequently queried columns (`job_id`, `created_at`)
- ✅ **Connection pooling** (SQLAlchemy pool, max 10 connections)
- ✅ **Cache layer** (Redis for frequently accessed data)
- ✅ **Lazy loading** in ORM (avoid N+1 queries)
- ✅ **Rate limiting** per endpoint (sliding window, `circuit_breaker.py`)
- ✅ **Pagination** for list endpoints (limit 100, offset-based)

**Example (rate limiting):**

```python
from arbitrage.rate_limiter import RateLimiter

limiter = RateLimiter(requests_per_minute=60)

@app.route("/api/arbitrage/jobs")
def list_jobs():
    if not limiter.is_allowed(request.remote_addr):
        return {"error": "Rate limit exceeded"}, 429
    # ... handler logic
```

### Accessibility (a11y) & Internationalization (i18n)

- ✅ **API responses** include human-readable messages (not just codes)
- ✅ **Polish & English support** (comments in English, user messages in Polish)
- ✅ **Error responses** include `error`, `message`, `code` fields
- ✅ **Timestamps** in ISO 8601 format (`2026-04-22T14:30:00Z`)

---

## 7️⃣ STANDARDY DOMENY (Domain Standards)

### Trinity-EBDI Framework

Every decision is evaluated in a **162-dimensional space** (3 perspectives × 6 agents × 9 laws):

| Perspective | Source | Aggregation | Pass Condition |
|-------------|--------|-------------|---|
| **Material** | CPU/RAM (psutil) | Harmonic mean | ≥ 0.3 |
| **Intellectual** | LLM quality score | Harmonic mean | ≥ 0.5 |
| **Essential** | Purpose + profit | Geometric mean | ≥ 0.2 |
| **Combined** | Average of 3 | Arithmetic mean | ≥ `TRINITY_MIN_COMBINED` |

### Guardian Laws Engine (9 Rules)

All decisions are validated against these canonical laws (see `docs/GUARDIAN_LAWS_CANONICAL.json`):

| # | Code | Name | Severity | Veto |
|---|------|------|----------|------|
| 1 | G1 | Unity | MEDIUM | — |
| 2 | G2 | Truth | HIGH | — |
| 3 | G3 | Rhythm | MEDIUM | — |
| 4 | G4 | Causality | HIGH | — |
| 5 | G5 | Transparency | MEDIUM | — |
| 6 | G6 | Nonmaleficence | **CRITICAL** | ✓ |
| 7 | G7 | Autonomy | HIGH | — |
| 8 | G8 | Justice | **CRITICAL** | ✓ |
| 9 | G9 | Sustainability | HIGH | — |

**Decision Rule:**

- 1 CRITICAL violation → **INSTANT DENY**
- 2+ any violations → **DENY**
- 0–1 non-critical violations → **APPROVE** (if Trinity score passes)

### Configuration Constants (from `arbitrage/config.py`)

```python
TRINITY_MIN_COMBINED = 0.5          # Minimum combined Trinity Score
TRINITY_MIN_MATERIAL = 0.3          # Min CPU/RAM availability
TRINITY_MIN_INTELLECTUAL = 0.5      # Min LLM quality
TRINITY_MIN_ESSENTIAL = 0.2         # Min purpose alignment

RATE_LIMIT_JOB_REQUESTS = 60        # Per minute, per IP
RATE_LIMIT_LLM_CALLS = 10           # Per minute
RATE_LIMIT_STRIPE_CALLS = 5         # Per minute

OLLAMA_TIMEOUT_SECONDS = 30
OPENROUTER_TIMEOUT_SECONDS = 45

MAX_DAILY_OPERATIONAL_COST = 500    # USD
MAX_BID_PER_JOB = 100               # USD
```

---

## 8️⃣ CHECKLIST PRZED PR (Pre-PR Checklist)

- [ ] **Code Quality**
  - [ ] Ran `ruff check`; no violations
  - [ ] Ran `black` ; formatted
  - [ ] Ran `mypy --strict`; all types pass
  - [ ] No `any` type hints
- [ ] **Tests**
  - [ ] New features have unit tests
  - [ ] Tests marked with appropriate `@pytest.mark` (unit, integration, e2e)
  - [ ] Coverage ≥80% (`pytest --cov`)
  - [ ] All tests pass locally
- [ ] **Documentation**
  - [ ] Added JSDoc/docstring to all public functions
  - [ ] Updated `CHANGELOG.md` (Keep a Changelog format)
  - [ ] Updated API docs if routes changed (`docs/openapi.yaml`)
- [ ] **Commit Messages**
  - [ ] Used Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.)
  - [ ] Linked to issue (#xyz)
- [ ] **Security & Performance**
  - [ ] No secrets in code (use `.env`)
  - [ ] No N+1 queries in database calls
  - [ ] Rate limiting applied to new endpoints
  - [ ] Ran `bandit -r arbitrage/ -ll`; no critical findings
- [ ] **Architecture**
  - [ ] No circular dependencies
  - [ ] Services don't import Blueprints
  - [ ] Domain logic in `arbitrage/*.py`, not in Blueprints

---

## 9️⃣ DEEP DIVE OPPORTUNITIES (For AI Orchestrators)

**Use these guidelines when:**

1. **Evaluating code quality** → Check against Section 3️⃣ (Code Standards)
2. **Designing new features** → Follow Section 2️⃣ (Architecture)
3. **Writing tests** → Follow Section 4️⃣ (QA & Testing)
4. **Making commits** → Follow Section 5️⃣ (Git & Operations)
5. **Reviewing security** → Check Section 6️⃣ (Security & Performance)
6. **Enforcing domain rules** → Reference Section 7️⃣ (Trinity-EBDI, Guardian Laws)

---

## 🔟 METADATA

| Attribute | Value |
|-----------|-------|
| **Project Name** | ADRION 369 v4.0 |
| **Team Language** | Polish (communication), English (code) |
| **Python Version** | 3.11+ |
| **Go Version** | 1.22+ |
| **Test Coverage** | ≥80% (enforced) |
| **Last Updated** | 2026-04-22 |
| **Manifest Version** | 5.0 |
| **Authority** | Project Lead (Adi Ha) |
| **Canonical Source** | `docs/GUARDIAN_LAWS_CANONICAL.json` |
| **Compression Protocol** | `docs/COMPRESSION_GUIDE.md` (Level 0–2 symbolic notation, 50–70% token savings) |

---

**🎯 This manifest is the Single Source of Truth. All AI agents, Copilots, and developers must conform to these standards.**
