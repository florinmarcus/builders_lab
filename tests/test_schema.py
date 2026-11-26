"""Schema checks: migrations apply, are re-runnable, and the key constraints hold."""

from __future__ import annotations

import psycopg
import pytest

from builders_api.db import migrate as migrate_mod


def _firm(conn) -> str:
    return conn.execute(
        "insert into firms (slug, name) values ('oakline', 'Oakline Build Ltd') returning id"
    ).fetchone()[0]


def test_migrate_is_rerunnable(db_url):
    assert migrate_mod.migrate(db_url) == []


def test_edited_migration_is_refused(db_url, conn):
    conn.execute("update schema_migrations set sha256 = 'changed'")
    conn.commit()
    with pytest.raises(migrate_mod.MigrationChangedError):
        migrate_mod.migrate(db_url)


def test_email_upsert_key_and_full_text_search(conn):
    firm = _firm(conn)
    sql = """insert into emails (firm_id, gmail_message_id, subject, sent_at, body_text, from_name)
             values (%s, 'm1', 'Pocket door', now(), %s, 'Victoria Hartley')
             on conflict (firm_id, gmail_message_id) do update set body_text = excluded.body_text"""
    conn.execute(sql, (firm, "Approved, thanks. Go ahead with the pocket door."))
    conn.execute(sql, (firm, "Approved, thanks. Go ahead with the pocket door to the utility room."))
    rows = conn.execute(
        "select subject from emails where search @@ websearch_to_tsquery('english', 'approved door')"
    ).fetchall()
    assert rows == [("Pocket door",)]


def test_fact_needs_a_source(conn):
    firm = _firm(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into facts (firm_id, fact_type, summary, prompt_version) values (%s, 'approval', 'x', 'v1')",
            (firm,),
        )


def test_contract_terms_need_a_date_basis(conn):
    firm = _firm(conn)
    conn.execute("insert into job_types (code, name) values ('commercial_fitout', 'Commercial fit-out')")
    job = conn.execute(
        """insert into jobs (firm_id, job_type_code, ref, title, address)
           values (%s, 'commercial_fitout', 'KWY-4', 'Unit 4 office refit', 'Kingsway Business Park') returning id""",
        (firm,),
    ).fetchone()[0]
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """insert into contract_terms (firm_id, job_id, party, counterparty, final_date_days_after_due,
                                           payment_notice_days_after_due, pay_less_days_before_final)
               values (%s, %s, 'subcontract', 'Fenwick Drylining', 21, 5, 5)""",
            (firm, job),
        )


def test_trace_and_quota_rows(conn):
    firm = _firm(conn)
    conn.execute(
        "insert into versions (id, kind, name, sha256) values ('extract.v1', 'prompt', 'extract', 'abc')"
    )
    conn.execute(
        """insert into traces (trace_id, firm_id, kind, name, model_id, version_id, input_tokens,
                               output_tokens, cost_usd, latency_ms, status, sources)
           values (gen_random_uuid(), %s, 'model', 'extract', 'haiku', 'extract.v1', 1200, 300,
                   0.0024, 850, 'ok', '[{"email": "m1"}]')""",
        (firm,),
    )
    conn.execute(
        "insert into quota_usage (firm_id, metric, day, used) values (%s, 'bedrock_usd', current_date, 0.0024)",
        (firm,),
    )
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            "insert into quota_limits (firm_id, metric, daily_limit) values (%s, 'made_up_metric', 1)",
            (firm,),
        )


def test_evals_firm_has_its_own_tool_call_limit(conn):
    """Migration 0004: the evals firm exists, holds no data, and has 5,000 tool calls a day (S161)."""
    row = conn.execute(
        """select f.name, q.daily_limit from firms f
           join quota_limits q on q.firm_id = f.id and q.metric = 'tool_calls' where f.slug = 'evals'"""
    ).fetchone()
    assert row is not None and float(row[1]) == 5000
    assert conn.execute("select count(*) from jobs j join firms f on f.id = j.firm_id where f.slug = 'evals'").fetchone()[0] == 0
