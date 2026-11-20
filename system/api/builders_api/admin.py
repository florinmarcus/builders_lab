"""Admin commands for Florin, run on the server (ADR 0007).

  python -m builders_api.admin keys create --firm oakline --label "Dan, Claude app" --expires 2026-12-31
  python -m builders_api.admin keys list [--firm oakline]
  python -m builders_api.admin keys extend --prefix 1a2b3c4d --expires 2027-01-31
  python -m builders_api.admin keys revoke --prefix 1a2b3c4d
  python -m builders_api.admin kill on|off|status
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys

from builders_api import security
from builders_api.db import connection


def create_key(firm_slug: str, label: str, expires_on: dt.date, grace_days: int = 7) -> str:
    key, prefix = security.new_key()
    with connection() as conn:
        row = conn.execute("select id from firms where slug = %s", (firm_slug,)).fetchone()
        if not row:
            raise SystemExit(f"No firm called '{firm_slug}'.")
        conn.execute(
            """insert into api_keys (firm_id, label, key_prefix, key_hash, expires_on, grace_days)
               values (%s, %s, %s, %s, %s, %s)""",
            (row["id"], label, prefix, security.hash_key(key), expires_on, grace_days),
        )
    return key


def list_keys(firm_slug: str | None = None) -> list[dict]:
    with connection() as conn:
        return conn.execute(
            """select f.slug as firm, k.key_prefix, k.label, k.expires_on, k.grace_days,
                      k.revoked_at is not null as revoked, k.last_used_at
               from api_keys k join firms f on f.id = k.firm_id
               where %(s)s::text is null or f.slug = %(s)s order by f.slug, k.created_at""",
            {"s": firm_slug},
        ).fetchall()


def extend_key(prefix: str, expires_on: dt.date) -> bool:
    with connection() as conn:
        cur = conn.execute("update api_keys set expires_on = %s where key_prefix = %s and revoked_at is null",
                           (expires_on, prefix))
        return cur.rowcount == 1


def revoke_key(prefix: str) -> bool:
    with connection() as conn:
        cur = conn.execute("update api_keys set revoked_at = now() where key_prefix = %s and revoked_at is null",
                           (prefix,))
        return cur.rowcount == 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="builders_api.admin")
    sub = p.add_subparsers(dest="area", required=True)
    keys = sub.add_parser("keys").add_subparsers(dest="cmd", required=True)
    c = keys.add_parser("create")
    c.add_argument("--firm", required=True)
    c.add_argument("--label", required=True)
    c.add_argument("--expires", required=True, type=dt.date.fromisoformat)
    c.add_argument("--grace-days", type=int, default=7)
    lst = keys.add_parser("list")
    lst.add_argument("--firm")
    e = keys.add_parser("extend")
    e.add_argument("--prefix", required=True)
    e.add_argument("--expires", required=True, type=dt.date.fromisoformat)
    r = keys.add_parser("revoke")
    r.add_argument("--prefix", required=True)
    k = sub.add_parser("kill")
    k.add_argument("state", choices=["on", "off", "status"])
    a = p.parse_args(argv)

    if a.area == "keys" and a.cmd == "create":
        key = create_key(a.firm, a.label, a.expires, a.grace_days)
        print("New key (shown once, store it safely):")
        print(key)
    elif a.area == "keys" and a.cmd == "list":
        for k_ in list_keys(a.firm):
            print(k_)
    elif a.area == "keys" and a.cmd == "extend":
        print("extended" if extend_key(a.prefix, a.expires) else "no active key with that prefix")
    elif a.area == "keys" and a.cmd == "revoke":
        print("revoked" if revoke_key(a.prefix) else "no active key with that prefix")
    elif a.area == "kill":
        if a.state != "status":
            security.set_kill_switch(a.state == "on")
        print("kill switch:", "ON (all requests refused)" if security.kill_switch_on(0) else "off")
    return 0


if __name__ == "__main__":
    sys.exit(main())
