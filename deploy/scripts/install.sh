#!/usr/bin/env bash
# First-time set-up of a fresh Amazon Linux 2023 server. Safe to run again.
# Usage (as root): install.sh [version]
# CloudFormation runs this at first boot. You can also run it by hand through Session Manager.
set -euo pipefail
BASE=${BASE:-/opt/builders-lab}; export BASE
REPO_URL=${REPO_URL:-https://github.com/florinmarcus/builders_lab.git}
SSM_PREFIX=${SSM_PREFIX:-/builders-lab/prod}; export SSM_PREFIX
COMPOSE_VERSION=v2.32.4
VERSION=${1:-main}
log() { printf '%s  %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

[ "$(id -u)" = 0 ] || { echo "run as root"; exit 1; }

log "packages"
dnf install -y -q docker git openssl cronie >/dev/null
dnf upgrade -y -q --security >/dev/null || true
dnf install -y -q dnf-automatic >/dev/null && \
  sed -i 's/^upgrade_type.*/upgrade_type = security/; s/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf && \
  systemctl enable --now dnf-automatic.timer
systemctl enable --now docker crond

if ! docker compose version >/dev/null 2>&1; then
  log "docker compose $COMPOSE_VERSION"
  mkdir -p /usr/local/lib/docker/cli-plugins
  arch=$(uname -m); [ "$arch" = aarch64 ] || [ "$arch" = x86_64 ] || { echo "unsupported $arch"; exit 1; }
  curl -fsSL -o /usr/local/lib/docker/cli-plugins/docker-compose \
    "https://github.com/docker/compose/releases/download/$COMPOSE_VERSION/docker-compose-linux-$arch"
  chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
fi

log "code"
mkdir -p "$BASE"
token=$(aws ssm get-parameter --name "$SSM_PREFIX/secrets/github_token" --with-decryption \
        --query Parameter.Value --output text 2>/dev/null || true)
url=$REPO_URL
if [ -n "$token" ] && [ "$token" != "None" ]; then url=${REPO_URL/https:\/\//https:\/\/x-access-token:$token@}; fi
if [ ! -d "$BASE/repo/.git" ]; then git clone --quiet "$url" "$BASE/repo"; else git -C "$BASE/repo" remote set-url origin "$url"; fi

log "settings and secrets"
"$BASE/repo/deploy/scripts/env-from-ssm.sh"

log "daily backup at 02:30 UTC"
echo "30 2 * * * root BASE=$BASE $BASE/repo/deploy/scripts/backup.sh daily >> /var/log/builders-backup.log 2>&1" \
  > /etc/cron.d/builders-backup

log "start"
"$BASE/repo/deploy/scripts/upgrade.sh" "$VERSION"
