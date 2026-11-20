#!/bin/sh
# Runs once, when the database volume is first created.
# The app connects as builders_app: read and write rows, no CREATE, DROP or ALTER (ADR 0007).
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<SQL
create role builders_app login password '${APP_DB_PASSWORD}';
revoke create on schema public from public;
grant usage on schema public to builders_app;
alter default privileges for role ${POSTGRES_USER} in schema public
    grant select, insert, update, delete on tables to builders_app;
alter default privileges for role ${POSTGRES_USER} in schema public
    grant usage, select on sequences to builders_app;
SQL
