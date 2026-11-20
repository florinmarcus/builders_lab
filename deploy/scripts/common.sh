#!/usr/bin/env bash
# shellcheck disable=SC2034  # variables used by the scripts that source this file
# Shared settings for the server scripts. Sourced, not run.
set -euo pipefail

BASE=${BASE:-/opt/builders-lab}
REPO_DIR="$BASE/repo"
ENV_FILE="$BASE/.env"
BACKUP_DIR="$BASE/backups"
STATE_DIR="$BASE/state"          # current_version, previous_version
REPO_URL=${REPO_URL:-https://github.com/florinmarcus/builders_lab.git}
SSM_PREFIX=${SSM_PREFIX:-/builders-lab/prod}

log() { printf '%s  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2; }  # stderr: never mixes with captured values
die() { log "ERROR: $*"; exit 1; }

dc() {  # docker compose with our env file, from the checked-out deploy folder
  docker compose --project-directory "$REPO_DIR/deploy" -f "$REPO_DIR/deploy/compose.yaml" \
    --env-file "$ENV_FILE" "$@"
}

set_env() {  # set_env KEY VALUE: add or replace a line in the env file
  local key=$1 value=$2
  touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
  grep -v "^${key}=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
  printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE.tmp"
  mv "$ENV_FILE.tmp" "$ENV_FILE"; chmod 600 "$ENV_FILE"
}

get_env() { grep "^$1=" "$ENV_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || true; }
