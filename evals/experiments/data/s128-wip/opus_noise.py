"""Opus judge noise (S128, 23 Nov 2026): the 150 designed noise units of the Fable round, judged twice by Opus 5.5 in
fresh runs, kept apart from every verdict store. Writes evals/experiments/data/semcheck-noise-opus-2026-11-23.json.

    python evals/experiments/data/s128-wip/opus_noise.py [run|report]
"""
import json, subprocess, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from system.rag import semcheck as S

ROOT = S.ROOT
DATA = ROOT / "evals/experiments/data"
OUT = DATA / "semcheck-noise-opus-2026-11-23.json"
WORK = ROOT / "corpus/parsed/_noise-opus"
MODEL = "claude-opus-5-5"


def klass(fs):
    fs = fs or []
    return "high" if any(f.get("severity") == "high" for f in fs) else ("low" if fs else "ok")


def packets():
    units = json.loads((DATA / "semcheck-noise-2026-11-23.json").read_text())["designed"]
    want = defaultdict(dict)
    for u in units:
        want[u["source_id"]][(u["version_id"], u["unit"])] = u
    out = []
    for rec, _tree, pk in S.sampled_packets(sorted(want)):
        u = want[rec["source_id"]].get((pk["version_id"], pk["unit"]))
        if u is not None:
            out.append((u, pk))
    return out


def run_once(n, pks):
    d = WORK / f"run{n}"
    (d / "packets").mkdir(parents=True, exist_ok=True)
    files = []
    for u, pk in pks:
        f = d / "packets" / f"{pk['key']}.json"
        f.write_text(S.dump_packet(pk), encoding="utf-8")
        files.append(f)

    def one(arg):
        i, fs = arg
        ans = d / f"batch_{i:04d}.jsonl"
        if ans.exists():
            return
        prompt = S.PROMPT.format(root=ROOT, answers=ans.relative_to(ROOT).as_posix(),
                                 packets="\n".join(f"- `{f.relative_to(ROOT).as_posix()}`" for f in fs))
        for _ in range(2):
            subprocess.run(["claude", "-p", prompt, "--model", MODEL, "--allowedTools", "Read,Write"],
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=2400, cwd=ROOT)
            if ans.exists():
                break
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, enumerate(S.batches(files), start=1)))
    got = {}
    for f in d.glob("batch_*.jsonl"):
        for line in f.read_text().splitlines():
            try:
                a = json.loads(line)
            except Exception:
                continue
            if isinstance(a, dict) and not S.check_answer(a):
                got[a["key"]] = a
    return got


def main():
    pks = packets()
    if sys.argv[1:] == ["run"]:
        r1, r2 = run_once(1, pks), run_once(2, pks)
        rows = []
        for u, pk in pks:
            rows.append({k: u[k] for k in ("source_id", "version_id", "unit", "family")} |
                        {"key": pk["key"], "unchanged": pk["key"] == u["key"], "fable_saved": u["saved"],
                         "fable_again": u["again"],
                         "opus_1": klass(r1[pk["key"]]["findings"]) if pk["key"] in r1 else None,
                         "opus_2": klass(r2[pk["key"]]["findings"]) if pk["key"] in r2 else None,
                         "opus_1_findings": (r1.get(pk["key"]) or {}).get("findings"),
                         "opus_2_findings": (r2.get(pk["key"]) or {}).get("findings")})
        OUT.write_text(json.dumps({"about": __doc__.strip().split("\n")[0], "model": MODEL, "units": rows},
                                  ensure_ascii=False, indent=1) + "\n")
    report()


def report():
    rows = [r for r in json.loads(OUT.read_text())["units"] if r["opus_1"] and r["opus_2"]]
    def flips(a, b, rs):
        hh = [r for r in rs if (r[a] == "high") != (r[b] == "high")]
        return len(hh), len(rs)
    n, t = flips("opus_1", "opus_2", rows)
    cls = sum(r["opus_1"] != r["opus_2"] for r in rows)
    h1 = [r for r in rows if r["opus_1"] == "high"]
    print(f"Opus run 1 vs run 2: {t} units, class flips {cls}, high-flag flips {n} ({n/t:.1%}, 95% {S.wilson(n,t)[0]:.1%} to {S.wilson(n,t)[1]:.1%}); "
          f"high to not high {sum(r['opus_2']!='high' for r in h1)} of {len(h1)}; not high to high {sum(r['opus_2']=='high' for r in rows if r['opus_1']!='high')} of {t-len(h1)}")
    same = [r for r in rows if r["unchanged"]]
    for a in ("fable_saved", "fable_again"):
        n, t = flips("opus_1", a, same)
        both = sum(r["opus_1"] == "high" and r[a] == "high" for r in same)
        print(f"Opus run 1 vs Fable {a}: {t} unchanged units, high-flag disagree {n} ({n/t:.1%}); both high {both}, "
              f"Opus only {sum(r['opus_1']=='high' and r[a]!='high' for r in same)}, Fable only {sum(r['opus_1']!='high' and r[a]=='high' for r in same)}")
    print("high rate: Opus run 1 {:.1%}, run 2 {:.1%}, Fable saved {:.1%} (same units)".format(
        sum(r['opus_1']=='high' for r in same)/len(same), sum(r['opus_2']=='high' for r in same)/len(same),
        sum(r['fable_saved']=='high' for r in same)/len(same)))
    fams = sorted({r["family"] for r in rows})
    for f in fams:
        rs = [r for r in rows if r["family"] == f]
        print(f"  {f}: {len(rs)} units, Opus flips {flips('opus_1','opus_2',rs)[0]}, Opus high {sum(r['opus_1']=='high' for r in rs)}, Fable high {sum(r['fable_saved']=='high' for r in rs)}")


if __name__ == "__main__":
    main()
