"""Tests for the purpose-built flats guide parser (system/rag/parse_flats.py).

Hand-made lines in the shape read_pdf gives them test each layout rule without a PDF. The real-file tests skip
where the raw file is missing; their counts come from the guide itself (contents pages, paragraph numbers as
printed, captions, the glossary table)."""

import re
from collections import Counter
from pathlib import Path

import pytest

from system.rag import parse_flats as F
from system.rag.chunk import chunk_tree
from system.rag.corpus import load_sources, parser_for
from system.rag.parse_guide import records, read_guide

ROOT = Path(__file__).parent.parent
SOURCE = "fso-guidance-collection"
TITLE = "Fire safety in purpose-built blocks of flats"
META = {"source_id": SOURCE, "version_id": "fire-safety-in-purpose-built-blocks-of-flats--x@2024-12-02-abc",
        "valid_from": "2024-12-02", "valid_to": None, "sha256": "abc", "title": TITLE}
GREEN = [0.76, 0.84, 0.18]
W, H = 596.0, 842.0


def ln(page, top, text, size=12.0, font="ArialMT", x0=54.0, colour=None, step=6.0):
    """A line as read_pdf gives it: words with x positions (step points per character)."""
    words, x = [], float(x0)
    for w in text.split():
        word = {"x0": x, "x1": x + step * len(w), "text": w, "s": size, "f": font}
        if colour:
            word["c"] = colour
        words.append(word)
        x += step * (len(w) + 1)
    return {"page": page, "top": float(top), "x0": float(x0), "size": size, "font": font, "text": text,
            "words": words}


def para(page, top, number, texts, x0=54.0, indent=28.3, step=16.0):
    """A numbered paragraph: the number hangs at x0, the text starts at x0 + indent."""
    first = ln(page, top, f"{number} {texts[0]}", x0=x0)
    first["words"][1:] = [{**w, "x0": w["x0"] + indent - 6 * (len(number) + 1),
                           "x1": w["x1"] + indent - 6 * (len(number) + 1)} for w in first["words"][1:]]
    return [first] + [ln(page, top + k * step, t, x0=x0 + indent) for k, t in enumerate(texts[1:], start=1)]


def footer(page, number):
    return ln(page, 805, f"Fire safety in purpose-built blocks of flats {number}", 10.0, colour=GREEN, x0=337)


def doc():
    lines, graphics, images = [], [], []
    lines += [ln(1, 150, "Fire safety in purpose-built", 35.0, "Arial-BoldMT", colour=GREEN)]
    lines += [ln(2, 56, "This guide was produced in 2011 and summarised the law at the time.", 14.0)]
    # page 3: a Part title on two lines and its Key points, running onto page 4
    lines += [ln(3, 43, "Part E: Managing fire risk –", 35.0, "Arial-BoldMT"),
              ln(3, 78, "preventing fires", 35.0),
              ln(3, 166, "Key points", 18.0),
              ln(3, 200, "• Prevention of fire, as far as possible, is essential."),
              ln(3, 222, "• Arson is a common cause of fire, so good security is part of fire"),
              ln(3, 238, "prevention.", x0=65)]
    lines += [ln(4, 68, "• Poor housekeeping in the common parts is a significant fire hazard.")]
    # page 4: a numbered section, a paragraph whose sentence runs on past a framed box onto page 5
    lines += [ln(4, 120, "41. Introduction", 18.0, colour=GREEN)]
    lines += para(4, 154, "41.1", ["The importance of preventing fires cannot be overstated. This is a",
                                   "key consideration in a fire risk assessment. Measures include:"])
    lines += [ln(4, 200, "• good physical security", x0=82.2), ln(4, 222, "• regular inspections and", x0=82.2)]
    lines += [ln(4, 300, "When inspecting the block, use the opportunity to:", font="Arial-BoldMT", x0=63),
              ln(4, 326, "look out for evidence of smoking in the common parts", x0=63),
              ln(4, 348, "check that no smoking signs are still in place", x0=63)]
    images += [{"page": 4, "top": 290.0, "bottom": 370.0, "x0": 54.0, "x1": 550.0}]  # the box frame
    graphics += [{"page": 4, "kind": "curve", "top": 330.0, "bottom": 333.0, "x0": 55.0, "x1": 58.0, "fill": True,
                  "stroke": False, "colour": [0.0]},
                 {"page": 4, "kind": "curve", "top": 352.0, "bottom": 355.0, "x0": 55.0, "x1": 58.0, "fill": True,
                  "stroke": False, "colour": [0.0]}]
    lines += [ln(4, 700, "2 Source: UK Fire Statistics 2008", 8.0)]
    lines += [footer(4, 52)]
    # page 5: the run-on, a sub-heading, a paragraph beside a figure with its caption above the drawing
    lines += [ln(5, 68, "maintenance of the electrical installation.²", x0=82.2)]
    lines += [ln(5, 100, "Fire resistance of existing compartment walls", font="Arial-BoldMT", x0=82.2)]
    lines += para(5, 130, "41.2", ["Older blocks may have", "a timber floor and lath and", "plaster ceilings below."])
    lines += [ln(5, 128, "Figure 1 – Shunt duct", font="Arial-BoldMT", x0=330),
              ln(5, 144, "arrangements", font="Arial-BoldMT", x0=330),
              ln(5, 300, "Note: Values are minimum values.", 10.0, x0=332)]
    images += [{"page": 5, "top": 170.0, "bottom": 290.0, "x0": 335.0, "x1": 540.0}]
    lines += [ln(5, 400, "42. Smoking", 18.0, colour=GREEN)]
    lines += para(5, 434, "42.2", ["By law, smoking is not allowed in the common parts of blocks of flats."])
    lines += [footer(5, 53)]
    # page 6: an appendix, its title in green 18pt, a paragraph printed without its "A"
    lines += [ln(6, 45, "Appendix 1", 35.0, "Arial-BoldMT", colour=GREEN),
              ln(6, 140, "History of fire safety design standards", 18.0, colour=GREEN)]
    lines += para(6, 180, "A1.1", ["To carry out a fire risk assessment for an older block of flats."])
    lines += para(6, 220, "1.2", ["This enables a sympathetic approach to old blocks of flats."])
    lines += [footer(6, 54)]
    return {"lines": lines, "graphics": graphics, "images": images, "tables": [], "rects": [],
            "page_count": 6, "page_width": W, "page_height": H,
            "pages": {p: {"width": W, "height": H} for p in range(1, 7)}}


@pytest.fixture(scope="module")
def tree():
    return F.build_tree(doc(), META)


def sec(tree, local):
    return next(s for s in tree["sections"] if s["id"] == f"flats:{local}")


def test_ids_are_prefixed_and_unique(tree):
    ids = [s["id"] for s in tree["sections"]]
    assert all(i.startswith("flats:") for i in ids) and len(ids) == len(set(ids))
    assert tree["parser"] == F.PARSER


def test_part_title_on_two_lines_and_key_points_box(tree):
    part = sec(tree, "part-e")
    assert part["type"] == "part" and part["heading_path"] == [TITLE, "Part E: Managing fire risk – preventing fires"]
    kp = sec(tree, "part-e-key-points")
    assert kp["type"] == "box" and kp["heading_path"][-1] == "Key points"
    assert kp["text"].count("• ") == 3 and "part of fire prevention." in kp["text"]
    assert kp["text"].endswith("significant fire hazard.")  # the bullet on the next page


def test_numbered_paragraph_keeps_its_text_across_a_box_and_a_page(tree):
    p = sec(tree, "41-1")
    assert p["type"] == "paragraph" and p["number"] == "41.1"
    assert p["heading_path"] == [TITLE, "Part E: Managing fire risk – preventing fires", "41. Introduction"]
    assert p["text"].startswith("The importance of preventing fires")
    assert p["text"].endswith("• regular inspections and maintenance of the electrical installation.²")
    assert p["footnotes"] == ["² Source: UK Fire Statistics 2008"]


def test_framed_box_with_bold_lead_and_drawn_bullets(tree):
    b = sec(tree, "41-box-1")
    assert b["type"] == "box" and b["title"] == "When inspecting the block, use the opportunity to:"
    assert b["text"] == "• look out for evidence of smoking in the common parts\n• check that no smoking signs are still in place"


def test_figure_caption_above_and_text_beside_it(tree):
    f = sec(tree, "figure-1")
    assert f["title"] == "Shunt duct arrangements" and f["caption_above"] is True
    assert f["area"]["top"] >= f["caption_box"]["bottom"] and f["area"]["x0"] >= 300
    assert f["area"]["bottom"] >= 300 and "Note: Values are minimum values." in f["labels"]
    p = sec(tree, "41-2")
    assert p["text"] == "Older blocks may have a timber floor and lath and plaster ceilings below."
    assert p["heading_path"][-1] == "Fire resistance of existing compartment walls"
    assert not any("Shunt" in s["text"] for s in tree["sections"] if s["type"] == "paragraph")


def test_footer_dropped_and_printed_page(tree):
    assert not any("Fire safety in purpose-built" in s["text"] for s in tree["sections"])
    assert sec(tree, "42-2")["printed_page"] == "53"


def test_paragraph_number_jump_and_misprint_are_issues(tree):
    assert "paragraph numbers jump from 42.0 to 42.2 on file page 5" in tree["issues"]
    assert sec(tree, "a1-2")["number"] == "A1.2"
    assert "paragraph A1.2 is printed as 1.2 (file page 6)" in tree["issues"]
    assert sec(tree, "appendix-1")["heading_path"][-1] == "Appendix 1 History of fire safety design standards"


def test_preface_panel_and_no_generic_headings(tree):
    assert sec(tree, "document-para-1")["text"].startswith("This guide was produced in 2011")
    assert not any(p in ("Note", "Text", "") for s in tree["sections"] for p in s["heading_path"])


def test_chunker_takes_the_tree(tree):
    chunks, _ = chunk_tree(tree, {"id": SOURCE, "kind": "guidance", "nation": "england"}, {})
    assert {"paragraph", "box", "figure"} <= {c["chunk_type"] for c in chunks}


def test_straddles():
    assert F.straddles(ln(1, 0, "Fire-resisting protected entrance hall", 9.0, x0=250), 300)
    two = ln(1, 0, "2 2", 9.0, x0=100)
    two["words"][1] = {**two["words"][1], "x0": 420.0, "x1": 425.0}
    assert not F.straddles(two, 310)


def test_sources_yaml_sends_the_flats_guide_to_parse_flats():
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    recs = records(SOURCE, src, F.MODULE)
    assert [r["version_id"].split("--")[0] for r in recs] == ["fire-safety-in-purpose-built-blocks-of-flats"]
    assert parser_for(src, recs[0]["version_id"]) == "parse_flats"


# ---------------------------------------------------------------- the real file

@pytest.fixture(scope="module")
def flats():
    pytest.importorskip("pdfplumber")
    src = next(s for s in load_sources()["sources"] if s["id"] == SOURCE)
    rec = next(iter(records(SOURCE, src, F.MODULE)), None)
    if rec is None or not (ROOT / rec["raw_path"]).exists():
        pytest.skip("flats guide raw file not on this machine")
    tree = F.build_tree(read_guide(ROOT / rec["raw_path"]), {**rec, "title": rec["part_title"]})
    F.drop_blank_pictures(ROOT / rec["raw_path"], tree)
    return tree


def test_real_flats_structure(flats):
    S = flats["sections"]
    by = {s["id"]: s for s in S}
    assert len({s["id"] for s in S}) == len(S)
    assert [s["number"] for s in S if s["type"] == "part"] == list("ABCDEFG")
    assert [s["number"] for s in S if s["type"] == "chapter" and s["number"]] == [str(n) for n in range(1, 89)]
    assert [s["number"] for s in S if s["type"] == "appendix"] == [str(n) for n in range(1, 14)]
    assert not any(p in ("Note", "Text", "") for s in S for p in s["heading_path"])


def test_real_flats_numbered_paragraphs(flats):
    S = flats["sections"]
    by = {s["id"]: s for s in S}
    nums = [s["number"] for s in S if s["type"] == "paragraph" and s["number"]]
    assert len(nums) == 705 and len(set(nums)) == 705
    # 71.6, 82.2 and 83.3 are not printed; 79.9 to 79.11 were removed (blacked out) in the 2024 reissue
    missing = {"71.6", "82.2", "83.3", "79.9", "79.10", "79.11"}
    per = Counter(n.rsplit(".", 1)[0] for n in nums)
    for head, count in per.items():
        expected = [f"{head}.{k}" for k in range(1, count + 1 + sum(m.startswith(head + ".") for m in missing))]
        assert [n for n in nums if n.rsplit(".", 1)[0] == head] == [e for e in expected if e not in missing], head

    def top(s):
        while s["parent_id"]:
            s = by[s["parent_id"]]
        return s["id"].split(":")[1]
    assert Counter(top(s) for s in S if s["type"] == "paragraph" and s["number"]) == {
        "introduction": 31, "part-a": 16, "part-b": 63, "part-c": 31, "part-d": 33, "part-e": 54, "part-f": 198,
        "part-g": 101, "appendix-1": 74, "appendix-2": 2, "appendix-3": 6, "appendix-6": 30, "appendix-7": 10,
        "appendix-8": 9, "appendix-9": 10, "appendix-10": 11, "appendix-11": 10, "appendix-12": 11,
        "appendix-13": 5}
    p = by["flats:56-36"]
    assert p["text"].startswith("Cross-over flats can sometimes present particular problems") \
        and p["text"].endswith("specialist advice may need to be sought.")
    assert by["flats:10-1"]["footnotes"] == ["² Source: UK Fire Statistics 2008"]


def test_real_flats_figures_boxes_tables_glossary(flats):
    S = flats["sections"]
    figs = [s for s in S if s["type"] == "figure"]
    assert sorted(int(s["number"]) for s in figs if s["number"]) == list(range(1, 14))  # Figures 1 to 13
    assert len([s for s in figs if not s["number"]]) == 33  # photos, two charts and the decision tree
    assert all(s["caption_above"] and s["area"]["top"] >= s["caption_box"]["bottom"] for s in figs if s["number"])
    tree_fig = next(s for s in figs if (s["title"] or "").startswith("Decision Tree"))
    assert tree_fig["file_page"] == 71 and "Adequate fire" in tree_fig["labels"]
    boxes = [s for s in S if s["type"] == "box"]
    assert len([b for b in boxes if b["title"] == "Key points"]) == 7 and len(boxes) == 27
    assert len([s for s in S if s["type"] == "table"]) == 2  # the acknowledgements list and the risk matrix
    defs = [s for s in S if s["type"] == "definition"]
    assert len(defs) == 55 and defs[0]["title"] == "Access room" and len(flats["definitions"]) == 55
    assert flats["issues"] == [
        "file page 122: 20 lines of text blacked out in the printed guide",
        "paragraph numbers jump from 71.5 to 71.7 on file page 112",
        "paragraph numbers jump from 79.8 to 79.12 on file page 122",
        "paragraph numbers jump from 82.1 to 82.3 on file page 127",
        "paragraph numbers jump from 83.2 to 83.4 on file page 130",
        "paragraph A1.62 is printed as 1.62 (file page 145)"]
    assert len(flats.get("dropped", [])) == 2  # two images that show nothing (pages 101 and 103)
    assert re.fullmatch(r"flats:[a-z0-9-]+", tree_fig["id"])
