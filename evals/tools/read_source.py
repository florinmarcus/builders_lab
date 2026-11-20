"""Read a corpus document as a person would: plain text from the raw files, no section ids, no chunks.

    python evals/tools/read_source.py <source_id>            # title and full text of its current version(s)
    python evals/tools/read_source.py <source_id> --pages 3-9  # PDFs: only some pages
    python evals/tools/read_source.py --list                 # in-scope sources: id, title, kind

For the golden set's business pass (agentic-rag-lab method, corpus/OVERNIGHT-PLAN.md S5): question writers must
not see the parser's section ids or the chunks, so this reads raw/ directly (XML text, HTML text, PDF text).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from system.rag.corpus import CORPUS_DIR, load_sources  # noqa: E402


def xml_text(data: bytes) -> str:
    from lxml import etree

    root = etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=True))
    for meta in root.iter("{http://www.legislation.gov.uk/namespaces/metadata}Metadata"):
        meta.getparent().remove(meta)
    for com in root.iter("{http://www.legislation.gov.uk/namespaces/legislation}Commentaries"):
        com.getparent().remove(com)
    out = []
    for el in root.iter():
        tag = el.tag.split("}")[-1] if isinstance(el.tag, str) else ""
        if tag in ("Title", "Number", "Pnumber", "Text", "td", "th"):
            t = " ".join("".join(el.itertext()).split())
            if t:
                out.append(t)
    return "\n".join(out)


def html_text(data: bytes) -> str:
    import lxml.html

    doc = lxml.html.fromstring(data)
    for bad in doc.xpath("//script|//style|//nav|//header|//footer|//noscript"):
        bad.drop_tree()
    main = doc.xpath("//main") or doc.xpath("//*[contains(@class,'govspeak')]") or [doc]
    text = main[0].text_content()
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def pdf_text(path: Path, pages: tuple[int, int] | None = None) -> str:
    import pdfplumber

    out = []
    with pdfplumber.open(str(path)) as pdf:
        for i, p in enumerate(pdf.pages, start=1):
            if pages and not (pages[0] <= i <= pages[1]):
                continue
            out.append(f"--- page {i} ---\n{p.extract_text() or ''}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sources = {s["id"]: s for s in load_sources()["sources"]}
    if argv and argv[0] == "--list":
        for s in sources.values():
            if s.get("mode") == "ingest" and s.get("fetch", {}).get("method", "none") != "none":
                print(f"{s['id']} | {s.get('kind')} | {s['title']}")
        return 0
    sid = argv[0]
    pages = None
    if "--pages" in argv:
        a, b = argv[argv.index("--pages") + 1].split("-")
        pages = (int(a), int(b))
    src = sources[sid]
    print(f"# {src['title']}\n")
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (CORPUS_DIR / "versions" / sid).glob("*.json")]
    for r in sorted((r for r in recs if r.get("valid_to") is None), key=lambda r: r["part"]):
        raw = ROOT / r["raw_path"]
        if not raw.exists():
            print(f"[{r['part']}: raw file not on this machine]")
            continue
        print(f"## {r.get('part_title') or r['part']} (edition {r.get('edition_date') or r.get('valid_from')})\n")
        mt = r.get("media_type", "")
        if "xml" in mt:
            print(xml_text(raw.read_bytes()))
        elif "html" in mt:
            print(html_text(raw.read_bytes()))
        elif "pdf" in mt:
            print(pdf_text(raw, pages))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
