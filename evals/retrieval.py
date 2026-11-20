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


def run_one(q: dict, search, url: str, top_k: int, rerank: bool, min_score: float) -> dict:
    t0 = time.time()
    rows = search.candidates(q["question"], url=url, n=top_k)
    cands = [M.section_key(r["source_id"], r["section_id"]) for r in rows]
    top, scores = cands[:5], []
    if rerank and rows:
        order = search.rerank(q["question"], [r["embed_text"] for r in rows], 5)
        kept = [(i, s) for i, s in order if s >= min_score]
        top, scores = [cands[i] for i, _ in kept], [round(s, 4) for _, s in kept]
    return {"id": q["id"], "role": q.get("role"), "kind": q.get("kind"), "multi_rule": q.get("multi_rule", False),
            "question": q["question"], "expected": q.get("expected_sections", []), "candidates": cands,
            "top5": top, "scores": scores, "latency_ms": int((time.time() - t0) * 1000)}


def log_cost(run: str, n_questions: int, chars: int, reranks: int) -> float:
    titan = chars / 4 / 1000 * TITAN_USD_PER_1K
    rr = reranks * RERANK_USD_PER_QUERY
    with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
        now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
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
            rows.append(r)
            chars += len(q["question"])
            reranks += 1 if cfg["rerank"] else 0
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(qs)}", flush=True)
            time.sleep(pace)
    cost = log_cost(f"{name}-{split}", len(qs), chars, reranks)
    summary = {"run": name, "split": split, "time": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
               "config": cfg, "cost_usd_this_call": round(cost, 4), **M.summarise(rows)}
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
    a = ap.parse_args(argv)
    if a.compare:
        print(json.dumps(compare(*a.compare, split=a.split), indent=1))
        return 0
    s = run(a.run, a.schema, a.split, a.pace, a.limit)
    print(json.dumps({k: v for k, v in s.items() if k != "config"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
