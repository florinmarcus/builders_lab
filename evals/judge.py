"""Answer eval (LLM as judge) on the golden set (corpus/OVERNIGHT-PLAN.md S8; agentic-rag-lab method).

    python evals/judge.py --retrieval E2-hybrid --schema corpus_next --split dev
    python evals/judge.py --retrieval E2-hybrid --split dev --limit 20      # a quick sample

For each question of a finished retrieval run (evals/results/<run>-<split>.jsonl):
1. the passages that search returned (its top 5, fetched by chunk id from the same schema);
2. an answer from a pinned answer model (Claude on Bedrock), told to answer only from the passages, cite them as
   [1]..[5], correct a false premise, ask one question back when the question is too vague, and say
   "NOT IN SOURCES" when the passages do not answer it;
3. a judge from another model family (pinned; Bedrock Converse, temperature 0) scores correctness, grounding and
   completeness 1-5 against the golden reference answer, reason before score, strict JSON; one retry, then
   "unjudged".
Code checks next to the judge: declined, asked back, citations only to passages that exist.
Pass = correctness >= 4 and grounding >= 4. Rows go to evals/results/<run>-judge-<split>.jsonl, the summary to
<run>-judge-<split>.summary.json, cost lines to evals/results/cost.jsonl (prices are estimates; verify).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))

RESULTS = ROOT / "evals" / "results"
GOLDEN = ROOT / "evals" / "golden" / "questions.jsonl"
ANSWER_MODEL = os.environ.get("EVAL_ANSWER_MODEL", "eu.anthropic.claude-haiku-4-5-20251001-v1:0")
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL", "openai.gpt-oss-120b-1:0")
REGION = "eu-west-2"
# USD per million tokens (input, output). Estimates from public price lists, 20 Nov 2026: verify.
PRICES = {ANSWER_MODEL: (1.10, 5.50), JUDGE_MODEL: (0.15, 0.60)}

ANSWER_SYSTEM = """You help small UK building firms with regulations and guidance. Answer the builder's question using
only the numbered passages given. Rules:
- Cite the passages you use as [1], [2] ... right after the sentence they support. Never cite a number not given.
- If the question rests on a wrong belief, say so plainly and give the correct rule.
- If the question is too vague to answer safely, start with "CLARIFY:" and ask one short question back.
- If the passages do not answer the question, start with "NOT IN SOURCES" and say what is missing. Do not answer
  from memory.
- Short sentences, plain English, at most about 150 words."""

JUDGE_SYSTEM = """You grade answers from a regulations assistant for UK builders. You get the question, its kind,
a reference answer written by an expert from the source documents, the passages the assistant was given, and the
assistant's answer. Grade three things from 1 (bad) to 5 (excellent), writing the reason BEFORE each score:
- correctness: does the answer agree with the reference answer on the facts that matter (rules, numbers, who must
  do what)? Kinds: "negative" = the question has a false premise; a correct answer corrects it. "out_of_scope" = the
  regulations do not cover it; a correct answer declines or says it is outside the sources, and invents no rule.
  "underspecified" = too vague; a correct answer asks a clarifying question or covers the main readings safely.
  An answer that says "NOT IN SOURCES" for an answerable question scores 2 at most.
- grounding: is every claim supported by the passages it cites? Claims from outside the passages lower the score,
  even when true.
- completeness: does it cover the main points of the reference answer?
Reply with JSON only, exactly these keys:
{"correctness_reason": "...", "correctness": n, "grounding_reason": "...", "grounding": n,
 "completeness_reason": "...", "completeness": n}"""

CITE_RE = re.compile(r"\[(\d{1,2})\]")


def declined(answer: str) -> bool:
    return answer.strip().upper().startswith("NOT IN SOURCES")


def asked_back(answer: str) -> bool:
    return answer.strip().upper().startswith("CLARIFY:")


def bad_citations(answer: str, n_passages: int) -> list[int]:
    return sorted({int(c) for c in CITE_RE.findall(answer) if not 1 <= int(c) <= n_passages})


def passages_block(passages: list[dict]) -> str:
    return "\n\n".join(f"[{i}] {p['source']} - {p['section']}\n{p['text']}" for i, p in enumerate(passages, 1))


def parse_judge(text: str) -> dict | None:
    """The judge's JSON, or None when it is missing a key or a score is not 1-5."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    for k in ("correctness", "grounding", "completeness"):
        if not isinstance(d.get(k), int) or not 1 <= d[k] <= 5 or not isinstance(d.get(f"{k}_reason"), str):
            return None
    return d


def passed(j: dict | None) -> bool | None:
    return None if j is None else (j["correctness"] >= 4 and j["grounding"] >= 4)


def summarise(rows: list[dict]) -> dict:
    judged = [r for r in rows if r.get("judge")]
    out = {"questions": len(rows), "judged": len(judged), "unjudged": len(rows) - len(judged)}
    if not judged:
        return out
    mean = lambda k, rs: round(sum(r["judge"][k] for r in rs) / len(rs), 3)  # noqa: E731
    out.update({"pass_rate": round(sum(passed(r["judge"]) for r in judged) / len(judged), 4),
                "correctness": mean("correctness", judged), "grounding": mean("grounding", judged),
                "completeness": mean("completeness", judged)})
    by_kind: dict[str, list] = {}
    for r in judged:
        by_kind.setdefault(r.get("kind", "?"), []).append(r)
    out["by_kind"] = {k: {"n": len(v), "pass_rate": round(sum(passed(r["judge"]) for r in v) / len(v), 4),
                          "declined": round(sum(r["declined"] for r in v) / len(v), 4),
                          "asked_back": round(sum(r["asked_back"] for r in v) / len(v), 4)}
                      for k, v in sorted(by_kind.items())}
    out["bad_citation_rows"] = sum(1 for r in rows if r.get("bad_citations"))
    return out


# ---------------------------------------------------------------- model and database calls

def fetch_passages(url: str, schema: str, row: dict) -> list[dict]:
    import psycopg
    from psycopg.rows import dict_row

    from system.rag import pgsearch as P

    s = P._schema(schema)
    out = []
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as conn:
        if row.get("top5_chunks"):
            for cid in row["top5_chunks"]:
                r = conn.execute(f"SELECT * FROM {s}.chunks WHERE id = %s", (cid,)).fetchone()
                if r:
                    out.append(r)
        else:  # older runs: the section's first chunk
            for key in row["top5"]:
                src, sec = key.split(":", 1)
                r = conn.execute(f"SELECT * FROM {s}.chunks WHERE source_id = %s AND split_part(section_id, '#', 1) = %s "
                                 "ORDER BY length(id), id LIMIT 1", (src, sec)).fetchone()
                if r:
                    out.append(r)
    return [{"source": p.get("source_title") or p["source_id"], "section": " > ".join((p.get("heading_path") or [])[-2:]),
             "text": p["text"], "chunk_id": p["id"]} for p in out]


_clients: dict = {}


def answer(question: str, passages: list[dict]) -> tuple[str, int, int]:
    import anthropic

    c = _clients.setdefault("answer", anthropic.AnthropicBedrock(aws_region=REGION))
    content = f"Passages:\n\n{passages_block(passages) if passages else '(no passages found)'}\n\nQuestion: {question}"
    r = c.messages.create(model=ANSWER_MODEL, max_tokens=2000, system=ANSWER_SYSTEM,
                          messages=[{"role": "user", "content": content}])
    text = "".join(b.text for b in r.content if b.type == "text")
    return text, r.usage.input_tokens, r.usage.output_tokens


def judge(q: dict, passages: list[dict], ans: str) -> tuple[dict | None, int, int, str]:
    import boto3

    c = _clients.setdefault("judge", boto3.client("bedrock-runtime", region_name=REGION))
    prompt = (f"Question: {q['question']}\nKind: {q.get('kind')}\nReference answer: {q.get('reference_answer')}\n\n"
              f"Passages given to the assistant:\n{passages_block(passages) if passages else '(none)'}\n\n"
              f"Assistant's answer:\n{ans}")
    tin = tout = 0
    raw = ""
    for _ in range(2):  # one retry on bad JSON
        r = c.converse(modelId=JUDGE_MODEL, system=[{"text": JUDGE_SYSTEM}],
                       messages=[{"role": "user", "content": [{"text": prompt}]}],
                       inferenceConfig={"maxTokens": 3000, "temperature": 0})
        tin += r["usage"]["inputTokens"]
        tout += r["usage"]["outputTokens"]
        raw = "".join(b.get("text", "") for b in r["output"]["message"]["content"])
        j = parse_judge(raw)
        if j:
            return j, tin, tout, raw
    return None, tin, tout, raw


def judge_one(q: dict, row: dict, url: str, schema: str) -> dict:
    for attempt in range(4):
        try:
            ps = fetch_passages(url, schema, row)
            ans, ain, aout = answer(q["question"], ps)
            j, jin, jout, raw = judge(q, ps, ans)
            break
        except Exception as e:  # throttling or a dropped connection: wait and retry
            if attempt == 3:
                return {"id": q["id"], "kind": q.get("kind"), "role": q.get("role"), "error": f"{type(e).__name__}: {e}"[:300]}
            time.sleep(15 * (attempt + 1))
    return {"id": q["id"], "kind": q.get("kind"), "role": q.get("role"), "question": q["question"],
            "passages": [p["chunk_id"] for p in ps], "answer": ans, "judge": j,
            "judge_raw": None if j else raw[:2000], "declined": declined(ans), "asked_back": asked_back(ans),
            "bad_citations": bad_citations(ans, len(ps)), "pass": passed(j),
            "tokens": {"answer_in": ain, "answer_out": aout, "judge_in": jin, "judge_out": jout}}


def log_cost(run: str, rows: list[dict]) -> float:
    t = {k: sum(r.get("tokens", {}).get(k, 0) for r in rows) for k in ("answer_in", "answer_out", "judge_in", "judge_out")}
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z"
    total = 0.0
    with open(RESULTS / "cost.jsonl", "a", encoding="utf-8") as f:
        for model, tin, tout in ((ANSWER_MODEL, t["answer_in"], t["answer_out"]), (JUDGE_MODEL, t["judge_in"], t["judge_out"])):
            pin, pout = PRICES[model]
            cost = tin / 1e6 * pin + tout / 1e6 * pout
            total += cost
            f.write(json.dumps({"time": now, "run": run, "model": model, "unit": "tokens", "in": tin, "out": tout,
                                "cost_usd": round(cost, 4), "price_note": "estimate, verify"}) + "\n")
    return total


def run(retrieval: str, schema: str, split: str, limit: int | None, workers: int) -> dict:
    sys.path.insert(0, str(ROOT / "evals"))
    import retrieval as R

    url = R.reader_url()
    golden = {q["id"]: q for q in (json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip())}
    rrows = [json.loads(l) for l in (RESULTS / f"{retrieval}-{split}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rrows = [r for r in rrows if r["id"] in golden][:limit] if limit else [r for r in rrows if r["id"] in golden]
    out_path = RESULTS / f"{retrieval}-judge-{split}.jsonl"
    done = {}
    if out_path.exists():
        done = {r["id"]: r for r in (json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip())
                if "error" not in r}
    todo = [r for r in rrows if r["id"] not in done]
    new: list[dict] = []
    with open(out_path, "a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=workers) as ex:
        for i, res in enumerate(ex.map(lambda r: judge_one(golden[r["id"]], r, url, schema), todo), 1):
            new.append(res)
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}", flush=True)
    rows = [done.get(r["id"]) or next(n for n in new if n["id"] == r["id"]) for r in rrows]
    cost = log_cost(f"{retrieval}-judge-{split}", new)
    summary = {"run": f"{retrieval}-judge", "split": split, "time": datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds") + "Z",
               "answer_model": ANSWER_MODEL, "judge_model": JUDGE_MODEL, "schema": schema,
               "cost_usd_this_call": round(cost, 4), "errors": sum(1 for r in rows if "error" in r), **summarise(rows)}
    (RESULTS / f"{retrieval}-judge-{split}.summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retrieval", required=True, help="retrieval run name, e.g. E2-hybrid")
    ap.add_argument("--schema", default="corpus_next")
    ap.add_argument("--split", default="dev", choices=["dev", "holdout", "all"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.retrieval, a.schema, a.split, a.limit, a.workers), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
