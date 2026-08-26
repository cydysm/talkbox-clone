#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATABASE_URL="${DATABASE_URL:?DATABASE_URL is required}"

mkdir -p "$BACKUP_DIR"
echo "Starting backup at $(date)"
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/talkbox_${TIMESTAMP}.sql.gz"

if [ -d /app/media ] && [ -n "$(ls -A /app/media 2>/dev/null)" ]; then
    tar -czf "$BACKUP_DIR/media_${TIMESTAMP}.tar.gz" -C /app media
fi

find "$BACKUP_DIR" -name "*.gz" -mtime "+$RETENTION_DAYS" -delete
echo "Backup complete: $BACKUP_DIR/talkbox_${TIMESTAMP}.sql.gz"
