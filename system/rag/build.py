"""Rebuild the regulations search corpus from Git, end to end, the same way on any machine.

    python -m system.rag.build                 # every source with a parser in corpus/sources.yaml
    python -m system.rag.build --load          # ... and load it into the corpus database (owner)
    python -m system.rag.build --source adb    # some sources only (chunk, embed and load still cover all)

Steps, each one the command the runbook (.claude/skills/corpus-document/SKILL.md) names:
1. raw files: python -m system.rag.harvest --only <sources>  (fetches only what is missing, hash checked)
2. parse: the parser named in sources.yaml (parse_legislation, parse_pdf, parse_adoc, parse_html), plus the modules
   in parser.files that take some files of a source (parse_guide); the saved model fixes in corpus/fixes/ make the
   result the same as on the machine that made them
3. python -m system.rag.chunk
4. python -m system.rag.embed      (Titan V2 in London; only new or changed chunks cost money)
5. python -m system.rag.localsearch --build   (the local index, for testing)
6. with --load: python -m system.rag.load   (as builders_corpus_owner, deploy/rds/)

Stops if any parsed tree still has open model checks: those need the check step in the runbook first.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from system.rag.corpus import CORPUS_DIR, load_sources

ROOT = CORPUS_DIR.parent


def run(*args: str) -> None:
    cmd = [sys.executable, "-m", *args]
    print("$ python -m " + " ".join(args), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def parse_commands(src: dict) -> list[list[str]]:
    p = src["parser"]
    mod, sid = p["module"], src["id"]
    if mod == "parse_legislation":
        return [[f"system.rag.{mod}", "--source", sid, "--current"]]
    if mod == "parse_adoc":
        return [[f"system.rag.{mod}", "--source", sid, "--part", part] for part in p.get("parts", [])]
    # Files sent to another parser by version id prefix (parser.files) are parsed by that module too.
    return [[f"system.rag.{m}", "--source", sid] for m in [mod, *(p.get("files") or {})]]


def open_checks(ids: list[str]) -> list[str]:
    out = []
    for sid in ids:
        for tree in (CORPUS_DIR / "parsed" / sid).glob("*.json"):
            n = len(json.loads(tree.read_text(encoding="utf-8")).get("checks", []))
            if n:
                out.append(f"{sid}/{tree.name}: {n} open model checks")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", nargs="*")
    ap.add_argument("--load", action="store_true", help="load into the corpus database at the end")
    ap.add_argument("--skip-harvest", action="store_true", help="raw files are already in corpus/raw")
    a = ap.parse_args(argv)
    sources = [s for s in load_sources()["sources"] if s.get("parser")]
    if a.source:
        sources = [s for s in sources if s["id"] in a.source]
    ids = [s["id"] for s in sources]
    print(f"{len(ids)} sources: {', '.join(ids)}")
    if not a.skip_harvest:
        run("system.rag.harvest", "--only", *ids, "--no-report")
    for s in sources:
        for cmd in parse_commands(s):
            run(*cmd)
    problems = open_checks(ids)
    if problems:
        print("Stopped: open model checks (run the check step in the runbook first):\n  " + "\n  ".join(problems))
        return 1
    run("system.rag.chunk")
    run("system.rag.embed")
    run("system.rag.localsearch", "--build")
    if a.load:
        run("system.rag.load")
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
