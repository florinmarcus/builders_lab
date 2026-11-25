"""What the library holds and does not hold, written from corpus/sources.yaml (S146, draft 3).

The decomposer prompt names the topics we hold and the documents we do not hold. Draft 2 wrote that list by hand and
said "planning" was not held, though gpdo-2015 and pd-householder-guide are ingested. This file builds both lists
from sources.yaml so they cannot drift:

    python evals/experiments/decomposer/library.py            # print the block
    python evals/experiments/decomposer/library.py --render d3 # prompt-d3.tmpl.md -> prompt-d3.md

A new topic tag or a new not-held source with no entry below stops the build: add a plain phrase or a group.
"""
import argparse
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
HERE = pathlib.Path(__file__).resolve().parent

# Topic tag of a held source -> plain words a builder would use. None: not a topic (language or audience).
TOPICS = {
    "building-regs": "Building Regulations and the Approved Documents", "building-control": "building control",
    "dutyholders": "dutyholder duties", "higher-risk-buildings": "higher-risk buildings",
    "structure": "structure", "fire": "fire safety", "alarms": "smoke and carbon monoxide alarms",
    "energy": "energy efficiency", "ventilation": "ventilation", "damp-mould": "damp and mould",
    "sanitation": "sanitation and hot water", "drainage": "drainage", "accessibility": "access for disabled people",
    "asbestos": "asbestos", "health-safety": "health and safety on site", "cdm": "CDM 2015",
    "dust": "dust and silica", "coshh": "hazardous substances (COSHH)", "cement": None,
    "work-at-height": "work at height", "riddor": "reporting accidents (RIDDOR)", "noise": "noise",
    "vibration": "vibration", "first-aid": "first aid", "welfare": "welfare facilities",
    "electrical": "electrical safety", "gas": "gas safety", "social-housing": "social and rented housing",
    "repairs": "landlord repairs", "awaab": "Awaab's Law", "hhsrs": "housing hazards (HHSRS)",
    "decent-homes": "the Decent Homes Standard", "voids": None, "procurement": "public procurement",
    "cis": "CIS", "vat": "VAT on building work", "party-wall": "party walls",
    "planning": "permitted development for houses (GPDO)",
    "payment": "payment and adjudication (Construction Act)", "contracts": None, "adjudication": None,
    "romanian": None, "migrant-workers": "workers from overseas", "workers": None,
}

# Not-held source id -> group shown in the prompt. Withdrawn and out-of-date sources are left out.
GROUPS = {
    "British Standards and PAS": lambda s: s["kind"] == "standard" and s["id"].startswith(("bs-", "pas-")),
    "BS 7671 and the IET wiring guides": lambda s: s["id"].startswith(("bs-7671", "iet-")),
    "gas industry standards and bulletins (IGEM, Gas Safe)": lambda s: s["id"] in {"igem-up-1b", "gas-safe-bulletins"},
    "NHBC Standards": lambda s: s["id"] == "nhbc-standards",
    "JCT and NEC contracts, schedules of rates": lambda s: s["kind"] == "contract",
    "Planning Portal guides (planning applications)": lambda s: s["id"] == "planning-portal",
    "TrustMark scheme documents": lambda s: s["id"].startswith("trustmark"),
    "Housing Ombudsman codes and reports": lambda s: s["id"].startswith("ombudsman"),
}
# Sources neither held nor worth naming: archives, Romanian copies of held texts, notes kept for us.
SKIP = {"ukgwa", "hse-ro-law", "fa2026-cis", "icaew-budget-2026-vat", "fire-pbbf", "hse-car-consultation"}
# Never in the library: kept by hand (no source in sources.yaml covers them).
NEVER = ["prices or costs of work", "insurance", "worker cards and trade qualifications",
         "manufacturers' instructions", "Scottish, Welsh or Northern Irish rules"]


def sources():
    d = yaml.safe_load((ROOT / "corpus/sources.yaml").read_text())
    return d["sources"] if isinstance(d, dict) else d


def held_topics(S):
    out, unknown = [], set()
    for s in S:
        if s["mode"] != "ingest" or s.get("status") == "out-of-date":
            continue
        for t in s.get("topics") or []:
            if t not in TOPICS:
                unknown.add(t)
            elif TOPICS[t] and TOPICS[t] not in out:
                out.append(TOPICS[t])
    if unknown:
        sys.exit(f"library.py: topic tags with no plain phrase in TOPICS: {sorted(unknown)}")
    return out


def not_held(S):
    groups, unplaced = {g: [] for g in GROUPS}, []
    for s in S:
        if s["mode"] == "ingest" or s.get("status") in ("withdrawn", "out-of-date") or s["id"] in SKIP:
            continue
        g = next((g for g, f in GROUPS.items() if f(s)), None)
        (groups[g] if g else unplaced).append(s["id"])
    if unplaced:
        sys.exit(f"library.py: not-held sources with no group in GROUPS or SKIP: {unplaced}")
    return [g for g, ids in groups.items() if ids]


def block():
    S = sources()
    held, missing = held_topics(S), not_held(S)
    return ("Topics it covers: " + "; ".join(held) + ".\n\n"
            "It does not hold: " + "; ".join(missing + NEVER) + ".")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", metavar="DRAFT", help="fill {LIBRARY} in prompt-DRAFT.tmpl.md")
    a = ap.parse_args()
    if not a.render:
        print(block())
        return
    tmpl = (HERE / f"prompt-{a.render}.tmpl.md").read_text()
    assert tmpl.count("{LIBRARY}") == 1
    (HERE / f"prompt-{a.render}.md").write_text(tmpl.replace("{LIBRARY}", block()))
    print(f"wrote prompt-{a.render}.md")


if __name__ == "__main__":
    main()
