-- 0003: mark an email as "facts extracted" even when it has no facts (e.g. an order confirmation). ADR 0006. 20 Nov 2026.
alter table emails add column facts_done_at timestamptz;
alter table emails add column facts_version text;   -- save_facts tool description version used
