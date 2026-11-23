"""paired_export.py SNAPDIR SRC...: write semcheck packets for the sampled units whose content differs between the
trees in SNAPDIR (before a fix) and corpus/parsed (after), BOTH sides, so one judge judges both (S128). Then run
`semcheck run --source SRC...`. Prints the unit pairs to pairs.json next to this script's output."""
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from system.rag import semcheck as S
from system.rag.corpus import CORPUS_DIR

snap, sids = Path(sys.argv[1]), sys.argv[2:]
def packets():
    return {(rec["source_id"], pk["version_id"], pk["unit"]): pk for rec, _t, pk in S.sampled_packets(sids)}
after = packets()
bak = CORPUS_DIR / "parsed" / "_bak_after"
swapped = []
try:
    for sid in sids:
        for f in (snap / sid).glob("*.json"):
            cur = CORPUS_DIR / "parsed" / sid / f.name
            if cur.exists() and cur.read_bytes() != f.read_bytes():
                (bak / sid).mkdir(parents=True, exist_ok=True)
                shutil.copy2(cur, bak / sid / f.name)
                shutil.copy2(f, cur)
                swapped.append((cur, bak / sid / f.name))
    before = packets()
finally:
    for cur, b in swapped:
        shutil.copy2(b, cur)
    shutil.rmtree(bak, ignore_errors=True)
pairs = []
for sid in sids:
    out = CORPUS_DIR / "parsed" / sid / "semcheck"
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.json"):
        old.unlink()
for k, a in after.items():
    b = before.get(k)
    if b is None or b["key"] == a["key"]:
        continue
    pairs.append({"source_id": k[0], "version_id": k[1], "unit": k[2], "family": a["family"], "stratum": a["stratum"],
                  "before": b["key"], "after": a["key"]})
    for pk in (b, a):
        (CORPUS_DIR / "parsed" / k[0] / "semcheck" / f"{pk['key']}.json").write_text(S.dump_packet(pk), encoding="utf-8")
Path(sys.argv[0]).with_name("pairs-last.json")  # copy it to pairs-fixN.json.write_text(json.dumps(pairs, indent=1))
print(f"{len(pairs)} changed units, {2 * len(pairs)} packets")
