"""Could free government MCP servers replace our own index for legislation and GOV.UK pages? (22 Nov 2026)

Live check of the hosted servers named in `research/reports/UK legislation MCP servers.md`, on the golden dev
questions whose expected sections are in legislation or on GOV.UK. Our own search is scored on the same
questions and the same labels.

    python -m evals.external_mcp fetch --system lex --mode raw        # live calls, saved to evals/external/runs/
    python -m evals.external_mcp fetch --system govuk --mode keyword
    python -m evals.external_mcp score                                # tables from saved runs, offline

Systems:
- lex      i.AI Lex (government, experimental): search_for_legislation_sections, section level.
- uklegal  paulieb89/uk-legal-mcp (community): legislation_search with full text, law level.
- govuk    paulieb89/govuk-mcp (community): govuk_search, the official GOV.UK Search API, page level.
- ours     our index: L1 (hybrid + rerank, the live setup) and V0 (vector only) rows for raw questions; X1/X2 for
           the keyword queries (evals/retrieval.py with EVAL_QUERIES_FROM=X0-keyword-queries).

Modes: raw (the builder's question as written) and keyword (one search query written by Sonnet for each
question, `evals/external/keyword-queries.jsonl`, the same for every system).

Scoring, per question, only on the expected sections that belong to the subset:
- LEG (legislation): law@k = one of the expected laws in the top k; prov@k = one of the expected provisions
  (regulation 12, section 108, schedule 1 ...; subsections count as their provision) in the top k.
- GOV (pages fetched from GOV.UK): page@k = one of the expected GOV.UK documents in the top k.
Holdout questions are never sent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden" / "questions.jsonl"
OUT = ROOT / "evals" / "external"
RESULTS = ROOT / "evals" / "results"
UA = "builders-lab-eval/0.1 (retrieval research)"

SERVERS = {
    "lex": ("https://lex.lab.i.ai.gov.uk/mcp", "search_for_legislation_sections",
            lambda q, k: {"query": q, "size": k, "include_text": False}),
    "uklegal": ("https://uk-legal-mcp.fly.dev/mcp", "legislation_search",
                lambda q, k: {"query": q, "limit": k, "fulltext": True}),
    "govuk": ("https://govuk-mcp.fly.dev/mcp", "govuk_search", lambda q, k: {"query": q, "count": k}),
}
PACE = {"lex": 1.2, "uklegal": 1.1, "govuk": 0.5}  # Lex allows 60 a minute; cyanheads-style shared hosts 1 a second
NOT_ENGLAND = {"ssi", "asp", "nisr", "nia", "apni", "nisi", "wsi", "asc", "anaw", "mwa", "aosp", "aip"}
PROVISION_KINDS = {"regulation", "section", "article", "schedule", "rule", "paragraph"}


# ---------------------------------------------------------------- ids and mapping

def law_path(path: str) -> str:
    """'ukpga/1996/53/part/II' -> 'ukpga/1996/53'; also strips a legislation.gov.uk address."""
    path = re.sub(r"^https?://(www\.)?legislation\.gov\.uk/(id/)?", "", path.strip("/"))
    parts = path.split("/")
    return "/".join(parts[:3])


def our_provision(section_id: str) -> tuple[str, str] | None:
    """'regulation-12-6' -> ('regulation', '12'); 'schedule-1-K4' -> ('schedule', '1'); other ids -> None."""
    m = re.match(r"([a-z]+)-([0-9]+[A-Z]*)", section_id)
    if not m or m.group(1) not in PROVISION_KINDS:
        return None
    return m.group(1), m.group(2)


def lex_provision(uri: str) -> tuple[str, tuple[str, str] | None]:
    """'http://www.legislation.gov.uk/id/uksi/2010/2214/regulation/12/6' -> ('uksi/2010/2214', ('regulation', '12'))."""
    path = re.sub(r"^https?://(www\.)?legislation\.gov\.uk/(id/)?", "", uri.strip("/"))
    parts = path.split("/")
    law, rest = "/".join(parts[:3]), parts[3:]
    if len(rest) >= 2 and rest[0] in PROVISION_KINDS:
        return law, (rest[0], rest[1])
    return law, None


def source_maps(sources: list[dict]) -> tuple[dict, dict]:
    """source id -> law path (legislation) and source id -> GOV.UK base path (pages fetched from GOV.UK)."""
    leg, gov = {}, {}
    for s in sources:
        f = s.get("fetch") or {}
        if f.get("method") == "legislation" and f.get("path"):
            leg[s["id"]] = law_path(f["path"])
        elif f.get("method") == "govuk" and f.get("page"):
            gov[s["id"]] = "/" + f["page"].strip("/")
    return leg, gov


def gold(q: dict, leg: dict, gov: dict) -> dict:
    """The expected laws, provisions and GOV.UK pages of a question."""
    laws, provs, pages = set(), set(), set()
    for e in q.get("expected_sections") or []:
        sid, sec = e.split(":", 1)
        if sid in leg:
            laws.add(leg[sid])
            p = our_provision(sec)
            if p:
                provs.add((leg[sid], *p))
        elif sid in gov:
            pages.add(gov[sid])
    return {"laws": laws, "provs": provs, "pages": pages}


def page_match(link: str, page: str) -> bool:
    """A GOV.UK result is the expected document if it is that page or one of its parts or attachments."""
    link = "/" + re.sub(r"^https?://www\.gov\.uk", "", link).strip("/")
    return link == page or link.startswith(page + "/")


# ---------------------------------------------------------------- MCP over HTTP (streamable, JSON or SSE)

def _post(url: str, payload: dict, sid: str | None, timeout: float = 60) -> tuple[dict | None, str | None]:
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "User-Agent": UA}
    if sid:
        h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(url, json.dumps(payload).encode(), h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        sid = r.headers.get("Mcp-Session-Id") or sid
        body = r.read().decode("utf-8", "replace")
    return parse_body(body), sid


def parse_body(body: str) -> dict | None:
    """A JSON-RPC reply sent as plain JSON or as server-sent events (the last data line)."""
    body = body.strip()
    if not body:
        return None
    if body.startswith("{"):
        return json.loads(body)
    data = [l[5:].strip() for l in body.splitlines() if l.startswith("data:")]
    return json.loads(data[-1]) if data else None


class Client:
    def __init__(self, url: str):
        self.url, self.n = url, 0
        r, self.sid = _post(url, {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "builders-lab-eval", "version": "0.1"}}}, None)
        self.server = (r or {}).get("result", {}).get("serverInfo", {})
        _post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, self.sid)

    def call(self, tool: str, args: dict) -> dict:
        self.n += 1
        r, _ = _post(self.url, {"jsonrpc": "2.0", "id": self.n, "method": "tools/call",
                                "params": {"name": tool, "arguments": args}}, self.sid)
        if r is None or "error" in r:
            raise RuntimeError(f"{tool}: {(r or {}).get('error')}")
        return r["result"]

    def tools(self) -> list[str]:
        self.n += 1
        r, _ = _post(self.url, {"jsonrpc": "2.0", "id": self.n, "method": "tools/list", "params": {}}, self.sid)
        return [t["name"] for t in r["result"]["tools"]]


def payload(result: dict) -> dict | list:
    """The tool's JSON answer: structuredContent if given, else the first text block parsed as JSON."""
    if result.get("structuredContent"):
        return result["structuredContent"]
    for c in result.get("content", []):
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except json.JSONDecodeError:
                return {"text": c["text"]}
    return {}


def normalise(system: str, data) -> list[dict]:
    """Each result as {law, prov, page, title, type}, in rank order."""
    out = []
    if system == "lex":
        rows = data.get("result", data) if isinstance(data, dict) else data
        for r in rows or []:
            law, prov = lex_provision(r.get("uri") or r.get("id") or "")
            out.append({"law": law, "prov": list(prov) if prov else None, "title": r.get("title"),
                        "type": r.get("legislation_type") or law.split("/")[0]})
    elif system == "uklegal":
        for r in (data.get("results") if isinstance(data, dict) else data) or []:
            url = r.get("url") or r.get("uri") or r.get("id") or ""
            law = law_path(url) if "legislation.gov.uk" in url else "/".join(
                str(r.get(k, "")) for k in ("type", "year", "number"))
            out.append({"law": law, "prov": None, "title": r.get("title"), "type": law.split("/")[0]})
    elif system == "govuk":
        for r in (data.get("results") if isinstance(data, dict) else data) or []:
            out.append({"page": r.get("link") or r.get("url"), "title": r.get("title"), "type": r.get("format")})
    return out


# ---------------------------------------------------------------- data

def load_sources() -> list[dict]:
    import yaml

    return yaml.safe_load((ROOT / "corpus" / "sources.yaml").read_text(encoding="utf-8"))["sources"]


def dev_questions() -> list[dict]:
    qs = [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [q for q in qs if q.get("split") == "dev" and q.get("expected_sections")]


def keyword_queries() -> dict[str, str]:
    p = OUT / "keyword-queries.jsonl"
    return {r["id"]: r["query"] for r in map(json.loads, p.read_text(encoding="utf-8").splitlines()) if r} if p.exists() else {}


def run_path(system: str, mode: str) -> Path:
    return OUT / "runs" / f"{system}-{mode}.jsonl"


def load_run(system: str, mode: str) -> dict[str, dict]:
    p = run_path(system, mode)
    if not p.exists():
        return {}
    return {r["id"]: r for r in map(json.loads, p.read_text(encoding="utf-8").splitlines()) if r}


# ---------------------------------------------------------------- fetch

def fetch(system: str, mode: str, k: int = 10, limit: int | None = None) -> int:
    leg, gov = source_maps(load_sources())
    need = "laws" if system in ("lex", "uklegal") else "pages"
    qs = [q for q in dev_questions() if gold(q, leg, gov)[need]]
    kw = keyword_queries()
    done = load_run(system, mode)
    url, tool, args = SERVERS[system]
    client = Client(url)
    path = run_path(system, mode)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as f:
        for q in qs[:limit]:
            if q["id"] in done and not done[q["id"]].get("error"):
                continue
            text = q["question"] if mode == "raw" else kw.get(q["id"])
            if not text:
                continue
            t0, err, res = time.time(), None, []
            for attempt in range(3):
                try:
                    res = normalise(system, payload(client.call(tool, args(text, k))))
                    err = None
                    break
                except Exception as e:  # network, rate limit, server error: recorded, retried
                    err = f"{type(e).__name__}: {e}"[:300]
                    time.sleep(5 * (attempt + 1))
                    try:
                        client = Client(url)
                    except Exception:
                        pass
            f.write(json.dumps({"id": q["id"], "query": text, "latency_ms": int((time.time() - t0) * 1000),
                                "error": err, "results": res}, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
            time.sleep(PACE[system])
    print(f"{system} {mode}: {n} questions fetched -> {path.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------- score

def ours_rows(run: str) -> dict[str, dict]:
    p = RESULTS / f"{run}-dev.jsonl"
    return {r["id"]: r for r in map(json.loads, p.read_text(encoding="utf-8").splitlines())} if p.exists() else {}


def ours_ranked(row: dict, k: int) -> list[str]:
    """Our ranked section keys: the re-ranked top 5 first (what the user gets), then the remaining candidates."""
    top = list(row.get("top5") or [])
    rest = [c for c in row.get("candidates") or [] if c not in top]
    return (top + rest)[:k]


def score_question(q: dict, g: dict, results: list[dict], leg: dict, gov: dict, k: int) -> dict:
    """Hits for one question from normalised results (external) at rank k."""
    top = results[:k]
    laws = [r.get("law") for r in top if r.get("law")]
    provs = [(r["law"], *r["prov"]) for r in top if r.get("law") and r.get("prov")]
    pages = [r.get("page") for r in top if r.get("page")]
    out = {}
    if g["laws"]:
        out["law"] = any(l in g["laws"] for l in laws)
        if g["provs"]:
            out["prov"] = any(p in g["provs"] for p in provs)
        out["not_england"] = sum(1 for r in top if (r.get("type") or "") in NOT_ENGLAND)
        out["outside_corpus"] = sum(1 for l in laws if l not in set(leg.values()))
    if g["pages"]:
        out["page"] = any(page_match(p, pg) for p in pages for pg in g["pages"])
    return out


def ours_as_results(keys: list[str], leg: dict, gov: dict) -> list[dict]:
    """Our section keys in the same shape as external results, so one scorer serves both."""
    out = []
    for key in keys:
        sid, sec = key.split(":", 1)
        if sid in leg:
            p = our_provision(sec.split("#", 1)[0])
            out.append({"law": leg[sid], "prov": list(p) if p else None, "type": leg[sid].split("/")[0]})
        elif sid in gov:
            out.append({"page": gov[sid]})
        else:
            out.append({"other": sid})
    return out


def score(k_list=(5, 10)) -> dict:
    leg, gov = source_maps(load_sources())
    qs = dev_questions()
    G = {q["id"]: gold(q, leg, gov) for q in qs}
    systems = {f"{s}-{m}": load_run(s, m) for s in SERVERS for m in ("raw", "keyword")}
    ours = {"ours-L1-raw": ours_rows("L1-full-hybrid"), "ours-V0-raw": ours_rows("V0-vector-only"),
            "ours-X1-keyword": ours_rows("X1-keyword-hybrid"), "ours-X2-keyword": ours_rows("X2-keyword-vector")}
    table = {}
    for name, rows in {**systems, **ours}.items():
        if not rows:
            continue
        for k in k_list:
            agg: dict[str, list] = {}
            lat, errs = [], 0
            for q in qs:
                r = rows.get(q["id"])
                if r is None:
                    continue
                if name.startswith("ours"):
                    res = ours_as_results(ours_ranked(r, k), leg, gov)
                else:
                    if r.get("error"):
                        errs += 1
                    res = r.get("results") or []
                    lat.append(r.get("latency_ms", 0))
                s = score_question(q, G[q["id"]], res, leg, gov, k)
                for m, v in s.items():
                    agg.setdefault(m, []).append(v)
            row = {m: round(sum(v) / len(v), 3) for m, v in agg.items() if v}
            row["n"] = {m: len(v) for m, v in agg.items()}
            if lat and k == k_list[0]:
                lat.sort()
                row["latency_p50_ms"], row["latency_p95_ms"] = lat[len(lat) // 2], lat[int(len(lat) * 0.95) - 1]
                row["errors"] = errs
            table[f"{name}@{k}"] = row
    return table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--system", required=True, choices=list(SERVERS))
    f.add_argument("--mode", required=True, choices=["raw", "keyword"])
    f.add_argument("--limit", type=int)
    sub.add_parser("score")
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        return fetch(a.system, a.mode, limit=a.limit)
    t = score()
    out = OUT / "summary.json"
    out.write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    for name, row in t.items():
        print(name, {m: v for m, v in row.items() if m != "n"}, "n=", row.get("n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
