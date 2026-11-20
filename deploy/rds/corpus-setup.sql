-- Builders regulations corpus on the shared RDS instance (ADR 0013).
-- Run ONCE as the RDS master user, connected to the default "postgres" database:
--
--   psql "host=<rds endpoint> port=5432 dbname=postgres user=<master> sslmode=require" \
--        -v owner_password='<new owner password>' -v reader_password='<new reader password>' \
--        -f deploy/rds/corpus-setup.sql
--
-- Creates a separate database next to the lab's, an owner user for the loader and a read-only user for the
-- Builders server. It does not touch the lab's database. Passwords go into Parameter Store, never into Git.

\set ON_ERROR_STOP on

-- Owner: creates and loads the corpus tables. Used only by the loader (laptop or Claude Code session).
CREATE ROLE builders_corpus_owner LOGIN PASSWORD :'owner_password';

-- Reader: the Builders server. Can only read, every transaction is read-only, few connections, short queries.
CREATE ROLE builders_corpus_reader LOGIN PASSWORD :'reader_password' CONNECTION LIMIT 5;
ALTER ROLE builders_corpus_reader SET default_transaction_read_only = on;
ALTER ROLE builders_corpus_reader SET statement_timeout = '5s';
ALTER ROLE builders_corpus_reader SET idle_in_transaction_session_timeout = '10s';

-- Postgres 16 on RDS: the master user is not a full superuser, so it must be a member of the owner role to
-- create a schema owned by it and to set default privileges for it.
GRANT builders_corpus_owner TO CURRENT_USER;

CREATE DATABASE builders_corpus OWNER builders_corpus_owner;
REVOKE ALL ON DATABASE builders_corpus FROM PUBLIC;
GRANT CONNECT ON DATABASE builders_corpus TO builders_corpus_reader;

\connect builders_corpus

CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector; needs the master user (rds_superuser)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE SCHEMA corpus AUTHORIZATION builders_corpus_owner;
GRANT USAGE ON SCHEMA corpus TO builders_corpus_reader;
-- Every table the owner creates in "corpus" is readable, and only readable, by the reader.
ALTER DEFAULT PRIVILEGES FOR ROLE builders_corpus_owner IN SCHEMA corpus GRANT SELECT ON TABLES TO builders_corpus_reader;

-- Check (should print: builders_corpus_reader | on)
SELECT rolname, (SELECT setting FROM pg_db_role_setting s, unnest(s.setconfig) setting
                 WHERE s.setrole = r.oid AND setting LIKE 'default_transaction_read_only%') AS read_only
FROM pg_roles r WHERE rolname = 'builders_corpus_reader';
