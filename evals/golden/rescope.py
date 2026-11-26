"""Out-of-scope questions that the library now answers (S146), 26 Nov 2026.

    python -m evals.golden.rescope      # rewrites business/, labelled/, questions.jsonl, pooled/rules.jsonl; logs to rescope-2026-11-26.jsonl

The 39 dev out_of_scope questions were checked against corpus/sources.yaml and live searches. Planning was labelled
out of scope before gpdo-2015 and pd-householder-guide were ingested. Two questions are now answerable (houses,
Class A of the GPDO). Two stay out of scope (a block of flats, council garages: householder rights do not cover
them) but their reference answers now say what the library does hold. Agreed by Florin, 26 Nov 2026. Reference
answers written by Claude from the parsed guide; Florin checks them with the calibration. labels_version "v5".
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
GUIDE = "pd-householder-guide"

CHANGES: dict[str, dict] = {
    "site-safety-062": {
        "business": {
            "kind": "answerable",
            "reference_answer": (
                "Usually not, if it is done as permitted development. For a house that is not detached, a single storey "
                "rear extension can go 3 m beyond the original rear wall, up to 4 m high, without planning permission. "
                "At 4 m you are over that limit, so you need the neighbour consultation (prior approval) scheme, which "
                "allows up to 6 m: notify the council and do not start until it says prior approval is not needed, "
                "grants it, or 42 days pass with no decision. That scheme is not available on article 2(3) land (for "
                "example a conservation area) or a site of special scientific interest, where the limit is 3 m and a "
                "4 m extension needs a planning application. Check with the council that permitted development rights "
                "have not been removed (Article 4 direction). Building regulations still apply."),
            "cited_clauses": [
                "pd-householder-guide Class A paragraph A.1(f) (3 m, 4 m height)",
                "pd-householder-guide Class A paragraph A.1(g) (6 m, neighbour consultation)",
                "pd-householder-guide Class A paragraph A.4 (prior approval, 42 days)",
                "pd-householder-guide Introduction (Article 4 directions; building regulations still apply)",
            ],
            "sources_read": [GUIDE, "gpdo-2015"],
            "multi_rule": True,
        },
        "labelled": {
            "expected_sections": [f"{GUIDE}:class-a-enlargement-improvement-or-alteration-text-4"],
            "label_confidence": "high",
            "label_note": "text-4 holds A.1(f) 3 m for a house that is not detached, A.1(g) 6 m and A.4 prior approval with 42 days",
        },
        "rules": {
            "scope": "builder; England; 4 m single storey rear extension to a semi-detached house",
            "rules": [
                "For a house that is not detached, a single storey rear extension is permitted development up to 3 m beyond the original rear wall and up to 4 m high.",
                "Beyond 3 m and up to 6 m it needs the prior approval (neighbour consultation) process, and work cannot start until the council says approval is not needed, grants it, or 42 days pass without a decision.",
                "On article 2(3) land (such as a conservation area) or a SSSI the limit stays 3 m, so 4 m needs a planning application.",
            ],
        },
        "why": "planning held since gpdo-2015 and pd-householder-guide were ingested; same sections as building-control-043",
    },
    "housing-repairs-059": {
        "business": {
            "kind": "answerable",
            "reference_answer": (
                "Possibly not. Council houses are houses, and Class A permitted development covers general alterations "
                "such as new windows. The condition is that the materials give a similar appearance to the existing "
                "house: the guidance says uPVC double glazing can be acceptable if the new windows look similar, for "
                "example in overall shape and in the colour and size of the frames. Swapping timber sashes for uPVC "
                "that looks different would not meet that condition and would need planning permission. In a "
                "conservation area, check with the local planning authority first: councils often remove these rights "
                "with an Article 4 direction, and then a planning application is needed."),
            "cited_clauses": [
                "pd-householder-guide Introduction, structure of the rules (Class A covers new windows and doors)",
                "pd-householder-guide Class A paragraph A.3(a) (materials of similar appearance; uPVC windows)",
                "pd-householder-guide Introduction, further restrictions (Article 4 directions)",
            ],
            "sources_read": [GUIDE, "gpdo-2015"],
            "multi_rule": True,
        },
        "labelled": {
            "expected_sections": [
                f"{GUIDE}:x-conditions-text-1",
                f"{GUIDE}:introduction-further-restrictions-on-permitted-development-text-1",
            ],
            "label_confidence": "medium",
            "label_note": "x-conditions-text-1: A.3(a) similar appearance and the uPVC windows example; further-restrictions: Article 4 directions. Medium: the guide does not discuss timber sash to uPVC in a conservation area directly",
        },
        "rules": {
            "scope": "contractor for a council; England; replacing timber sash windows with uPVC on houses in a conservation area",
            "rules": [
                "Replacing windows on a house can be permitted development under Class A, provided the materials give a similar appearance to the existing house; uPVC can qualify if the windows look similar in shape and frame colour and size.",
                "A local planning authority can remove permitted development rights with an Article 4 direction (common in conservation areas), so check with it first; if removed, a planning application is needed.",
            ],
        },
        "why": "planning held since pd-householder-guide was ingested; council houses are dwellinghouses under Class A",
    },
    "fire-safety-066": {
        "business": {
            "reference_answer": (
                "Not covered for a block of flats. The library holds the householder permitted development rules, but "
                "they apply to houses only, not to buildings containing flats; the guidance says planning permission "
                "should be sought in those cases. Whether new windows on the block need permission, especially in a "
                "conservation area, is for the local planning authority: ask it before ordering the windows."),
            "cited_clauses": ["pd-householder-guide Introduction (rights do not apply to flats)",
                              "pd-householder-guide General issues (definition of dwellinghouse)"],
            "sources_read": [GUIDE],
        },
        "labelled": {"label_note": "out of scope: householder rights (pd-householder-guide, gpdo Part 1) do not cover flats"},
        "why": "still out of scope, but the old answer said planning is not covered at all; householder rules are now held",
    },
    "asbestos-065": {
        "business": {
            "reference_answer": (
                "Not covered for garages like these. The library holds the householder permitted development rules, "
                "which cover houses and the buildings around them, not a block of council garages. The asbestos "
                "documents explain how to remove the sheets safely, not whether re-roofing needs planning "
                "permission. Ask the local planning authority."),
            "cited_clauses": ["pd-householder-guide Introduction (Part 1 covers houses and their curtilage)"],
            "sources_read": [GUIDE],
        },
        "labelled": {"label_note": "out of scope: householder rights do not cover a block of council garages"},
        "why": "still out of scope, but the old answer said planning is not covered at all; householder rules are now held",
    },
}


def rewrite(path: Path, fields: str, log: list[dict]) -> set[str]:
    rows = [json.loads(line) for line in path.open() if line.strip()]
    done = set()
    for r in rows:
        c = CHANGES.get(r.get("id"))
        if not c:
            continue
        new = dict(c.get("business", {})) if fields == "business" else dict(c.get("labelled", {}))
        if fields == "questions":
            new = {**c.get("business", {}), **c.get("labelled", {}), "labels_version": "v5"}
        for k, v in new.items():
            if r.get(k) != v:
                log.append({"file": str(path.relative_to(HERE)), "id": r["id"], "field": k, "old": r.get(k), "new": v,
                            "why": c["why"]})
                r[k] = v
        done.add(r["id"])
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    return done


def main() -> None:
    log: list[dict] = []
    seen_b = set().union(*(rewrite(p, "business", log) for p in sorted((HERE / "business").glob("*.jsonl"))))
    seen_l = set().union(*(rewrite(p, "labelled", log) for p in sorted((HERE / "labelled").glob("*.jsonl"))))
    seen_q = rewrite(HERE / "questions.jsonl", "questions", log)
    for where, seen in (("business", seen_b), ("labelled", seen_l), ("questions.jsonl", seen_q)):
        if seen != set(CHANGES):
            raise SystemExit(f"{where}: questions not found {sorted(set(CHANGES) - seen)}")
    rules_path = HERE / "pooled" / "rules.jsonl"
    rules = [json.loads(line) for line in rules_path.open() if line.strip()]
    have = {r["id"] for r in rules}
    for qid, c in CHANGES.items():
        if "rules" in c and qid not in have:
            rules.append({"id": qid, **c["rules"], "judge": "claude-rescope-2026-11-26"})
            log.append({"file": "pooled/rules.jsonl", "id": qid, "field": "rules", "old": None, "new": c["rules"]["rules"],
                        "why": c["why"]})
    rules_path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rules))
    (HERE / "rescope-2026-11-26.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log))
    print(f"{len(log)} changes in {len({r['id'] for r in log})} questions")


if __name__ == "__main__":
    main()
