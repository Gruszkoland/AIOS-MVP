#!/usr/bin/env bash
###############################################################################
# ADRION 369 — OpenRouter Fully Automated Deployment
#
# Purpose: Migrate from local Ollama to OpenRouter API
# Status: Production-ready
# Time: ~15 minutes fully automated
#
# Usage: bash scripts/deploy_openrouter.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
}

###############################################################################
# STEP 1: Input Validation
###############################################################################

log_step "STEP 1: OpenRouter API Key Input"

if [ -z "$1" ]; then
    log_info "Enter your OpenRouter API Key (sk-or-v1-...):"
    read -sp "API Key: " OPENROUTER_KEY
    echo ""
else
    OPENROUTER_KEY=$1
fi

# Validate key format
if [[ ! "$OPENROUTER_KEY" =~ ^sk-or-v1- ]]; then
    log_error "Invalid API key format. Must start with 'sk-or-v1-'"
    exit 1
fi

if [ ${#OPENROUTER_KEY} -lt 20 ]; then
    log_error "API key too short. Should be 40+ characters"
    exit 1
fi

log_success "API Key format validated"

###############################################################################
# STEP 2: Update .env File
###############################################################################

log_step "STEP 2: Update Environment Configuration"

if [ ! -f .env ]; then
    log_error ".env file not found"
    exit 1
fi

# Create backup
cp .env .env.backup.openrouter
log_success "Backup created: .env.backup.openrouter"

# Update LLM settings
sed -i.bak "s/LLM_BACKEND=.*/LLM_BACKEND=openrouter/" .env
sed -i.bak "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=$OPENROUTER_KEY|" .env
sed -i.bak "s|LLM_MODEL=.*|LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free|" .env

log_success "Updated .env:"
log_info "  LLM_BACKEND=openrouter"
log_info "  LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free"
log_info "  OPENROUTER_API_KEY=***[HIDDEN]***"

# Clean up sed backup
rm -f .env.bak

###############################################################################
# STEP 3: Python Configuration Validation
###############################################################################

log_step "STEP 3: Validate Python Configuration"

python3 << 'EOF' || {
    echo "Failed to validate config"
    exit 1
}
from arbitrage.config import LLM_BACKEND, OPENROUTER_KEY, LLM_MODEL
import sys

if LLM_BACKEND != 'openrouter':
    print(f"ERROR: LLM_BACKEND={LLM_BACKEND}, expected openrouter")
    sys.exit(1)

if not OPENROUTER_KEY:
    print("ERROR: OPENROUTER_KEY not set")
    sys.exit(1)

if 'llama-3.1-8b' not in LLM_MODEL.lower():
    print(f"WARNING: LLM_MODEL={LLM_MODEL} (expected llama-3.1-8b)")

print(f"✓ LLM_BACKEND={LLM_BACKEND}")
print(f"✓ LLM_MODEL={LLM_MODEL}")
print(f"✓ OPENROUTER_KEY set: {bool(OPENROUTER_KEY)}")
EOF

log_success "Python configuration valid"

###############################################################################
# STEP 4: Test OpenRouter API Connectivity
###############################################################################

log_step "STEP 4: Test OpenRouter API Connectivity"

log_info "Testing API endpoint..."

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $OPENROUTER_KEY" \
  https://openrouter.ai/api/v1/models)

if [ "$RESPONSE" != "200" ]; then
    log_error "OpenRouter API returned HTTP $RESPONSE"
    log_info "Possible causes:"
    log_info "  1. Invalid API key"
    log_info "  2. API key not activated yet"
    log_info "  3. Network connectivity issue"
    exit 1
fi

log_success "OpenRouter API connectivity confirmed"

###############################################################################
# STEP 5: Build Docker Image
###############################################################################

log_step "STEP 5: Build Docker Image"

log_info "Building adrion-api image (this may take 2-3 minutes)..."

if ! docker-compose -f docker-compose.cloud.yml build --no-cache adrion-api 2>&1 | tee /tmp/docker_build.log; then
    log_error "Docker build failed"
    log_info "Last 20 lines of build log:"
    tail -20 /tmp/docker_build.log
    exit 1
fi

if grep -q "Step .* : FROM" /tmp/docker_build.log; then
    log_success "Docker image built successfully"
else
    log_error "Docker build may have failed"
    exit 1
fi

###############################################################################
# STEP 6: Start Docker Service
###############################################################################

log_step "STEP 6: Start Docker Service"

log_info "Starting adrion-api container..."
docker-compose -f docker-compose.cloud.yml up -d adrion-api

log_success "Container started (ID: $(docker-compose -f docker-compose.cloud.yml ps -q adrion-api))"

###############################################################################
# STEP 7: Health Check
###############################################################################

log_step "STEP 7: Wait for Service Health Check"

MAX_ATTEMPTS=30
ATTEMPT=0

log_info "Waiting for service to be ready (max 30 seconds)..."

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker-compose -f docker-compose.cloud.yml exec -T adrion-api \
        curl -s -f http://localhost:8001/api/arbitrage/status > /dev/null 2>&1; then
        log_success "Service is healthy and responding"
        break
    fi

    ATTEMPT=$((ATTEMPT + 1))

    if [ $((ATTEMPT % 5)) -eq 0 ]; then
        log_info "Still waiting... ($(($MAX_ATTEMPTS - $ATTEMPT))s remaining)"
    fi

    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    log_error "Service health check timeout"
    log_info "Recent logs:"
    docker-compose -f docker-compose.cloud.yml logs --tail 10 adrion-api
    exit 1
fi

###############################################################################
# STEP 8: Test API Endpoint
###############################################################################

log_step "STEP 8: Test API Endpoint"

log_info "Testing /api/arbitrage/analyze endpoint..."

TEST_REQUEST='{
    "job_title": "Content Writing",
    "budget_usd": 200,
    "description": "Write blog posts about technology trends"
}'

RESPONSE=$(curl -s -X POST http://localhost:8001/api/arbitrage/analyze \
    -H "Content-Type: application/json" \
    -d "$TEST_REQUEST")

if echo "$RESPONSE" | grep -q '"score"'; then
    log_success "API endpoint responding correctly"
    log_info "Sample response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    log_error "API returned unexpected response:"
    echo "$RESPONSE"
    exit 1
fi

###############################################################################
# STEP 9: Performance Metrics
###############################################################################

log_step "STEP 9: Gather Performance Metrics"

log_info "Testing latency..."

# Using curl's -w flag to get timing
START_TIME=$(date +%s%N)

curl -s -X POST http://localhost:8001/api/arbitrage/analyze \
    -H "Content-Type: application/json" \
    -d "$TEST_REQUEST" > /dev/null

END_TIME=$(date +%s%N)
LATENCY_MS=$(( (END_TIME - START_TIME) / 1000000 ))

log_success "API Response Time: ${LATENCY_MS}ms"

# Get container stats
CONTAINER_ID=$(docker-compose -f docker-compose.cloud.yml ps -q adrion-api)
STATS=$(docker stats --no-stream $CONTAINER_ID)

log_success "Container Resource Usage:"
echo "$STATS" | tail -1 | awk '{print "  Memory: " $6 " | CPU: " $3}'

###############################################################################
# STEP 10: Summary and Next Steps
###############################################################################

log_step "✅ DEPLOYMENT COMPLETE"

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  🚀 OpenRouter Migration Successful!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo "  • Backend: OpenRouter API"
echo "  • Model: Llama 3.1 8B (OpenRouter Free)"
echo "  • Status: ✅ Running"
echo "  • Latency: ${LATENCY_MS}ms"
echo "  • Health: ✅ Healthy"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo "  1. Monitor logs:"
echo "     docker-compose logs -f adrion-api"
echo ""
echo "  2. Test arbitrage analysis:"
echo "     curl -X POST http://localhost:8001/api/arbitrage/analyze \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"job_title\": \"Test\", \"budget_usd\": 500, \"description\": \"\"}'"
echo ""
echo "  3. Check OpenRouter usage:"
echo "     https://openrouter.ai/usage"
echo ""
echo "  4. View resource consumption:"
echo "     docker stats"
echo ""
echo -e "${YELLOW}⚠️  Important:${NC}"
echo "  • Free tier: ~20-50 requests/minute"
echo "  • Keep API key secure (in .env only)"
echo "  • Backup .env.backup.openrouter in case rollback needed"
echo ""
echo -e "${BLUE}🔄 Rollback (if needed):${NC}"
echo "  1. Restore .env: cp .env.backup.openrouter .env"
echo "  2. Change LLM_BACKEND=ollama"
echo "  3. Restart: docker-compose restart adrion-api"
echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""

# Log to Genesis Record
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
GENESIS_LOG="Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/openrouter_deployment_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$(dirname "$GENESIS_LOG")"

cat > "$GENESIS_LOG" << GENEOF
TIMESTAMP: $TIMESTAMP
STATUS: SUCCESS
OPERATION: OpenRouter Deployment
LATENCY_MS: $LATENCY_MS
BACKEND: openrouter
MODEL: meta-llama/llama-3.1-8b-instruct:free
HEALTH_CHECK: PASS
API_TEST: PASS
CONTAINER_ID: $CONTAINER_ID
GENEOF

log_success "Deployment logged to Genesis Record"

exit 0
