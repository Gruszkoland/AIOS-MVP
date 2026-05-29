# AIOS v1.0 — Operational Runbooks

**Last Updated:** 2026-06-29  
**Audience:** On-call engineers, SREs, incident commanders

---

## 🚨 CRITICAL RUNBOOKS

### RUNBOOK 1: PostgreSQL Primary Failover

**Severity:** CRITICAL | **RTO:** <5s | **RPO:** 0 bytes

**Symptoms:**
- Prometheus alert: `ConfirmedByzantineAgent` or `QuorumDrop`
- Grafana dashboard shows "Replication lag: CRITICAL"
- Logs show: `pg_isready -U aios: ERROR: role "aios" does not exist`

**Immediate Actions (< 5 minutes):**

1. **Verify problem:**
   ```bash
   kubectl exec -n aios postgresql-primary-0 -- pg_isready -U aios
   # Expected: accepting connections
   # If error: proceed to step 2
   ```

2. **Check standby health:**
   ```bash
   kubectl exec -n aios postgresql-standby-0 -- pg_isready -U aios
   # Must return: accepting connections
   ```

3. **Trigger automatic failover:**
   ```bash
   # pg_failover.sh runs automatically every 30s
   # Wait 30 seconds for automated detection + promotion
   kubectl get pods -n aios -l app=postgresql -w
   # Watch for: postgresql-standby-0 restarting → ready
   ```

4. **Verify new primary:**
   ```bash
   # After promotion, old standby becomes new primary
   kubectl exec -n aios postgresql-standby-0 -- \
     psql -U aios -d aios_mvp -c "SELECT version();"
   # Should return: PostgreSQL 15.x
   ```

**Validation (< 30 seconds after failover):**

```bash
# Confirm all agents can connect to new primary
kubectl exec -n aios deployment/aios-agents-0 -- \
  psql -h postgresql-standby-0.postgresql-standby.aios.svc.cluster.local \
       -U aios -d aios_mvp -c "SELECT 1;"
# Expected: 1 row

# Check replication lag (should be 0)
kubectl exec -n aios postgresql-standby-0 -- \
  psql -U aios -d aios_mvp -c "SELECT now() - pg_last_wal_receive_lsn() < '0'::interval;"
# Expected: t (true)
```

**Post-Failover Recovery (< 5 minutes):**

1. **Restart original primary (now standby):**
   ```bash
   kubectl delete pod postgresql-primary-0 -n aios
   # Pod automatically recreates and connects as standby
   kubectl get pod -n aios -l role=primary -w
   ```

2. **Verify replication restored:**
   ```bash
   sleep 60
   kubectl exec -n aios postgresql-standby-0 -- \
     psql -U aios -c "SELECT slot_name, active FROM pg_replication_slots;"
   # Expected: 2 active slots (standby_1, standby_2)
   ```

3. **Monitor replication lag:**
   ```bash
   # Check every 10s for 2 minutes
   for i in {1..12}; do
     kubectl exec -n aios postgresql-standby-0 -- \
       psql -U aios -t -c "SELECT EXTRACT(EPOCH FROM now() - pg_last_wal_receive_lsn()*'0'::interval) AS lag_sec;"
     sleep 10
   done
   # Lag should decrease toward 0
   ```

**Rollback (if needed):**

```bash
# Demote standby back to original primary (manual process)
kubectl exec -n aios postgresql-primary-0 -- \
  psql -U postgres -c "SELECT pg_ctl('promote', 'fast');"
# This is NOT recommended unless data corruption detected
# Instead: plan full recovery in staging first
```

**Escalation:**
- If failover takes >30s: Page on-call manager
- If replication won't restore: Contact database team + prepare PITR restore

---

### RUNBOOK 2: Byzantine Agent Detection & Isolation

**Severity:** CRITICAL | **RTO:** <2 min | **Response:** Isolate + Investigate

**Symptoms:**
- Prometheus alert: `ByzantineAgentDetected`
- Grafana Byzantine Agents gauge > 0
- Consensus rounds show anomalous voting patterns
- Decision latency P99 > 1ms suddenly

**Immediate Actions (< 2 minutes):**

1. **Identify suspect agent:**
   ```bash
   # Check Prometheus for highest Byzantine score
   curl -s http://prometheus:9090/api/v1/query?query=byzantine_agent_suspected_total | jq
   # Look for: agent-X with highest count
   ```

2. **Isolate suspect pod:**
   ```bash
   # DO NOT DELETE YET — we need logs for forensics
   # Drain pod from service by marking not-ready
   kubectl exec -n aios deployment/aios-agents -- \
     touch /tmp/not_ready_marker  # Custom readiness probe checks this
   # Or use kubectl set env to disable agent:
   kubectl set env deployment/aios-agents AGENT_ENABLED=false -c agent-1
   ```

3. **Verify quorum maintained:**
   ```bash
   # Count remaining healthy agents
   kubectl get pods -n aios -l app=aios-agents \
     --field-selector=status.phase=Running | wc -l
   # Must be >= 8/12 (for Byzantine n > 3f)
   # If < 8: immediately escalate
   ```

**Investigation (during isolation):**

```bash
# Get agent logs from last 5 minutes
kubectl logs -n aios deployment/aios-agents -c agent-1 --tail=1000 > agent-1-logs.txt

# Look for:
# - Duplicate decisions with different timestamps
# - Consensus votes contradicting previous messages
# - Cryptographic signature failures
# - Network partition symptoms (clock skew > 5s)

# Export metrics for analysis
curl -s http://prometheus:9090/api/v1/query_range \
  ?query=byzantine_agent_suspected_total{agent="agent-1"} \
  &start=<5min-ago>&step=10s | jq > byzantine-timeline.json
```

**Containment Decision:**

```bash
# If investigation shows hardware failure (logs clean, network OK):
# → Restart the agent
kubectl delete pod aios-agents-<pod-id> -n aios

# If investigation shows Byzantine behavior (duplicate voting, signature failures):
# → PERMANENT ISOLATION: scale deployment down
kubectl scale deployment aios-agents --replicas=11 -n aios
# Update PDB: min_available = 8/11 = 8 (still meets n > 3f)
kubectl patch pdb aios-pdb -p '{"spec":{"minAvailable":"8"}}'
```

**Post-Incident:**

```bash
# Create incident ticket
echo "Byzantine Agent Investigation: agent-1" > incident-$(date +%s).md
echo "- Start: $(date -u +'%Y-%m-%d %H:%M:%S') UTC" >> incident-*.md
echo "- Detection: Prometheus alert Byzantine_AgentDetected" >> incident-*.md
echo "- Decision: Permanent isolation (scale to 11 agents)" >> incident-*.md
echo "- RCA: See agent-1-logs.txt" >> incident-*.md

# Escalate if 2+ Byzantine agents detected simultaneously
if [ $(kubectl get pods -n aios -o json | jq '[.items[] | select(.metadata.labels.byzantine=="true")] | length') -ge 2 ]; then
  echo "CRITICAL: Multiple Byzantine agents. Page security team."
fi
```

**Escalation:**
- If < 8 agents remain healthy: Page on-call director (quorum threatened)
- If 2+ Byzantine agents: Page security + database team (potential attack)
- If Byzantine logs show network partition: Page network operations

---

### RUNBOOK 3: Quorum Loss — Emergency Recovery

**Severity:** CRITICAL | **RTO:** <15 min | **Response:** Restore or Degrade

**Symptoms:**
- Prometheus alert: `QuorumBelowMinimum` (n ≤ 3f, i.e., <8 agents)
- Consensus halted: no new rounds for >5 minutes
- Decisions cannot be committed

**Immediate Actions (< 5 minutes):**

1. **Count healthy agents:**
   ```bash
   kubectl get pods -n aios -l app=aios-agents \
     --field-selector=status.phase=Running,metadata.deletionTimestamp='' | wc -l
   # If < 8: QUORUM LOST
   ```

2. **Check node health:**
   ```bash
   # Are nodes down?
   kubectl get nodes
   # Should show all nodes Ready
   
   # If nodes NotReady: drain & evacuate
   kubectl drain <node-name> --ignore-daemonsets --force
   ```

3. **Restart crashed pods:**
   ```bash
   # Find pending/failed pods
   kubectl get pods -n aios -l app=aios-agents \
     --field-selector=status.phase=Failed,status.phase=Pending
   
   # Force restart
   kubectl delete pod <pod-name> -n aios
   
   # Scale up if replicas insufficient
   kubectl scale deployment aios-agents --replicas=12 -n aios
   ```

**Verification (after pod restart):**

```bash
# Wait for all pods ready (up to 60s)
kubectl wait --for=condition=ready pod -l app=aios-agents -n aios --timeout=60s

# Count again
HEALTHY=$(kubectl get pods -n aios -l app=aios-agents \
  --field-selector=status.phase=Running | wc -l)

if [ $HEALTHY -ge 8 ]; then
  echo "✅ Quorum restored ($HEALTHY agents)"
else
  echo "❌ Quorum still lost ($HEALTHY agents)"
  # Proceed to degraded mode
fi
```

**Degraded Mode (if quorum cannot be restored):**

```bash
# Switch to single-leader mode (no Byzantine consensus)
kubectl set env deployment/aios-agents \
  CONSENSUS_MODE=single-leader \
  FAILURE_TOLERANCE=0

# Log degraded status
echo "[$(date -u)] Degraded mode activated: $HEALTHY agents, quorum lost" >> /var/log/aios-degraded.log

# Notify stakeholders
# - Slack: #aios-incidents "Degraded mode: quorum lost, single-leader only"
# - PagerDuty: Create incident "AIOS Quorum Loss - Degraded Mode Active"
```

**Recovery to Full Consensus:**

```bash
# Once additional agents available (from other nodes or scaled):
kubectl scale deployment aios-agents --replicas=12 -n aios
kubectl wait --for=condition=ready pod -l app=aios-agents -n aios --timeout=120s

# Switch back to Byzantine consensus
kubectl set env deployment/aios-agents \
  CONSENSUS_MODE=byzantine-pbft \
  FAILURE_TOLERANCE=3

# Monitor
kubectl logs -f deployment/aios-agents -c aios | grep "Consensus mode"
```

**Escalation:**
- If quorum cannot be restored within 5 min: Page director
- If degraded mode active for >1 hour: Page VP of Operations
- If data loss suspected: Contact database team + prepare legal notification

---

## 🔧 MAINTENANCE RUNBOOKS

### RUNBOOK 4: Controlled Pod Restart (Maintenance)

**RTO:** <2 min per pod | **Downtime Impact:** None (traffic rerouted)

**Prerequisites:**
- Check Pod Disruption Budget: `kubectl get pdb -n aios`
- Minimum available must be >= 8 for 12-pod cluster
- Current healthy pods: `kubectl get pods -n aios --field-selector=status.phase=Running | wc -l`

**Procedure:**

```bash
# 1. Verify maintenance is allowed
HEALTHY=$(kubectl get pods -n aios --field-selector=status.phase=Running | wc -l)
MIN_REQUIRED=8
if [ $HEALTHY -le $MIN_REQUIRED ]; then
  echo "Cannot disrupt: only $HEALTHY healthy pods (need > $MIN_REQUIRED)"
  exit 1
fi

# 2. Delete one pod (Kubernetes recreates with latest config)
kubectl delete pod aios-agents-<pod-id> -n aios

# 3. Watch pod restart
kubectl get pod aios-agents-<pod-id> -w -n aios
# Status should progress: Pending → ContainerCreating → Running

# 4. Wait for readiness
kubectl wait --for=condition=ready pod aios-agents-<pod-id> -n aios --timeout=60s

# 5. Verify this pod caught up with consensus
# (Check logs for "Synced to latest view" message)
kubectl logs aios-agents-<pod-id> -n aios | tail -20

# 6. Repeat for next pod (wait 30s between restarts)
sleep 30
```

**Rolling Update (all pods):**

```bash
# Automatic rolling update via deployment
kubectl set image deployment/aios-agents \
  aios-agents=gcr.io/aios/aios-agents:v1.0.1 -n aios

# Watch progress
kubectl rollout status deployment/aios-agents -n aios --timeout=5m

# Verify all pods running new version
kubectl get pods -n aios -l app=aios-agents -o wide
```

---

### RUNBOOK 5: Database Backup & Restore

**Full Backup to GCS:**

```bash
# Manual backup (outside CronJob)
POD="postgresql-primary-0"
NAMESPACE="aios"
BACKUP_FILE="aios-backup-$(date -u +'%Y-%m-%d-%H%M%S').sql.gz"

kubectl exec -n $NAMESPACE $POD -- \
  pg_dump -U aios -d aios_mvp | gzip > /tmp/$BACKUP_FILE

gsutil cp /tmp/$BACKUP_FILE gs://aios-database-backups/

# Verify upload
gsutil ls gs://aios-database-backups/ | tail -1
```

**Point-in-Time Recovery (PITR):**

```bash
# Find target time
TARGET_TIME="2026-06-29 10:30:00"

# Create restore pod
kubectl run postgresql-restore-pitr \
  --image=postgres:15-alpine \
  -n aios \
  -- sleep 3600

# Wait for ready
kubectl wait --for=condition=ready pod/postgresql-restore-pitr -n aios --timeout=30s

# Restore from latest backup
LATEST=$(gsutil ls gs://aios-database-backups/ | tail -1)
kubectl exec postgresql-restore-pitr -n aios -- \
  sh -c "gsutil cp $LATEST - | gunzip | psql -U aios -d aios_mvp"

# Verify
kubectl exec postgresql-restore-pitr -n aios -- \
  psql -U aios -d aios_mvp -c "SELECT MAX(created_at) FROM decisions;"
```

---

## 📞 INCIDENT RESPONSE TEMPLATE

**Use this template for all incidents:**

```markdown
# Incident Report

**Date:** 2026-06-29  
**Severity:** [CRITICAL | HIGH | MEDIUM | LOW]  
**Status:** [INVESTIGATING | MITIGATED | RESOLVED]  

## Timeline

| Time (UTC) | Event |
|-----------|-------|
| 14:32 | Alert triggered: [alert name] |
| 14:33 | On-call engineer engaged |
| 14:35 | Root cause identified: [cause] |
| 14:40 | Mitigation applied: [action] |
| 14:45 | Service restored |

## Root Cause

[Detailed explanation of what went wrong]

## Impact

- **Affected Users:** [number]
- **Duration:** [minutes]
- **Data Loss:** [yes/no + details]
- **Financial Impact:** [estimate]

## Resolution

[Steps taken to fix the issue]

## Prevention

[Changes to prevent recurrence]

## Follow-ups

- [ ] Implement prevention measure
- [ ] Update runbook
- [ ] Post-incident review: [date]
- [ ] Training completed: [date]
```

---

**Last Update:** 2026-06-29 UTC  
**Next Review:** 2026-07-29
