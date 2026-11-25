"""Fix gold labels that do not state any of the question's rules (S116, S152), 25 Nov 2026.

    python -m evals.golden.relabel          # rewrites questions.jsonl and labelled/*.jsonl, logs to relabel-2026-11-25.jsonl

The v2 pool judges said "no" to these labelled sections when they were planted as known "yes" lines, and fresh
judges agreed. Each was read against the question's rules (pooled/rules.jsonl) with one test: does this section,
on its own, state at least one of the rules? Sections that only cross-refer (an amount "for paragraph 7 of
Schedule 11"), only amend another Act, give a general requirement, or cover a side point are dropped. Where a
section that does state the rule exists, it replaces the weak one. Decided by Claude, 25 Nov 2026; Florin checks
them with the calibration. Changed questions get labels_version "v4".
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent

# question id -> list of (old id, new ids, why). new ids empty = dropped.
CHANGES: dict[str, list[tuple[str, list[str], str]]] = {
    "building-control-043": [
        ("pd-householder-guide:class-a-enlargement-improvement-or-alteration-text-1",
         ["pd-householder-guide:class-a-enlargement-improvement-or-alteration-text-4"],
         "text-1 holds A.1(a)-(e) only; A.1(f) 3 m / 4 m, A.1(g) and A.4 prior approval with 42 days are in text-4"),
    ],
    "site-safety-008": [
        ("hse-l153:regulation-7-application-to-domestic-clients-text-1", ["hse-l153:para-53"],
         "para 53 (housing associations, councils, landlords are not domestic clients) is now its own section"),
        ("cdm2015:regulation-4", ["cdm2015:regulation-2-term-domestic-client"],
         "reg 4 lists client duties but not who is a domestic client; the reg 2 definition states rule 2"),
    ],
    "building-control-048": [
        ("party-wall-act-1996:section-2-2", [],
         "s2(2) gives the right to cut away a chimney breast but not the notice or the two months; s3(2) is labelled"),
    ],
    "building-control-006": [
        ("adl:v1-para-10.3", [], "draught-proofing only, not in the rules; Table 4.2 and ADL 2026 Table 3.2 are labelled"),
    ],
    "asbestos-044": [
        ("car-amd-2026:regulation-2-3", [],
         "the reference updates themselves, with no start date; reg 1(2) and 1(3) state the dates"),
    ],
    "asbestos-029": [
        ("car2012:regulation-22-3", [],
         "applies 22(1)(a)-(c) to NNLW by cross-reference and adds medical timing; reg 22(1) and the HSE texts are labelled"),
    ],
    "building-control-022": [
        ("br2010:schedule-1-J3", [], "general requirement on fuel storage and CO; ADJ 3.43-3.45 state the alarm rules"),
    ],
    "housing-repairs-045": [
        ("hfhh-act-2018:section-1-4", [],
         "amending text for s10 (adds prescribed hazards) that does not state a rule on its own; the landlord guide is labelled"),
    ],
    "money-018": [
        ("cis-regs-2005:regulation-28", [],
         "amounts given only 'for paragraph 3(1) / 7 / 11 of Schedule 11'; no per-director rule. The GOV.UK page states it. "
         "Finance Act 2004 Schedule 11 is not in the corpus"),
    ],
}


def apply(row: dict, log: list[dict], file: str) -> bool:
    changes = CHANGES.get(row.get("id"))
    if not changes:
        return False
    keys = list(row.get("expected_sections") or [])
    for old, new, why in changes:
        if old not in keys:
            raise SystemExit(f"{file}: {row['id']} has no label {old}")
        i = keys.index(old)
        keys[i:i + 1] = [k for k in new if k not in keys]
        log.append({"file": file, "id": row["id"], "old": old, "new": new, "why": why})
    if not keys:
        raise SystemExit(f"{file}: {row['id']} would have no labels")
    row["expected_sections"] = keys
    return True


def main() -> None:
    log: list[dict] = []
    paths = [HERE / "questions.jsonl", *sorted((HERE / "labelled").glob("*.jsonl"))]
    seen: dict[str, set[str]] = {}
    for path in paths:
        rows = [json.loads(line) for line in path.open()]
        name = str(path.relative_to(HERE))
        for r in rows:
            if apply(r, log, name):
                seen.setdefault(name if name == "questions.jsonl" else "labelled", set()).add(r["id"])
                if name == "questions.jsonl":
                    r["labels_version"] = "v4"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    for where, ids in seen.items():
        missing = set(CHANGES) - ids
        if missing:
            raise SystemExit(f"{where}: questions not found {sorted(missing)}")
    (HERE / "relabel-2026-11-25.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log))
    print(f"{len(log)} label changes in {len({r['id'] for r in log})} questions across {len({r['file'] for r in log})} files")


if __name__ == "__main__":
    main()
