"""Tests for the 2023-2024 Home Office booklet parser (system/rag/parse_booklet.py).

Hand-made lines test each layout rule; the real-file tests skip where the raw files are missing, and take their
counts from the booklets (contents pages, headings, captions as printed)."""

from collections import Counter
from pathlib import Path

import pytest

from system.rag import parse_booklet as B
from system.rag.chunk import chunk_tree
from system.rag.corpus import load_sources, parser_for
from system.rag.parse_guide import records, read_guide

ROOT = Path(__file__).parent.parent
SOURCE = "fso-guidance-collection"
TITLE = "A guide to making your small block of flats safe from fire"
META = {"source_id": SOURCE, "version_id": "making-your-small-block-of-flats-safe-from-fire--x@2025-01-20-abc",
        "valid_from": "2025-01-20", "valid_to": None, "sha256": "abc", "title": TITLE}
LIGHT, MEDIUM, BOLD, REGULAR = "HelveticaNeue-Light", "HelveticaNeue-Medium", "HelveticaNeue-Bold", "HelveticaNeue"
W, H = 595.3, 841.9


def ln(page, top, text, size=12.0, font=LIGHT, x0=70.9, colour=None):
    words, x = [], float(x0)
    for w in text.split():
        word = {"x0": x, "x1": x + 5.5 * len(w), "text": w, "s": size, "f": font}
        if colour:
            word["c"] = colour
        words.append(word)
        x += 5.5 * (len(w) + 1)
    return {"page": page, "top": float(top), "x0": float(x0), "size": size, "font": font, "text": text,
            "words": words}


def col(page, top, texts, x0, step=14.4):
    return [ln(page, top + k * step, t, x0=x0) for k, t in enumerate(texts)]


def header(page, number):
    return [ln(page, 26.6, "A guide to making your small block of flats safe from fire", 8.0, x0=342),
            ln(page, 34.0, str(number), 8.0, MEDIUM, x0=547)]


def doc():
    lines, graphics = [], []
    lines += [ln(1, 60, "A Guide to making your small", 33.0, BOLD), ln(2, 60, "© Crown copyright 2024")]
    lines += [ln(3, 100, "Contents", 35.0, MEDIUM), ln(3, 258, "1. Introduction", 12.0, MEDIUM)]
    # page 4: chapter title, magenta repeat, lead paragraph, two columns with a sentence across them
    lines += header(4, 1) + [ln(4, 89, "Introduction", colour=[0.9, 0.0, 0.49]), ln(4, 100, "1. Introduction", 35.0, MEDIUM)]
    lines += [ln(4, 230, "This Guide has been published to", 14.0, MEDIUM), ln(4, 247, "provide simple advice.", 14.0, MEDIUM)]
    lines += col(4, 300, ["The fire safety legislation applies to", "the common parts of blocks of flats and to"], 70.9)
    lines += col(4, 300, ["the doors of every flat that open into", "the common parts of the building.¹"], 321.7)
    lines += [ln(4, 400, "Scope of this Guide", 16.0, BOLD, x0=321.7)]
    lines += col(4, 430, ["This Guide is intended to cover small", "general needs blocks of flats."], 321.7)
    lines += [ln(4, 560, "You have a responsibility", 14.0, REGULAR, x0=100), ln(4, 577, "to keep residents safe.", 14.0, REGULAR, x0=100)]
    lines += [ln(4, 797, "1 www.gov.uk/guidance/check-your-fire-safety-responsibilities", 11.0)]
    # page 5: a captioned figure in the left column, text in the right column, a form with Yes/No boxes
    lines += header(5, 2) + [ln(5, 95, "Figure 1", 12.0, MEDIUM)]
    lines += [ln(5, 150, "Stair", 9.0, MEDIUM, x0=120), ln(5, 210, "Entrance", 9.0, MEDIUM, x0=160)]
    graphics += [{"page": 5, "kind": "rect", "top": 120.0, "bottom": 260.0, "x0": 72.0, "x1": 230.0, "fill": False,
                  "stroke": True, "colour": [0.5]}]
    lines += col(5, 95, ["Flats are often arranged around a", "single common stairway, with two flats",
                         "on each floor of the block and a door", "from the street into the stairway."], 321.7)
    lines += [ln(5, 400, "8. Fire risk assessment checklist", 35.0, MEDIUM), ln(5, 460, "Arson", 15.0, REGULAR)]
    q = ln(5, 490, "Is the building adequately secured?   Yes   No")
    q["words"][-2] = {**q["words"][-2], "x0": 440.0, "x1": 459.0}
    q["words"][-1] = {**q["words"][-1], "x0": 514.0, "x1": 529.0}
    lines += [q]
    return {"lines": lines, "graphics": graphics, "images": [], "tables": [], "rects": [], "page_count": 5,
            "page_width": W, "page_height": H, "pages": {p: {"width": W, "height": H} for p in range(1, 6)}}


@pytest.fixture(scope="module")
def tree():
    return B.build_tree(doc(), META)


def sec(tree, local):
    return next(s for s in tree["sections"] if s["id"] == f"small-flats:{local}")


def test_slug_from_version_id_and_unique_ids(tree):
    ids = [s["id"] for s in tree["sections"]]
    assert all(i.startswith("small-flats:") for i in ids) and len(ids) == len(set(ids))
    assert B.slug_for("check-your-fire-safety-responsibilities-under-sect--x@1") == "bsa-section-156"


def test_chapter_lead_paragraph_and_columns(tree):
    ch = sec(tree, "1-introduction")
    assert ch["type"] == "chapter" and ch["number"] == "1" and ch["heading_path"] == [TITLE, "1. Introduction"]
    assert sec(tree, "1-introduction-para-1")["text"] == "This Guide has been published to provide simple advice."
    p = sec(tree, "1-introduction-para-2")
    assert p["text"] == ("The fire safety legislation applies to the common parts of blocks of flats and to the doors "
                         "of every flat that open into the common parts of the building.¹")
    assert p["footnotes"] == ["¹ www.gov.uk/guidance/check-your-fire-safety-responsibilities"]
    assert p["printed_page"] == "1"
    assert not any("A guide to making" in s["text"] or s["text"] == "Introduction" for s in tree["sections"])


def test_heading_and_callout_box(tree):
    h = sec(tree, "1-introduction-scope-of-this-guide")
    assert h["type"] == "heading" and h["heading_path"][-1] == "Scope of this Guide"
    assert sec(tree, "1-introduction-scope-of-this-guide-para-1")["text"].endswith("blocks of flats.")
    box = next(s for s in tree["sections"] if s["type"] == "box")
    assert box["text"] == "You have a responsibility to keep residents safe." and box["title"] is None


def test_figure_in_its_column(tree):
    f = sec(tree, "figure-1")
    assert f["title"] is None and f["heading_path"][-1] == "Figure 1"
    assert f["area"]["x1"] < 315 and f["area"]["bottom"] >= 259 and f["labels"] == ["Stair", "Entrance"]
    assert any(s["text"].endswith("a door from the street into the stairway.") for s in tree["sections"])


def test_checklist_drops_the_answer_boxes(tree):
    p = sec(tree, "8-fire-risk-assessment-arson-para-1")
    assert p["text"] == "Is the building adequately secured?"


def test_chunker_takes_the_tree(tree):
    chunks, _ = chunk_tree(tree, {"id": SOURCE, "kind": "guidance", "nation": "england"}, {})
    assert {"paragraph", "box", "figure"} <= {c["chunk_type"] for c in chunks}


def test_sources_yaml_sends_the_four_booklets_to_parse_booklet():
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    recs = records(SOURCE, src, B.MODULE)
    assert sorted(B.slug_for(r["version_id"]) for r in recs) == \
        ["bsa-section-156", "fire-safety-england-regs", "small-flats", "small-paying-guest"]
    assert all(parser_for(src, r["version_id"]) == "parse_booklet" for r in recs)


# ---------------------------------------------------------------- real files

def _tree(slug):
    pytest.importorskip("pdfplumber")
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    rec = next((r for r in records(SOURCE, src, B.MODULE) if B.slug_for(r["version_id"]) == slug), None)
    if rec is None or not (ROOT / rec["raw_path"]).exists():
        pytest.skip(f"{slug} raw file not on this machine")
    tree = B.build_tree(read_guide(ROOT / rec["raw_path"]), {**rec, "title": rec["part_title"]})
    B.drop_blank_pictures(ROOT / rec["raw_path"], tree)
    return tree


@pytest.fixture(scope="module")
def booklets():
    return {s: _tree(s) for s in ("bsa-section-156", "fire-safety-england-regs", "small-flats", "small-paying-guest")}


def chapters(tree):
    return [s["title"] if not s["number"] else f"{s['number']}. {s['title']}" for s in tree["sections"]
            if s["type"] == "chapter"]


def test_real_booklets_follow_their_contents(booklets):
    assert chapters(booklets["bsa-section-156"]) == [
        "Who is this guidance for?", "To which buildings do these new fire safety requirements apply?",
        "Background to Section 156 of the Building Safety Act 2022", "Duties for all Responsible Persons",
        "Duties of Responsible Persons for buildings which contain two or more sets of domestic premises",
        "Other changes to fire safety legislation"]
    assert len(chapters(booklets["fire-safety-england-regs"])) == 9
    assert chapters(booklets["small-flats"])[1:] == [
        "1. Introduction", "2. Your responsibilities", "3. Fire risk assessment", "4. Fire hazards",
        "5. Fire safety measures", "6. Home fire safety advice", "7. Sample fire action notice",
        "8. Fire risk assessment checklist – small blocks of flats"]
    assert [c.split(".")[0] for c in chapters(booklets["small-paying-guest"])[1:]] == [str(n) for n in range(1, 10)]
    for t in booklets.values():
        S = t["sections"]
        assert len({s["id"] for s in S}) == len(S) and not t["issues"]
        assert not any(p in ("Note", "Text", "") for s in S for p in s["heading_path"])
        assert not any(s["text"] in ("Yes", "No", "N/A") for s in S)


def test_real_booklet_figures_and_boxes(booklets):
    small, guest = booklets["small-flats"], booklets["small-paying-guest"]
    figs = [s for s in small["sections"] if s["type"] == "figure"]
    assert sorted(int(s["number"]) for s in figs if s["number"]) == list(range(1, 10))  # Figures 1 to 9
    assert len(figs) == 26 and len([s for s in small["sections"] if s["type"] == "box"]) == 3
    f5 = next(s for s in figs if s["number"] == "5")
    assert "Smoke alarm" in f5["labels"] and f5["area"]["bottom"] < 740  # the shared key is not cut in half
    gfigs = [s for s in guest["sections"] if s["type"] == "figure"]
    assert len(gfigs) == 11 and not any(s["number"] for s in gfigs)
    assert Counter(s["type"] for s in booklets["bsa-section-156"]["sections"])["paragraph"] == 38
