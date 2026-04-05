#!/usr/bin/env bash
# ADRION 369 — PostgreSQL Backup Script
#
# Usage:
#   bash scripts/backup/backup-postgres.sh
#   BACKUP_DIR=/mnt/backups bash scripts/backup/backup-postgres.sh
#
# Environment variables (all have defaults):
#   BACKUP_DIR   — directory to store backups  (default: ./backups)
#   DB_HOST      — PostgreSQL host              (default: localhost)
#   DB_PORT      — PostgreSQL port              (default: 5432)
#   DB_USER      — database user                (default: adrion)
#   DB_NAME      — database name                (default: genesis_record)
#   PGPASSWORD   — password (or use .pgpass)   (default: adrion_pass)
#   RETENTION_DAYS — how many days to keep     (default: 7)

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-adrion}"
DB_NAME="${DB_NAME:-genesis_record}"
export PGPASSWORD="${PGPASSWORD:-adrion_pass}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "[BACKUP] Starting dump: ${DB_NAME} → ${BACKUP_FILE}"
pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --no-password \
    --format=plain \
    --clean \
    --if-exists \
    "${DB_NAME}" \
  | gzip -9 > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
echo "[BACKUP] Done. Size: ${BACKUP_SIZE} → ${BACKUP_FILE}"

# Alert if backup is suspiciously large (> 5 GB)
BACKUP_BYTES=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}")
if [ "${BACKUP_BYTES}" -gt $((5 * 1024 * 1024 * 1024)) ]; then
    echo "[BACKUP] WARNING: backup size ${BACKUP_SIZE} exceeds 5 GB threshold!" >&2
fi

# Prune old backups
echo "[BACKUP] Pruning backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "backup_${DB_NAME}_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete
REMAINING=$(ls "${BACKUP_DIR}" | grep -c "backup_${DB_NAME}_" || true)
echo "[BACKUP] ${REMAINING} backup(s) retained."
