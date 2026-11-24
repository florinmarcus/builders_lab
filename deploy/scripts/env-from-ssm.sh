#!/usr/bin/env bash
# Write /opt/builders-lab/.env from AWS Parameter Store. Creates missing secrets once (random), then keeps them.
# Settings: $SSM_PREFIX/domain, $SSM_PREFIX/tls_directive, $SSM_PREFIX/support_contact (plain strings, from CloudFormation)
# Secrets:  $SSM_PREFIX/secrets/<name> (SecureString, created here if missing)
source "$(dirname "$0")/common.sh"

param() { aws ssm get-parameter --name "$1" --with-decryption --query Parameter.Value --output text 2>/dev/null || true; }

secret() {  # secret NAME: read, or create once with a random value
  local name="$SSM_PREFIX/secrets/$1" value
  value=$(param "$name")
  if [ -z "$value" ] || [ "$value" = "None" ]; then
    value=$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 40)
    aws ssm put-parameter --name "$name" --type SecureString --value "$value" --no-overwrite >/dev/null
    log "created secret $name"
    value=$(param "$name")  # re-read in case another run created it first
  fi
  printf '%s' "$value"
}

mkdir -p "$BASE"
set_env DOMAIN "$(param "$SSM_PREFIX/domain")"
set_env TLS_DIRECTIVE "$(param "$SSM_PREFIX/tls_directive")"
set_env SUPPORT_CONTACT "$(param "$SSM_PREFIX/support_contact")"
for s in POSTGRES_PASSWORD APP_DB_PASSWORD API_KEY_PEPPER MCP_PATH_SECRET; do
  set_env "$s" "$(secret "$(echo "$s" | tr 'A-Z' 'a-z')")"
done
# Regulations corpus: the corpus-db container (compose.yaml). An outside URL in secrets/corpus_reader_url wins.
for s in CORPUS_SUPER_PASSWORD CORPUS_OWNER_PASSWORD CORPUS_READER_PASSWORD; do
  set_env "$s" "$(secret "$(echo "$s" | tr 'A-Z' 'a-z')")"
done
reader_url=$(param "$SSM_PREFIX/secrets/corpus_reader_url")
if [ -z "$reader_url" ] || [ "$reader_url" = "None" ]; then
  reader_url="postgresql://builders_corpus_reader:$(get_env CORPUS_READER_PASSWORD)@corpus-db:5432/builders_corpus"
fi
set_env CORPUS_READER_URL "$reader_url"
set_env RAG_ENABLED "$(param "$SSM_PREFIX/rag_enabled")"   # "on" once the server role has its Bedrock rights
# Demo Gmail (optional): login token and addresses, stored once by Florin (system/data/mock/README.md).
set_env BUILDER_INBOX "$(param "$SSM_PREFIX/secrets/builder_inbox")"
set_env SIMULATOR_SENDERS "$(param "$SSM_PREFIX/secrets/simulator_senders")"
token=$(param "$SSM_PREFIX/secrets/gmail_token")
[ -n "$token" ] && [ "$token" != "None" ] || token="{}"
printf '%s' "$token" > "$BASE/gmail-token.json"
chown 10001 "$BASE/gmail-token.json" 2>/dev/null || true  # the app user (uid 10001) must read it
chmod 600 "$BASE/gmail-token.json"
[ -n "$(get_env DOMAIN)" ] || die "no domain in $SSM_PREFIX/domain"
log "wrote $ENV_FILE"
