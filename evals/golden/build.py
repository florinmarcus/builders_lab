"""Build the golden set from the business and labelling passes (agentic-rag-lab method; corpus/OVERNIGHT-PLAN.md S5).

    python evals/golden/build.py

Inputs:
- evals/golden/business/<role>.jsonl: questions, kinds and reference answers (written blind to the parser).
- evals/golden/labelled/<role>.jsonl: {"id", "expected_sections": ["<source>:<section>", ...], "label_confidence",
  "label_note"} from the separate labelling pass.
Outputs:
- evals/golden/questions.jsonl: kept questions with expected_sections and split (dev or holdout).
- evals/golden/dropped.jsonl: questions dropped by the copy filter (5+ words in a row shared with an expected
  section's text or heading), with the shared words.
- evals/golden/holdout-ids.txt: the holdout (about 20% per role, chosen by a stable hash of the id). Commit it
  before the first eval run; never tune on it.
Fails on an unknown section id (a typo must not score as "not found"), duplicate ids, or unknown kinds.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "evals" / "golden"
KINDS = {"answerable", "negative", "out_of_scope", "underspecified"}
WORD = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*%?", re.I)
HOLDOUT_SHARE = 0.2
RUN = 5


def words(text: str) -> list[str]:
    return [w.lower() for w in WORD.findall(text or "")]


def shared_run(a: str, b: str) -> list[str]:
    """Longest run of words that a and b share, in order (longest common substring on words)."""
    wa, wb = words(a), words(b)
    best, best_end = 0, 0
    prev = [0] * (len(wb) + 1)
    for i in range(1, len(wa) + 1):
        cur = [0] * (len(wb) + 1)
        for j in range(1, len(wb) + 1):
            if wa[i - 1] == wb[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best, best_end = cur[j], i
        prev = cur
    return wa[best_end - best:best_end]


def is_holdout(qid: str) -> bool:
    return int(hashlib.sha256(qid.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF < HOLDOUT_SHARE


def section_index() -> dict[str, dict]:
    idx = {}
    for t in (ROOT / "corpus" / "parsed").glob("*/*.json"):
        try:
            d = json.loads(t.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if "sections" not in d:
            continue
        for s in d["sections"]:
            idx.setdefault(f"{d['source_id']}:{s['id']}", s)
    return idx


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def build(index: dict | None = None) -> dict:
    index = index if index is not None else section_index()
    business = {q["id"]: q for p in sorted((GOLDEN / "business").glob("*.jsonl")) for q in read_jsonl(p)}
    labels = {l["id"]: l for p in sorted((GOLDEN / "labelled").glob("*.jsonl")) for l in read_jsonl(p)} \
        if (GOLDEN / "labelled").exists() else {}
    problems, kept, dropped = [], [], []
    for qid, q in business.items():
        if q.get("kind") not in KINDS:
            problems.append(f"{qid}: unknown kind {q.get('kind')}")
            continue
        lab = labels.get(qid, {})
        expected = lab.get("expected_sections", [])
        for e in expected:
            if e not in index:
                problems.append(f"{qid}: unknown section {e}")
        row = {**q, "expected_sections": expected, "label_confidence": lab.get("label_confidence"),
               "label_note": lab.get("label_note"), "labelled": qid in labels,
               "split": "holdout" if is_holdout(qid) else "dev"}
        run = []
        for e in expected:
            s = index.get(e, {})
            for target in (s.get("text") or "", " ".join(s.get("heading_path") or [])):
                r = shared_run(q["question"], target)
                if len(r) > len(run):
                    run = r
        if len(run) >= RUN:
            dropped.append({**row, "shared_run": len(run), "shared_words": " ".join(run)})
        else:
            kept.append(row)
    return {"kept": kept, "dropped": dropped, "problems": problems, "business": len(business), "labelled": len(labels)}


def write(r: dict) -> None:
    (GOLDEN / "questions.jsonl").write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in r["kept"]), encoding="utf-8")
    (GOLDEN / "dropped.jsonl").write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in r["dropped"]), encoding="utf-8")
    hold = sorted(q["id"] for q in r["kept"] + r["dropped"] if q["split"] == "holdout")
    (GOLDEN / "holdout-ids.txt").write_text("\n".join(hold) + "\n", encoding="utf-8")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    r = build()
    if r["problems"]:
        print("Problems (nothing written):\n  " + "\n  ".join(r["problems"][:50]))
        return 1
    write(r)
    with_sections = [q for q in r["kept"] if q["expected_sections"]]
    print(f"business {r['business']}, labelled {r['labelled']}, kept {len(r['kept'])} "
          f"({len(with_sections)} with sections; dev {sum(q['split'] == 'dev' for q in with_sections)}, "
          f"holdout {sum(q['split'] == 'holdout' for q in with_sections)}), dropped by copy filter {len(r['dropped'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
