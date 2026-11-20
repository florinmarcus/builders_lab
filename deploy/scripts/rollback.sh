#!/usr/bin/env bash
# Go back to the previous version (code only; the database stays as it is).
# For a database restore too: backup.sh lists files in /opt/builders-lab/backups; see deploy/README.md.
source "$(dirname "$0")/common.sh"
prev=$(cat "$STATE_DIR/previous_version" 2>/dev/null || true)
[ -n "$prev" ] || die "no previous version recorded"
exec "$REPO_DIR/deploy/scripts/upgrade.sh" "$prev"
