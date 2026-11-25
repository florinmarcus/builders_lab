"""Query decomposer prompt tuning (see README.md here).

  python run.py build --draft d1 --set tune --keys keys.json --work DIR   # Haiku batches (10 questions each)
  python run.py judge --draft d1 --set tune --keys keys.json --work DIR   # after Haiku: judge batches
  python run.py score --draft d1 --set tune --work DIR                     # after judge: results file + counts

Haiku and the judge run as Claude Code subagents on the user's plan; this script only writes their inputs
and reads their outputs (one JSON line per id, in DIR/haiku-*.out.jsonl and DIR/judge-*.out.jsonl)."""
import argparse, collections, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "evals"))
KIND = {"law": "law", "approved-document": "approved_document", "acop": "approved_code", "guidance": "guidance"}
BATCH = 10


def load(args):
    split = json.loads((HERE / "split.json").read_text())
    ids = split[args.set]
    rows = {r["id"]: r for r in map(json.loads, open(ROOT / "evals/golden/questions.jsonl"))}
    prompt = (HERE / f"prompt-{args.draft}.md").read_text()
    return [rows[i] for i in ids], prompt, hashlib.sha256(prompt.encode()).hexdigest()[:12]


def batches(xs):
    return [xs[i:i + BATCH] for i in range(0, len(xs), BATCH)]


def read_out(work, pattern):
    out = {}
    for f in sorted(work.glob(pattern)):
        for line in f.read_text().splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                out[d["id"]] = d
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["build", "judge", "score"])
    ap.add_argument("--draft", required=True)
    ap.add_argument("--set", required=True, choices=["tune", "check"])
    ap.add_argument("--keys")
    ap.add_argument("--work", required=True)
    args = ap.parse_args()
    rows, prompt, sha = load(args)
    work = pathlib.Path(args.work) / f"{args.draft}-{args.set}"
    work.mkdir(parents=True, exist_ok=True)

    if args.step == "build":
        for n, b in enumerate(batches(rows), 1):
            items = [{"id": r["id"], "question": r["question"]} for r in b]
            (work / f"haiku-{n}.in.json").write_text(json.dumps({"prompt": prompt, "items": items}, indent=1))
        print(f"{len(rows)} questions, prompt {args.draft} sha {sha}, batches in {work}")

    elif args.step == "judge":
        import retrieval
        keys = json.loads(pathlib.Path(args.keys).read_text())
        haiku = read_out(work, "haiku-*.out.jsonl")
        missing = [r["id"] for r in rows if r["id"] not in haiku]
        if missing:
            sys.exit(f"no Haiku output for: {missing}")
        for n, b in enumerate(batches(rows), 1):
            items = []
            for r in b:
                h = dict(haiku[r["id"]]); h.pop("id", None)
                items.append({
                    "id": r["id"], "question": r["question"], "output": h.get("output", h),
                    "reference_answer": r["reference_answer"],
                    "expected_sections": [{"section": s, "kinds": [KIND[l] for l in retrieval.lanes_of(s, keys)]}
                                          for s in r["expected_sections"]],
                    "label": r["kind"], "vague": r["vague"], "multi_rule": r["multi_rule"]})
            (work / f"judge-{n}.in.json").write_text(json.dumps({"items": items}, indent=1))
        print(f"judge batches in {work}")

    else:
        haiku = read_out(work, "haiku-*.out.jsonl")
        judge = read_out(work, "judge-*.out.jsonl")
        res = ROOT / f"evals/results/D-decompose-{args.draft}-{args.set}.jsonl"
        with res.open("w") as f:
            for r in rows:
                h = dict(haiku.get(r["id"], {})); h.pop("id", None)
                j = dict(judge.get(r["id"], {})); j.pop("id", None)
                f.write(json.dumps({"id": r["id"], "label": r["kind"], "prompt": args.draft, "prompt_sha": sha,
                                    "output": h.get("output", h), "judge": "judge-v1", "verdict": j}) + "\n")
        v = collections.Counter(judge.get(r["id"], {}).get("verdict", "missing") for r in rows)
        c = collections.Counter(judge[r["id"]].get("cause") for r in rows
                                if judge.get(r["id"], {}).get("verdict") in ("bad", "partly"))
        print(f"{args.draft} on {args.set}: {dict(v)}\ncauses (bad+partly): {c.most_common()}\n-> {res}")


if __name__ == "__main__":
    main()
