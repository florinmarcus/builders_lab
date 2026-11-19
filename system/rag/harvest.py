"""Harvest the shared regulations corpus.

    python -m system.rag.harvest                 # all sources
    python -m system.rag.harvest --only br2010   # some sources
    python -m system.rag.harvest --priority 1    # priority 1 only

Fetches each source in corpus/sources.yaml, stores new versions (by hash) and
writes corpus/harvest-report.md. Never overwrites a stored version.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import traceback
from datetime import date
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin

import requests
from lxml import etree

from system.rag.corpus import CORPUS_DIR, Fetched, Store, check_chain, load_sources, part_key, slugify, validate_sources

USER_AGENT = "builders-lab-corpus-harvester/0.1 (research prototype)"
LEG_BASE = "https://www.legislation.gov.uk/"
GOVUK_API = "https://www.gov.uk/api/content"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dct": "http://purl.org/dc/terms/",
    "ukm": "http://www.legislation.gov.uk/namespaces/metadata",
}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class FetchError(Exception):
    pass


class Http:
    def __init__(self, tries: int = 3, pause: float = 0.4, timeout: int = 120):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.tries, self.pause, self.timeout = tries, pause, timeout

    def get(self, url: str) -> requests.Response:
        last = None
        for attempt in range(self.tries):
            try:
                time.sleep(self.pause)
                r = self.s.get(url, timeout=self.timeout, allow_redirects=True)
                if r.status_code == 200:
                    return r
                if r.status_code in (404, 410, 403, 405, 401):
                    raise FetchError(f"HTTP {r.status_code} for {url}")
                last = f"HTTP {r.status_code} for {url}"
            except FetchError:
                raise
            except requests.RequestException as e:
                last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** (attempt + 1))
        raise FetchError(last or f"failed {url}")


def media_type(r: requests.Response, default: str = "application/octet-stream") -> str:
    ct = r.headers.get("Content-Type", default).split(";")[0].strip().lower()
    if ct in ("application/octet-stream", "binary/octet-stream", ""):
        url = r.url.lower()
        for ext, t in ((".pdf", "application/pdf"), (".xml", "application/xml"), (".html", "text/html"), (".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")):
            if url.split("?")[0].endswith(ext):
                return t
    return ct


def last_modified(r: requests.Response) -> str | None:
    lm = r.headers.get("Last-Modified")
    if not lm:
        return None
    try:
        return parsedate_to_datetime(lm).date().isoformat()
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- legislation.gov.uk


def leg_versions(http: Http, path: str) -> list[str]:
    """Point-in-time version dates for a legislation path, oldest first."""
    whole = len(path.strip("/").split("/")) == 3
    url = LEG_BASE + path.strip("/") + ("/contents/data.xml" if whole else "/data.xml")
    root = etree.fromstring(http.get(url).content)
    dates = set()
    for link in root.iterfind(".//atom:link", NS):
        if link.get("rel") == "http://purl.org/dc/terms/hasVersion" and DATE_RE.match(link.get("title", "")):
            dates.add(link.get("title"))
    return sorted(dates)


def leg_title(root) -> str:
    t = root.find(".//dc:title", {"dc": "http://purl.org/dc/elements/1.1/"})
    return (t.text or "").strip() if t is not None and t.text else ""


def fetch_legislation(http: Http, store: Store, source: dict, history_from: str, emit) -> list[Fetched]:
    """Legislation history is stored through emit() as each version arrives, so a crash keeps progress."""
    fetch = source["fetch"]
    path = fetch["path"].strip("/")
    history = fetch.get("history", "current")
    part = "main"
    out: list[Fetched] = []

    if history == "made":
        url = f"{LEG_BASE}{path}/made/data.xml"
        r = http.get(url)
        root = etree.fromstring(r.content)
        made = root.find(".//ukm:Made", NS)
        made_date = made.get("Date") if made is not None else None
        in_force = str(source["in_force"]) if source.get("in_force") else None
        out.append(Fetched(part, leg_title(root) or source["title"], r.content, "application/xml", url,
                           made_date, in_force or made_date or date.today().isoformat(),
                           "in_force" if in_force else ("published" if made_date else "first_seen"),
                           dedupe_on_date=True))
        return out

    if history == "current":
        url = f"{LEG_BASE}{path}/data.xml"
        r = http.get(url)
        root = etree.fromstring(r.content)
        v = root.find(".//dct:valid", NS)
        vdate = v.text.strip() if v is not None and v.text else None
        if vdate is None:  # never revised: the made/enacted text is the current one
            el = root.find(".//ukm:Made", NS)
            if el is None:
                el = root.find(".//ukm:EnactmentDate", NS)
            vdate = el.get("Date") if el is not None else date.today().isoformat()
        out.append(Fetched(part, leg_title(root) or source["title"], r.content, "application/xml", url,
                           vdate, vdate, "point_in_time", dedupe_on_date=True))
        return out

    # history == "all": every version in force on or after history_from.
    start = str(source.get("history_from") or history_from)
    dates = leg_versions(http, path)
    if not dates:
        raise FetchError(f"no point-in-time versions listed for {path}")
    keep = [d for d in dates if d >= start]
    before = [d for d in dates if d < start]
    if before:
        keep.insert(0, before[-1])  # the version already in force on the start date
    for d in keep:
        if store.has_date(source["id"], part, d):
            continue
        url = f"{LEG_BASE}{path}/{d}/data.xml"
        r = http.get(url)
        root = etree.fromstring(r.content)
        emit(Fetched(part, leg_title(root) or source["title"], r.content, "application/xml", url,
                     d, d, "point_in_time", dedupe_on_date=True))
    return out


# ---------------------------------------------------------------- GOV.UK


def govuk_json(http: Http, page: str) -> dict:
    return http.get(GOVUK_API + page).json()


def html_doc(title: str, url: str, body: str) -> bytes:
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>'
        f'<link rel="canonical" href="{url}"></head><body><h1>{title}</h1>\n{body}\n</body></html>'
    ).encode("utf-8")


def page_body(d: dict) -> str:
    det = d.get("details", {})
    body = det.get("body")
    if isinstance(body, list):  # some formats give a list of content types
        body = next((b.get("content") for b in body if b.get("content_type") == "text/html"), "")
    parts = [body or ""]
    for sec in det.get("parts", []) or []:  # guides and manuals split into parts
        b = sec.get("body")
        if isinstance(b, list):
            b = next((x.get("content") for x in b if x.get("content_type") == "text/html"), "")
        parts.append(f"<h2>{sec.get('title', '')}</h2>\n{b or ''}")
    return "\n".join(p for p in parts if p)


def iso_day(ts: str | None) -> str | None:
    return ts[:10] if ts else None


def fetch_govuk(http: Http, store: Store, source: dict) -> list[Fetched]:
    fetch = source["fetch"]
    page = fetch["page"]
    d = govuk_json(http, page)
    published = iso_day(d.get("public_updated_at")) or date.today().isoformat()
    in_force = str(source["in_force"]) if source.get("in_force") else None
    want = fetch.get("attachments", "none")
    match = re.compile(fetch["match"], re.I) if fetch.get("match") else None
    parts_map = {k: re.compile(v, re.I) for k, v in (fetch.get("parts") or {}).items()}
    out: list[Fetched] = []
    page_url = "https://www.gov.uk" + page

    if fetch.get("body") or want == "none":
        body = page_body(d)
        if body.strip():
            out.append(Fetched("page", d.get("title", source["title"]), html_doc(d.get("title", ""), page_url, body),
                               "text/html", page_url, published, published, "published"))
        # Manuals list their sections as child pages.
        for grp in d.get("details", {}).get("child_section_groups", []) or []:
            for sec in grp.get("child_sections", []) or []:
                bp = sec.get("base_path")
                if not bp:
                    continue
                sd = govuk_json(http, bp)
                sb = page_body(sd)
                if sb.strip():
                    sp = iso_day(sd.get("public_updated_at")) or published
                    out.append(Fetched(slugify(bp.rsplit("/", 1)[-1]), sd.get("title", bp),
                                       html_doc(sd.get("title", ""), "https://www.gov.uk" + bp, sb),
                                       "text/html", "https://www.gov.uk" + bp, sp, sp, "published"))

    if want != "none":
        for a in d.get("details", {}).get("attachments", []) or []:
            title = a.get("title") or ""
            atype = a.get("attachment_type")
            if match and not match.search(title):
                continue
            is_pdf = (a.get("content_type") or "").endswith("pdf")
            if atype == "external":
                continue
            if want == "pdf" and not is_pdf:
                continue
            if want == "html" and atype != "html":
                continue
            part = None
            for k, rx in parts_map.items():
                if rx.search(title):
                    part = k
                    break
            if parts_map and part is None:
                continue
            part = part or part_key(title)
            if atype == "html":
                url = a.get("url", "")
                path = url.replace("https://www.gov.uk", "")
                hd = govuk_json(http, path)
                content = html_doc(hd.get("title", title), "https://www.gov.uk" + path, page_body(hd))
                mt, furl = "text/html", "https://www.gov.uk" + path
            else:
                furl = urljoin("https://www.gov.uk", a.get("url", ""))
                r = http.get(furl)
                content, mt = r.content, media_type(r, a.get("content_type") or "application/octet-stream")
            vf, basis = (in_force, "in_force") if (in_force and not store.records(source["id"], part)) else (published, "published")
            out.append(Fetched(part, title, content, mt, furl, published, vf, basis))
    if not out:
        raise FetchError(f"nothing matched on {page} (attachments={want}, match={fetch.get('match')})")
    return out


# ---------------------------------------------------------------- plain URL


def fetch_url(http: Http, store: Store, source: dict) -> list[Fetched]:
    url = source["fetch"].get("url") or source["url"]
    r = http.get(url)
    mt = media_type(r)
    lm = last_modified(r)
    in_force = str(source["in_force"]) if source.get("in_force") else None
    part = source["fetch"].get("part", "main")
    if in_force and not store.records(source["id"], part):
        vf, basis = in_force, "in_force"
    elif lm:
        vf, basis = lm, "published"
    else:
        vf, basis = date.today().isoformat(), "first_seen"
    return [Fetched(part, source["title"], r.content, mt, r.url, lm, vf, basis)]


# ---------------------------------------------------------------- run


def run(only: list[str] | None = None, priority: int | None = None, report: bool = True) -> int:
    doc = load_sources()
    errors = validate_sources(doc)
    if errors:
        print("sources.yaml has problems:\n  " + "\n  ".join(errors))
        return 2
    history_from = str((doc.get("defaults") or {}).get("history_from", "2010-10-01"))
    store, http = Store(), Http()
    rows = []
    for s in doc["sources"]:
        if only and s["id"] not in only:
            continue
        if priority and int(s.get("priority", 3)) > priority:
            continue
        method = s["fetch"]["method"]
        if s["mode"] == "link_only" or method == "none":
            rows.append((s, "skipped", 0, s.get("status") or "link only"))
            continue
        new: list[dict] = []

        def emit(f: Fetched, s=s, new=new) -> None:
            rec = store.add(s, f)
            if rec:
                new.append(rec)

        try:
            if method == "legislation":
                fetched = fetch_legislation(http, store, s, history_from, emit)
            elif method == "govuk":
                fetched = fetch_govuk(http, store, s)
            else:
                fetched = fetch_url(http, store, s)
            for f in fetched:
                emit(f)
            total = len(store.records(s["id"]))
            rows.append((s, "ok", len(new), f"{total} versions stored"))
            print(f"ok      {s['id']}: {len(new)} new, {total} total", flush=True)
        except Exception as e:  # keep going; report the failure
            msg = f"{type(e).__name__}: {e}"
            if not isinstance(e, FetchError):
                traceback.print_exc()
            rows.append((s, "failed", len(new), msg))
            print(f"FAILED  {s['id']}: {msg}", flush=True)
    if report:
        write_report(doc, store, rows, partial=bool(only or priority))
    return 0 if not any(r[1] == "failed" for r in rows) else 1


def write_report(doc: dict, store: Store, rows: list, partial: bool) -> None:
    ok = [r for r in rows if r[1] == "ok"]
    failed = [r for r in rows if r[1] == "failed"]
    skipped = [r for r in rows if r[1] == "skipped"]
    total_recs, total_bytes, chain_problems = 0, 0, []
    for s in doc["sources"]:
        recs = store.records(s["id"])
        total_recs += len(recs)
        total_bytes += sum(r["bytes"] for r in recs)
        for part in sorted({r["part"] for r in recs}):
            chain_problems += [f"{s['id']}/{part}: {p}" for p in check_chain(store.records(s["id"], part))]
    lines = [
        "# Harvest report",
        "",
        f"Run: {date.today().isoformat()}{' (partial run)' if partial else ''}. Generated by `python -m system.rag.harvest`.",
        "",
        f"- Sources in this run: {len(rows)}. Fetched: {len(ok)}. Failed: {len(failed)}. Not fetched (link only, withdrawn): {len(skipped)}.",
        f"- New versions this run: {sum(r[2] for r in rows)}.",
        f"- Stored in total: {total_recs} versions, {total_bytes / 1e6:.1f} MB of raw files (not in git).",
        f"- Version chain problems: {len(chain_problems)}.",
        "",
    ]
    if failed:
        lines += ["## Failed", "", "| id | reason |", "|---|---|"]
        lines += [f"| {s['id']} | {msg.replace('|', '/')} |" for s, _, _, msg in failed]
        lines.append("")
    if chain_problems:
        lines += ["## Version chain problems", ""] + [f"- {p}" for p in chain_problems] + [""]
    lines += ["## Fetched", "", "| id | new | stored |", "|---|---|---|"]
    lines += [f"| {s['id']} | {n} | {msg} |" for s, _, n, msg in ok]
    lines += ["", "## Not fetched", "", "| id | mode | reason |", "|---|---|---|"]
    lines += [f"| {s['id']} | {s['mode']} | {msg} |" for s, _, _, msg in skipped]
    (CORPUS_DIR / "harvest-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="source ids to fetch")
    ap.add_argument("--priority", type=int, help="fetch sources with this priority or higher (1 is highest)")
    ap.add_argument("--no-report", action="store_true")
    a = ap.parse_args(argv)
    return run(a.only, a.priority, report=not a.no_report)


if __name__ == "__main__":
    sys.exit(main())
