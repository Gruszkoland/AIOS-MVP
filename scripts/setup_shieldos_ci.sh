#!/usr/bin/env bash
# ShieldOS CI Setup Script — ADRION 369
# Headless setup for GitHub Actions (Ubuntu latest).
# No interactive prompts. No sudo. Ephemeral containers via Docker.
#
# Usage:
#   bash scripts/setup_shieldos_ci.sh
#
# Environment variables expected (set by GitHub Actions or caller):
#   DATABASE_URL, DB_ENGINE, POSTGRES_*, ENVIRONMENT,
#   UAP_API_KEY, JWT_SECRET, DRM_HMAC_SECRET, LOG_LEVEL

set -euo pipefail

# ── Globals ───────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/logs"
REPORT_FILE="${REPORT_DIR}/ci_setup_report_$(date -u +%Y%m%d_%H%M%S).json"
CI_PG_NAME="adrion-ci-postgres-$$"
CI_REDIS_NAME="adrion-ci-redis-$$"

# Step result tracker (associative array)
declare -A STEP_STATUS=()
OVERALL_OK=true
START_TIME=$(date +%s)

mkdir -p "${REPORT_DIR}"

# ── Logging helpers ───────────────────────────────────────────────────────────

log()   { echo "[$(date -u +%H:%M:%S)] [INFO]  $*"; }
warn()  { echo "[$(date -u +%H:%M:%S)] [WARN]  $*" >&2; }
error() { echo "[$(date -u +%H:%M:%S)] [ERROR] $*" >&2; }

step_ok()   { STEP_STATUS["$1"]="ok";   log  "  OK   $1${2:+ — $2}"; }
step_fail() { STEP_STATUS["$1"]="fail"; error "  FAIL $1 — $2"; OVERALL_OK=false; }
step_skip() { STEP_STATUS["$1"]="skip"; log  "  SKIP $1${2:+ — $2}"; }
step_warn() { STEP_STATUS["$1"]="warn"; warn "  WARN $1${2:+ — $2}"; }

# ── Cleanup on exit ───────────────────────────────────────────────────────────

cleanup() {
    local exit_code=$?
    log "Cleaning up ephemeral containers..."
    docker rm -f "${CI_PG_NAME}"    >/dev/null 2>&1 || true
    docker rm -f "${CI_REDIS_NAME}" >/dev/null 2>&1 || true
    exit "${exit_code}"
}
trap cleanup EXIT

# ── Phase 1: Validate prerequisites ──────────────────────────────────────────

log "=== Phase 1: Prerequisites ==="

# Python 3.11+
if python3 -c "import sys; assert sys.version_info >= (3, 11), f'Need 3.11+, got {sys.version}'" 2>/dev/null; then
    step_ok "python" "$(python3 --version)"
else
    step_fail "python" "Python 3.11+ required"
    exit 1
fi

# pip available
if python3 -m pip --version >/dev/null 2>&1; then
    step_ok "pip" "$(python3 -m pip --version | cut -d' ' -f1-2)"
else
    step_fail "pip" "pip not available"
    exit 1
fi

# Docker daemon
if docker info >/dev/null 2>&1; then
    step_ok "docker" "$(docker --version | head -1)"
else
    step_fail "docker" "Docker daemon not accessible"
    exit 1
fi

# Go (optional — warn only)
if command -v go >/dev/null 2>&1; then
    GO_VER="$(go version | awk '{print $3}')"
    step_ok "go" "${GO_VER}"
    HAS_GO=true
else
    step_warn "go" "go not found — Go tests will be skipped"
    HAS_GO=false
fi

# ── Phase 2: Install Python dependencies ─────────────────────────────────────

log "=== Phase 2: Python dependencies ==="

cd "${PROJECT_ROOT}"

python3 -m pip install --upgrade pip --quiet

if [ -f "requirements-arbitrage.txt" ]; then
    python3 -m pip install -r requirements-arbitrage.txt --quiet && \
        step_ok "pip_arbitrage" || step_fail "pip_arbitrage" "Failed to install requirements-arbitrage.txt"
else
    step_skip "pip_arbitrage" "requirements-arbitrage.txt not found"
fi

# Dev dependencies (pytest, coverage, hypothesis)
if [ -f "requirements-dev.txt" ]; then
    python3 -m pip install -r requirements-dev.txt --quiet && \
        step_ok "pip_dev" || step_warn "pip_dev" "requirements-dev.txt install failed (non-critical)"
else
    python3 -m pip install pytest pytest-cov pytest-timeout --quiet && \
        step_ok "pip_dev" "Installed pytest + pytest-cov + pytest-timeout" || \
        step_warn "pip_dev" "Could not install dev dependencies"
fi

# ── Phase 3: Ephemeral CI infrastructure ─────────────────────────────────────

log "=== Phase 3: Ephemeral CI infrastructure ==="

# Determine if GitHub Actions already provides postgres service
if [ -n "${DATABASE_URL:-}" ] && echo "${DATABASE_URL}" | grep -q "localhost:5432"; then
    log "Using GitHub Actions postgres service (DATABASE_URL already set)"
    step_ok "ci_postgres" "Using GitHub Actions service"
    step_ok "ci_redis" "Using GitHub Actions service (port 6379)"
else
    # Launch ephemeral PostgreSQL
    log "Starting ephemeral PostgreSQL (${CI_PG_NAME})..."
    docker run -d \
        --name "${CI_PG_NAME}" \
        --env POSTGRES_DB=genesis_record_test \
        --env POSTGRES_USER=adrion \
        --env POSTGRES_PASSWORD=ci_test_password \
        --publish 5433:5432 \
        --health-cmd="pg_isready -U adrion" \
        --health-interval=3s \
        --health-timeout=3s \
        --health-retries=15 \
        postgres:15-alpine >/dev/null

    # Wait for readiness (max 45s)
    WAIT_START=$(date +%s)
    until docker exec "${CI_PG_NAME}" pg_isready -U adrion >/dev/null 2>&1; do
        if [ $(( $(date +%s) - WAIT_START )) -gt 45 ]; then
            step_fail "ci_postgres" "Timeout waiting for PostgreSQL readiness"
            exit 1
        fi
        sleep 2
    done
    step_ok "ci_postgres" "Ephemeral PostgreSQL on port 5433"

    # Export connection vars for ephemeral PG
    export DATABASE_URL="postgresql://adrion:ci_test_password@localhost:5433/genesis_record_test"
    export POSTGRES_HOST="localhost"
    export POSTGRES_PORT="5433"
    export POSTGRES_USER="adrion"
    export POSTGRES_PASSWORD="ci_test_password"
    export POSTGRES_DB="genesis_record_test"

    # Launch ephemeral Redis
    log "Starting ephemeral Redis (${CI_REDIS_NAME})..."
    docker run -d \
        --name "${CI_REDIS_NAME}" \
        --publish 6380:6379 \
        redis:7-alpine >/dev/null 2>&1
    step_ok "ci_redis" "Ephemeral Redis on port 6380"
fi

# ── Phase 4: Environment configuration ───────────────────────────────────────

log "=== Phase 4: Environment configuration ==="

# Apply CI-safe defaults for any unset variables
export DB_ENGINE="${DB_ENGINE:-postgresql}"
export ENVIRONMENT="${ENVIRONMENT:-test}"
export DEBUG_MODE="${DEBUG_MODE:-false}"
export LOG_LEVEL="${LOG_LEVEL:-WARNING}"
export UAP_API_KEY="${UAP_API_KEY:-ci-placeholder-api-key-change-in-prod}"
export JWT_SECRET="${JWT_SECRET:-ci-placeholder-jwt-secret-change-in-prod}"
export DRM_HMAC_SECRET="${DRM_HMAC_SECRET:-ci-placeholder-drm-secret-change-in-pr}"

step_ok "env_setup" "ENVIRONMENT=${ENVIRONMENT} DB_ENGINE=${DB_ENGINE}"

# ── Phase 5: Python tests ─────────────────────────────────────────────────────

log "=== Phase 5: Python tests ==="

PYTEST_EXIT=0
python3 -m pytest tests/ \
    --tb=short \
    --timeout=60 \
    --no-header \
    -q \
    2>&1 | tee "${REPORT_DIR}/pytest_main.txt" || PYTEST_EXIT=$?

if [ "${PYTEST_EXIT}" -eq 0 ]; then
    step_ok "pytest_main"
elif [ "${PYTEST_EXIT}" -eq 5 ]; then
    step_skip "pytest_main" "No tests collected (exit 5)"
else
    step_fail "pytest_main" "Tests failed (exit ${PYTEST_EXIT}) — see logs/pytest_main.txt"
fi

# UAP tests (separate test suite)
if [ -d "uap/tests" ]; then
    UAP_EXIT=0
    python3 -m pytest uap/tests/ \
        --tb=short \
        --timeout=60 \
        --no-header \
        -q \
        2>&1 | tee "${REPORT_DIR}/pytest_uap.txt" || UAP_EXIT=$?
    if [ "${UAP_EXIT}" -eq 0 ]; then
        step_ok "pytest_uap"
    elif [ "${UAP_EXIT}" -eq 5 ]; then
        step_skip "pytest_uap" "No UAP tests collected"
    else
        step_fail "pytest_uap" "UAP tests failed (exit ${UAP_EXIT})"
    fi
else
    step_skip "pytest_uap" "uap/tests directory not found"
fi

# ── Phase 6: Go tests ────────────────────────────────────────────────────────

log "=== Phase 6: Go tests ==="

if [ "${HAS_GO}" = "true" ] && [ -f "go.mod" ]; then
    GO_EXIT=0
    go test ./... -timeout 120s -count=1 2>&1 | tee "${REPORT_DIR}/go_test.txt" || GO_EXIT=$?
    if [ "${GO_EXIT}" -eq 0 ]; then
        step_ok "go_tests"
    else
        step_fail "go_tests" "Go tests failed (exit ${GO_EXIT}) — see logs/go_test.txt"
    fi
else
    step_skip "go_tests" "Go not available or go.mod not found"
fi

# ── Phase 7: Hermetic verification ───────────────────────────────────────────

log "=== Phase 7: Hermetic verification ==="

if [ -f "scripts/verify_shieldos_hermetic.py" ]; then
    HERMETIC_EXIT=0
    python3 scripts/verify_shieldos_hermetic.py --json \
        > "${REPORT_DIR}/hermetic_report.json" 2>&1 || HERMETIC_EXIT=$?

    if [ "${HERMETIC_EXIT}" -eq 0 ]; then
        HERMETIC_SCORE=$(python3 -c "
import json, sys
try:
    with open('${REPORT_DIR}/hermetic_report.json') as f:
        r = json.load(f)
    print(r.get('hermetic_score', 0))
except Exception:
    print(0)
")
        if [ "${HERMETIC_SCORE:-0}" -ge 70 ]; then
            step_ok "hermetic_check" "Score ${HERMETIC_SCORE}/100"
        else
            step_warn "hermetic_check" "Score ${HERMETIC_SCORE}/100 below recommended threshold (70)"
        fi
    else
        step_warn "hermetic_check" "Hermetic verification script failed"
    fi
else
    step_skip "hermetic_check" "scripts/verify_shieldos_hermetic.py not found"
fi

# ── Phase 8: Generate report ─────────────────────────────────────────────────

log "=== Phase 8: Generating CI report ==="

END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))

# Collect step results as JSON
STEPS_JSON="{"
FIRST=1
for key in "${!STEP_STATUS[@]}"; do
    [ "${FIRST}" -eq 1 ] || STEPS_JSON+=","
    STEPS_JSON+="\"${key}\":\"${STEP_STATUS[$key]}\""
    FIRST=0
done
STEPS_JSON+="}"

cat > "${REPORT_FILE}" <<EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "duration_seconds": ${DURATION},
  "environment": "${ENVIRONMENT:-unknown}",
  "platform": "$(uname -s)-$(uname -m)",
  "python_version": "$(python3 --version 2>&1)",
  "go_version": "$(go version 2>/dev/null | head -1 || echo 'not available')",
  "overall_success": ${OVERALL_OK},
  "steps": ${STEPS_JSON}
}
EOF

log "Report: ${REPORT_FILE}"
log "Duration: ${DURATION}s"

# ── Exit decision ─────────────────────────────────────────────────────────────

CRITICAL_STEPS=("python" "docker" "env_setup")
for step in "${CRITICAL_STEPS[@]}"; do
    if [ "${STEP_STATUS[$step]:-unknown}" = "fail" ]; then
        error "Critical step '${step}' failed — CI setup FAILED"
        exit 1
    fi
done

# pytest_main failure is a hard failure
if [ "${STEP_STATUS[pytest_main]:-unknown}" = "fail" ]; then
    error "Python tests failed — CI setup FAILED"
    exit 1
fi

log "CI setup COMPLETE (${DURATION}s)"
exit 0
