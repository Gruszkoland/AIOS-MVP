#!/bin/bash
BACKUP_DIR=/opt/adrion-system/backups
DATE=$(date +%Y%m%d_%H%M%S)

for DB in n8n_prod genesis_record; do
  docker exec adrion_postgres pg_dump -U adrion -Fc "$DB" > "$BACKUP_DIR/${DB}_${DATE}.dump" 2>/dev/null
  if [ $? -eq 0 ] && [ -s "$BACKUP_DIR/${DB}_${DATE}.dump" ]; then
    SIZE=$(du -sh "$BACKUP_DIR/${DB}_${DATE}.dump" | cut -f1)
    echo "[$DATE] OK: $DB -> ${DB}_${DATE}.dump ($SIZE)"
  else
    rm -f "$BACKUP_DIR/${DB}_${DATE}.dump"
    echo "[$DATE] FAIL: $DB"
  fi
done

find "$BACKUP_DIR" -name '*.dump' -mtime +7 -delete
echo "[$DATE] Total backups: $(ls $BACKUP_DIR/*.dump 2>/dev/null | wc -l)"
