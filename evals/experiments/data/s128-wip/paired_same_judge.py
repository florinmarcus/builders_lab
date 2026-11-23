"""paired_same_judge.py PAIRS.json [MODEL] [--list]: paired before/after for one judge (default Opus 5.5)."""
import json, sys
from math import comb
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from system.rag import semcheck as S

def high(v):
    return any(f["severity"] == "high" and (f.get("settled") or {}).get("as") != "model-wrong" for f in v.get("findings") or [])
pairs = json.loads(Path(sys.argv[1]).read_text())
model = next((a for a in sys.argv[2:] if not a.startswith("--")), S.MODEL)
store = {}
rows, missing = [], 0
allv = {}
for sid in sorted({p["source_id"] for p in pairs} | {"circ-adb-2024", "circ-01-2024", "circ-01-2026"}):
    allv.update(S.load_verdicts(sid, model)["verdicts"])  # a page printed in two sources has one key and one verdict
for p in pairs:
    b, a = allv.get(p["before"]), allv.get(p["after"])
    if not b or not a:
        missing += 1
        continue
    rows.append((p, high(b), high(a), a))
fixed = [r for r in rows if r[1] and not r[2]]
broken = [r for r in rows if not r[1] and r[2]]
n, k = len(fixed) + len(broken), min(len(fixed), len(broken))
p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0
hb = sum(r[1] for r in rows)
print(f"judge {model}: {len(rows)} paired units ({missing} missing a verdict); high before {hb} / after {sum(r[2] for r in rows)}; "
      f"fixed {len(fixed)}; broken {len(broken)}; McNemar p {p:.2g}")
if "--list" in sys.argv:
    for r in broken:
        print("BROKEN", r[0]["source_id"], r[0]["version_id"][:50], r[0]["unit"])
        for f in r[3]["findings"]:
            if f["severity"] == "high":
                print("    ", f["kind"], f["problem"][:230], "|", f["evidence"][:200])
