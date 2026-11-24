"""Remap gold labels whose section ids no longer exist in the corpus (S116), 24 Nov 2026.

    python -m evals.golden.remap            # rewrites questions.jsonl, logs every change to remap-2026-11-24.jsonl

Labels were written against older trees. Since then some parsers renamed sections (fire door guidance ids gained
the page title, manual-br chapters gained their titles, ms34 moved to paragraph numbers), the Romanian HSE leaflets
were dropped (English-only corpus, S130: the English leaflet with the same content is used) and the regulation 2
chunks became one chunk per defined term. Each old id maps to one or more new ids, decided by reading the question,
its reference answer and the new section's text (Claude, 24 Nov 2026). A map that differs per question is keyed
by (question id, old id). Remapped questions get labels_version "v3".
"""

from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
FD = "fire-safety-england-regulations-2022-fire-door-guidance-acce-"

# old id -> new ids, the same for every question
BY_ID: dict[str, list[str]] = {
    "hse-hsg264:appendix-4-table-1": ["hse-hsg264:appendix-4-table-p67", "hse-hsg264:appendix-4-table-p67-2"],
    "hse-ms34:who-can-carry-out-medical-surveillance-text-1": ["hse-ms34:para-13", "hse-ms34:para-14"],
    "manual-br:chapter-3-text-1": ["manual-br:chapter-3-do-i-need-to-notify-someone-text-1"],
    "manual-br:chapter-4-text-1": ["manual-br:chapter-4-is-a-building-control-body-involved-text-1"],
    "manual-br:chapter-b-text-1": ["manual-br:chapter-b-should-a-building-control-body-be-involved-text-1"],
    "manual-br:chapter-c-text-1": ["manual-br:chapter-c-competent-person-schemes-and-third-party-testing-text-1"],
    "awaab-tenants:document-4-locuin-ele-n-cazul-c-rora-se-aplic-legea-awaab-text-1":
        ["awaab-tenants:chapter-4-is-my-home-covered-under-awaab-s-law-text-2",
         "awaab-tenants:chapter-4-is-my-home-covered-under-awaab-s-law-text-1"],
    "decent-home-2006:section-4-text-1": ["decent-home-2006:section-4-introduction-text-1"],
    "awaab-collection:document-costs-m-total-transition-average-annual-total-cost-text-1":
        ["awaab-collection:document-monetised-costs-text-1"],
    "hse-cis65:document-text-1": ["hse-cis65:document-what-you-need-to-know-as-a-busy-builder-text-1"],
    "hse-ro-indg450:document-text-1": ["hse-indg450:document-your-health-and-safety-text-1"],
    "hse-ro-indg410:document-alte-sfaturi-text-1": ["hse-indg410:document-other-advice-text-1"],
}

# (question id, old id) -> new ids, where the right section depends on the question
BY_QUESTION: dict[tuple[str, str], list[str]] = {
    ("site-safety-011", "hse-ro-indg410:document-obliga-iile-angajatorului-dvs-text-1"):
        ["hse-indg410:document-information-and-training-text-1"],
    ("site-safety-057", "hse-ro-indg410:document-obliga-iile-angajatorului-dvs-text-1"):
        ["hse-indg410:document-equipment-and-clothing-text-1"],
    ("asbestos-028", "car2012:regulation-2-1"):
        ["car2012:regulation-2-term-relevant-doctor", "car2012:regulation-2-term-appointed-doctor"],
    ("asbestos-049", "car2012:regulation-2-1"): ["car2012:regulation-2-term-the-control-limit"],
}


def new_ids(qid: str, old: str) -> list[str] | None:
    if (qid, old) in BY_QUESTION:
        return BY_QUESTION[(qid, old)]
    if old in BY_ID:
        return BY_ID[old]
    m = re.fullmatch(r"fser-fire-doors:((?:para-[\d.]+)|(?:top-text-\d+))", old)
    if m:
        return [f"fser-fire-doors:{FD}{m.group(1)}"]
    return None


def remap_list(qid: str, keys: list[str], log: list[dict], field: str) -> list[str]:
    out: list[str] = []
    for k in keys:
        n = new_ids(qid, k)
        if n is None:
            out.append(k)
            continue
        log.append({"id": qid, "field": field, "old": k, "new": n})
        out.extend(x for x in n if x not in out)
    return out


def main() -> None:
    path = HERE / "questions.jsonl"
    qs = [json.loads(line) for line in path.open()]
    log: list[dict] = []
    for q in qs:
        before = len(log)
        for field in ("expected_sections", "also_acceptable"):
            if q.get(field):
                q[field] = remap_list(q["id"], q[field], log, field)
        if len(log) > before:
            q["labels_version"] = "v3"
    path.write_text("".join(json.dumps(q, ensure_ascii=False) + "\n" for q in qs))
    (HERE / "remap-2026-11-24.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log))
    print(f"{len(log)} labels remapped in {len({r['id'] for r in log})} questions")


if __name__ == "__main__":
    main()
