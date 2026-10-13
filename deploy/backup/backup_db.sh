#!/bin/bash
# Backs up the PostgreSQL database and MEDIA_ROOT to the attached volume at
# /mnt/backups. Run by:
#   - deploy/systemd/ifiplatform-backup.timer daily at 05:00
#   - deploy/deploy.sh right before `migrate`
# or by hand on the server:
#   bash deploy/backup/backup_db.sh
#
# Each run writes a DB dump and a media archive with the same timestamp.
# Restore them as a pair: the database only stores the media files' paths.
set -euo pipefail

ENV_FILE="/home/ubuntu/IfiPlatform/ifiplatform/.env"
MEDIA_DIR="/home/ubuntu/IfiPlatform/ifiplatform/media"

# --- Load ONLY the DB variables from .env ---
while IFS='=' read -r key value; do
  case "$key" in
    DB_NAME|DB_USER|DB_PASSWORD|DB_HOST|DB_PORT)
      export "$key=$value"
      ;;
  esac
done < <(grep -E '^(DB_NAME|DB_USER|DB_PASSWORD|DB_HOST|DB_PORT)=' "$ENV_FILE")

# --- Config ---
MOUNT="/mnt/backups"
DB_BACKUP_DIR="$MOUNT/postgres"
MEDIA_BACKUP_DIR="$MOUNT/media"
RETENTION_DAYS=14
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILENAME="${DB_NAME}_${TIMESTAMP}.dump"
MEDIA_FILENAME="media_${TIMESTAMP}.tar.gz"

mountpoint -q "$MOUNT" || { echo "$(date -Is) ERROR: $MOUNT is not mounted" >&2; exit 1; }

mkdir -p "$DB_BACKUP_DIR" "$MEDIA_BACKUP_DIR"

# --- Database: dump to temp, verify, then keep ---
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
  -Fc -f "${DB_BACKUP_DIR}/${DB_FILENAME}.tmp" "$DB_NAME"
pg_restore -l "${DB_BACKUP_DIR}/${DB_FILENAME}.tmp" > /dev/null
mv "${DB_BACKUP_DIR}/${DB_FILENAME}.tmp" "${DB_BACKUP_DIR}/${DB_FILENAME}"

# --- Media: tar to temp, verify, then keep ---
if [ -d "$MEDIA_DIR" ]; then
  tar -czf "${MEDIA_BACKUP_DIR}/${MEDIA_FILENAME}.tmp" -C "$(dirname "$MEDIA_DIR")" "$(basename "$MEDIA_DIR")"
  tar -tzf "${MEDIA_BACKUP_DIR}/${MEDIA_FILENAME}.tmp" > /dev/null
  mv "${MEDIA_BACKUP_DIR}/${MEDIA_FILENAME}.tmp" "${MEDIA_BACKUP_DIR}/${MEDIA_FILENAME}"
else
  echo "$(date -Is) WARNING: $MEDIA_DIR not found, skipping media backup" >&2
fi

# --- Delete old backups and stray temp files ---
find "$DB_BACKUP_DIR" -name "${DB_NAME}_*.dump" -mtime +"$RETENTION_DAYS" -delete
find "$MEDIA_BACKUP_DIR" -name "media_*.tar.gz" -mtime +"$RETENTION_DAYS" -delete
# Only our own folders: $MOUNT also holds lost+found, which only root can read.
find "$DB_BACKUP_DIR" "$MEDIA_BACKUP_DIR" -name "*.tmp" -mtime +1 -delete

echo "$(date -Is) Backup completed: ${DB_FILENAME}, ${MEDIA_FILENAME}"
