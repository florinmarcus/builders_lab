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
            **M.summarise(rows), "in_corpus": M.summarise([r for r in rows if r.get("in_corpus")])}


def run_one(q: dict, search, url: str, top_k: int, rerank: bool, min_score: float) -> dict:
    t0 = time.time()
    rows = search.candidates(q["question"], url=url, n=top_k)
    cands = [M.section_key(r["source_id"], r["section_id"]) for r in rows]
    reranked = [[cands[i], None, rows[i]["id"]] for i in range(min(5, len(rows)))]
    if rerank and rows:
        order = search.rerank(q["question"], [r["embed_text"] for r in rows], 5)
        reranked = [[cands[i], round(s, 6), rows[i]["id"]] for i, s in order]
    top, scores, chunks = apply_floor(reranked, min_score)
    return {"id": q["id"], "role": q.get("role"), "kind": q.get("kind"), "multi_rule": q.get("multi_rule", False),
            "question": q["question"], "expected": q.get("expected_sections", []), "candidates": cands,
            "reranked": reranked, "top5": top, "top5_chunks": chunks, "scores": scores, "latency_ms": int((time.time() - t0) * 1000)}


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
    qs = load_questions(split)
    qs = [q for q in qs if q.get("expected_sections")] + [q for q in qs if not q.get("expected_sections")]
    qs = qs[:limit] if limit else qs
    RESULTS.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS / f"{name}-{split}.jsonl"
    done = {}
    if out_path.exists():  # resume a stopped run
        done = {r["id"]: r for r in (json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip())}
    rows, chars, reranks = [], 0, 0
    with open(out_path, "a", encoding="utf-8") as f:
        for i, q in enumerate(qs, 1):
            if q["id"] in done:
                done[q["id"]]["in_corpus"] = in_corpus(done[q["id"]]["expected"], loaded)
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
            rows.append(r)
            chars += len(q["question"])
            reranks += 1 if cfg["rerank"] else 0
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(qs)}", flush=True)
            time.sleep(pace)
    cost = log_cost(f"{name}-{split}", len(qs), chars, reranks)
    summary = {"run": name, "split": split, "time": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
               "config": cfg, "cost_usd_this_call": round(cost, 4), **M.summarise(rows),
               "in_corpus": M.summarise([r for r in rows if r.get("in_corpus")])}
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
