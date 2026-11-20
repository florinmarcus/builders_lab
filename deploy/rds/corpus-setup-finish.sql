-- Finish a corpus set-up that stopped at "must be able to SET ROLE builders_corpus_owner" (first run, 20 Nov 2026).
-- The roles, the database and pgvector exist; this sets fresh passwords (the first ones were never stored),
-- adds the missing membership, and creates the schema and the reader's rights. Safe to run more than once.
-- Run as the RDS master user, connected to "postgres", with -v owner_password=... -v reader_password=...

\set ON_ERROR_STOP on

ALTER ROLE builders_corpus_owner PASSWORD :'owner_password';
ALTER ROLE builders_corpus_reader PASSWORD :'reader_password';
GRANT builders_corpus_owner TO CURRENT_USER;

\connect builders_corpus

CREATE SCHEMA IF NOT EXISTS corpus AUTHORIZATION builders_corpus_owner;
GRANT USAGE ON SCHEMA corpus TO builders_corpus_reader;
ALTER DEFAULT PRIVILEGES FOR ROLE builders_corpus_owner IN SCHEMA corpus GRANT SELECT ON TABLES TO builders_corpus_reader;

-- Check (should print: builders_corpus_reader | default_transaction_read_only=on)
SELECT rolname, (SELECT setting FROM pg_db_role_setting s, unnest(s.setconfig) setting
                 WHERE s.setrole = r.oid AND setting LIKE 'default_transaction_read_only%') AS read_only
FROM pg_roles r WHERE rolname = 'builders_corpus_reader';
