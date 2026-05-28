# PostgreSQL Multi-Region Replication — Phase 4-1

## Streaming Replication Architecture

```
Primary (us-east-1)
  └─ WAL Streaming
      ├─ Standby-1 (us-east-1b) — Hot standby, 0 RPO
      ├─ Standby-2 (eu-west-1) — Async, ~1s RPO
      └─ Standby-3 (ap-northeast-1) — Async, ~2s RPO
```

## Configuration: Primary

```postgresql
# File: /etc/postgresql/15/main/postgresql.conf

# Replication
max_wal_senders = 10
wal_keep_size = 1GB
max_replication_slots = 10
hot_standby = on
wal_level = logical  # Must be logical for Kubernetes PVC snapshots

# Synchronous replication (n > 3f: wait for 8/12 acknowledgment)
synchronous_commit = on
synchronous_standby_names = 'standby_1,standby_2,standby_3'

# Streaming replication
wal_recycle = on
wal_buffers = 256MB
shared_buffers = 4GB
effective_cache_size = 12GB

# Archive WAG for disaster recovery
archive_mode = on
archive_command = 'gsutil -h "Cache-Control:no-cache,max-age=0" cp %p gs://aios-wal-archive/%f'
archive_timeout = 300

# Monitoring
log_replication_commands = on
log_connections = on
log_disconnections = on
```

## Configuration: Standby (Hot Standby)

```postgresql
# File: /etc/postgresql/15/main/recovery.conf

standby_mode = 'on'
primary_conninfo = 'host=primary.internal port=5432 user=replicator password=CHANGE_ME'
restore_command = 'gsutil cp gs://aios-wal-archive/%f %p'
recovery_target_timeline = 'latest'
```

## Kubernetes StatefulSet: Primary

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-primary
  namespace: aios
spec:
  serviceName: postgresql-primary
  replicas: 1
  selector:
    matchLabels:
      role: primary
      tier: data
  template:
    metadata:
      labels:
        role: primary
        tier: data
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: topology.kubernetes.io/region
                operator: In
                values:
                - us-east-1
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        - containerPort: 5433
          name: replication
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: admin-password
        - name: POSTGRES_USER
          value: aios
        - name: POSTGRES_DB
          value: aios_mvp
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: postgres-config
          mountPath: /etc/postgresql/15/main/postgresql.conf
          subPath: postgresql.conf
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U aios -d aios_mvp
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U aios -d aios_mvp
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 2
          failureThreshold: 2
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
      volumes:
      - name: postgres-config
        configMap:
          name: postgresql-config-primary
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes:
      - ReadWriteOnce
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

## Kubernetes StatefulSet: Hot Standby

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql-standby
  namespace: aios
spec:
  serviceName: postgresql-standby
  replicas: 1
  selector:
    matchLabels:
      role: standby
      tier: data
  template:
    metadata:
      labels:
        role: standby
        tier: data
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
            - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                - us-east-1b
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: role
                operator: In
                values:
                - primary
            topologyKey: kubernetes.io/hostname
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: admin-password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: postgres-recovery
          mountPath: /var/lib/postgresql/recovery.conf
          subPath: recovery.conf
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U aios
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U aios && [ -f /var/lib/postgresql/data/standby.signal ]
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 2
      volumes:
      - name: postgres-recovery
        configMap:
          name: postgresql-recovery-standby
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes:
      - ReadWriteOnce
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi
```

## Failover Script: pg_failover.sh

```bash
#!/bin/bash
# Promote standby to primary on detected primary failure

PRIMARY_POD="postgresql-primary-0"
STANDBY_POD="postgresql-standby-0"
NAMESPACE="aios"
TIMEOUT=30

check_primary_health() {
    kubectl exec -n $NAMESPACE $PRIMARY_POD -- pg_isready -U aios &>/dev/null
    return $?
}

promote_standby() {
    echo "[$(date -u +'%Y-%m-%d %H:%M:%S')] Primary failure detected. Promoting standby..."

    kubectl exec -n $NAMESPACE $STANDBY_POD -- psql -U aios -c "SELECT pg_promote();" || {
        echo "CRITICAL: Standby promotion failed!"
        exit 1
    }

    echo "Standby promoted to primary. Waiting for connections..."
    sleep 10

    # Verify new primary is accepting connections
    kubectl exec -n $NAMESPACE $STANDBY_POD -- pg_isready -U aios || {
        echo "CRITICAL: New primary not ready after promotion!"
        exit 1
    }

    echo "Primary failover complete. New primary is $STANDBY_POD"
}

wait_for_recovery() {
    local max_wait=$1
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        if check_primary_health; then
            echo "Primary recovered"
            return 0
        fi
        sleep 5
        ((elapsed += 5))
    done
    return 1
}

main() {
    echo "PostgreSQL failover monitor started"

    while true; do
        if ! check_primary_health; then
            echo "Primary health check failed"
            if ! wait_for_recovery $TIMEOUT; then
                promote_standby
            fi
        fi
        sleep 30
    done
}

main "$@"
```

## Kubernetes CronJob: Backup to Cloud Storage

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgresql-backup
  namespace: aios
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: google/cloud-sdk:alpine
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: admin-password
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_FILE="aios-backup-$(date -u +'%Y-%m-%d-%H%M%S').sql.gz"
              pg_dump -h postgresql-primary.aios.svc.cluster.local -U aios -d aios_mvp | gzip > /tmp/$BACKUP_FILE
              gsutil cp /tmp/$BACKUP_FILE gs://aios-database-backups/
              gsutil retention set 7d gs://aios-database-backups/$BACKUP_FILE || echo "Retention policy not configured"
              rm /tmp/$BACKUP_FILE
          restartPolicy: OnFailure
```

## Disaster Recovery: Point-in-Time Recovery (PITR)

```bash
#!/bin/bash
# Restore database to specific point-in-time

TARGET_TIME="2026-06-29 10:30:00"
RESTORE_POD="postgresql-restore-pitr"
NAMESPACE="aios"

# 1. Create new PostgreSQL instance from WAL archive
kubectl run $RESTORE_POD \
    --image=postgres:15-alpine \
    -n $NAMESPACE \
    --env="POSTGRES_PASSWORD=CHANGE_ME" \
    -- sleep 3600

# Wait for pod readiness
kubectl wait --for=condition=Ready pod/$RESTORE_POD -n $NAMESPACE --timeout=60s

# 2. Restore latest backup
LATEST_BACKUP=$(gsutil ls -r gs://aios-database-backups/ | tail -1)
echo "Restoring from: $LATEST_BACKUP"

kubectl exec -n $NAMESPACE $RESTORE_POD -- \
    gsutil cp $LATEST_BACKUP - | gunzip | psql -U aios -d aios_mvp

# 3. Apply WAL archive up to target time
kubectl exec -n $NAMESPACE $RESTORE_POD -- \
    sh -c 'echo "recovery_target_timeline = latest" > /var/lib/postgresql/data/recovery.conf && \
           echo "recovery_target_xid = <XID_FROM_LOGARCHIVE>" >> /var/lib/postgresql/data/recovery.conf'

# 4. Verify PITR was successful
kubectl exec -n $NAMESPACE $RESTORE_POD -- psql -U aios -c "SELECT NOW();"

echo "PITR restore complete at $TARGET_TIME"
```

## Monitoring: pgAdmin 4 Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: pgadmin
  namespace: aios
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 80
    name: http
  selector:
    app: pgadmin

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgadmin
  namespace: aios
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pgadmin
  template:
    metadata:
      labels:
        app: pgadmin
    spec:
      containers:
      - name: pgadmin
        image: dpage/pgadmin4:latest
        ports:
        - containerPort: 80
        env:
        - name: PGADMIN_DEFAULT_EMAIL
          value: "admin@aios.internal"
        - name: PGADMIN_DEFAULT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: pgadmin-password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Health Check Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Replication lag | >100ms | >1s | Page on-call |
| WAL queue depth | >50MB | >500MB | Trigger standby |
| Primary connection time | >50ms | >200ms | Alert SRE |
| Standby apply delay | >500ms | >5s | Investigate |
| Backup age | >36h | >48h | Manual backup |

---

**Status:** Ready for Phase 4-1 (Kubernetes integration)
