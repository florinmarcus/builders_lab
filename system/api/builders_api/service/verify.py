"""verify_answer: deterministic checks on a drafted answer (architecture/design/agent-contracts.md).

Plain code, no model (ADR 0006). Read-only: never changes data.
"""

from __future__ import annotations

import datetime as dt
import re
import uuid
from typing import Any

from builders_api.db import connection
from builders_api.errors import ValidationError
from builders_api.service import payments, regulations
from builders_api.service.facts import _norm
from builders_api.terminology import fold

from builders_api.contracts import CONTRACT_VERSION as CONTRACT  # noqa: E402
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
RO_MONTHS = {"ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4, "mai": 5, "iunie": 6, "iulie": 7,
             "august": 8, "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12}

BANNED = [
    (r"\bno asbestos\b", "Never say \"no asbestos\": say what the survey covered and found."),
    (r"\basbestos[- ]free\b", "Never say \"asbestos-free\"."),
    (r"\b(free of|does not contain|doesnt contain|contains no) asbestos\b", "Never state that asbestos is absent."),
    (r"\bi(?: have|ve)? (?:sent|emailed|paid|signed|submitted)\b", "Drafts only: never say something was sent, paid or signed."),
    (r"\b(?:is|are) (?:fully )?compliant\b", "Never say work is compliant; say what the rules say."),
    # Romanian, compared without diacritics
    (r"\bfara azbest\b", "Niciodată „fără azbest”: spuneți ce a acoperit studiul și ce a găsit."),
    (r"\bnu (?:contine|are|exista) azbest\b", "Niciodată nu afirmați că nu există azbest."),
    (r"\bam (?:trimis|platit|semnat)\b", "Doar ciorne: nu spuneți că ați trimis, plătit sau semnat."),
    (r"\beste (?:complet )?conform\b", "Nu spuneți că lucrarea este conformă; spuneți ce prevăd regulile."),
]
PII = [
    (r"(?:\+44\s?7\d{3}|\b07\d{3})\s?\d{3}\s?\d{3}\b", "phone number"),
    (r"[\w.+-]+@[\w-]+\.[\w.-]+", "email address"),
    (r"\b[A-CEGHJ-PR-TW-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b", "National Insurance number"),
]
AMOUNT = re.compile(r"£\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{2}))?")
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?(?:\s+(20\d{2}))?\b", re.I)
SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b")
RO_DMY = re.compile(r"\b(\d{1,2})\s+(ianuarie|februarie|martie|aprilie|mai|iunie|iulie|august|septembrie|octombrie|noiembrie|decembrie)(?:\s+(20\d{2}))?\b")


def amounts(text: str) -> set[int]:
    """£ amounts in pence."""
    out = set()
    for whole, pence in AMOUNT.findall(text):
        out.add(int(whole.replace(",", "")) * 100 + int(pence or 0))
    return out


def dates(text: str) -> set[tuple[int, int, int | None]]:
    """(day, month, year or None) for ISO, '30 Nov 2026', '30 November' and 25/11/2026 forms."""
    out: set[tuple[int, int, int | None]] = set()
    for y, m, d in ISO_DATE.findall(text):
        out.add((int(d), int(m), int(y)))
    for d, mon, y in DMY.findall(text):
        out.add((int(d), MONTHS[mon[:3].lower()], int(y) if y else None))
    for d, m, y in SLASH.findall(text):
        out.add((int(d), int(m), int(y)))
    for d, mon, y in RO_DMY.findall(fold(text)):
        out.add((int(d), RO_MONTHS[mon], int(y) if y else None))
    return out


def _date_backed(d: tuple[int, int, int | None], known: set[tuple[int, int, int | None]]) -> bool:
    day, month, year = d
    return any(k[0] == day and k[1] == month and (year is None or k[2] in (None, year)) for k in known)


def _source_text(conn, firm: uuid.UUID, source: dict) -> str | None:
    """Text of a cited source, or None if it does not exist for this firm."""
    stype, sid = source.get("type"), str(source.get("id", ""))
    if stype in ("email", "document"):
        try:
            uid = uuid.UUID(sid)
        except ValueError:
            return None
        if stype == "email":
            row = conn.execute("select subject, body_text from emails where id = %s and firm_id = %s", (uid, firm)).fetchone()
            return None if not row else row["subject"] + "\n" + row["body_text"]
        row = conn.execute("select filename, text_content from attachments where id = %s and firm_id = %s",
                           (uid, firm)).fetchone()
        return None if not row else row["filename"] + "\n" + row["text_content"]
    if stype == "calculation":  # id = job ref; recompute payment dates
        try:
            result = payments.get_payment_dates(firm, sid)
        except Exception:  # noqa: BLE001
            return None
        return " ".join(str(v) for c in result["contracts"] for v in c["current_cycle"].values() if v)
    return None


def _regulation_has(quote: str) -> bool:
    found = regulations.search_regulations(quote, limit=10)["passages"]
    return any(_norm(quote) in _norm(p.get("text") or "") for p in found)


def verify_answer(firm: uuid.UUID, text: str, claims: list[dict]) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise ValidationError("text is required: the answer exactly as it will be shown.")
    problems: list[dict[str, Any]] = []

    def add(code, message, claim=None, severity="error"):
        problems.append({"code": code, "severity": severity, "message": message, **({"claim": claim} if claim else {})})

    lower = fold(text)
    for pattern, message in BANNED:
        if re.search(pattern, lower):
            add("BANNED_PHRASE", message)
    for pattern, kind in PII:
        if re.search(pattern, text):
            add("PERSONAL_DATA", f"Answer contains a {kind}. Keep it only if the user needs it.", severity="warning")

    cited_texts: list[str] = []
    with connection() as conn:
        for c in claims:
            cid, quote, source = c.get("id") or "?", (c.get("quote") or "").strip(), c.get("source") or {}
            if source.get("type") == "regulation":
                if not quote:
                    add("QUOTE_NOT_IN_SOURCE", "Regulation claims need an exact quote.", cid)
                elif not _regulation_has(quote):
                    add("QUOTE_NOT_IN_SOURCE", "Quote not found in the regulations passages.", cid)
                else:
                    cited_texts.append(quote)
                continue
            src = _source_text(conn, firm, source)
            if src is None:
                add("SOURCE_NOT_FOUND", "Cited source does not exist for this firm.", cid)
                continue
            cited_texts.append(src)
            if source.get("type") != "calculation":
                if not quote:
                    add("QUOTE_NOT_IN_SOURCE", "Every claim needs an exact quote.", cid)
                elif _norm(quote) not in _norm(src):
                    add("QUOTE_NOT_IN_SOURCE", "Quote not found word for word in the cited source.", cid)

    answer_amounts, answer_dates = amounts(text), dates(text)
    if (answer_amounts or answer_dates) and not claims:
        add("NO_CLAIMS", "The answer states amounts or dates but cites no claims.")
    known_amounts = set().union(*(amounts(t) for t in cited_texts)) if cited_texts else set()
    known_dates = set().union(*(dates(t) for t in cited_texts)) if cited_texts else set()
    for a in sorted(answer_amounts - known_amounts):
        add("NUMBER_NOT_IN_SOURCES", f"£{a / 100:,.2f} does not appear in any cited source.")
    today = dt.date.today()
    for d in sorted(answer_dates, key=lambda x: (x[2] or 0, x[1], x[0])):
        if (d[0], d[1]) == (today.day, today.month):
            continue  # "today" is not a claim
        if not _date_backed(d, known_dates):
            label = f"{d[0]} {list(MONTHS)[d[1] - 1].title()}" + (f" {d[2]}" if d[2] else "")
            add("NUMBER_NOT_IN_SOURCES", f"Date {label} does not appear in any cited source.")

    return {
        "contract": CONTRACT,
        "pass": not any(p["severity"] == "error" for p in problems),
        "problems": problems,
        "checked": {"claims": len(claims), "amounts": len(answer_amounts), "dates": len(answer_dates)},
    }
