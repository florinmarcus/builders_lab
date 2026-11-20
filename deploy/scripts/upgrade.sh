#!/usr/bin/env bash
# Upgrade (or first start) to a git version, with automatic rollback.
# Usage: upgrade.sh [version]   version = commit, tag or branch (default: main)
# Steps: fetch -> build image -> backup -> migrate -> restart -> health check -> (roll back if unhealthy)
source "$(dirname "$0")/common.sh"
VERSION=${1:-main}
exec 9>"$BASE/.upgrade.lock"; flock -n 9 || die "another upgrade is running"
mkdir -p "$STATE_DIR"

cd "$REPO_DIR" || exit 1
git fetch --quiet --tags origin
sha=$(git rev-parse --verify --quiet "origin/$VERSION^{commit}" || git rev-parse --verify "$VERSION^{commit}")
short=${sha:0:12}
prev=$(cat "$STATE_DIR/current_version" 2>/dev/null || true)
log "upgrade: ${prev:-none} -> $short"

git checkout --quiet --detach "$sha"
# DOCKER_BUILD_EXTRA: optional extra flags, e.g. for a build behind a proxy (empty on the server)
# shellcheck disable=SC2086
docker build --quiet ${DOCKER_BUILD_EXTRA:-} -t "builders-api:$short" "$REPO_DIR" >/dev/null
set_env APP_IMAGE "builders-api:$short"

# The Gmail token file must exist before compose starts, or Docker creates a folder in its place.
[ -d "$BASE/gmail-token.json" ] && rmdir "$BASE/gmail-token.json"   # left by an older deploy
if [ ! -f "$BASE/gmail-token.json" ]; then
  printf '{}' > "$BASE/gmail-token.json"
  chown 10001 "$BASE/gmail-token.json" 2>/dev/null || true  # the app user (uid 10001) must read it
  chmod 600 "$BASE/gmail-token.json"
fi

dc up -d db
dc exec -T db sh -c 'until pg_isready -q -U builders_owner -d builders; do sleep 1; done'

backup=""
migrated=no
if [ -n "$prev" ]; then
  backup=$("$REPO_DIR/deploy/scripts/backup.sh" "before-$short" | tail -1)
fi

applied=$(dc run --rm --no-deps app python -m builders_api.db.migrate)
log "$applied"
case "$applied" in *"nothing new"*) ;; *) migrated=yes ;; esac

dc up -d --remove-orphans app caddy

healthy=no
for _ in $(seq 1 30); do
  if dc exec -T app python -m builders_api.healthcheck >/dev/null 2>&1 \
     && dc exec -T app python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)" >/dev/null 2>&1; then
    healthy=yes; break
  fi
  sleep 2
done

if [ "$healthy" = yes ]; then
  [ -n "$prev" ] && [ "$prev" != "$short" ] && echo "$prev" > "$STATE_DIR/previous_version"
  echo "$short" > "$STATE_DIR/current_version"
  log "healthy: running $short"
  exit 0
fi

log "NOT healthy: rolling back"
dc logs --tail 50 app || true
[ -n "$prev" ] || die "first start failed; nothing to roll back to"
if [ "$migrated" = yes ] && [ -n "$backup" ]; then
  log "restoring database from $backup"
  dc stop app
  dc exec -T db pg_restore -U builders_owner -d builders --clean --if-exists < "$backup"
fi
git checkout --quiet --detach "$prev"
set_env APP_IMAGE "builders-api:$prev"
dc up -d app caddy
for _ in $(seq 1 30); do
  dc exec -T app python -m builders_api.healthcheck >/dev/null 2>&1 && break
  sleep 2
done
die "upgrade to $short failed; rolled back to $prev"
