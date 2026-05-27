# ADRION 369 — Disaster Recovery & Recovery Plan

## Executive Summary

**RPO (Recovery Point Objective):** 1 day (24-hour backup window)
**RTO (Recovery Time Objective):** 5 minutes (production) / 15 minutes (dev)
**DR Region:** `eu-west-1` (Ireland) — failover from primary `eu-central-1`
**Failover Mode:** Automatic (CloudWatch alarms → SNS → manual promotion)
**Backup Retention:** 7 days (dev), 30 days (prod)

---

## 1. INFRASTRUCTURE TOPOLOGY

### Primary Site (eu-central-1)
```
Primary RDS: db.t3.large (500GB, Multi-AZ)
  ├── Automatic daily snapshots (3 AM UTC)
  ├── Binary logs enabled (for logical replication)
  ├── Encryption: KMS
  └── Backup retention: 30 days
```

### Standby Site (eu-west-1)
```
Standby RDS: db.t3.large (cross-region read replica)
  ├── Read-only mode (async replication)
  ├── Replication lag monitoring: < 5 seconds
  ├── Backup vault: KMS-encrypted
  ├── SNS alerts on lag threshold
  └── Health checks: Route53 CloudWatch integration
```

### Replication Flow
```
Primary DB (eu-central-1)
  ↓ async replication (< 5s lag)
Standby DB (eu-west-1)
  ↓ automated backup
Backup Vault (eu-west-1)
  ↓ retention: 30 days
Archive (S3 Glacier — optional)
```

---

## 2. FAILOVER PROCEDURES

### Scenario A: Primary Database Failure (Unplanned)

**Detection:** CloudWatch alarm triggers (CPU spike, connection errors)

**Steps:**

1. **Alert Phase (Automatic):**
   - CloudWatch detects: CPU > 80% OR free storage < 10% OR unhealthy targets
   - SNS notification sent to `ops-team@adrion369.dev`
   - Slack alert (via Lambda webhook — optional)

2. **Assessment Phase (5-10 minutes, manual):**
   ```
   # Check standby replication lag
   aws rds describe-db-instances \
     --db-instance-identifier adrion-standby \
     --region eu-west-1 \
     --query 'DBInstances[0].StatusInfos'

   # Lag < 5s: safe to promote
   # Lag > 30s: data loss risk — escalate
   ```

3. **Promotion Phase (2-3 minutes):**
   ```bash
   # Promote standby to standalone primary
   aws rds promote-read-replica \
     --db-instance-identifier adrion-standby \
     --region eu-west-1 \
     --backup-retention-period 30

   # Update RDS endpoint in app config
   # Old: adrion-primary.c123abcd.eu-central-1.rds.amazonaws.com
   # New: adrion-standby.xxxx1234.eu-west-1.rds.amazonaws.com
   ```

4. **Application Failover (1-2 minutes):**
   ```bash
   # Update ENV variables in ECS
   aws ecs update-service \
     --cluster adrion-cluster \
     --service adrion-api \
     --region eu-west-1 \
     --force-new-deployment

   # Restart application instances
   # Monitor: /health endpoints
   ```

5. **Verification (5 minutes):**
   - App health checks: `GET /health → 200 OK`
   - DB connectivity: test queries
   - Log aggregation: check for errors
   - DNS propagation: 2-5 minutes for Route53 failover

**Total RTO: ~5-15 minutes** (depends on alerting latency)

### Scenario B: Regional Outage (All of eu-central-1 down)

**Detection:** CloudWatch alarms silent (timeout), Route53 health check fails

**Steps:**

1. **Declare disaster:** Primary region unreachable for 5+ minutes
2. **Initiate promotion:** Follow Scenario A steps 3-5
3. **Infrastructure rebuild:**
   ```bash
   # Switch Terraform to standby region
   terraform apply -var-file=environments/prod.tfvars \
     -var="aws_region=eu-west-1" \
     -var="dr_region=ap-southeast-1"  # new DR in Singapore
   ```
4. **DNS failover:** Update Route53 health check thresholds (Route53 → new primary IP)

### Scenario C: Data Corruption (Detected Post-Failover)

**Fallback to Point-in-Time:**

```bash
# Restore from snapshot (backup vault)
aws backup start-recovery-point-restore \
  --recovery-point-arn arn:aws:backup:eu-west-1:ACCOUNT:recovery-point:SNAPSHOT_ID \
  --iam-role-arn arn:aws:iam::ACCOUNT:role/adrion-backup-role

# Or manual RDS snapshot restore
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier adrion-restored \
  --db-snapshot-identifier adrion-prod-2026-05-27-03-00 \
  --region eu-west-1 \
  --enable-iam-database-authentication
```

---

## 3. MONITORING & ALERTS

### CloudWatch Metrics (Standby)

| Metric                    | Threshold | Action       |
|---------------------------|-----------|--------------|
| AuroraBinlogReplicaLag    | > 5s      | SNS → Page   |
| DatabaseConnections       | > 900     | Scale-up     |
| CPUUtilization            | > 80%     | Investigate  |
| FreeableMemory            | < 512MB   | Restart      |
| FreeStorageSpace          | < 10%     | Expand vol   |

### Replication Health Check
```bash
# Automated check (run hourly via Lambda)
select extract(epoch from (now() - pg_last_xact_replay_timestamp())) as replication_lag_seconds;
# Expected: < 5000 ms
```

### Dashboard (CloudWatch)
- **Replication Lag:** trending graph, threshold line
- **Primary CPU:** vs. Standby CPU (should track closely)
- **Backup Status:** vault integrity, latest snapshot timestamp
- **Failover Readiness:** green = ready, red = investigate

---

## 4. BACKUP STRATEGY

### Schedule
- **Frequency:** Daily at 03:00 UTC (off-peak)
- **Retention:** 30 days (prod), 7 days (dev)
- **Location:** Backup Vault (eu-west-1) + optional Glacier archive

### Backup Verification (Weekly)
```bash
# Restore to temporary instance
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier adrion-test-restore \
  --db-snapshot-identifier <latest_snapshot> \
  --region eu-west-1

# Run smoke tests
psql -h <restore-endpoint> -U postgres -d adrion -c "SELECT COUNT(*) FROM users;"

# Clean up
aws rds delete-db-instance --db-instance-identifier adrion-test-restore --skip-final-snapshot
```

### Data Retention Tiers
```
Hot (0-7 days):   On-demand snapshots, immediate restore
Warm (8-30 days): Vault copies, restore in < 5 min
Cold (31-90d):    Glacier archive, restore in 1-24 hours (optional)
```

---

## 5. RUNBOOK: COMMON OPERATIONS

### Check Standby Health
```bash
aws rds describe-db-instances \
  --db-instance-identifier adrion-standby \
  --region eu-west-1 \
  --query 'DBInstances[0].[DBInstanceStatus,MasterUsername,DBInstanceClass,AllocatedStorage]'
```

### Manually Promote Standby
```bash
aws rds promote-read-replica \
  --db-instance-identifier adrion-standby \
  --region eu-west-1 \
  --no-backup-retention-period  # Remove replica role
```

### Resync After Primary Recovery
```bash
# 1. Create new standby from recovered primary
aws rds create-db-instance-read-replica \
  --db-instance-identifier adrion-replica-new \
  --source-db-instance-identifier adrion-primary \
  --db-instance-class db.t3.large \
  --region eu-west-1

# 2. Delete old standby
aws rds delete-db-instance \
  --db-instance-identifier adrion-standby \
  --region eu-west-1 \
  --skip-final-snapshot
```

### Test RTO/RPO Quarterly
```bash
# Simulate failover (Q1, Q2, Q3, Q4)
1. Snapshot primary
2. Create test instance in eu-west-1
3. Measure: promotion time + app restart time
4. Verify: data integrity at failover point
5. Document: actual RTO/RPO vs. target
6. Clean up: destroy test instance
```

---

## 6. TERRAFORM DEPLOYMENT

### Enable DR (Production)
```bash
cd terraform

# Deploy primary + standby
terraform apply -var-file=environments/prod.tfvars

# Verify standby replication
aws rds describe-db-instances \
  --region eu-west-1 \
  --filters Name=db-instance-identifier,Values=adrion-standby
```

### Outputs
```bash
terraform output standby_endpoint  # Read-only replica endpoint
terraform output rpo_minutes       # RPO (1440 = 1 day)
terraform output rto_minutes       # RTO (5 min prod)
```

### Destroy DR (if needed)
```bash
terraform destroy -var-file=environments/prod.tfvars \
  -target=aws_db_instance.standby \
  -target=aws_backup_vault.dr_vault
```

---

## 7. COMPLIANCE & TESTING

### Annual DR Drill
- [ ] Execute full failover (non-prod first)
- [ ] Measure actual RTO/RPO
- [ ] Test data integrity
- [ ] Verify backup integrity
- [ ] Document findings
- [ ] Update runbook

### Audit Trail
- CloudTrail: all RDS API calls
- VPC Flow Logs: data transfer to standby
- RDS events: failover timestamps
- SNS logs: alert delivery
- Backup Vault logs: snapshot creation/restore

---

## 8. CONTACTS & ESCALATION

| Role              | Contact          | Trigger                          |
|-------------------|------------------|----------------------------------|
| On-Call DBA       | +48-XXX-XXX-XXX | Replication lag > 30s            |
| DevOps Lead       | slack: #oncall   | Failover initiated               |
| CISO              | ciso@...         | Data corruption suspected        |
| AWS Support       | Premium plan     | AWS infrastructure failure       |

---

## 9. KNOWN LIMITATIONS

- **Maximum Replication Lag:** 5-10 seconds (acceptable for non-financial)
- **Cross-Region Failover:** No automatic DNS update (manual or Route53 health check)
- **Downtime During Promotion:** ~2-5 minutes (connection pool drain + standby promotion)
- **Data Loss Window:** Up to 24 hours (last backup) if standby also compromised

---

## 10. POST-INCIDENT REVIEW TEMPLATE

```
Incident Date: _______________
Failure Mode: primary DB | standby lag | backup failure | other
RTO Achieved: _____ min (target: 5 min)
RPO Achieved: _____ min (target: 1440 min)

Root Cause:
_____________________________________________________________________

Corrective Actions:
1. ___________________________________________________________________
2. ___________________________________________________________________

Follow-up: _______________________________________________
```

---

**Last Updated:** 2026-05-27
**Next Review:** 2026-08-27
**DR Drill Scheduled:** Q3 2026
