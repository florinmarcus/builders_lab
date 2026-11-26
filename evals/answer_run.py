"""Answer runs for the answer judge (ADR 0021): Sonnet answers dev questions with the regulations search only.

    python evals/answer_run.py batches --run R1 --out DIR      # every dev question, batches of 15, fixed order
    python evals/answer_run.py collect --run R1 --out DIR      # check every answer is there; write the manifest

The answers are written by Sonnet 5.5 helpers in a Claude Code session on Florin's plan, each given
evals/answers/ANSWER-BRIEF.md and one batch file; each writes DIR/answers-<batch>.json. DIR holds questions and
answers that can quote corpus text: keep it out of git (the scratchpad). Git keeps only the manifest
(evals/answers/<run>.manifest.json): ids, searches, trace ids, answer lengths, brief and golden hashes.
Dev only, never the holdout.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evals" / "golden" / "questions.jsonl"
BRIEF = ROOT / "evals" / "answers" / "ANSWER-BRIEF.md"
MANIFESTS = ROOT / "evals" / "answers"
BATCH = 15
MODEL = "sonnet-5.5"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def dev_questions() -> list[dict]:
    qs = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sorted((q for q in qs if q["split"] == "dev"), key=lambda q: q["id"])


def batches(run: str, out: Path) -> None:
    qs = dev_questions()
    out.mkdir(parents=True, exist_ok=True)
    for i in range(0, len(qs), BATCH):
        batch = [{"id": q["id"], "question": q["question"]} for q in qs[i:i + BATCH]]
        (out / f"batch-{i // BATCH + 1:02d}.json").write_text(json.dumps(batch, indent=1, ensure_ascii=False))
    meta = {"run": run, "model": MODEL, "brief": BRIEF.name, "brief_sha": sha(BRIEF), "golden_sha": sha(GOLDEN),
            "questions": len(qs), "batches": -(-len(qs) // BATCH)}
    (out / "run.json").write_text(json.dumps(meta, indent=1))
    print(f"{len(qs)} dev questions in {meta['batches']} batches:", dict(collections.Counter(q["kind"] for q in qs)))


def collect(run: str, out: Path) -> int:
    meta = json.loads((out / "run.json").read_text())
    if meta["brief_sha"] != sha(BRIEF) or meta["golden_sha"] != sha(GOLDEN):
        print("warning: the brief or the golden set changed since the batches were written")
    want = [q["id"] for b in sorted(out.glob("batch-*.json")) for q in json.loads(b.read_text())]
    got: dict[str, dict] = {}
    for f in sorted(out.glob("answers-*.json")):
        for a in json.loads(f.read_text()):
            got[a["id"]] = a
    missing = [i for i in want if i not in got or not str(got[i].get("answer", "")).strip()]
    rows = [{"id": i, "searches": got[i].get("searches", []), "trace_ids": got[i].get("trace_ids", []),
             "answer_words": len(got[i]["answer"].split())} for i in want if i not in missing]
    manifest = {**meta, "collected": datetime.date.today().isoformat(),
                "commit": subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                         text=True).stdout.strip(),
                "answered": len(rows), "missing": missing,
                "searches_per_question": round(sum(len(r["searches"]) for r in rows) / max(len(rows), 1), 2),
                "rows": rows}
    path = MANIFESTS / f"{run}.manifest.json"
    path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    print(f"{len(rows)} answered, {len(missing)} missing -> {path.relative_to(ROOT)}")
    return 1 if missing else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["batches", "collect"])
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.step == "batches":
        batches(a.run, a.out)
        return 0
    return collect(a.run, a.out)


if __name__ == "__main__":
    raise SystemExit(main())
