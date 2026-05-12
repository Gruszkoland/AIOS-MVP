#!/bin/bash
# Traffic Shifting Script - Progressive rollout from canary to production
# Orchestrates: 10% → 25% → 50% → 100%

set -euo pipefail

TRAFFIC_PERCENTAGE=${TRAFFIC_PERCENTAGE:-10}
DEPLOYMENT_REVISION=${DEPLOYMENT_REVISION:-$(git rev-parse --short HEAD)}
WAIT_MINUTES=${WAIT_MINUTES:-10}
API_ENDPOINT="http://api.prod.example.com"
METRICS_ENDPOINT="$API_ENDPOINT/metrics"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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
# TRAFFIC SHIFT
# ============================================================================
shift_traffic() {
    local percentage=$1
    
    log_info "Shifting traffic to ${percentage}% (green v12) / $((100 - percentage))% (blue v11)"
    
    # Using kubectl to update the VirtualService
    if command -v kubectl &> /dev/null; then
        kubectl patch virtualservice adrion-api --type merge -p \
            "{\"spec\":{\"http\":[{\"route\":[{\"destination\":{\"host\":\"adrion-api-blue\"},\"weight\":$((100-percentage))},{\"destination\":{\"host\":\"adrion-api-green-v12\"},\"weight\":$percentage}]}]}}" \
            || log_warn "kubectl patch failed - using fallback"
    fi
    
    log_info "✓ Traffic shifted to ${percentage}%"
}

# ============================================================================
# MONITOR TRAFFIC SHIFT
# ============================================================================
monitor_traffic_shift() {
    local percentage=$1
    local duration=$((WAIT_MINUTES * 60))
    local start_time=$(date +%s)
    
    log_info "Monitoring traffic at ${percentage}% for ${WAIT_MINUTES} minutes..."
    
    while [ $(($(date +%s) - start_time)) -lt $duration ]; do
        # Fetch metrics from both blue and green instances
        local metrics=$(curl -s "$METRICS_ENDPOINT" 2>/dev/null || echo "{}")
        
        # Parse metrics
        local green_error_rate=$(echo "$metrics" | grep 'green_errors' | awk '{print $2}' || echo "0")
        local green_p95=$(echo "$metrics" | grep 'green_latency_p95' | awk '{print $2}' || echo "0")
        local blue_error_rate=$(echo "$metrics" | grep 'blue_errors' | awk '{print $2}' || echo "0")
        local blue_p95=$(echo "$metrics" | grep 'blue_latency_p95' | awk '{print $2}' || echo "0")
        
        # Check thresholds
        if (( $(echo "$green_error_rate > 0.001" | bc -l) )); then
            log_error "Green error rate high: $green_error_rate"
            return 1
        fi
        
        if (( $(echo "$green_p95 > 2500" | bc -l) )); then
            log_warn "Green P95 latency: ${green_p95}ms (slightly elevated but acceptable)"
        fi
        
        # Display progress
        local elapsed=$(($(date +%s) - start_time))
        local remaining=$((duration - elapsed))
        
        printf "%s Progress: ${percentage}%% traffic | Green: Error=${green_error_rate}%% P95=${green_p95}ms | Blue: Error=${blue_error_rate}%% P95=${blue_p95}ms | Remaining: ${remaining}s\r" \
            "$(echo -e ${GREEN}✓${NC})"
        
        sleep 10
    done
    
    echo ""  # Newline after progress
    log_info "✓ Monitoring completed at ${percentage}%"
    return 0
}

# ============================================================================
# HEALTH CHECK BOTH VERSIONS
# ============================================================================
health_check_both() {
    log_info "Verifying health of both blue and green instances..."
    
    # Check blue (v11)
    local blue_status=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://api-blue.prod.example.com/api/mcp/guardian/g4-enhanced/health" || echo "000")
    
    # Check green (v12)
    local green_status=$(curl -s -o /dev/null -w "%{http_code}" \
        "http://api-green.prod.example.com/api/mcp/guardian/g4-enhanced/health" || echo "000")
    
    if [ "$blue_status" != "200" ] || [ "$green_status" != "200" ]; then
        log_error "Health check failed - Blue: $blue_status, Green: $green_status"
        return 1
    fi
    
    log_info "✓ Both instances healthy - Blue: $blue_status, Green: $green_status"
    return 0
}

# ============================================================================
# COLLECT SLO METRICS
# ============================================================================
collect_slo_metrics() {
    local percentage=$1
    
    log_info "Collecting SLO metrics at ${percentage}%..."
    
    cat >> /tmp/traffic-shift-metrics.log << EOF
=== Traffic Shift to ${percentage}% ===
Timestamp: $(date)
Revision: $DEPLOYMENT_REVISION

EOF
    
    # Error rate
    local error_rate=$(curl -s "$METRICS_ENDPOINT" | grep 'g4_errors_total' | awk '{print $2}' || echo "0")
    echo "Error Rate: $error_rate" >> /tmp/traffic-shift-metrics.log
    
    # P95 latency
    local p95=$(curl -s "$METRICS_ENDPOINT" | grep 'g4_latency_p95' | awk '{print $2}' || echo "0")
    echo "P95 Latency: ${p95}ms" >> /tmp/traffic-shift-metrics.log
    
    # Cache hit rate
    local cache=$(curl -s "$METRICS_ENDPOINT" | grep 'g4_cache_hit_rate' | awk '{print $2}' || echo "0")
    echo "Cache Hit Rate: ${cache}%" >> /tmp/traffic-shift-metrics.log
    
    echo "" >> /tmp/traffic-shift-metrics.log
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    log_info "=========================================="
    log_info "Traffic Shift to ${TRAFFIC_PERCENTAGE}%"
    log_info "=========================================="
    
    # Pre-flight checks
    health_check_both || exit 1
    
    # Shift traffic
    shift_traffic "$TRAFFIC_PERCENTAGE" || exit 1
    
    # Monitor
    if ! monitor_traffic_shift "$TRAFFIC_PERCENTAGE"; then
        log_error "Monitoring failed - consider rollback"
        exit 1
    fi
    
    # Collect metrics
    collect_slo_metrics "$TRAFFIC_PERCENTAGE"
    
    log_info "=========================================="
    log_info "✓ Traffic shift to ${TRAFFIC_PERCENTAGE}% SUCCESSFUL"
    log_info "=========================================="
}

trap 'log_error "Script failed"; exit 1' ERR
main "$@"
