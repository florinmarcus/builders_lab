"""R1: re-rank pilot. Does the re-ranker do better with other inputs, on a small sample first?

Takes B3's saved rows (mixed + agent queries), picks questions in three groups by where B3's re-ranker put the
best labelled section: good (rank 1-3), middle (4-8), bad (in the 50 candidates but not in the top 8). Rebuilds the
same 50 candidates B3 re-ranked (checked against the saved list), then re-ranks all 50 four ways:

  base         the builder's question, passage = heading path + text (what B3 and live do)
  plain        the agent's plain rewrite (saved from E3) as the query
  title        the question; passage starts with the document title, legal weight and edition date
  plain+title  both

Run:  CORPUS_READER_URL=<local> python evals/rerank_pilot.py --model amazon.rerank-v1:0 --per-group 10
Out:  evals/results/R1-rerank-pilot-<model short>.jsonl and .summary.json (labels, ranks and scores only).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))
import metrics as M  # noqa: E402
from retrieval import RESULTS, reader_url, saved_queries  # noqa: E402

B3 = RESULTS / "B3-v2-fused-k20-dev-dev.jsonl"
VARIANTS = ["base", "plain", "title", "plain+title"]
WEIGHT = {"law": "law", "statutory-guidance": "Approved Document", "approved-code": "Approved Code of Practice",
          "guidance": "guidance"}
USD_PER_CALL = {"amazon.rerank-v1:0": 0.001, "cohere.rerank-v3-5:0": 0.002}  # Bedrock pricing, per query of up to 100 docs


def best_rank(expected: list[str], keys: list[str]) -> int | None:
    """1-based rank of the first labelled section in keys, None if absent."""
    for i, k in enumerate(keys, 1):
        if k in expected:
            return i
    return None


def sample(rows: list[dict], per_group: int, seed: int) -> list[tuple[str, dict]]:
    groups: dict[str, list[dict]] = {"good": [], "middle": [], "bad": []}
    for r in rows:
        if not r["expected"]:
            continue
        rank = best_rank(r["expected"], [x[0] for x in r["reranked"]])
        if rank and rank <= 3:
            groups["good"].append(r)
        elif rank and rank <= 8:
            groups["middle"].append(r)
        elif best_rank(r["expected"], r["candidates"]):
            groups["bad"].append(r)
    rnd = random.Random(seed)
    return [(g, r) for g, rs in groups.items() for r in rnd.sample(rs, min(per_group, len(rs)))]


def header(c: dict) -> str:
    d = c.get("edition_date") or c.get("valid_from")
    return f"{c.get('source_title') or c['source_id']} ({WEIGHT.get(c.get('legal_weight'), c.get('legal_weight'))}" \
           f"{', ' + d.isoformat() if hasattr(d, 'isoformat') else ''})"


def rerank_all(model: str, query: str, texts: list[str]) -> list[tuple[int, float]]:
    import boto3

    region = os.environ.get("RAG_RERANK_REGION", "eu-central-1")
    r = boto3.client("bedrock-agent-runtime", region_name=region).rerank(
        queries=[{"type": "TEXT", "textQuery": {"text": query}}],
        sources=[{"type": "INLINE", "inlineDocumentSource": {"type": "TEXT", "textDocument": {"text": t[:8000]}}}
                 for t in texts],
        rerankingConfiguration={"type": "BEDROCK_RERANKING_MODEL", "bedrockRerankingConfiguration": {
            "numberOfResults": len(texts),
            "modelConfiguration": {"modelArn": f"arn:aws:bedrock:{region}::foundation-model/{model}"}}})
    return [(x["index"], x["relevanceScore"]) for x in r["results"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="amazon.rerank-v1:0")
    ap.add_argument("--per-group", type=int, default=10)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(argv)
    os.environ["RAG_SCHEMA"] = "corpus_v2"
    from system.rag import pgsearch as P

    url = reader_url()
    b3 = [json.loads(l) for l in B3.read_text(encoding="utf-8").splitlines()]
    picked = sample(b3, a.per_group, a.seed)
    name = f"R1-rerank-pilot-{a.model.split('.')[0]}"
    out, calls = [], 0
    for group, r in picked:
        extra = [x for x in (saved_queries("E3-rewrite", r["id"]) or []) if x != r["question"]]
        lists = [P.candidates(x, url=url, n=50) for x in [r["question"]] + extra]
        cands = P.one_per_section(P.rrf(*lists))[:50]
        keys = [M.section_key(c["source_id"], c["section_id"]) for c in cands]
        same = keys == r["candidates"][:50]
        queries = {"base": r["question"], "plain": extra[0] if extra else r["question"]}
        row = {"id": r["id"], "role": r["role"], "group": group, "expected": r["expected"],
               "b3_rank": best_rank(r["expected"], [x[0] for x in r["reranked"]]), "same_candidates": same,
               "ranks": {}, "label_scores": {}}
        for v in VARIANTS:
            q = queries["plain" if v.startswith("plain") else "base"]
            texts = [(header(c) + "\n" if "title" in v else "") + c["embed_text"] for c in cands]
            order = rerank_all(a.model, q, texts)
            calls += 1
            ranked = [keys[i] for i, _ in order]
            row["ranks"][v] = best_rank(r["expected"], ranked)
            row["label_scores"][v] = max((round(s, 4) for i, s in order if keys[i] in r["expected"]), default=None)
        out.append(row)
        print(group, r["id"], "b3", row["b3_rank"], row["ranks"], "" if same else "(candidates differ)", flush=True)

    (RESULTS / f"{name}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out), encoding="utf-8")
    summary = {"model": a.model, "per_group": a.per_group, "seed": a.seed, "questions": len(out),
               "same_candidates": sum(x["same_candidates"] for x in out), "calls": calls,
               "cost_usd": round(calls * USD_PER_CALL.get(a.model, 0.002), 3), "variants": {}}
    for v in VARIANTS:
        ranks = [x["ranks"][v] or 51 for x in out]
        s = {"found_in_8": sum(k <= 8 for k in ranks), "median_rank": statistics.median(ranks), "by_group": {}}
        if v != "base":
            s["vs_base_better"] = sum((x["ranks"][v] or 51) < (x["ranks"]["base"] or 51) for x in out)
            s["vs_base_worse"] = sum((x["ranks"][v] or 51) > (x["ranks"]["base"] or 51) for x in out)
        for g in ("good", "middle", "bad"):
            s["by_group"][g] = sum((x["ranks"][v] or 51) <= 8 for x in out if x["group"] == g)
        summary["variants"][v] = s
    (RESULTS / f"{name}.summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
        import datetime

        f.write(json.dumps({"time": datetime.datetime.now().isoformat(timespec="seconds"), "run": name,
                            "model": a.model, "unit": "rerank queries", "in": calls, "out": 0,
                            "cost_usd": summary["cost_usd"]}) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
