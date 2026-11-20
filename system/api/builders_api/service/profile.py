"""get_firm_profile: who the firm is, its people, jobs, contacts and what is due soon. Plain code (ADR 0006).

The live context Claude loads at the start of a conversation, instead of a static file that goes stale.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.service import jobs as jobs_service
from builders_api.service import payments

SOON_DAYS = 14


def get_firm_profile(firm: uuid.UUID, today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.date.today()
    with connection() as conn:
        f = conn.execute("select name from firms where id = %s", (firm,)).fetchone()
        staff = conn.execute("select name, role, email from staff where firm_id = %s order by role desc, name",
                             (firm,)).fetchall()
        own = jobs_service.own_addresses(conn, firm)
        job_rows = conn.execute(
            """select j.id, j.ref, j.title, j.address, j.job_type_code, j.status, j.start_date, j.target_date,
                      c.name as client, c.kind as client_kind, c.email as client_email
               from jobs j left join clients c on c.id = j.client_id where j.firm_id = %s order by j.ref""",
            (firm,)).fetchall()
        contacts = conn.execute(
            """select job_id, from_name, lower(from_address) as address, count(*) n, max(sent_at)::date as last
               from emails where firm_id = %s and job_id is not null group by 1, 2, 3 order by 1, n desc""",
            (firm,)).fetchall()
        dated = conn.execute(
            """select f.job_id, f.fact_type, f.summary, f.fact_date from facts f
               where f.firm_id = %s and f.fact_date between %s and %s order by f.fact_date""",
            (firm, today, today + dt.timedelta(days=SOON_DAYS))).fetchall()
        counts = conn.execute(
            """select job_id, count(*) filter (where true) emails from emails where firm_id = %s group by job_id""",
            (firm,)).fetchall()
        docs = conn.execute("select job_id, count(*) n from attachments where firm_id = %s group by job_id",
                            (firm,)).fetchall()
        terms = conn.execute("select job_id, party, counterparty, contract_form from contract_terms where firm_id = %s",
                             (firm,)).fetchall()
    n_emails = {r["job_id"]: r["emails"] for r in counts}
    n_docs = {r["job_id"]: r["n"] for r in docs}
    out_jobs, due_soon = [], []
    for j in job_rows:
        people = [{"name": c["from_name"], "email": c["address"], "emails": c["n"], "last": c["last"].isoformat()}
                  for c in contacts if c["job_id"] == j["id"] and c["address"] not in own][:6]
        contracts = [{"party": t["party"], "with": t["counterparty"], "form": t["contract_form"]}
                     for t in terms if t["job_id"] == j["id"]]
        out_jobs.append({
            "ref": j["ref"], "title": j["title"], "address": j["address"], "type": j["job_type_code"],
            "status": j["status"], "client": j["client"], "client_kind": j["client_kind"], "client_email": j["client_email"],
            "start_date": j["start_date"].isoformat() if j["start_date"] else None,
            "target_date": j["target_date"].isoformat() if j["target_date"] else None,
            "days_to_target": (j["target_date"] - today).days if j["target_date"] else None,
            "contacts": people, "contracts": contracts,
            "emails_filed": n_emails.get(j["id"], 0), "documents": n_docs.get(j["id"], 0),
        })
        if j["target_date"] and today <= j["target_date"] <= today + dt.timedelta(days=SOON_DAYS):
            due_soon.append({"date": j["target_date"].isoformat(), "job": j["ref"], "what": "Target completion"})
        if contracts:
            nxt = payments.get_payment_dates(firm, j["ref"], today)["next_deadline"]
            if nxt and nxt["date"] <= (today + dt.timedelta(days=SOON_DAYS)).isoformat():
                due_soon.append({"date": nxt["date"], "job": j["ref"],
                                 "what": f"{nxt['what'].replace('_', ' ')} ({nxt['contract']})"})
    ref_of = {j["id"]: j["ref"] for j in job_rows}
    for d in dated:
        if d["fact_type"] in ("key_date", "certificate_pending", "request"):
            due_soon.append({"date": d["fact_date"].isoformat(), "job": ref_of.get(d["job_id"]), "what": d["summary"]})
    due_soon.sort(key=lambda x: x["date"])
    seen, unique = set(), []
    for d in due_soon:
        key = (d["date"], d["job"], d["what"][:40])
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return {
        "firm": {"name": f["name"] if f else None, "today": today.isoformat()},
        "people": [{"name": s["name"], "role": s["role"], "email": s["email"]} for s in staff],
        "our_addresses": sorted(own),
        "jobs": out_jobs,
        "due_in_next_14_days": unique,
        "note": "Live from the firm's records. Use job refs in other tools. Emails from our_addresses were sent by us.",
    }
