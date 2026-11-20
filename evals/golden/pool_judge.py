"""Pooled relevance judging for the golden set (TREC-style pooling; corpus/OVERNIGHT-PLAN.md S5/S7).

    python evals/golden/pool_judge.py            # judge every new (question, section) pair in the dev pool
    python evals/golden/pool_judge.py --dry-run  # only count the pairs

Labels written by one labeller are narrow: a GOV.UK booklet can answer a party wall question as well as the Act
the labeller chose. The pool is every section that any retrieval run put in a dev question's re-ranked top 5 and
that does not already touch an expected section. A judge model from another family than the answer model grades
each pair blind (it does not know which run found it) against the question and the reference answer:
2 = the section itself states the answer or the rule the reference answer rests on; 1 = related or partial;
0 = not relevant. Grade 2 becomes "also_acceptable" in questions.jsonl (build.py). Metrics report strict recall
(original labels) next to pooled recall. Holdout questions are never pooled.

Judgments are cached in evals/golden/pooled/judgments.jsonl (keyed by question id and section key).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "evals" / "golden"))
import build as B  # noqa: E402
import metrics as M  # noqa: E402

POOL = ROOT / "evals" / "golden" / "pooled" / "judgments.jsonl"
RESULTS = ROOT / "evals" / "results"
MODEL = "openai.gpt-oss-120b-1:0"
PRICE = (0.15, 0.60)  # USD per million tokens, estimate (verify)

SYSTEM = """You judge whether one passage from UK building regulations or official guidance answers a builder's
question. You get the question, an expert's reference answer and the passage. Grade strictly:
2 = the passage itself states the answer, or the rule or fact the reference answer rests on, clearly enough that a
    builder could act on it;
1 = related or partly useful, but it does not give the answer;
0 = not relevant.
Reply with JSON only: {"reason": "one sentence", "grade": 0|1|2}"""


def pool_pairs(questions: dict, runs: list[Path], done: set) -> list[tuple[str, str]]:
    pairs = []
    for path in runs:
        for line in path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            q = questions.get(r["id"])
            if not q or q.get("split") != "dev" or not q.get("expected_sections"):
                continue
            for x in r.get("reranked") or [[k] for k in r.get("top5", [])]:
                key = x[0]
                if not any(M.touches(e, key) for e in q["expected_sections"]) and (r["id"], key) not in done:
                    done.add((r["id"], key))
                    pairs.append((r["id"], key))
    return pairs


def parse(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    return d if d and d.get("grade") in (0, 1, 2) else None


def judge(client, q: dict, section_text: str) -> tuple[dict | None, int, int]:
    prompt = f"Question: {q['question']}\nReference answer: {q.get('reference_answer')}\n\nPassage:\n{section_text[:6000]}"
    tin = tout = 0
    for _ in range(2):
        r = client.converse(modelId=MODEL, system=[{"text": SYSTEM}], messages=[{"role": "user", "content": [{"text": prompt}]}],
                            inferenceConfig={"maxTokens": 1500, "temperature": 0})
        tin += r["usage"]["inputTokens"]
        tout += r["usage"]["outputTokens"]
        d = parse("".join(b.get("text", "") for b in r["output"]["message"]["content"]))
        if d:
            return d, tin, tout
    return None, tin, tout


def section_text(index: dict, key: str) -> str:
    """A section's own text, or (for a heading) the text of its children, with its breadcrumb."""
    s = index.get(key)
    if not s:
        return ""
    text = s.get("text") or ""
    if len(text) < 200:
        src = key.split(":")[0]
        kids = [v.get("text") or "" for k, v in index.items() if k.startswith(f"{src}:") and v.get("parent_id") == s["id"]]
        text = (text + "\n" + "\n".join(kids)).strip()
    return " > ".join(s.get("heading_path") or []) + "\n" + text


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    questions = {q["id"]: q for q in map(json.loads, (ROOT / "evals/golden/questions.jsonl").read_text(encoding="utf-8").splitlines())}
    done = set()
    if POOL.exists():
        done = {(j["id"], j["section"]) for j in map(json.loads, POOL.read_text(encoding="utf-8").splitlines())}
    runs = sorted(RESULTS.glob("E*-dev.jsonl"))
    runs = [p for p in runs if "-judge-" not in p.name]
    pairs = pool_pairs(questions, runs, set(done))
    print(f"{len(pairs)} new pairs from {len(runs)} runs ({len(done)} judged before)")
    if a.dry_run or not pairs:
        return 0
    import boto3

    client = boto3.client("bedrock-runtime", region_name="eu-west-2")
    index = B.section_index()
    POOL.parent.mkdir(parents=True, exist_ok=True)
    tokens = [0, 0]

    def one(pair):
        qid, key = pair
        text = section_text(index, key)
        if not text.strip():
            return {"id": qid, "section": key, "grade": None, "reason": "section not in current trees"}
        d, tin, tout = judge(client, questions[qid], text)
        tokens[0] += tin
        tokens[1] += tout
        return {"id": qid, "section": key, "grade": d["grade"] if d else None, "reason": d.get("reason") if d else "unjudged",
                "model": MODEL}

    with open(POOL, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, j in enumerate(ex.map(one, pairs), 1):
            f.write(json.dumps(j, ensure_ascii=False) + "\n")
            f.flush()
            if i % 100 == 0:
                print(f"  {i}/{len(pairs)}", flush=True)
    cost = tokens[0] / 1e6 * PRICE[0] + tokens[1] / 1e6 * PRICE[1]
    with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"time": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
                            "run": "pool-judge", "model": MODEL, "unit": "tokens", "in": tokens[0], "out": tokens[1],
                            "cost_usd": round(cost, 4), "price_note": "estimate, verify"}) + "\n")
    print(f"done; cost about ${cost:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
