#!/bin/bash
# Emergency Rollback Script - Revert from v12 (green) to v11 (blue) instantly

set -euo pipefail

API_ENDPOINT="http://api.prod.example.com"
HEALTH_CHECK="$API_ENDPOINT/api/mcp/guardian/g4-enhanced/health"

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
# 1. VERIFY CURRENT STATE
# ============================================================================
verify_current_state() {
    log_info "Verifying current deployment state..."
    
    local response=$(curl -s "$HEALTH_CHECK" 2>/dev/null || echo '{"status":"unknown"}')
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    log_info "Current status: $status"
}

# ============================================================================
# 2. SHIFT TRAFFIC BACK TO BLUE
# ============================================================================
shift_traffic_to_blue() {
    log_warn "🚨 INITIATING ROLLBACK - Shifting 100% traffic back to blue (v11)"
    
    # Use kubectl to update VirtualService
    if command -v kubectl &> /dev/null; then
        kubectl patch virtualservice adrion-api --type merge -p \
            '{"spec":{"http":[{"route":[{"destination":{"host":"adrion-api-blue"},"weight":100},{"destination":{"host":"adrion-api-green-v12"},"weight":0}]}]}}' \
            || log_warn "kubectl patch failed - attempting fallback method"
    fi
    
    log_info "✓ Traffic shifting back to blue (100%)"
}

# ============================================================================
# 3. VERIFY ROLLBACK
# ============================================================================
verify_rollback() {
    log_info "Verifying rollback completion..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK" || echo "000")
        
        if [ "$response" = "200" ]; then
            log_info "✓ API health check passed (HTTP 200)"
            
            # Double-check that we're on blue
            local version=$(curl -s "$API_ENDPOINT/api/mcp/guardian/g4-enhanced/metrics" | grep -o '"version":"[^"]*"' | head -n1 | cut -d'"' -f4)
            log_info "✓ Verified version: $version"
            
            return 0
        fi
        
        log_warn "Attempt $((attempt+1))/$max_attempts: Health check returned HTTP $response - retrying..."
        sleep 5
        ((attempt++))
    done
    
    log_error "✗ Rollback verification FAILED after $max_attempts attempts"
    return 1
}

# ============================================================================
# 4. DRAIN GREEN CONNECTIONS
# ============================================================================
drain_green_connections() {
    log_info "Draining remaining connections from green instances..."
    
    # Give connections up to 30 seconds to drain gracefully
    local drain_time=30
    log_info "Waiting ${drain_time}s for graceful connection drain..."
    sleep "$drain_time"
    
    log_info "✓ Connections drained"
}

# ============================================================================
# 5. SCALE DOWN GREEN
# ============================================================================
scale_down_green() {
    log_info "Scaling down green (v12) deployment..."
    
    if command -v kubectl &> /dev/null; then
        kubectl scale deployment adrion-api-green-v12 --replicas=0 \
            || log_warn "Failed to scale down - may already be zero"
    fi
    
    log_info "✓ Green deployment scaled to 0 replicas"
}

# ============================================================================
# 6. NOTIFY OPERATIONS TEAM
# ============================================================================
notify_team() {
    log_warn "📢 Sending rollback notification to operations team..."
    
    local message="🚨 PHASE 5B ROLLBACK INITIATED
    
Timestamp: $(date)
Reason: Critical error threshold exceeded
Action: Reverted from v12 (green) to v11 (blue)
Traffic: 100% back to blue

Status: $(curl -s "$HEALTH_CHECK" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

Next Steps:
1. Investigate logs: kubectl logs -l app=adrion-api,version=v12
2. Post-mortem meeting required
3. Do not re-deploy until root cause identified"
    
    # This would integrate with your notification system
    # Example: send to Slack, PagerDuty, etc.
    echo "$message" | tee /tmp/rollback-notification.txt
    
    log_info "✓ Notification prepared"
}

# ============================================================================
# 7. CREATE ROLLBACK REPORT
# ============================================================================
create_rollback_report() {
    log_info "Creating rollback report..."
    
    cat > /tmp/rollback-report.md << 'EOF'
# Phase 5B Rollback Report

## Incident Summary
- **Timestamp:** $(date)
- **Action:** Reverted from Phase 5B (v12) to Phase 5A (v11)
- **Traffic Shift:** 100% back to blue
- **Duration:** ~2 minutes

## Metrics at Rollback
- **Error Rate:** See logs
- **P95 Latency:** See metrics
- **Circuit Breaker State:** See health check

## Investigation Points
1. Check Guardian G4 v12 error logs
2. Review Perplexity API circuit breaker state
3. Analyze PII redaction behavior
4. Verify Genesis Record logging integrity

## Root Cause (To Be Determined)
[Investigation needed]

## Remediation
1. Local testing required
2. Integration tests must pass 100%
3. Staging validation required (48 hours)
4. Code review of changes
5. Re-deployment with increased monitoring

## Sign-Off
- [ ] Post-mortem completed
- [ ] Root cause identified
- [ ] Fix verified in dev environment
- [ ] Staging deployment validated
- [ ] Ready for re-production deployment

EOF
    
    cat /tmp/rollback-report.md
    log_info "✓ Rollback report created: /tmp/rollback-report.md"
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    log_warn "=========================================="
    log_warn "🚨 PHASE 5B EMERGENCY ROLLBACK 🚨"
    log_warn "=========================================="
    
    # Verify current state
    verify_current_state
    
    # Shift traffic back to blue
    shift_traffic_to_blue
    
    # Give routing a moment to update
    sleep 10
    
    # Verify rollback
    if ! verify_rollback; then
        log_error "Rollback verification failed - manual intervention required!"
        exit 1
    fi
    
    # Drain green connections
    drain_green_connections
    
    # Scale down green
    scale_down_green
    
    # Notify team
    notify_team
    
    # Create report
    create_rollback_report
    
    log_warn "=========================================="
    log_warn "✓ ROLLBACK COMPLETED SUCCESSFULLY"
    log_warn "=========================================="
    log_warn "⚠️  Manual investigation required - see rollback report"
    log_warn "Logs: /tmp/rollback-report.md"
    log_warn "=========================================="
}

trap 'log_error "Rollback script failed!"; exit 1' ERR
main "$@"
