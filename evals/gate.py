"""Regression gate for regulations search (25 Nov 2026).

Before a change to search, chunks or agent prompts is kept, its dev run is compared with the baseline question by
question. It fails when the change loses more than it gains for real, drops the score by more than 2 points, or
loses a must-pass question. Dev only: the holdout is never used for tuning.

    python evals/gate.py baseline B1-v2-mixed-k20-dev-dev     # set the baseline (after a change is kept)
    python evals/gate.py check NEW-RUN-dev                    # exit 1 if the gate fails; lists lost and gained
    python evals/gate.py must-pass                            # (re)pick the must-pass list from the baseline

The run itself: `python evals/retrieval.py ... --split dev` (see evals/experiments/B-mixed-vs-lanes.md).
"Found": an expected section in the first N passages (lanes: N/4 per lane). N is fixed in the baseline (8).
"""

from __future__ import annotations

import argparse
import datetime
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paired as P  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
GATE = HERE / "gate"
BASELINE = GATE / "baseline.json"
MUST_PASS = GATE / "must-pass.txt"
QUESTIONS = HERE / "golden" / "questions.jsonl"
MAX_DROP = 0.02      # overall score may not fall more than 2 points
P_LOSS = 0.05        # more lost than gained, and the sign test says it is not luck
PER_ROLE = 5         # must-pass questions per role (6 roles, 30 in all)


def load_run(run: str) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, (RESULTS / f"{run}.jsonl").read_text(encoding="utf-8").splitlines())
            if r.get("expected")}


def holdout_ids() -> set[str]:
    return {q["id"] for q in map(json.loads, QUESTIONS.read_text(encoding="utf-8").splitlines()) if q.get("split") == "holdout"}


def found_map(rows: dict[str, dict], n: int) -> dict[str, bool]:
    return {q: P.found(r, n) for q, r in sorted(rows.items())}


def pick_must_pass(baseline: dict, rows: dict[str, dict], per_role: int = PER_ROLE, seed: int = 25) -> list[str]:
    """per_role questions per role that the baseline finds, answerable ones first, random within that (seeded)."""
    rng = random.Random(seed)
    by_role: dict[str, list[str]] = {}
    for q, hit in baseline["found"].items():
        if hit:
            by_role.setdefault(rows[q].get("role") or "?", []).append(q)
    out = []
    for role in sorted(by_role):
        ids = sorted(by_role[role])
        rng.shuffle(ids)
        ids.sort(key=lambda q: rows[q].get("kind") != "answerable")  # stable: answerable first, shuffled within
        out += ids[:per_role]
    return out


def check(baseline: dict, new: dict[str, bool], must: list[str]) -> dict:
    """The gate verdict: lost, gained, the paired test and the reasons to fail (empty = pass)."""
    old = baseline["found"]
    ids = sorted(set(old) & set(new))
    missing = sorted(set(old) - set(new))
    r = P.compare([new[q] for q in ids], [old[q] for q in ids])
    lost = [q for q in ids if old[q] and not new[q]]
    gained = [q for q in ids if new[q] and not old[q]]
    score_old = sum(old[q] for q in ids) / len(ids)
    score_new = sum(new[q] for q in ids) / len(ids)
    fails = []
    if missing:
        fails.append(f"{len(missing)} baseline questions not in the new run")
    if len(lost) > len(gained) and r["p"] < P_LOSS:
        fails.append(f"loses more than it gains, not luck (lost {len(lost)}, gained {len(gained)}, p {r['p']})")
    if score_old - score_new > MAX_DROP:
        fails.append(f"score drops {score_old - score_new:.3f} (more than {MAX_DROP})")
    must_lost = [q for q in must if q in lost]
    if must_lost:
        fails.append(f"loses must-pass questions: {', '.join(must_lost)}")
    return {"questions": len(ids), "score_old": round(score_old, 4), "score_new": round(score_new, 4),
            "lost": lost, "gained": gained, "p": r["p"], "ci95": r["ci95"], "fails": fails}


def git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=HERE).stdout.strip()
    except OSError:
        return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("run")
    b.add_argument("--n", type=int, default=8)
    c = sub.add_parser("check")
    c.add_argument("run")
    sub.add_parser("must-pass")
    a = ap.parse_args(argv)
    GATE.mkdir(exist_ok=True)

    if a.cmd in ("baseline", "check"):
        rows = load_run(a.run)
        if set(rows) & holdout_ids():
            print("refused: the run holds holdout questions; the gate is dev only")
            return 2

    if a.cmd == "baseline":
        base = {"run": a.run, "n": a.n, "set": datetime.date.today().isoformat(), "commit": git_head(),
                "found": found_map(rows, a.n)}
        BASELINE.write_text(json.dumps(base, indent=0) + "\n")
        hits = sum(base["found"].values())
        print(f"baseline {a.run}: found {hits}/{len(base['found'])} at {a.n} passages -> {BASELINE.relative_to(HERE.parent)}")
        if not MUST_PASS.exists():
            a.cmd = "must-pass"
        else:
            return 0

    base = json.loads(BASELINE.read_text())
    if a.cmd == "must-pass":
        rows = load_run(base["run"])
        ids = pick_must_pass(base, rows)
        MUST_PASS.write_text("# Must-pass questions for evals/gate.py: found by the baseline, 5 per role. Edit by hand if needed.\n"
                             + "\n".join(ids) + "\n")
        print(f"{len(ids)} must-pass questions -> {MUST_PASS.relative_to(HERE.parent)}")
        return 0

    must = [x.strip() for x in MUST_PASS.read_text().splitlines() if x.strip() and not x.startswith("#")] if MUST_PASS.exists() else []
    v = check(base, found_map(rows, base["n"]), must)
    text = {q: rows[q]["question"][:90] for q in v["lost"] + v["gained"] if q in rows}
    print(f"gate: {a.run} against baseline {base['run']} ({v['questions']} dev questions, found in {base['n']} passages)")
    print(f"score {v['score_old']} -> {v['score_new']}; lost {len(v['lost'])}, gained {len(v['gained'])}; p {v['p']}; 95% CI {v['ci95']}")
    for name in ("lost", "gained"):
        for q in v[name]:
            print(f"  {name:6} {q}  {text.get(q, '')}")
    if v["fails"]:
        print("FAIL: " + "; ".join(v["fails"]))
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
