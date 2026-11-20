#!/usr/bin/env bash
# Dump the database to $BACKUP_DIR (keeps the newest 14). Usage: backup.sh [label]
source "$(dirname "$0")/common.sh"
mkdir -p "$BACKUP_DIR"; chmod 700 "$BACKUP_DIR"
file="$BACKUP_DIR/$(date -u +%Y%m%dT%H%M%SZ)-${1:-manual}.dump"
dc exec -T db pg_dump -U builders_owner -d builders -Fc > "$file"
log "backup: $file ($(du -h "$file" | cut -f1))"
ls -1t "$BACKUP_DIR"/*.dump | tail -n +15 | xargs -r rm -f
echo "$file"
