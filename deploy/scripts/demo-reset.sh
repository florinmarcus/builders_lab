#!/usr/bin/env bash
# Put the demo back to its clean start, then (optionally) drop in demo-day emails.
# Usage (as root on the server):
#   demo-reset.sh                 restore baseline, empty the mail folder, feed today's emails
#   demo-reset.sh --no-today      restore baseline and empty the mail folder only
#   demo-reset.sh --save-baseline save the current database as the new baseline
# API keys and the kill switch are kept as they are now (not taken from the baseline).
source "$(dirname "$0")/common.sh"
BASELINE="$BASE/demo-baseline.dump"

if [ "${1:-}" = "--save-baseline" ]; then
  dc exec -T db pg_dump -U builders_owner -d builders -Fc > "$BASELINE.tmp" && mv "$BASELINE.tmp" "$BASELINE"
  chmod 600 "$BASELINE"
  log "baseline saved: $BASELINE ($(du -h "$BASELINE" | cut -f1))"
  exit 0
fi
[ -s "$BASELINE" ] || die "no baseline at $BASELINE (run with --save-baseline first)"

keep=$(mktemp); chmod 600 "$keep"
dc exec -T db pg_dump -U builders_owner -d builders --data-only -t api_keys -t server_flags > "$keep"
"$REPO_DIR/deploy/scripts/backup.sh" before-demo-reset >/dev/null

dc stop app
dc exec -T db pg_restore -U builders_owner -d builders --clean --if-exists < "$BASELINE"
dc exec -T db psql -q -U builders_owner -d builders -c "truncate api_keys, server_flags"
dc exec -T db psql -q -U builders_owner -d builders < "$keep"
rm -f "$keep"
dc run --rm --no-deps app python -m builders_api.db.migrate   # re-apply migrations newer than the baseline
dc start app
for _ in $(seq 1 30); do dc exec -T app python -m builders_api.healthcheck >/dev/null 2>&1 && break; sleep 2; done

dc exec -T app sh -c 'rm -f /data/mail/*.eml'
log "baseline restored, mail folder emptied"
if [ "${1:-}" != "--no-today" ]; then
  dc exec -T app python -m builders_api.admin feed today
fi
log "demo ready: ask \"check my emails\" / \"what came in today?\""
