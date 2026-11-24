#!/bin/sh
# Runs once, when the corpus-db volume is first created (ADR 0013, London since 24 Nov 2026).
# The same set-up as deploy/rds/corpus-setup.sql: an owner for the loader, a read-only reader for the app.
# The superuser (POSTGRES_USER) owns nothing the app uses; passwords come from Parameter Store via .env.
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres \
     -v owner_password="$CORPUS_OWNER_PASSWORD" -v reader_password="$CORPUS_READER_PASSWORD" <<'SQL'
CREATE ROLE builders_corpus_owner LOGIN PASSWORD :'owner_password';
CREATE ROLE builders_corpus_reader LOGIN PASSWORD :'reader_password' CONNECTION LIMIT 5;
ALTER ROLE builders_corpus_reader SET default_transaction_read_only = on;
ALTER ROLE builders_corpus_reader SET statement_timeout = '5s';
ALTER ROLE builders_corpus_reader SET idle_in_transaction_session_timeout = '10s';
CREATE DATABASE builders_corpus OWNER builders_corpus_owner;
REVOKE ALL ON DATABASE builders_corpus FROM PUBLIC;
GRANT CONNECT ON DATABASE builders_corpus TO builders_corpus_reader;
\connect builders_corpus
CREATE EXTENSION IF NOT EXISTS vector;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA corpus AUTHORIZATION builders_corpus_owner;
GRANT USAGE ON SCHEMA corpus TO builders_corpus_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE builders_corpus_owner IN SCHEMA corpus GRANT SELECT ON TABLES TO builders_corpus_reader;
SQL
