#!/bin/bash
# PostgreSQL backup cron setup for adrion-system
set -e

BACKUP_DIR=/opt/adrion-system/backups
mkdir -p "$BACKUP_DIR"

# Create backup script
cat > /opt/adrion-system/backup_postgres.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=/opt/adrion-system/backups
DATE=$(date +%Y%m%d_%H%M%S)
PGPASSWORD=$(grep POSTGRES_PASSWORD /opt/adrion-system/.env | cut -d= -f2)

# Backup all databases
for DB in n8n_prod genesis_record; do
  docker exec adrion_postgres pg_dump -U adrion -Fc "$DB" > "$BACKUP_DIR/${DB}_${DATE}.dump" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "[$DATE] OK: $DB -> ${DB}_${DATE}.dump"
  else
    echo "[$DATE] FAIL: $DB"
  fi
done

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -delete
echo "[$DATE] Cleanup done. Current backups: $(ls $BACKUP_DIR/*.dump 2>/dev/null | wc -l)"
EOF

chmod +x /opt/adrion-system/backup_postgres.sh

# Add cron job: daily at 03:00
CRON_LINE="0 3 * * * /opt/adrion-system/backup_postgres.sh >> /opt/adrion-system/backups/backup.log 2>&1"
(crontab -l 2>/dev/null | grep -v backup_postgres; echo "$CRON_LINE") | crontab -

echo "Cron backup configured:"
crontab -l | grep backup

# Run initial backup now
echo "Running initial backup..."
bash /opt/adrion-system/backup_postgres.sh
ls -lh /opt/adrion-system/backups/*.dump 2>/dev/null || echo "No dumps yet"
