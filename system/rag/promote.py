"""Promote the staging corpus to live, or roll back (corpus/OVERNIGHT-PLAN.md, S0 and S9).

    python -m system.rag.promote status      # chunk counts and load times of corpus, corpus_next, corpus_prev
    python -m system.rag.promote promote     # corpus_next becomes corpus; the old corpus is kept as corpus_prev
    python -m system.rag.promote rollback    # corpus_prev becomes corpus again; the promoted one is kept as corpus_failed

Runs as builders_corpus_owner (owner URL from Parameter Store, as system.rag.load). Each swap is one transaction:
the server sees the old corpus or the new one, never half. Grants are given explicitly, because default privileges
belong to a schema and do not follow a rename. Promote only when every S9 check in the plan passes.
"""

from __future__ import annotations

import argparse
import sys

from system.rag.load import READER_ROLE, owner_url


def _grants(schema: str) -> str:
    return (f"GRANT USAGE ON SCHEMA {schema} TO {READER_ROLE};\n"
            f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO {READER_ROLE};\n")


def promote_sql() -> str:
    return ("DROP SCHEMA IF EXISTS corpus_prev CASCADE;\n"
            "ALTER SCHEMA corpus RENAME TO corpus_prev;\n"
            "ALTER SCHEMA corpus_next RENAME TO corpus;\n" + _grants("corpus"))


def rollback_sql() -> str:
    return ("DROP SCHEMA IF EXISTS corpus_failed CASCADE;\n"
            "ALTER SCHEMA corpus RENAME TO corpus_failed;\n"
            "ALTER SCHEMA corpus_prev RENAME TO corpus;\n" + _grants("corpus"))


def status(url: str) -> list[tuple]:
    import psycopg

    out = []
    with psycopg.connect(url) as conn:
        for s in ("corpus", "corpus_next", "corpus_prev", "corpus_failed"):
            if conn.execute("SELECT to_regclass(%s)", (f"{s}.stats",)).fetchone()[0] is None:
                out.append((s, None, None))
                continue
            row = conn.execute(f"SELECT chunk_count, loaded_at FROM {s}.stats ORDER BY loaded_at DESC LIMIT 1").fetchone()
            out.append((s, *(row or (None, None))))
    return out


def run(url: str, sql: str) -> None:
    import psycopg

    with psycopg.connect(url) as conn:
        with conn.transaction():
            for stmt in [x.strip() for x in sql.split(";") if x.strip()]:
                conn.execute(stmt)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["status", "promote", "rollback"])
    a = ap.parse_args(argv)
    url = owner_url()
    if a.action == "promote":
        run(url, promote_sql())
    elif a.action == "rollback":
        run(url, rollback_sql())
    for s, n, t in status(url):
        print(f"{s:14} {'(none)' if n is None else f'{n} chunks, loaded {t}'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
