#!/bin/bash
# ADRION 369 - Automated SQLite Backup Script (Healer Persona)
# Trinity Perspective: Material (Safety) x Intellectual (Automation) x Essential (Continuity)

DB_PATH=${DB_PATH:-"/app/data/arbitrage.db"}
BACKUP_DIR=${BACKUP_DIR:-"/backups"}
RETENTION_DAYS=7
RETENTION_WEEKS=4
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/arbitrage_backup_${TIMESTAMP}.sqlite.gz"
ALERT_URL=${ALERT_URL:-""} # Optional Alert-Sink endpoint

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting backup of ${DB_PATH}..."

# Use SQLite .backup command for safe copy even if WAL mode is active
# Note: Requires sqlite3 binary installed in the container
if sqlite3 "${DB_PATH}" ".backup '${BACKUP_DIR}/temp_backup.sqlite'"; then
    gzip -c "${BACKUP_DIR}/temp_backup.sqlite" > "${BACKUP_FILE}"
    rm "${BACKUP_DIR}/temp_backup.sqlite"
    
    echo "[$(date)] Backup successful: ${BACKUP_FILE}"
    
    # Rotation: Remove daily backups older than 7 days
    find "${BACKUP_DIR}" -name "arbitrage_backup_*.sqlite.gz" -mtime +${RETENTION_DAYS} -exec rm {} \;
    
    # Optional logic for weekly/monthly can be added here but keeping simple 7-day rolling for now
    
else
    echo "[$(date)] ERROR: Backup failed!" >&2
    if [ -n "$ALERT_URL" ]; then
        curl -X POST -H "Content-Type: application/json" \
             -d "{\"status\": \"critical\", \"service\": \"backup-service\", \"message\": \"SQLite backup failed for ADRION 369\"}" \
             "$ALERT_URL"
    fi
    exit 1
fi
