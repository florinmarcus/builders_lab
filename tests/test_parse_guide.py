"""Tests for the Home Office fire risk assessment guide parser (system/rag/parse_guide.py).

Most tests use hand-made lines in the shape read_pdf gives them, so they need no PDF. The real-file tests skip
where the raw files are missing; their counts come from the guides themselves (contents pages, captions and
"Case study" boxes as printed)."""

import json
import re
from pathlib import Path

import pytest

from system.rag import parse_guide as G
from system.rag.build import parse_commands
from system.rag.chunk import chunk_tree
from system.rag.corpus import load_sources, parser_for

ROOT = Path(__file__).parent.parent
SOURCE = "fso-guidance-collection"
TITLE = "Fire safety risk assessment: offices and shops"
META = {"source_id": SOURCE, "version_id": "fire-safety-risk-assessment-offices-and-shops--x@2023-09-12-abc",
        "valid_from": "2023-09-12", "valid_to": None, "sha256": "abc", "title": TITLE}
BODY = "ITCGaramondStd-Lt"
BLUE = [1.0, 0.88, 0.0, 0.05]
W, H = 595.0, 842.0


def ln(page, top, text, size=10.0, font=BODY, x0=100.0, colour=None):
    """A line as read_pdf gives it: words with x positions (5 points per character), size, font and colour."""
    words, x = [], float(x0)
    for w in text.split():
        word = {"x0": x, "x1": x + 5 * len(w), "text": w, "s": size, "f": font}
        if colour:
            word["c"] = colour
        words.append(word)
        x += 5 * (len(w) + 1)
    return {"page": page, "top": float(top), "x0": float(x0), "size": size, "font": font, "text": text,
            "words": words}


def body(page, top, texts, x0=100.0, step=12.0):
    return [ln(page, top + k * step, t, x0=x0) for k, t in enumerate(texts)]


def rect(page, top, bottom, x0, x1, fill=True, stroke=False, colour=(0.2, 0.18, 0.0, 0.01), kind="rect"):
    return {"page": page, "kind": kind, "top": top, "bottom": bottom, "x0": x0, "x1": x1, "fill": fill,
            "stroke": stroke, "colour": colour}


def side_tab(page):
    return ([ln(page, 120, "Part 2 • Further guidance on fire risk assessment", 8.6, "HelveticaNeueLTStd-Lt", 560),
             ln(page, 800, str(39 + page), 9.0, "HelveticaNeueLTStd-Lt", 45)],
            [rect(page, 0, H, 553, W, colour=(0.2, 0.18, 0.0, 0.01))])


def doc():
    lines, graphics, images = [], [], []
    lines += [ln(1, 300, "Fire safety risk assessment", 28.0, "HelveticaNeueLTStd-Lt")]
    lines += [ln(2, 98, "Contents", 28.0, "HelveticaNeueLTStd-Lt"), ln(2, 140, "Part 2 Further guidance 41")]
    # page 3: Part and Section titles, a numbered heading, two paragraphs, a figure with its caption ABOVE the
    # photo, a sub-heading, a case study box and a footnote
    lines += [ln(3, 90, "Part 2 Further guidance on fire risk assessment", 28.0, "HelveticaNeueLTStd-Lt"),
              ln(3, 130, "Section 1 Further guidance on fire risks", 24.0, "HelveticaNeueLTStd-Lt"),
              ln(3, 170, "1.2 Storage", 13.0, "HelveticaNeueLTStd-Bd", colour=BLUE)]
    lines += body(3, 190, ["Poor housekeeping and storage of goods can increase",
                           "the risk of fire in all kinds of premises and shops."])
    lines += body(3, 226, ["Store excess stock in a dedicated storage area away",
                           "from escape routes and from all sources of heat."])
    lines += [ln(3, 260, "Figure 14: An example of poor storage", 9.0, "HelveticaNeueLTStd-It")]
    images += [{"page": 3, "top": 274.0, "bottom": 400.0, "x0": 100.0, "x1": 300.0}]
    lines += [ln(3, 420, "Voids", 10.0, "HelveticaNeueLTStd-Bd")]
    lines += body(3, 434, ["Voids should not be used for storing combustible things",
                           "and should be covered by the Regulations 2002⁷ as well."])
    graphics += [rect(3, 470, 560, 100, 300)]
    lines += [ln(3, 476, "Case study", 9.0, "HelveticaNeueLTStd-Roman", 105),
              ln(3, 490, "A retailer had too much stock in the shop", 9.0, "HelveticaNeueLTStd-Roman", 105),
              ln(3, 501, "and moved it to a safe dedicated storeroom.", 9.0, "HelveticaNeueLTStd-Roman", 105)]
    lines += [ln(3, 780, "⁷ Dangerous Substances and Explosive Atmospheres Regulations 2002.", 7.0,
                 "HelveticaNeueLTStd-Roman")]
    # page 4: two columns; a sentence runs on from the left column to the right; a wrapped numbered heading;
    # a figure with its caption BELOW the drawing (as in Part 1)
    lines += [ln(4, 90, "1.3 Dangerous substances: storage,", 13.0, "HelveticaNeueLTStd-Bd", colour=BLUE),
              ln(4, 105, "display and use", 13.0, "HelveticaNeueLTStd-Bd", colour=BLUE)]
    lines += body(4, 125, ["Specific precautions are needed when you store",
                           "dangerous substances in your premises because",
                           "the risk of fire in"])
    lines += body(4, 125, ["the building is otherwise much higher than",
                           "it would be without these substances present.",
                           "Your supplier can give you good advice on this."], x0=330)
    lines += [ln(4, 200, "Flammable liquids", 10.0, "HelveticaNeueLTStd-Bd", 330)]
    lines += body(4, 214, ["Highly flammable liquids present a particularly",
                           "high fire risk in all shops and in offices too."], x0=330)
    graphics += [rect(4, 300, 420, 100, 300, fill=False, stroke=True, colour=(0.0,)),
                 rect(4, 320, 380, 140, 260, fill=True, colour=(0.9, 0.1, 0.1))]
    lines += [ln(4, 350, "FUEL", 7.8, "HelveticaNeue-Roman", 180),
              ln(4, 426, "Figure 15: The fire triangle", 10.0, "HelveticaNeueLTStd-It")]
    for p in (3, 4):
        tl, tg = side_tab(p)
        lines += tl
        graphics += tg
    return {"lines": lines, "graphics": graphics, "images": images, "tables": [], "rects": [],
            "page_count": 4, "page_width": W, "page_height": H,
            "pages": {p: {"width": W, "height": H} for p in range(1, 5)}}


@pytest.fixture(scope="module")
def tree():
    return G.build_tree(doc(), META)


def sec(tree, local):
    return next(s for s in tree["sections"] if s["id"] == f"offices-shops:{local}")


def test_ids_are_prefixed_with_the_guide_and_unique(tree):
    ids = [s["id"] for s in tree["sections"]]
    assert all(i.startswith("offices-shops:") for i in ids) and len(ids) == len(set(ids))
    assert tree["parser"] == G.PARSER and tree["title"] == TITLE


def test_guide_slug():
    assert G.guide_slug("Fire safety risk assessment: offices and shops") == "offices-shops"
    assert G.guide_slug("Fire safety risk assessment: means of escape for disabled people (single document, "
                        "including appendices)") == "means-escape-disabled-people"
    assert G.guide_slug("Fire safety risk assessment: theatres, cinemas and similar premises") == \
        "theatres-cinemas-similar-premises"


def test_part_section_headings_and_heading_path(tree):
    types = {s["id"].split(":")[1]: s["type"] for s in tree["sections"]}
    assert types["part-2"] == "part" and types["section-1"] == "chapter"
    voids = sec(tree, "1-2-storage-voids-para-1")
    assert voids["type"] == "paragraph"
    assert voids["heading_path"] == [TITLE, "Part 2 Further guidance on fire risk assessment",
                                     "Section 1 Further guidance on fire risks", "1.2 Storage", "Voids"]
    assert voids["parent_id"] == "offices-shops:1-2-storage-voids"
    h = sec(tree, "1-3-dangerous-substances-storage-display")
    assert h["number"] == "1.3" and h["title"] == "Dangerous substances: storage, display and use"
    assert not any(p in ("Note", "Text") for s in tree["sections"] for p in s["heading_path"])


def test_one_paragraph_per_paragraph(tree):
    p1, p2 = sec(tree, "1-2-storage-para-1"), sec(tree, "1-2-storage-para-2")
    assert p1["text"].startswith("Poor housekeeping") and p1["text"].endswith("shops.")
    assert p2["text"].startswith("Store excess stock")


def test_sentence_runs_on_across_the_column(tree):
    p = sec(tree, "1-3-dangerous-substances-storage-display-para-1")
    assert "the risk of fire in the building is otherwise much higher" in p["text"]
    assert p["text"].endswith("good advice on this.")
    fl = sec(tree, "1-3-dangerous-substances-storage-display-flammable-liquids-para-1")
    assert fl["heading_path"][-1] == "Flammable liquids"


def test_figure_with_its_caption_above_the_photo(tree):
    f = sec(tree, "figure-14")
    assert f["type"] == "figure" and f["number"] == "14" and f["title"] == "An example of poor storage"
    assert f["caption_above"] is True and f["image_bbox"]["top"] == 274.0
    assert f["area"]["top"] >= f["caption_box"]["bottom"] and f["area"]["bottom"] <= 402
    assert f["heading_path"][-1] == "Figure 14 An example of poor storage"


def test_figure_with_its_caption_below_the_drawing(tree):
    f = sec(tree, "figure-15")
    assert f["caption_above"] is False and "image_bbox" not in f
    assert f["area"]["bottom"] <= f["caption_box"]["top"] and f["area"]["top"] <= 300
    assert f["labels"] == ["FUEL"]
    assert {c["section_id"] for c in tree["checks"]} >= {f["id"], sec(tree, "figure-14")["id"]}


def test_case_study_box(tree):
    b = sec(tree, "1-2-storage-voids-case-study-1")
    assert b["type"] == "box" and b["title"] == "Case study"
    assert b["text"] == "A retailer had too much stock in the shop and moved it to a safe dedicated storeroom."
    assert not any("retailer" in s["text"] for s in tree["sections"] if s["type"] == "paragraph")


def test_side_tab_page_numbers_and_footnotes(tree):
    assert not any("Further guidance on fire risk assessment" in s["text"] for s in tree["sections"])
    assert sec(tree, "1-2-storage-para-1")["printed_page"] == "42"
    voids = sec(tree, "1-2-storage-voids-para-1")
    assert "Regulations 2002⁷" in voids["text"]
    assert voids["footnotes"] == ["⁷ Dangerous Substances and Explosive Atmospheres Regulations 2002."]


def test_heading_number_jump_is_an_issue():
    d = doc()
    d["lines"] = [l for l in d["lines"] if l["page"] != 4 or not l["text"].startswith(("1.3", "display"))]
    d["lines"].append(ln(4, 90, "1.4 Equipment and machinery", 13.0, "HelveticaNeueLTStd-Bd", colour=BLUE))
    issues = G.build_tree(d, META)["issues"]
    assert any("jump from 1.2 to 1.4" in i for i in issues)


def test_chunker_takes_the_tree_unchanged(tree):
    chunks, _ = chunk_tree(tree, {"id": SOURCE, "kind": "guidance", "nation": "england"}, {})
    kinds = {c["chunk_type"] for c in chunks}
    assert {"paragraph", "figure", "box"} <= kinds
    assert all(c["embed_text"].startswith(TITLE) for c in chunks)


# ---------------------------------------------------------------- choosing the parser per file

def test_parser_for_sends_some_files_to_another_module():
    src = {"parser": {"module": "parse_pdf", "files": {"parse_guide": ["fire-safety-risk-assessment-offices-"]}}}
    assert parser_for(src, "fire-safety-risk-assessment-offices-and-shops--x@1") == "parse_guide"
    assert parser_for(src, "fire-safety-risk-assessment-5-step-checklist--x@1") == "parse_pdf"
    assert parser_for({"parser": {"module": "parse_pdf"}}, "anything") == "parse_pdf"
    assert parser_for({}, "anything") is None


def test_build_runs_every_parser_a_source_names():
    src = {"id": "s", "parser": {"module": "parse_pdf", "files": {"parse_guide": ["x"]}}}
    assert parse_commands(src) == [["system.rag.parse_pdf", "--source", "s"], ["system.rag.parse_guide", "--source", "s"]]
    assert parse_commands({"id": "s", "parser": {"module": "parse_pdf"}}) == [["system.rag.parse_pdf", "--source", "s"]]


def test_sources_yaml_sends_the_guides_and_only_the_guides_to_parse_guide():
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    recs = G.records(SOURCE, src)
    names = [r["version_id"].split("--")[0] for r in recs]
    assert len(recs) == 13 and all(n.startswith("fire-safety-risk-assessment-") for n in names)
    assert not any("5-step" in n for n in names)
    assert parser_for(src, "fire-safety-risk-assessment-5-step-checklist--fire-safety-risk-assessment-5-step-"
                           "checklist@2025-01-20-2ae5e597") == "parse_pdf"


# ---------------------------------------------------------------- real files

def _tree(prefix):
    pytest.importorskip("pdfplumber")
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    rec = next((r for r in G.records(SOURCE, src) if r["version_id"].startswith(prefix)), None)
    if rec is None or not (ROOT / rec["raw_path"]).exists():
        pytest.skip(f"{prefix} raw file not on this machine")
    return G.build_tree(G.read_guide(ROOT / rec["raw_path"]), {**rec, "title": rec["part_title"]})


@pytest.fixture(scope="module")
def offices():
    return _tree("fire-safety-risk-assessment-offices-and-shops--")


@pytest.fixture(scope="module")
def animal():
    return _tree("fire-safety-risk-assessment-animal-premises-and-st--")


@pytest.fixture(scope="module")
def disabled():
    return _tree("fire-safety-risk-assessment-means-of-escape-for-di--")


def numbered(tree):
    """Numbered headings by the Step, Section, chapter or appendix they belong to."""
    by = {s["id"]: s for s in tree["sections"]}
    out: dict[str, list[str]] = {}
    for s in tree["sections"]:
        if s["type"] == "heading" and s["number"]:
            p = s
            while by[p["parent_id"]]["type"] == "heading":
                p = by[p["parent_id"]]
            out.setdefault(p["parent_id"].split(":")[1], []).append(s["number"])
    return out


def kinds(tree, kind):
    return [s for s in tree["sections"] if s["type"] == kind]


def _clean(tree):
    """Checks every guide must pass: no "Note"/"Text" breadcrumbs, no side tab text, figure crops on the right
    side of their caption and clear of other captions."""
    S = tree["sections"]
    assert not any(p in ("Note", "Text") for s in S for p in s["heading_path"])
    assert not any("Further guidance on fire risk assessment and fire precautions" in s["text"] for s in S)
    assert len({s["id"] for s in S}) == len(S)
    figs = [s for s in S if s["type"] == "figure" and s.get("area")]
    for f in figs:
        a, c = f["area"], f["caption_box"]
        if f["number"] and f["caption_above"]:
            assert a["top"] >= c["bottom"] - 0.1, f["id"]
        elif f["number"]:
            assert a["bottom"] <= c["top"] + 0.1, f["id"]
        for o in figs:
            oc = o["caption_box"]
            if o is not f and o["number"] and oc["page"] == a["page"]:
                assert not (a["top"] < oc["top"] + 5 < a["bottom"] and a["x0"] < oc["x0"] + 5 < a["x1"]), (f["id"], o["id"])


def test_real_offices_and_shops(offices):
    _clean(offices)
    assert numbered(offices) == {
        "step-1": ["1.1", "1.2", "1.3"],
        "step-3": ["3.1", "3.2", "3.3", "3.4", "3.4.1", "3.4.2", "3.4.3", "3.4.4", "3.4.5", "3.4.6"],
        "step-4": ["4.1", "4.2", "4.3", "4.4"],
        "section-1": [f"1.{n}" for n in range(1, 14)], "section-2": [f"2.{n}" for n in range(1, 8)],
        "section-3": ["3.1", "3.2", "3.3"], "section-4": ["4.1", "4.2"], "section-7": ["7.1", "7.2", "7.3", "7.4"],
        "appendix-a": ["A1", "A2"], "appendix-b": ["B1", "B2", "B3"]}
    figs = [s for s in kinds(offices, "figure") if s["number"]]
    assert sorted(int(s["number"]) for s in figs) == list(range(1, 64))  # Figures 1 to 63
    assert len(kinds(offices, "box")) == 7  # seven "Case study" boxes
    assert [s["number"] for s in kinds(offices, "table") if s["number"]] == ["1", "2", "3"]
    assert [s["id"].split(":")[1] for s in offices["sections"] if s["type"] in ("part", "appendix")] == \
        ["part-1", "part-2", "appendix-a", "appendix-b", "appendix-c", "appendix-d"]
    assert [s["number"] for s in offices["sections"] if s["type"] == "chapter" and s["number"]] == \
        ["1", "2", "3", "4", "5", "1", "2", "3", "4", "5", "6", "7", "8"]  # Steps 1-5, Sections 1-8
    assert not offices["issues"]
    f14 = next(s for s in figs if s["number"] == "14")
    assert f14["caption_above"] and f14.get("image_bbox") and f14["title"] == "An example of poor storage"
    p = next(s for s in offices["sections"] if s["heading_path"][-1] == "Flammable liquids" and s["type"] == "paragraph")
    assert p["heading_path"][-2] == "1.3 Dangerous substances: storage, display and use"


def test_real_animal_premises(animal):
    _clean(animal)
    n = numbered(animal)
    assert n["section-1"] == [f"1.{k}" for k in range(1, 16)] and n["section-2"] == [f"2.{k}" for k in range(1, 10)]
    assert n["section-7"] == ["7.1", "7.2", "7.3", "7.4", "7.5"]
    figs = sorted(int(s["number"]) for s in kinds(animal, "figure") if s["number"])
    assert figs == [k for k in range(1, 58) if k != 10]  # the guide has no Figure 10
    assert len(kinds(animal, "box")) == 3
    # the guide prints "Table 3" twice and Appendix C's first heading without "C1": both are listed as issues
    assert len(animal["issues"]) == 2


def test_real_means_of_escape_for_disabled_people(disabled):
    _clean(disabled)
    n = numbered(disabled)
    assert n["chapter-1"] == [f"1.{k}" for k in range(1, 8)]
    assert n["chapter-3"] == [f"3.{k}" for k in range(1, 6)]
    assert [x for x in n["chapter-4"] if x.count(".") == 1] == [f"4.{k}" for k in range(1, 10)]
    assert [s["number"] for s in disabled["sections"] if s["type"] == "appendix"] == [str(k) for k in range(1, 8)]
    boxes = kinds(disabled, "box")
    assert len(boxes) == 8 and all(re.match(r"^Example( \d)?$", b["title"]) for b in boxes)
    assert not disabled["issues"]


def test_real_ids_are_unique_across_the_guides(offices, animal, disabled):
    ids = [s["id"] for t in (offices, animal, disabled) for s in t["sections"]]
    assert len(ids) == len(set(ids))
    assert json.loads(json.dumps(offices))["sections"]
