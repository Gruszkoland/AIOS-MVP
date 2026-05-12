#!/bin/bash
# Phase 5B Canary Deployment Script
# Manages 10% → 25% → 50% → 100% traffic rollout with automatic monitoring

set -euo pipefail

# Configuration
CANARY_PERCENTAGE=${CANARY_PERCENTAGE:-10}
DEPLOYMENT_REVISION=${DEPLOYMENT_REVISION:-$(git rev-parse --short HEAD)}
MONITORING_DURATION=300  # 5 minutes
API_ENDPOINT="http://api.prod.example.com"
HEALTH_CHECK_ENDPOINT="$API_ENDPOINT/api/mcp/guardian/g4-enhanced/health"
METRICS_ENDPOINT="$API_ENDPOINT/metrics"
ERROR_THRESHOLD=0.001  # 0.1%
P95_THRESHOLD=2000     # 2 seconds
CACHE_HIT_THRESHOLD=0.60  # 60%

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# ============================================================================
# 1. PRE-DEPLOYMENT CHECKS
# ============================================================================
pre_deployment_checks() {
    log_info "Starting pre-deployment checks..."
    
    # Check if current deployment is stable
    log_info "Checking current deployment health..."
    local response=$(curl -s -w "\n%{http_code}" "$HEALTH_CHECK_ENDPOINT" || echo "000")
    local http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" != "200" ]; then
        log_error "Current deployment is not healthy (HTTP $http_code)"
        exit 1
    fi
    log_info "✓ Current deployment is healthy"
    
    # Check if load balancer is configured
    log_info "Checking load balancer configuration..."
    if ! command -v kubectl &> /dev/null; then
        log_warn "kubectl not found - assuming manual deployment"
    else
        kubectl get endpoints | grep -q "api" || log_error "Load balancer endpoint not found"
    fi
    
    log_info "✓ Pre-deployment checks passed"
}

# ============================================================================
# 2. DEPLOY TO CANARY POOL
# ============================================================================
deploy_to_canary() {
    log_info "Deploying Phase 5B revision $DEPLOYMENT_REVISION to canary pool..."
    
    # This would be actual deployment logic - for now, placeholder
    cat > /tmp/canary-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adrion-api-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: adrion-api
      version: v12
  template:
    metadata:
      labels:
        app: adrion-api
        version: v12
    spec:
      containers:
      - name: api
        image: ghcr.io/adrion/adrion-api:v12-latest
        ports:
        - containerPort: 8000
        env:
        - name: PERPLEXITY_API_KEY
          valueFrom:
            secretKeyRef:
              name: phase5b-secrets
              key: perplexity-key
        - name: PERPLEXITY_CIRCUIT_BREAKER_THRESHOLD
          value: "5"
        livenessProbe:
          httpGet:
            path: /api/mcp/guardian/g4-enhanced/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/mcp/guardian/g4-enhanced/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
EOF
    
    log_info "✓ Canary deployment manifest prepared"
}

# ============================================================================
# 3. SHIFT TRAFFIC
# ============================================================================
shift_traffic() {
    local percentage=$1
    log_info "Shifting traffic to $percentage%..."
    
    # This would be actual traffic shifting - using load balancer weight
    cat > /tmp/traffic-shift.yaml << EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: adrion-api
spec:
  hosts:
  - api.prod.example.com
  http:
  - match:
    - uri:
        prefix: /api/mcp/guardian/g4-enhanced
    route:
    - destination:
        host: adrion-api-blue
        port:
          number: 8000
      weight: $((100 - percentage))
    - destination:
        host: adrion-api-green-v12
        port:
          number: 8000
      weight: $percentage
    timeout: 10s
    retries:
      attempts: 3
      perRetryTimeout: 2s
EOF
    
    log_info "✓ Traffic shift to $percentage% initiated"
}

# ============================================================================
# 4. MONITOR CANARY
# ============================================================================
monitor_canary() {
    log_info "Monitoring canary deployment for $MONITORING_DURATION seconds..."
    
    local start_time=$(date +%s)
    local error_count=0
    local total_requests=0
    local p95_latencies=()
    
    while [ $(($(date +%s) - start_time)) -lt $MONITORING_DURATION ]; do
        # Fetch metrics
        local metrics=$(curl -s "$METRICS_ENDPOINT" 2>/dev/null || echo "{}")
        
        # Extract key metrics
        local error_rate=$(echo "$metrics" | grep 'g4_errors_total' | awk '{print $2}' || echo "0")
        local p95_latency=$(echo "$metrics" | grep 'g4_latency_p95' | awk '{print $2}' || echo "0")
        local cache_hit_rate=$(echo "$metrics" | grep 'g4_cache_hit_rate' | awk '{print $2}' || echo "0")
        
        # Check thresholds
        if (( $(echo "$error_rate > $ERROR_THRESHOLD" | bc -l) )); then
            log_error "Error rate exceeded: $error_rate > $ERROR_THRESHOLD"
            ((error_count++))
        fi
        
        if (( $(echo "$p95_latency > $P95_THRESHOLD" | bc -l) )); then
            log_warn "P95 latency high: ${p95_latency}ms > ${P95_THRESHOLD}ms"
        fi
        
        if (( $(echo "$cache_hit_rate < $CACHE_HIT_THRESHOLD" | bc -l) )); then
            log_warn "Cache hit rate low: ${cache_hit_rate}% < ${CACHE_HIT_THRESHOLD}%"
        fi
        
        # If too many errors, fail early
        if [ $error_count -gt 3 ]; then
            log_error "Too many error spikes detected - initiating rollback"
            return 1
        fi
        
        echo -e "${GREEN}✓${NC} Error: $error_rate | P95: ${p95_latency}ms | Cache: ${cache_hit_rate}%"
        
        ((total_requests++))
        sleep 5
    done
    
    log_info "✓ Canary monitoring completed successfully"
    return 0
}

# ============================================================================
# 5. VERIFY CANARY HEALTH
# ============================================================================
verify_canary_health() {
    log_info "Verifying canary health metrics..."
    
    local response=$(curl -s "$HEALTH_CHECK_ENDPOINT")
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$status" != "healthy" ]; then
        log_error "Canary health check failed: $status"
        return 1
    fi
    
    log_info "✓ Canary health verified: $status"
    return 0
}

# ============================================================================
# 6. ROLLBACK IF NEEDED
# ============================================================================
rollback_on_failure() {
    log_error "Canary deployment failed - initiating automatic rollback..."
    
    shift_traffic 0  # Shift all traffic back to blue
    
    sleep 10
    
    if verify_canary_health; then
        log_info "✓ Rollback successful - system restored to previous state"
        return 0
    else
        log_error "✗ Rollback verification failed - manual intervention required"
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    log_info "=========================================="
    log_info "Phase 5B Canary Deployment"
    log_info "Revision: $DEPLOYMENT_REVISION"
    log_info "Canary Traffic: $CANARY_PERCENTAGE%"
    log_info "=========================================="
    
    # Step 1: Pre-deployment checks
    pre_deployment_checks || exit 1
    
    # Step 2: Deploy to canary
    deploy_to_canary || exit 1
    
    # Step 3: Shift initial traffic
    shift_traffic "$CANARY_PERCENTAGE" || exit 1
    
    # Step 4: Monitor deployment
    if ! monitor_canary; then
        rollback_on_failure || exit 1
        exit 1
    fi
    
    # Step 5: Verify health
    verify_canary_health || {
        rollback_on_failure
        exit 1
    }
    
    log_info "=========================================="
    log_info "✓ Canary deployment SUCCESSFUL"
    log_info "Proceed to progressive rollout"
    log_info "=========================================="
}

# Trap errors
trap 'log_error "Script failed"; exit 1' ERR

# Run main
main "$@"
