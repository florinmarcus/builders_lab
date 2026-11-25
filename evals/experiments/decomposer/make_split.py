"""Fixed split of dev questions for tuning the query decomposer prompt: 60 to tune on, 30 to check the winner.
Stratified by kind; holdout never touched. Run once; the output is committed."""
import json, random, collections, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
rows = [json.loads(l) for l in open(ROOT / "evals/golden/questions.jsonl")]
hold = set(open(ROOT / "evals/golden/holdout-ids.txt").read().split())
dev = [r for r in rows if r.get("split") == "dev" and r["id"] not in hold]
rng = random.Random(20261125)
by = collections.defaultdict(list)
for r in sorted(dev, key=lambda r: r["id"]):
    by[r["kind"]].append(r["id"])
tune, check = [], []
for kind, ids in sorted(by.items()):
    rng.shuffle(ids)
    n_t = round(60 * len(ids) / len(dev)); n_c = round(30 * len(ids) / len(dev))
    tune += ids[:n_t]; check += ids[n_t:n_t + n_c]
out = {"seed": 20261125, "tune": sorted(tune), "check": sorted(check)}
(ROOT / "evals/experiments/decomposer/split.json").write_text(json.dumps(out, indent=1) + "\n")
k = {r["id"]: r for r in dev}
for name in ("tune", "check"):
    print(name, len(out[name]), collections.Counter(k[i]["kind"] for i in out[name]), "vague", sum(k[i]["vague"] for i in out[name]))
