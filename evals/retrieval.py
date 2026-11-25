"""Retrieval eval on the golden set, through the server's own search path (corpus/OVERNIGHT-PLAN.md, S6).

    python evals/retrieval.py --run E1-baseline --schema corpus_next --split dev
    python evals/retrieval.py --run E1-baseline --schema corpus_next --split holdout   # once, at the end
    python evals/retrieval.py --compare E1-baseline E2-hybrid                          # McNemar on Recall@5

Per question: the question is embedded (Titan V2), the nearest chunks are fetched from the chosen schema,
one per section (pgsearch.candidates: what the server re-ranks), then re-ranked (Amazon Rerank) to the top 5,
with the server's relevance floor. Rows go to evals/results/<run>.jsonl (expected sections, the candidate
section keys in order, the top 5, scores, latency), the summary to evals/results/<run>.summary.json and one line to
evals/results/runs.jsonl. Cost lines go to evals/results/cost.jsonl. Rows can be re-scored with no new calls.

Settings that change the search (environment, as on the server): RAG_TOP_K, RAG_RERANK, RAG_MIN_SCORE,
RAG_RERANK_MODEL. Hybrid and other experiments add their own switches; each run records its full config.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))
import metrics as M  # noqa: E402

RESULTS = ROOT / "evals" / "results"
GOLDEN = ROOT / "evals" / "golden" / "questions.jsonl"
TITAN_USD_PER_1K = 0.0001     # London, checked 20 Nov 2026 (system/rag/embed.py)
KEEP = int(os.environ.get("EVAL_KEEP", "5"))  # re-ranked passages kept per search (same re-rank cost); 20 for recall@10/20 and pooling
RERANK_USD_PER_QUERY = 0.001  # Amazon Rerank, about $1 per 1,000 queries of up to 100 documents (ADR 0013; verify)


def reader_url() -> str:
    url = os.environ.get("CORPUS_READER_URL")
    if url:
        return url
    import boto3

    return boto3.client("ssm", region_name="eu-west-2").get_parameter(
        Name="/builders-lab/prod/secrets/corpus_reader_url", WithDecryption=True)["Parameter"]["Value"]


def load_questions(split: str, path: Path = GOLDEN) -> list[dict]:
    qs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [q for q in qs if split == "all" or q.get("split", "dev") == split]


def config(schema: str, search) -> dict:
    c = {k: v for k, v in search.cfg().items() if k != "url"}
    c["schema"] = schema
    c["hybrid"] = os.environ.get("RAG_HYBRID", "0")
    c["rewrite"] = os.environ.get("EVAL_REWRITE", "0")
    c["queries_from"] = os.environ.get("EVAL_QUERIES_FROM")
    c["fuse"] = os.environ.get("EVAL_FUSE", "0")
    c["rerank_with"] = os.environ.get("EVAL_RERANK_WITH", "question")
    c["lanes"] = os.environ.get("EVAL_LANES", "0")
    c["per_lane"] = int(os.environ.get("EVAL_PER_LANE", "2"))
    c["keep"] = KEEP
    c["golden_sha"] = hashlib.sha256(GOLDEN.read_bytes()).hexdigest()[:12] if GOLDEN.exists() else None
    return c


def loaded_sources(url: str, schema: str) -> set[str]:
    import psycopg

    with psycopg.connect(url, connect_timeout=5) as conn:
        return set(conn.execute(f"SELECT sources FROM {schema}.stats LIMIT 1").fetchone()[0])


def in_corpus(expected: list[str], loaded: set[str]) -> bool:
    """Every expected section's source is loaded in the schema: a miss is then the search's fault, not a gap."""
    return bool(expected) and all(e.split(":")[0] in loaded for e in expected)


def apply_floor(reranked: list, floor: float) -> tuple[list, list, list]:
    """The passages the server would return: re-ranked top 5 minus those under the relevance floor."""
    kept = [r for r in reranked if r[1] is None or r[1] >= floor]
    return [r[0] for r in kept], [r[1] for r in kept], [r[2] for r in kept]


def pooled(rows: list[dict], path: Path = GOLDEN) -> dict:
    """Recall with the pooled labels: expected sections plus sections the pool judge graded as also answering
    (golden questions.jsonl "also_acceptable", dev only). Strict numbers stay the headline next to these."""
    acc = {q["id"]: q.get("also_acceptable") or [] for q in map(json.loads, path.read_text(encoding="utf-8").splitlines())}         if path.exists() else {}
    scored = [r for r in rows if r.get("expected")]
    if not scored:
        return {"questions": 0}
    ext = lambda r: r["expected"] + acc.get(r["id"], [])  # noqa: E731
    mean = lambda f: round(sum(f(r) for r in scored) / len(scored), 4)  # noqa: E731
    return {"questions": len(scored), "with_acceptable": sum(1 for r in scored if acc.get(r["id"])),
            "recall@50": mean(lambda r: M.recall_at(ext(r), r["candidates"], 50)),
            "recall@5": mean(lambda r: M.recall_at(ext(r), r["top5"], 5)),
            **({f"recall@{k}": mean(lambda r, k=k: M.recall_at(ext(r), r["top5"], k)) for k in (10, 20) if KEEP >= k}),
            "mrr@5": mean(lambda r: M.reciprocal_rank(ext(r), r["top5"]))}


def rescore(name: str, split: str, floor: float) -> dict:
    """Recompute top 5 and metrics for another relevance floor from saved rows (no new calls)."""
    rows = [json.loads(l) for l in (RESULTS / f"{name}-{split}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        r["top5"], r["scores"], r["top5_chunks"] = apply_floor(r["reranked"], floor)
    empty = sum(1 for r in rows if not r["top5"])
    by_kind_empty: dict[str, list] = {}
    for r in rows:
        by_kind_empty.setdefault(r.get("kind", "?"), []).append(not r["top5"])
    return {"run": name, "floor": floor, "empty_top5": empty, "rows": len(rows),
            "empty_by_kind": {k: round(sum(v) / len(v), 3) for k, v in sorted(by_kind_empty.items())},
            **M.summarise(rows), "in_corpus": M.summarise([r for r in rows if r.get("in_corpus")]),
            "pooled": pooled(rows), "pooled_in_corpus": pooled([r for r in rows if r.get("in_corpus")])}


# E3: the plugin's regulations specialist writes the search queries (ADR 0006: the model runs in Claude, not on
# our server). Proposed instruction for plugin/agents/regulations.md, simulated with the eval answer model.
REWRITE_PROMPT = """You are the regulations specialist of a UK builders' assistant. Before searching the regulations
corpus (UK building law and HSE / GOV.UK guidance), write exactly two search queries for this builder's question:
1. the question restated in plain, complete words, keeping its facts (who, what work, where);
2. the same need in the words the law and official guidance use (for example "licensable work with asbestos",
   "notifiable non-licensed work", "duty to manage", "competent person scheme", "construction phase plan").
Do not answer the question. Reply with a JSON list of two strings only.

Question: """
REWRITE_MODEL = os.environ.get("EVAL_REWRITE_MODEL", "eu.anthropic.claude-haiku-4-5-20251001-v1:0")
_rw_client = None


def rewrite(question: str) -> tuple[list[str], int, int]:
    global _rw_client
    import anthropic

    _rw_client = _rw_client or anthropic.AnthropicBedrock(aws_region="eu-west-2")
    r = _rw_client.messages.create(model=REWRITE_MODEL, max_tokens=400,
                                   messages=[{"role": "user", "content": REWRITE_PROMPT + question}])
    text = "".join(b.text for b in r.content if b.type == "text")
    try:
        qs = [x for x in json.loads(text[text.index("["):text.rindex("]") + 1]) if isinstance(x, str) and x.strip()][:2]
    except ValueError:
        qs = []
    return (qs or [question]), r.usage.input_tokens, r.usage.output_tokens


def search_one(query: str, search, url: str, top_k: int, rerank: bool) -> tuple[list[str], list]:
    rows = search.candidates(query, url=url, n=top_k)
    cands = [M.section_key(r["source_id"], r["section_id"]) for r in rows]
    reranked = [[cands[i], None, rows[i]["id"]] for i in range(min(5, len(rows)))]
    if rerank and rows:
        order = search.rerank(query, [r["embed_text"] for r in rows], KEEP)
        reranked = [[cands[i], round(s, 6), rows[i]["id"]] for i, s in order]
    return cands, reranked


def merge(results: list[tuple[list[str], list]]) -> tuple[list[str], list]:
    """Several searches: candidates interleaved (first, then second ...), re-ranked passages by score, one per section."""
    cands, seen = [], set()
    for i in range(max(len(c) for c, _ in results)):
        for c, _ in results:
            if i < len(c) and c[i] not in seen:
                seen.add(c[i])
                cands.append(c[i])
    best: dict[str, list] = {}
    for _, rr in results:
        for x in rr:
            if x[0] not in best or (x[1] or 0) > (best[x[0]][1] or 0):
                best[x[0]] = x
    return cands, sorted(best.values(), key=lambda x: -(x[1] or 0))[:KEEP]


def fused_search(question: str, extra: list[str], search, url: str, top_k: int, rerank: bool) -> tuple[list[str], list]:
    """E5: one search call with extra queries from the agent: candidates of the question and of each extra query,
    fused by RRF, one per section, the first top_k re-ranked against the builder's ORIGINAL question."""
    lists = [search.candidates(x, url=url, n=top_k) for x in [question] + extra]
    rows = search.one_per_section(search.rrf(*lists))[:top_k]
    cands = [M.section_key(r["source_id"], r["section_id"]) for r in rows]
    reranked = [[cands[i], None, rows[i]["id"]] for i in range(min(5, len(rows)))]
    if rerank and rows:
        rq = question
        if os.environ.get("EVAL_RERANK_WITH") == "all" and extra:  # E6: the agent's words help the re-rank too
            rq = question + "\n" + "\n".join(extra)
        order = search.rerank(rq, [r["embed_text"] for r in rows], KEEP)
        reranked = [[cands[i], round(s, 6), rows[i]["id"]] for i, s in order]
    return cands, reranked


_saved_queries: dict[str, list[str]] = {}


def saved_queries(run: str, qid: str) -> list[str] | None:
    """Reuse the queries an earlier rewrite run wrote, so a new search setting costs no model calls."""
    if run not in _saved_queries:
        path = RESULTS / f"{run}-dev.jsonl"
        _saved_queries[run] = {r["id"]: r.get("queries") for r in map(json.loads, path.read_text(encoding="utf-8").splitlines())}             if path.exists() else {}
    return _saved_queries[run].get(qid)


def label_lanes(url: str, schema: str, search) -> dict:
    """Which lane each section key belongs to, from the chunks' legal weight: {"source:section": {lanes}}."""
    import psycopg

    lane_of = {w: lane for lane, ws in search.LANES.items() for w in ws}
    out: dict[str, set] = {}
    with psycopg.connect(url, connect_timeout=5) as conn:
        for src, sec, w in conn.execute(f"SELECT DISTINCT source_id, section_id, legal_weight FROM {schema}.chunks"):
            if w in lane_of:
                out.setdefault(M.section_key(src, sec), set()).add(lane_of[w])
    return out


def lanes_of(expected: str, keys: dict) -> list[str]:
    """The lanes of an expected section: those of every chunk section it touches (a parent or a part)."""
    src = expected.split(":")[0]
    hit = keys.get(expected)
    if hit is None:
        hit = set().union(*([v for k, v in keys.items() if k.startswith(src + ":") and M.touches(expected, k)] or [set()]))
    return sorted(hit)


def lanes_search(query: str, search, url: str, top_k: int, rerank: bool) -> dict:
    """ADR 0016 lanes: one embedding, then per lane its own candidates and its own re-rank (top 5 kept, so the
    lane size can be tuned on saved rows)."""
    vec = search.embed_question(query)
    out = {}
    for lane, weights in search.LANES.items():
        rows = search.candidates(query, url=url, n=top_k, weights=weights, vector=vec)
        cands = [M.section_key(r["source_id"], r["section_id"]) for r in rows]
        rr = [[cands[i], None, rows[i]["id"]] for i in range(min(5, len(rows)))]
        if rerank and rows:
            rr = [[cands[i], round(s, 6), rows[i]["id"]] for i, s in search.rerank(query, [r["embed_text"] for r in rows], 5)]
        out[lane] = {"candidates": cands, "reranked": rr}
    return out


def lane_scores(rows: list[dict], per_lane: int) -> dict:
    """Per lane: of the questions with a label in that lane, how often the lane's own top per_lane (and top 50)
    holds one of them. "any": some label found in its own lane's short list. "every_lane": every lane that has
    labels found one. Labels in no lane (source not loaded) are left out."""
    scored = [r for r in rows if r.get("expected") and r.get("lanes")]
    out = {"questions": len(scored), "per_lane": per_lane}
    for lane in ("law", "approved-document", "acop", "guidance"):
        qs = [r for r in scored if any(lane in r["expected_lanes"].get(e, []) for e in r["expected"])]
        exp = lambda r: [e for e in r["expected"] if lane in r["expected_lanes"].get(e, [])]  # noqa: E731
        top = lambda r: [x[0] for x in r["lanes"][lane]["reranked"]]  # noqa: E731
        n = len(qs) or 1
        out[lane] = {"questions": len(qs),
                     f"recall@{per_lane}": round(sum(M.recall_at(exp(r), top(r), per_lane) for r in qs) / n, 4),
                     "recall@5": round(sum(M.recall_at(exp(r), top(r), 5) for r in qs) / n, 4),
                     "recall@50": round(sum(M.recall_at(exp(r), r["lanes"][lane]["candidates"], 50) for r in qs) / n, 4)}

    def found(r, lane):
        exp = [e for e in r["expected"] if lane in r["expected_lanes"].get(e, [])]
        return M.recall_at(exp, [x[0] for x in r["lanes"][lane]["reranked"]], per_lane) == 1.0
    has = lambda r: [l for l in r["lanes"] if any(l in r["expected_lanes"].get(e, []) for e in r["expected"])]  # noqa: E731
    n = len(scored) or 1
    out["any"] = round(sum(any(found(r, l) for l in has(r)) for r in scored) / n, 4)
    out["every_lane"] = round(sum(bool(has(r)) and all(found(r, l) for l in has(r)) for r in scored) / n, 4)
    return out


def run_one(q: dict, search, url: str, top_k: int, rerank: bool, min_score: float) -> dict:
    t0 = time.time()
    if os.environ.get("EVAL_LANES") == "1":
        per = int(os.environ.get("EVAL_PER_LANE", "2"))
        lanes = lanes_search(q["question"], search, url, top_k, rerank)
        cands = [c for i in range(top_k) for v in lanes.values() if i < len(v["candidates"]) for c in [v["candidates"][i]]]
        top = [x for v in lanes.values() for x in v["reranked"][:per]]
        return {"id": q["id"], "role": q.get("role"), "kind": q.get("kind"), "multi_rule": q.get("multi_rule", False),
                "question": q["question"], "expected": q.get("expected_sections", []), "candidates": cands,
                "queries": [q["question"]], "rewrite_tokens": [0, 0], "lanes": lanes, "reranked": top,
                "top5": [x[0] for x in top], "top5_chunks": [x[2] for x in top], "scores": [x[1] for x in top],
                "latency_ms": int((time.time() - t0) * 1000)}
    queries, rw_in, rw_out = ([q["question"]], 0, 0)
    reuse = os.environ.get("EVAL_QUERIES_FROM")
    if reuse and saved_queries(reuse, q["id"]):
        queries = saved_queries(reuse, q["id"])
    elif os.environ.get("EVAL_REWRITE") == "1":
        queries, rw_in, rw_out = rewrite(q["question"])
    if os.environ.get("EVAL_FUSE") == "1":
        extra = [x for x in queries if x != q["question"]]
        cands, reranked = fused_search(q["question"], extra, search, url, top_k, rerank)
        queries = [q["question"]] + extra
    else:
        cands, reranked = merge([search_one(x, search, url, top_k, rerank) for x in queries])
    top, scores, chunks = apply_floor(reranked, min_score)
    return {"id": q["id"], "role": q.get("role"), "kind": q.get("kind"), "multi_rule": q.get("multi_rule", False),
            "question": q["question"], "expected": q.get("expected_sections", []), "candidates": cands,
            "queries": queries, "rewrite_tokens": [rw_in, rw_out], "reranked": reranked, "top5": top, "top5_chunks": chunks, "scores": scores, "latency_ms": int((time.time() - t0) * 1000)}


def log_cost(run: str, n_questions: int, chars: int, reranks: int) -> float:
    titan = chars / 4 / 1000 * TITAN_USD_PER_1K
    rr = reranks * RERANK_USD_PER_QUERY
    with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
        now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"
        f.write(json.dumps({"time": now, "run": run, "model": "amazon.titan-embed-text-v2:0", "unit": "input tokens (est.)",
                            "in": chars // 4, "out": 0, "cost_usd": round(titan, 4)}) + "\n")
        f.write(json.dumps({"time": now, "run": run, "model": "amazon.rerank-v1:0", "unit": "rerank queries",
                            "in": reranks, "out": 0, "cost_usd": round(rr, 4)}) + "\n")
    return titan + rr


def run(name: str, schema: str, split: str, pace: float, limit: int | None) -> dict:
    os.environ["RAG_SCHEMA"] = schema
    from system.rag import pgsearch as P

    url = reader_url()
    cfg = config(schema, P)
    loaded = loaded_sources(url, P._schema(schema))
    keys = label_lanes(url, P._schema(schema), P) if cfg["lanes"] == "1" else {}
    qs = load_questions(split)
    qs = [q for q in qs if q.get("expected_sections")] + [q for q in qs if not q.get("expected_sections")]
    qs = qs[:limit] if limit else qs
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / f"{name}-{split}.jsonl"
    done = {}
    if out_path.exists():  # resume a stopped run
        done = {r["id"]: r for r in (json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip())}
    rows, chars, reranks, rw_tokens = [], 0, 0, [0, 0]
    with open(out_path, "a", encoding="utf-8") as f:
        for i, q in enumerate(qs, 1):
            if q["id"] in done:
                done[q["id"]]["in_corpus"] = in_corpus(done[q["id"]]["expected"], loaded)
                if keys:
                    done[q["id"]]["expected_lanes"] = {e: lanes_of(e, keys) for e in done[q["id"]]["expected"]}
                rows.append(done[q["id"]])
                continue
            for attempt in range(4):
                try:
                    r = run_one(q, P, url, cfg["top_k"], cfg["rerank"], cfg["min_score"])
                    break
                except Exception as e:  # throttling: wait and retry
                    if attempt == 3:
                        raise
                    time.sleep(10 * (attempt + 1))
                    print(f"  retry {q['id']}: {type(e).__name__}", flush=True)
            r["in_corpus"] = in_corpus(r["expected"], loaded)
            if keys:
                r["expected_lanes"] = {e: lanes_of(e, keys) for e in r["expected"]}
            rows.append(r)
            chars += sum(len(x) for x in r["queries"])
            reranks += (len(r["lanes"]) if r.get("lanes") else 1 if os.environ.get("EVAL_FUSE") == "1"
                        else len(r["queries"])) if cfg["rerank"] else 0
            rw_tokens[0] += r["rewrite_tokens"][0]
            rw_tokens[1] += r["rewrite_tokens"][1]
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(qs)}", flush=True)
            time.sleep(pace)
    cost = log_cost(f"{name}-{split}", len(qs), chars, reranks)
    if rw_tokens[0]:
        rw_cost = rw_tokens[0] / 1e6 * 1.10 + rw_tokens[1] / 1e6 * 5.50  # Haiku 4.5 estimate, verify
        cost += rw_cost
        with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
                                "run": f"{name}-{split}", "model": REWRITE_MODEL, "unit": "tokens", "in": rw_tokens[0],
                                "out": rw_tokens[1], "cost_usd": round(rw_cost, 4), "price_note": "estimate, verify"}) + "\n")
    summary = {"run": name, "split": split, "time": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
               "config": cfg, "cost_usd_this_call": round(cost, 4), **M.summarise(rows),
               "in_corpus": M.summarise([r for r in rows if r.get("in_corpus")])}
    if cfg["lanes"] == "1":
        summary["lanes"] = lane_scores(rows, cfg["per_lane"])
        summary["note"] = ("lanes run: top-level recall@5 counts only the first 5 of the lanes' lists together; "
                           "use lanes.any and the per-lane numbers")
    (RESULTS / f"{name}-{split}.summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    with open(RESULTS / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({k: summary[k] for k in ("run", "split", "time", "questions", "recall@50", "recall@5", "mrr@5", "ndcg@5")
                            if k in summary}) + "\n")
    return summary


def compare(a: str, b: str, split: str = "dev") -> dict:
    load = lambda n: {r["id"]: r for r in (json.loads(l) for l in (RESULTS / f"{n}-{split}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}  # noqa: E731
    ra, rb = load(a), load(b)
    ids = [i for i in ra if i in rb and ra[i]["expected"]]
    hit = lambda r, k: M.recall_at(r["expected"], r["top5"] if k == 5 else r["candidates"], k) == 1.0  # noqa: E731
    return {"questions": len(ids), "recall@5": M.mcnemar([hit(ra[i], 5) for i in ids], [hit(rb[i], 5) for i in ids]),
            "recall@50": M.mcnemar([hit(ra[i], 50) for i in ids], [hit(rb[i], 50) for i in ids])}


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run")
    ap.add_argument("--schema", default="corpus_next")
    ap.add_argument("--split", default="dev", choices=["dev", "holdout", "all"])
    ap.add_argument("--pace", type=float, default=3.2, help="seconds between questions (re-rank quota)")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--compare", nargs=2)
    ap.add_argument("--rescore", help="run name: recompute metrics for --floor from saved rows")
    ap.add_argument("--floor", type=float, default=0.05)
    a = ap.parse_args(argv)
    if a.rescore:
        print(json.dumps(rescore(a.rescore, a.split, a.floor), indent=1))
        return 0
    if a.compare:
        print(json.dumps(compare(*a.compare, split=a.split), indent=1))
        return 0
    s = run(a.run, a.schema, a.split, a.pace, a.limit)
    print(json.dumps({k: v for k, v in s.items() if k != "config"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
