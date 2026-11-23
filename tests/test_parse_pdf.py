"""Tests for the guidance PDF parser (ADR 0010). The tree builder works on simple "lines", so most tests
use hand-made lines (mock text) and need no PDF. Real-file tests skip where raw files are missing."""

import json
from pathlib import Path

import pytest

from system.rag.fixes import load_fixes
from system.rag.parse_pdf import build_tree, photo_box, read_guidance, read_pdf

ROOT = Path(__file__).parent.parent
META = {"source_id": "demo-guide", "version_id": "main@2024-01-01-abc", "valid_from": "2024-01-01",
        "valid_to": None, "sha256": "abc", "title": "Demo guide"}
GREEN = (0.86, 0.9, 0.83)
BEIGE = (0.89, 0.83, 0.73)


def ln(page, top, text, size=10.0, font="HelveticaNeue-Light", x0=180.0, words=None):
    """A line as read_pdf gives it. Words get rough x positions (5 points per character) unless given."""
    if words is None:
        words, x = [], float(x0)
        for w in text.split():
            words.append({"x0": x, "text": w})
            x += 5 * (len(w) + 1)
    return {"page": page, "top": float(top), "x0": float(x0), "size": size, "font": font, "text": text,
            "words": words}


def two_captions(page, top, left, right):
    words = [{"x0": 180.0 + 5 * i, "text": w} for i, w in enumerate(left.split())]
    words += [{"x0": 360.0 + 5 * i, "text": w} for i, w in enumerate(right.split())]
    return ln(page, top, f"{left} {right}", 9.0, "HelveticaNeue", 180, words)


def header_footer(page):
    return [ln(page, 43, "Health and Safety", 9.0, "HelveticaNeue-Bold", 466),
            ln(page, 54, "Executive", 9.0, "HelveticaNeue-Bold", 466),
            ln(page, 823, f"Demo guide Page {page} of 9", 8.0)]


def doc():
    pages = {}
    pages[1] = [ln(1, 300, "Demo guide", 28.0, "HelveticaNeue-MediumCond")]
    pages[2] = [ln(2, 98, "Contents", 28.0, "HelveticaNeue-Medium"), ln(2, 140, "Introduction 4")]
    pages[3] = [
        ln(3, 98, "1 Introduction", 28.0, "HelveticaNeue-Medium"),
        ln(3, 150, "Legal requirements", 11.0, "HelveticaNeue-Bold"),
        ln(3, 170, "1 Dutyholders must manage asbestos in non-domestic"),
        ln(3, 182, "premises. This includes asbestos-"),
        ln(3, 194, "containing materials (ACMs).*"),
        ln(3, 210, "2 The survey should cover:"),
        ln(3, 222, "■■ all rooms; and", 9.0, "ZapfDingbatsITC", 184),
        ln(3, 234, "roof voids.", 10.0, "HelveticaNeue-Light", 198),
        ln(3, 250, "3 Surveyors work at heights of"),
        ln(3, 262, "2 m or more in some cases."),
        ln(3, 300, "Box 1: The purpose of a survey", 11.0, "HelveticaNeue-Bold", 199),
        ln(3, 330, "■■ To help manage asbestos.", 9.0, "ZapfDingbatsITC", 184),
        ln(3, 400, "Sampling is work with asbestos.", 10.0, "HelveticaNeue", 185),
        ln(3, 790, "* ACMs means asbestos-containing materials.", 8.0, "HelveticaNeue-Light", 180),
    ]
    pages[4] = [
        ln(4, 100, "4 A survey has two parts."),
        ln(4, 124, "Material", 7.5, "HelveticaNeue-Roman", 230),
        ln(4, 132, "assessment", 7.5, "HelveticaNeue-Roman", 230),
        ln(4, 200, "Figure 1 Steps in managing asbestos", 9.0, "HelveticaNeue", 54),
        two_captions(4, 300, "Figure 2 Lagged pipe", "Figure 3 AIB panel"),
        ln(4, 400, "Sample variable Score Examples", 8.0, "HelveticaNeue-Bold", 59),
        ln(4, 420, "Product type 1 Asbestos cement", 8.0, "HelveticaNeue-Light", 59),
        ln(4, 450, "Table 1 Material scores", 9.0, "HelveticaNeue", 50),
    ]
    pages[5] = [
        ln(5, 98, "Appendix 1: Refurbishment and", 28.0, "HelveticaNeue-Medium"),
        ln(5, 132, "demolition surveys", 28.0, "HelveticaNeue-Medium"),
        ln(5, 180, "1 Refurbishment surveys need access."),
        ln(5, 200, "2 They are intrusive."),
    ]
    pages[6] = [
        ln(6, 98, "References", 28.0, "HelveticaNeue-Medium"),
        ln(6, 140, "1 Managing asbestos in premises L143 HSE Books"),
    ]
    lines = [l for p in sorted(pages) for l in header_footer(p) + pages[p]]
    rects = [{"page": 3, "top": 290, "bottom": 360, "x0": 180, "x1": 541, "colour": GREEN},
             {"page": 3, "top": 390, "bottom": 420, "x0": 180, "x1": 541, "colour": BEIGE}]
    images = [{"page": 4, "top": 240, "bottom": 295, "x0": 180, "x1": 340},
              {"page": 4, "top": 240, "bottom": 295, "x0": 360, "x1": 520}]
    return {"lines": lines, "rects": rects, "images": images, "page_count": 6}


@pytest.fixture(scope="module")
def tree():
    return build_tree(doc(), META)


def sec(tree, sid):
    found = [s for s in tree["sections"] if s["id"] == sid]
    assert len(found) == 1, f"{sid}: {len(found)} found ({[s['id'] for s in tree['sections']]})"
    return found[0]


def all_text(tree):
    return "\n".join(s["text"] for s in tree["sections"]) + "\n".join(
        " ".join(s.get("labels", [])) for s in tree["sections"])


def test_metadata_and_parser(tree):
    assert tree["source_id"] == "demo-guide" and tree["parser"].startswith("guidance-pdf/")


def test_headers_footers_contents_and_cover_are_dropped(tree):
    t = all_text(tree)
    assert "Health and Safety" not in t and "Executive" not in t and "Page 3 of 9" not in t
    assert "Introduction 4" not in t  # contents page
    assert not [s for s in tree["sections"] if s["title"] in ("Contents", "Demo guide")]


def test_chapters_and_headings(tree):
    ch = sec(tree, "chapter-1")
    assert ch["type"] == "chapter" and ch["number"] == "1" and ch["title"] == "Introduction"
    h = sec(tree, "chapter-1-legal-requirements")
    assert h["type"] == "heading" and h["parent_id"] == "chapter-1"
    app = sec(tree, "appendix-1")
    assert app["title"] == "Refurbishment and demolition surveys"  # two title lines merged


def test_numbered_paragraphs_with_breadcrumb_and_printed_page(tree):
    p1 = sec(tree, "para-1")
    assert p1["type"] == "paragraph" and p1["parent_id"] == "chapter-1-legal-requirements"
    assert p1["heading_path"] == ["Demo guide", "1 Introduction", "Legal requirements", "Paragraph 1"]
    assert p1["printed_page"] == "3"
    assert p1["text"] == "Dutyholders must manage asbestos in non-domestic premises. This includes asbestos-containing materials (ACMs).*"


def test_bullets_cleaned_and_kept_in_paragraph(tree):
    assert sec(tree, "para-2")["text"] == "The survey should cover:\n• all rooms; and roof voids."


def test_number_at_start_of_a_wrapped_line_is_not_a_paragraph(tree):
    assert sec(tree, "para-3")["text"] == "Surveyors work at heights of 2 m or more in some cases."
    assert not [s for s in tree["sections"] if s["id"] == "para-2" and "heights" in s["text"]]


def test_paragraph_continues_on_next_page(tree):
    assert sec(tree, "para-4")["printed_page"] == "4"


def test_box_is_its_own_section_and_not_in_paragraphs(tree):
    b = sec(tree, "box-1")
    assert b["type"] == "box" and b["title"] == "The purpose of a survey"
    assert b["text"] == "• To help manage asbestos."
    assert "To help manage" not in sec(tree, "para-3")["text"]


def test_highlighted_note_and_footnote(tree):
    notes = [s for s in tree["sections"] if s["type"] == "note"]
    assert [n["text"] for n in notes] == ["Sampling is work with asbestos."]
    assert notes[0]["parent_id"] == "chapter-1-legal-requirements"
    assert sec(tree, "para-1")["footnotes"] == ["* ACMs means asbestos-containing materials."]


def test_figures_from_captions_with_labels_and_images(tree):
    f1 = sec(tree, "figure-1")
    assert f1["type"] == "figure" and f1["title"] == "Steps in managing asbestos"
    assert f1["labels"] == ["Material", "assessment"]
    f2, f3 = sec(tree, "figure-2"), sec(tree, "figure-3")
    assert (f2["title"], f3["title"]) == ("Lagged pipe", "AIB panel")
    assert f2["image_bbox"] and f3["image_bbox"] and f2["image_bbox"] != f3["image_bbox"]
    assert "Material" not in sec(tree, "para-4")["text"]


def test_table_is_recorded_with_raw_rows_and_a_check(tree):
    t = sec(tree, "table-1")
    assert t["type"] == "table" and t["title"] == "Material scores"
    assert "Product type 1 Asbestos cement" in t["text"]
    assert any(c["kind"] == "table" and c["section_id"] == "table-1" for c in tree["checks"])


def test_appendix_paragraphs_restart_numbering(tree):
    a = sec(tree, "appendix-1-para-1")
    assert a["parent_id"] == "appendix-1" and a["text"] == "Refurbishment surveys need access."
    assert sec(tree, "appendix-1-para-2")["heading_path"][-2:] == ["Appendix 1 Refurbishment and demolition surveys", "Paragraph 2"]


def test_references_kept_as_one_back_matter_section(tree):
    r = sec(tree, "references")
    assert r["type"] == "references" and "L143" in r["text"]


def test_tree_is_json(tree):
    json.dumps(tree, ensure_ascii=False)


# ---------------------------------------------------------------- step B: grids, figure areas, fixes

def doc_with_grids():
    d = doc()
    d["tables"] = [
        {"page": 4, "top": 395, "bottom": 440, "x0": 50, "x1": 545,
         "rows": [["Sample variable", "Score", "Examples"], ["Product type", "1", "Asbestos cement"]]},
        {"page": 4, "top": 120, "bottom": 140, "x0": 220, "x1": 300, "rows": [["Material"], ["assessment"]]},
    ]
    return d


def test_table_grid_from_the_pdf_table_on_its_page():
    t = sec(build_tree(doc_with_grids(), META), "table-1")
    assert t["grid"] == [["Sample variable", "Score", "Examples"], ["Product type", "1", "Asbestos cement"]]
    assert t["grid_source"] == "pdf"


def test_repeated_header_rows_on_later_pages_are_dropped():
    d = doc_with_grids()
    d["lines"].append(ln(5, 600, "Product type 2 Lagging", 8.0, "HelveticaNeue-Light", 59))
    d["tables"].append({"page": 5, "top": 590, "bottom": 640, "x0": 50, "x1": 545,
                        "rows": [["Sample variable", "Score", "Examples"], ["Product type", "2", "Lagging"]]})
    tree = build_tree(d, META)
    grids = [s["grid"] for s in tree["sections"] if s["type"] == "table" and s.get("grid")]
    assert ["Product type", "2", "Lagging"] in grids[-1]
    assert sum(r == ["Sample variable", "Score", "Examples"] for g in grids for r in g) <= len(grids)


def test_figure_area_for_cutting_the_image():
    f1 = sec(build_tree(doc_with_grids(), META), "figure-1")
    a = f1["area"]
    assert a["page"] == 4 and a["top"] <= 124 and a["bottom"] >= 200
    assert sec(build_tree(doc_with_grids(), META), "figure-2")["area"]["top"] == 240  # photo: the image box


def test_saved_table_fix_replaces_the_grid_and_adds_row_sentences():
    tree = build_tree(doc_with_grids(), META)
    key = next(c["key"] for c in tree["checks"] if c["section_id"] == "table-1")
    fix = {"key": key, "kind": "table", "reason": "test",
           "value": {"columns": ["Sample variable", "Score", "Examples"],
                     "rows": [["Product type", "1", "Asbestos cement"]],
                     "sentences": ["Product type scores 1 for asbestos cement."]}}
    fixed = build_tree(doc_with_grids(), META, fixes=[fix])
    t = sec(fixed, "table-1")
    assert t["grid_source"] == "model" and t["columns"] == ["Sample variable", "Score", "Examples"]
    assert t["row_sentences"] == ["Product type scores 1 for asbestos cement."]
    assert not [c for c in fixed["checks"] if c["section_id"] == "table-1"]


def test_caption_second_lines_stay_with_their_caption():
    d = doc()
    words = [{"x0": 180.0, "x1": 186.0, "text": "passageway"}, {"x0": 360.0, "x1": 366.0, "text": "bend"}]
    d["lines"].append(ln(4, 312, "passageway bend", 9.0, "HelveticaNeue-Light", 180, words))
    tree = build_tree(d, META)
    assert sec(tree, "figure-2")["title"] == "Lagged pipe passageway"
    assert sec(tree, "figure-3")["title"] == "AIB panel bend"


def test_text_beside_a_caption_on_the_same_line_is_cut_off():
    d = doc()
    words = [{"x0": 54.0, "x1": 80.0, "text": "Figure"}, {"x0": 83.0, "x1": 90.0, "text": "9"},
             {"x0": 93.0, "x1": 130.0, "text": "Locations"}, {"x0": 340.0, "x1": 400.0, "text": "Note:"},
             {"x0": 403.0, "x1": 440.0, "text": "survey"}]
    d["lines"].append(ln(4, 700, "Figure 9 Locations Note: survey", 9.0, "HelveticaNeue", 54, words))
    assert sec(build_tree(d, META), "figure-9")["title"] == "Locations"


def test_bold_caption_above_its_table_takes_the_rows_below():
    d = doc()
    d["lines"] += [
        ln(5, 300, "Table 3 Priority assessment algorithm", 10.0, "HelveticaNeue-Bold", 54),
        ln(5, 320, "Assessment factor Score Examples", 9.0, "HelveticaNeue-Bold", 54),
        ln(5, 335, "Normal occupant activity 0 Rare disturbance", 9.0, "HelveticaNeue-Light", 54),
        ln(5, 400, "3 They follow the plan."),
    ]
    tree = build_tree(d, META)
    t = sec(tree, "table-3")
    assert t["title"] == "Priority assessment algorithm"
    assert "Normal occupant activity 0 Rare disturbance" in t["text"]
    assert sec(tree, "appendix-1-para-3")["text"] == "They follow the plan."


def test_bold_italic_callout_is_a_note_not_a_heading():
    d = doc()
    d["lines"] += [ln(5, 230, "Take care, these dates are only", 12.0, "HelveticaNeue-BoldItalic", 192),
                   ln(5, 245, "a guideline.", 12.0, "HelveticaNeue-BoldItalic", 192)]
    tree = build_tree(d, META)
    assert not [s for s in tree["sections"] if s["type"] == "heading" and "Take care" in s["title"]]
    notes = [s for s in tree["sections"] if s["type"] == "note"]
    assert any(n["text"] == "Take care, these dates are only a guideline." for n in notes)


def test_leading_dash_in_a_title_is_dropped():
    d = doc()
    for l in d["lines"]:
        if l["text"] == "Appendix 1: Refurbishment and":
            l["text"] = "Appendix 1 - Refurbishment and"
    assert sec(build_tree(d, META), "appendix-1")["title"] == "Refurbishment and demolition surveys"


def test_saved_figure_description():
    tree = build_tree(doc_with_grids(), META)
    key = next(c["key"] for c in tree["checks"] if c["section_id"] == "figure-2")
    fixed = build_tree(doc_with_grids(), META,
                       fixes=[{"key": key, "kind": "figure_description", "value": "A lagged pipe.", "reason": "test"}])
    f2 = sec(fixed, "figure-2")
    assert f2["description"] == "A lagged pipe." and f2["description_source"] == "model"


def test_photo_box_finds_the_photo_inside_a_padded_image_box():
    """The image box is wider than the photo and holds part of a neighbour photo; words printed beside the
    photo belong to it (HSG227 figures 3 and 5)."""
    from PIL import Image, ImageDraw
    PIL_scale = 2.0
    page = Image.new("RGB", (600, 400), "white")
    d = ImageDraw.Draw(page)
    d.rectangle([20, 20, 80, 120], fill="grey")      # neighbour photo, points 10-40
    d.rectangle([100, 30, 200, 130], fill="black")   # the photo, points 50-100 x 15-65
    d.rectangle([205, 100, 240, 115], fill="red")    # "BAD PRACTICE" beside it
    d.rectangle([20, 0, 400, 8], fill="black")       # body text above, across both columns
    area = {"page": 1, "top": 2.0, "bottom": 90.0, "x0": 30.0, "x1": 105.0}  # padded, overlaps the neighbour
    caption = {"page": 1, "top": 70.0, "x0": 50.0}
    box = photo_box(page, area, caption, PIL_scale, right_limit=150.0)
    assert box["x0"] == pytest.approx(50, abs=1) and box["x1"] == pytest.approx(120.5, abs=1)
    assert box["top"] == pytest.approx(15, abs=1) and box["bottom"] == pytest.approx(65.5, abs=1)


def test_photo_box_with_the_caption_above_takes_the_photo_below_it():
    """Home Office fire safety guides print the caption above the photo (below=True): the photo is the first
    block under the caption, not the text or the photo above it, and the box is never upside down."""
    from PIL import Image, ImageDraw
    page = Image.new("RGB", (600, 400), "white")
    d = ImageDraw.Draw(page)
    d.rectangle([100, 0, 200, 60], fill="grey")      # another photo above the caption (points 0-30)
    d.rectangle([100, 70, 300, 78], fill="black")    # the caption's own letters (points 35-39)
    d.rectangle([100, 90, 240, 190], fill="black")   # the photo, points 50-120 x 45-95
    area = {"page": 1, "top": 42.0, "bottom": 100.0, "x0": 48.0, "x1": 125.0}  # padded image box
    caption = {"page": 1, "top": 35.0, "bottom": 40.0, "x0": 50.0}
    box = photo_box(page, area, caption, 2.0, right_limit=150.0, below=True)
    assert box["top"] == pytest.approx(45, abs=1) and box["bottom"] == pytest.approx(95.5, abs=1)
    assert box["x0"] == pytest.approx(50, abs=1) and box["x1"] == pytest.approx(120.5, abs=1)
    # the default (caption below the photo) is unchanged for the same caption: nothing tall above it
    assert photo_box(page, area, caption, 2.0, right_limit=150.0) == area


def test_superscripts_and_backwards_words():
    """Raised footnote numbers become superscript digits; a jump back to the left starts a new word. Both are
    options of read_pdf (off for the HSE guides)."""
    from system.rag.parse_pdf import _words, mark_superscripts
    chars = [{"text": t, "x0": x, "x1": x + 5, "size": s, "bottom": b, "fontname": "F", "top": b - s}
             for t, x, s, b in [("O", 0, 10, 100), ("r", 5, 10, 100), ("d", 10, 10, 100), ("1", 15, 6, 96)]]
    assert [w["text"] for w in _words(mark_superscripts(chars))] == ["Ord¹"]
    jump = [{"text": t, "x0": x, "x1": x + 5, "size": 10, "fontname": "F", "top": 0}
            for t, x in [("o", 300), ("u", 305), ("t", 310), ("F", 100), ("o", 105), ("r", 110)]]
    assert [w["text"] for w in _words(jump)] == ["outFor"]
    assert [w["text"] for w in _words(jump, split_backwards=True)] == ["out", "For"]


def test_photo_box_keeps_the_image_box_when_nothing_is_drawn_above_the_caption():
    from PIL import Image
    area = {"page": 1, "top": 10.0, "bottom": 60.0, "x0": 50.0, "x1": 100.0}
    assert photo_box(Image.new("RGB", (300, 200), "white"), area, {"page": 1, "top": 70.0, "x0": 50.0},
                     2.0, right_limit=140.0) == area


# ---------------------------------------------------------------- real file

def _record(source_id):
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / source_id).glob("*.json")]
    cur = [r for r in recs if r["valid_to"] is None]
    if not cur or not (ROOT / cur[0]["raw_path"]).exists():
        pytest.skip(f"{source_id} raw file not on this machine")
    return cur[0]


@pytest.fixture(scope="module")
def hsg264():
    pytest.importorskip("pdfplumber")
    r = _record("hse-hsg264")
    return build_tree(read_guidance(ROOT / r["raw_path"]), {**r, "title": "HSG264 Asbestos: The survey guide"},
                      fixes=load_fixes("hse-hsg264"))


def test_real_all_checks_settled_by_saved_fixes(hsg264):
    assert hsg264["checks"] == []
    S = {s["id"]: s for s in hsg264["sections"]}
    assert all(S[f"figure-{n}"]["description_source"] == "model" for n in range(1, 53))
    assert all(s["grid_source"] == "model" and s["row_sentences"] for s in S.values() if s["type"] == "table")
    assert S["figure-8"]["title"] == "Sprayed coating on building passageway"
    assert S["figure-52"]["title"] == "Typical locations for the most common asbestos material"


def test_real_paragraph_numbering(hsg264):
    paras = [s for s in hsg264["sections"] if s["type"] == "paragraph"]
    main = [int(s["number"]) for s in paras if s["id"].startswith("para-")]
    assert main == list(range(1, 150))
    for app, last in (("appendix-1", 36), ("appendix-3", 20), ("appendix-6", 11)):
        nums = [int(s["number"]) for s in paras if s["id"].startswith(app + "-para-")]
        assert nums == list(range(1, last + 1)), app


def test_real_boxes_figures_tables(hsg264):
    boxes = sorted(int(s["number"]) for s in hsg264["sections"] if s["type"] == "box")
    assert boxes == list(range(1, 12))
    figs = sorted(int(s["number"]) for s in hsg264["sections"] if s["type"] == "figure")
    assert figs == list(range(1, 53))
    assert "table-1" in {s["id"] for s in hsg264["sections"]}
    assert len([s for s in hsg264["sections"] if s["type"] == "table"]) >= 3


def test_real_table_grids(hsg264):
    S = {s["id"]: s for s in hsg264["sections"]}
    assert len(S["table-1"]["grid"][0]) == 11
    a4 = S["appendix-4-table-p67"]["grid"]  # a ruled table with no caption, one per page (S105)
    assert any(r and r[0].startswith("Product type") for r in a4)
    # One ruled table over five pages (S105): joined into parts of at most four pages (S118), one family
    a2 = [S["appendix-2-table-p52"], S["appendix-2-table-p56"]]
    assert sorted(S["appendix-2-table-p52"]["spans"]) == ["52", "53", "54", "55"]
    assert all(t["columns"][0] == "Asbestos product" for t in a2)
    assert not [r for t in a2 for r in t["grid"] if r and r[0] == "Asbestos product"]  # header not repeated


def test_real_text_is_clean(hsg264):
    for s in hsg264["sections"]:
        for bad in ("Health and Safety\nExecutive", "Page 1", "■", "Asbestos: The survey guide Page"):
            assert bad not in s["text"], (s["id"], bad)
    p14 = next(s for s in hsg264["sections"] if s["id"] == "para-14")
    assert p14["text"].startswith("To help comply with the legal requirements")
    assert p14["heading_path"][-2:] == ["Appointed person", "Paragraph 14"]
    assert p14["printed_page"] == "10"


@pytest.fixture(scope="module")
def hsg227():
    pytest.importorskip("pdfplumber")
    r = _record("hse-hsg227")
    return build_tree(read_guidance(ROOT / r["raw_path"]), {**r, "title": "HSG227 A comprehensive guide to managing asbestos"},
                      fixes=load_fixes("hse-hsg227"))


def test_real_hsg227_structure(hsg227):
    secs = hsg227["sections"]
    paras = [s for s in secs if s["type"] == "paragraph"]
    assert [int(s["number"]) for s in paras if s["id"].startswith("para-")] == list(range(1, 91))
    for app, last in (("appendix-1", 24), ("appendix-2", 11), ("appendix-3", 9), ("appendix-5", 15), ("appendix-6", 21)):
        assert [int(s["number"]) for s in paras if s["id"].startswith(app + "-para-")] == list(range(1, last + 1)), app
    assert sorted(int(s["number"]) for s in secs if s["type"] == "table") == list(range(1, 16))
    assert sorted(int(s["number"]) for s in secs if s["type"] == "figure") == list(range(1, 15))
    assert not [s for s in secs if s["type"] in ("chapter", "appendix") and "sotsebsA" in s["title"]]  # mirrored text
    assert next(s for s in secs if s["id"] == "appendix-3")["title"] == "Priority assessment and algorithm"
    t3 = next(s for s in secs if s["id"] == "table-3")
    assert t3["title"].startswith("Priority assessment algorithm") and t3.get("grid")
    assert not [s for s in secs if s["type"] == "heading" and s["title"].startswith("Take care")]  # callout


def test_real_hsg227_all_checks_settled_by_saved_fixes(hsg227):
    assert hsg227["checks"] == []
    t3 = next(s for s in hsg227["sections"] if s["id"] == "table-3")
    # 4 + 1 (occupant activity) + 12 (likelihood) + 12 (human exposure) + 8 (maintenance) score options
    assert t3["grid_source"] == "model" and len(t3["row_sentences"]) == 37


def test_real_hsg227_worked_examples_share_one_layout(hsg227):
    S = {s["id"]: s for s in hsg227["sections"]}
    cols = S["table-4"]["columns"]
    assert cols == ["Assessment factor", "Sub-factor", "Variable(s) selected", "Score for each variable", "Overall score"]
    for n in range(4, 15):
        t = S[f"table-{n}"]
        assert t["columns"] == cols, n
        overall = [r[4] for r in t["grid"] if r[0] == "Likelihood of disturbance"]
        assert overall[:2] == ["", ""] and overall[2].startswith("average") and len(overall) == 3, (n, overall)  # once, as printed
        assert all("was assessed as" in x or " is " in x for x in t["row_sentences"]), n


def test_real_hsg227_photo_crops_do_not_overlap(hsg227):
    pdfium = pytest.importorskip("pypdfium2")
    from system.rag.parse_pdf import _next_caption_x
    pdf = pdfium.PdfDocument(str(ROOT / _record("hse-hsg227")["raw_path"]))
    tree = hsg227
    A = {}
    for s in tree["sections"]:
        if s["type"] == "figure" and s.get("image_bbox"):
            page = pdf[s["area"]["page"] - 1].render(scale=2.0).to_pil()
            A[s["id"]] = photo_box(page, s["area"], s["caption_box"], 2.0, _next_caption_x(tree, s))
    assert A["figure-3"]["x0"] > A["figure-2"]["x1"]
    assert A["figure-9"]["x0"] > A["figure-8"]["x1"] and A["figure-10"]["x0"] > A["figure-9"]["x1"]
    assert A["figure-5"]["x1"] > 340  # "BAD PRACTICE" printed beside the photo is kept
    for n in (3, 5, 6, 9):  # nothing below the caption's top
        cap = next(s for s in tree["sections"] if s["id"] == f"figure-{n}")["caption_box"]
        assert A[f"figure-{n}"]["bottom"] < cap["top"], n


# ---------------------------------------------------------------- layouts beyond the pilot (S2c, 20 Nov 2026)

from system.rag.parse_pdf import normalise_bullet, split_columns  # noqa: E402


def wl(page, top, parts, size=10.0, font="HelveticaNeue-Light"):
    """A line as pdfplumber joins it, from (x0, text, size, font, bold) parts; words get sizes and x1."""
    words = []
    for x0, text, s, f, b in parts:
        x = x0
        for t in text.split():
            w = {"x0": float(x), "x1": float(x + 5 * len(t)), "text": t, "s": s, "f": f, "t": float(top)}
            if b:
                w["b"] = True
            words.append(w)
            x += 5 * (len(t) + 1)
    first = parts[0]
    return {"page": page, "top": float(top), "x0": float(first[0]), "size": first[2], "font": first[3],
            "text": " ".join(w["text"] for w in words), "words": words}


def sidebar_page():
    side, main = "HelveticaNeue-Medium", "HelveticaNeue-Roman"
    rows = [("Workers are at risk", "Asbestos essentials task sheets tell employers what to do"),
            ("of developing disease", "when they need to work on or near asbestos materials and"),
            ("from breathing fibres", "they help you decide which category of work it is and how"),
            ("in the air at work", "to plan the work safely with the right equipment for it.")]
    lines = [wl(1, 100 + 14 * i, [(34, a, 10.0, side, False), (215, b, 11.0, main, False)]) for i, (a, b) in enumerate(rows)]
    lines.append(wl(1, 60, [(215, "Why is asbestos a problem?", 13.0, "HelveticaNeue-Heavy", True)]))
    return lines


def test_sidebar_lines_are_cut_from_the_main_column_and_marked_aside():
    out = split_columns(sidebar_page(), 11.0, 595.0)
    side = [l for l in out if l.get("aside")]
    main = [l for l in out if not l.get("aside")]
    assert [l["text"] for l in side][0] == "Workers are at risk"
    assert all(l["x0"] >= 215 for l in main) and len(main) == 5
    assert main[1]["size"] == 11.0 and side[0]["size"] == 10.0  # each part keeps its own size


def test_table_cells_and_hanging_numbers_are_not_columns():
    rows = [wl(1, 100 + 14 * i, [(54, f"{i + 1}", 10.0, "Light", False), (90, "Work with materials containing asbestos HSE Books", 10.0, "Light", False)]) for i in range(4)]
    assert all("band" not in l for l in split_columns(rows, 10.0, 595.0))
    ruled = [wl(1, 100 + 14 * i, [(54, "Controlled wet stripping", 10.0, "Light", False), (250, "Up to one thorough soaking of it", 10.0, "Light", False)]) for i in range(4)]
    box = [{"page": 1, "top": 95, "bottom": 160, "x0": 50, "x1": 545}]
    assert all("band" not in l for l in split_columns(ruled, 10.0, 595.0, box))


def test_symbol_bullets_become_dots_and_take_the_text_size():
    l = normalise_bullet(wl(1, 100, [(57, "n", 10.0, "ZapfDingbatsITC", False), (70, "installing a kitchen", 10.0, "Light", False)]))
    assert l["text"] == "• installing a kitchen"
    small = normalise_bullet(wl(1, 100, [(178, "■", 8.0, "ZapfDingbatsITC", False), (190, "crocidolite (blue asbestos);", 10.0, "Light", False)]))
    assert small["size"] == 10.0 and small["text"].startswith("■ crocidolite")


def short_doc(lines, pages=2, **kw):
    d = {"lines": [ln(1, 300, "Task sheet a0", 30.0, "HelveticaNeue-Condensed")] + lines, "rects": [], "images": [],
         "page_count": pages}
    d.update(kw)
    return d


def test_document_without_chapter_titles_is_one_chapter_and_page_one_is_content():
    t = build_tree(short_doc([ln(1, 400, "What to do first", 13.0, "HelveticaNeue-Heavy"),
                              ln(1, 420, "Check what asbestos is present before you start work on site."),
                              ln(2, 100, "Ask the client for the register.")]), META)
    assert sec(t, "document")["title"] == "Demo guide"
    assert sec(t, "document-what-to-do-first")["type"] == "heading"
    assert "Check what asbestos" in sec(t, "document-what-to-do-first-text-1")["text"]


def test_margin_label_split_from_its_number_and_text_keeps_the_text_font():
    lines = [ln(2, 98, "1 Introduction", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "1 The Regulations apply to employers.", x0=180),
             wl(2, 200, [(57, "ACOP", 12.0, "HelveticaNeue-Bold", True)]),
             wl(2, 198, [(155, "2", 12.0, "HelveticaNeue-Bold", True), (180, "2 Employers should plan the work.", 10.0, "HelveticaNeue-Medium", False)]),
             ln(2, 300, "3 More guidance text here.", x0=180)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    p2 = sec(t, "para-2")
    assert p2["text"] == "Employers should plan the work." and p2["status"] == "acop"
    assert sec(t, "para-3")["status"] == "acop"


def test_body_size_caption_takes_the_rows_below_and_a_continued_table_joins_it():
    lines = [ln(3, 98, "1 Introduction", 28.0, "HelveticaNeue-Medium"),
             ln(3, 150, "1 Some work needs no licence.", x0=180),
             ln(3, 180, "Table 2 Examples of non-licensable work", 10.0, "HelveticaNeue-Medium", x0=180),
             ln(3, 210, "Maintenance work on asbestos cement products.", x0=184),
             ln(3, 234, "Drilling textured decorative coatings.", x0=184),
             ln(4, 104, "Table 2 Examples of non-licensable work continued", 10.0, "HelveticaNeue-Medium", x0=180),
             ln(4, 135, "Painting AIB.", x0=181),
             ln(4, 200, "2 To decide if other work is NNLW, assess it.", x0=180)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 4}, META)
    t2 = sec(t, "table-2")
    assert "Maintenance work" in t2["text"] and "Painting AIB." in t2["text"]
    assert sec(t, "para-2")["text"].startswith("To decide")


def test_contents_heading_inside_a_chapter_is_not_a_chapter():
    lines = [ln(2, 98, "1 Plans of work", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "1 The plan must be written.", x0=180),
             ln(2, 180, "Contents", 12.0, "HelveticaNeue-Bold", x0=180),
             ln(2, 200, "2 The plan should include the site layout.", x0=180)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    assert sec(t, "para-2")["text"].startswith("The plan should")


def test_statutory_instrument_layout_parts_regulation_headings_and_footnotes():
    T = "TimesNewRomanPSMT"
    B = "TimesNewRomanPS-BoldMT"
    lines = [ln(1, 200, "CONTENTS", 14.0, T, x0=260), ln(1, 220, "PART 1", 12.0, T, x0=278),
             ln(1, 260, "1. Citation and commencement", 10.5, T, x0=90),
             ln(2, 320, "PART 1", 14.0, T, x0=275), ln(2, 342, "Introduction", 12.0, T, x0=268),
             wl(2, 372, [(90, "Citation and commencement", 10.5, B, True)]),
             ln(2, 392, "1.—(1) These Regulations may be cited as the Demo Regulations.", 10.5, B, x0=98),
             ln(2, 404, "(2) They come into force on 1st January 2026.", 10.5, T, x0=98),
             wl(2, 430, [(90, "Interpretation", 10.5, B, True)]),
             ln(2, 450, "2. In these Regulations “lessor” has the meaning in the 1985 Act(a).", 10.5, T, x0=98),
             ln(2, 740, "(a) 1985 c. 70. Sections 10A and 10B were inserted by", 8.0, T, x0=90),
             ln(2, 749, "section 42 of the 2023 Act.", 8.0, T, x0=107),
             ln(3, 100, "PART 2", 14.0, T, x0=275), ln(3, 122, "Emergency action", 12.0, T, x0=250),
             wl(3, 150, [(90, "Requirement to take emergency action", 10.5, B, True)]),
             ln(3, 170, "3.—(1) This regulation applies if Condition 1 applies.", 10.5, T, x0=98)]
    lines += [ln(2, 500 + 12 * i, "words of the definition run on here for a while", 10.5, T, x0=107) for i in range(6)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    assert sec(t, "part-1")["title"] == "Introduction" and sec(t, "part-2")["title"] == "Emergency action"
    assert not [s for s in t["sections"] if s["id"] == "part-1-2"]  # the contents page is skipped
    assert sec(t, "part-1-interpretation")["type"] == "heading"
    assert sec(t, "para-1")["text"].startswith("(1) These Regulations")
    assert sec(t, "para-3")["text"].startswith("(1) This regulation") and sec(t, "para-3")["parent_id"].startswith("part-2")
    assert sec(t, "para-2")["footnotes"] == ["(a) 1985 c. 70. Sections 10A and 10B were inserted by section 42 of the 2023 Act."]


def test_photo_named_by_the_short_line_below_it():
    lines = [ln(1, 400, "Examples", 13.0, "HelveticaNeue-Heavy"),
             wl(1, 250, [(215, "Asbestos lagging", 9.0, "Light", False), (340, "Sprayed asbestos", 9.0, "Light", False)])]
    images = [{"page": 1, "top": 120, "bottom": 246, "x0": 214, "x1": 320},
              {"page": 1, "top": 120, "bottom": 246, "x0": 335, "x1": 441}]
    t = build_tree(short_doc(lines, images=images), META)
    titles = sorted(s["title"] for s in t["sections"] if s["id"].startswith("photo-"))
    assert titles == ["Asbestos lagging", "Sprayed asbestos"]
    assert not t["issues"]


def test_page_of_short_boxes_is_one_diagram_figure():
    lines = [wl(2, 100, [(44, "Decision flow chart", 13.0, "HelveticaNeue-Heavy", True)])]
    for i in range(16):
        lines.append(ln(2, 130 + 40 * (i // 4), "Is the work removal?", 11.0, x0=50 + 130 * (i % 4)))
    lines.append(ln(1, 400, "The flow chart helps you decide who should do the work and what kind of work it is.", 11.0))
    t = build_tree(short_doc(lines), META)
    f = sec(t, "figure-p2")
    assert f["type"] == "figure" and f["title"] == "Decision flow chart" and len(f["labels"]) == 16


def test_short_scattered_labels_are_a_drawing_and_prose_small_print_is_text():
    lines = [ln(2, 98, "1 Labelling", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "1 The label must look like this, and it must be printed so that it can be read.", x0=180),
             ln(2, 162, "It goes on raw asbestos, on asbestos waste and on products containing asbestos.", x0=180)]
    lines += [ln(2, 300 + 12 * i, t, 8.0, x0=300) for i, t in enumerate(["h", "20 mm", "H", "50 mm", "30 mm"])]
    lines += [ln(2, 700, "Published by the Health and Safety Executive in 2017 as guidance.", 8.0, x0=180)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    f = sec(t, "chapter-1-figure-1")
    assert f["type"] == "figure" and f["labels"][:2] == ["h", "20 mm"]
    assert not [s for s in t["sections"] if s["type"] == "table"]
    assert any(s.get("small_print") and "Published by" in s["text"] for s in t["sections"])


def _footnote_page(foot_lines, tables=()):
    lines = [ln(2, 98, "1 Exemptions", 28.0, "HelveticaNeue-Medium")]
    lines += [ln(2, 150 + 12 * i, BODY, x0=180) for i in range(4)]
    lines += foot_lines
    return build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "graphics": [], "pages": PAGES,
                       "tables": list(tables)}, META)


def test_footnotes_and_back_cover_at_the_foot_of_a_page_are_text_not_a_table():
    for foot in ([ln(2, 800, "1 Exemptions apply", 8.0, x0=60)],                      # supplier guide
                 [ln(2, 797, "2 www.gov.uk/government/collections/fire-safety", 8.0, x0=60)],
                 [ln(2, 766, "5", 8.0, x0=60), ln(2, 776, "For example; https://pubmed.ncbi.nlm.nih.gov/2896/", 8.0, x0=70)],
                 [ln(2, 716, "£6", 8.0, x0=60), ln(2, 730, "ISBN 0-11-753947-3", 8.0, x0=60)]):  # back cover
        # A page number read as a one-cell "table" does not make the footnote a table (supplier guide).
        t = _footnote_page(foot, tables=[{"page": 2, "top": 795.0, "bottom": 810.0, "x0": 40.0, "x1": 560.0,
                                          "rows": [["", "154", ""]]}])
        assert not [s for s in t["sections"] if s["type"] == "table"], foot[0]["text"]
        assert any(s.get("small_print") for s in t["sections"])
    # Small print in the same place cut into cells, or inside a ruled table, is still a table.
    t = _footnote_page([ln(2, 760, "1 Exemptions apply", 8.0, x0=60), ln(2, 772, "2 Exemptions apply", 8.0, x0=60)],
                       tables=[{"page": 2, "top": 750.0, "bottom": 790.0, "x0": 40.0, "x1": 560.0,
                                "rows": [["1", "Exemptions apply"], ["2", "Exemptions apply"]]}])
    assert [s for s in t["sections"] if s["type"] == "table"]


def test_imprint_bullet_list_and_stray_marks_in_small_print_are_not_a_table():
    def bullet(top, text):
        words = [{"x0": 60.0, "text": "(cid:2)"}] + [{"x0": 120.0 + 5 * i, "text": w} for i, w in enumerate(text.split())]
        return ln(2, top, "(cid:2) " + text, 8.0, x0=60, words=words)
    t = _footnote_page([bullet(300, "a building notice given to the local authority; or"),
                        bullet(310, "full plans deposited with the local authority; or"),
                        bullet(320, "an initial notice given by an approved inspector.")])
    assert not [s for s in t["sections"] if s["type"] == "table"]  # the gap after the bullet is an indent
    t = _footnote_page([ln(2, 500, "ISBN: 9780117540965", 8.0, x0=60), ln(2, 510, "ID P2352380 2/2010 1876 19585", 8.0, x0=60, words=[
        {"x0": 60.0, "text": "ID"}, {"x0": 75.0, "text": "P2352380"}, {"x0": 300.0, "text": "2/2010"},
        {"x0": 400.0, "text": "1876"}, {"x0": 450.0, "text": "19585"}])])
    assert not [s for s in t["sections"] if s["type"] == "table"]  # the printer's imprint, mid-page
    t = _footnote_page([ln(2, 600, ",.\"'C;\",'\",", 8.0, x0=60, words=[{"x0": 60.0, "text": ",.\"'C;"}, {"x0": 200.0, "text": "\",'\","}])])
    assert not [s for s in t["sections"] if s["type"] == "table"]  # stray marks, no word


def test_a_lone_short_label_is_text_but_short_lines_that_others_join_stay_a_table():
    t = _footnote_page([ln(2, 400, "RCS dust", 8.0, x0=300)])  # the label beside a photo (CIS54)
    assert not [s for s in t["sections"] if s["type"] == "table"]
    assert any(s.get("small_print") and s["text"] == "RCS dust" for s in t["sections"])
    gapped = {"words": [{"x0": 60.0, "text": "OELsol"}, {"x0": 300.0, "text": "551"}]}
    t = _footnote_page([ln(2, 400, "1/OELsol", 8.0, x0=60), ln(2, 460, "OELsol 551", 8.0, x0=60, **gapped)])
    assert [s for s in t["sections"] if s["type"] == "table"]  # a worked equation over two blocks (EH40)


def test_formula_subscripts_inside_a_text_line_are_not_a_table():
    # "A(8)week" in L140: "week" in 6 pt print just under the 10 pt line it belongs to.
    lines = [ln(2, 98, "1 Exposure", 28.0, "HelveticaNeue-Medium")]
    lines += [ln(2, 398.5, "68 The value obtained for A(8) according to the formula provided in", x0=178.6),
              ln(2, 410.5, "Schedule 1 may be compared with the ELV in the usual way.", x0=178.6),
              ln(2, 404.6, "week", 6.0, x0=317.7), ln(2, 500, "T = T Equation 3", x0=178.6),
              ln(2, 507, "EAV a 0", 6.0, x0=184.1), ln(2, 514, "hv", 6.0, x0=221.1)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "graphics": [], "pages": PAGES}, META)
    assert not [s for s in t["sections"] if s["type"] == "table"]


def _shape(page, x0, top, x1, bottom, kind="rect"):
    return {"page": page, "kind": kind, "top": float(top), "bottom": float(bottom), "x0": float(x0), "x1": float(x1),
            "fill": False, "stroke": True, "colour": (0.0,)}


def _flow_chart_page():
    lines = [wl(2, 100, [(44, "Decision flow chart", 13.0, "HelveticaNeue-Heavy", True)])]
    for i in range(16):
        lines.append(ln(2, 130 + 40 * (i // 4), "Is the work removal?", 11.0, x0=50 + 130 * (i % 4)))
    lines.append(ln(1, 400, "The flow chart helps you decide who should do the work and what kind of work it is.", 11.0))
    return lines


PAGES = {1: {"width": 595.0, "height": 842.0}, 2: {"width": 595.0, "height": 842.0}}


def drawn_doc(lines, **kw):
    """short_doc as read_guidance gives it: with drawn shapes (graphics) and page sizes."""
    return {**short_doc(lines, **kw), "pages": PAGES, "graphics": kw.get("graphics", [])}


def test_page_of_short_lines_is_a_diagram_only_with_drawn_boxes_around_them():
    lines = _flow_chart_page()
    boxes = [_shape(2, 45 + 130 * (i % 4), 125 + 40 * (i // 4), 160 + 130 * (i % 4), 150 + 40 * (i // 4))
             for i in range(16)]
    boxes.append(_shape(2, 100, 268, 104, 300, "line"))  # an arrow below the last box
    t = build_tree(drawn_doc(lines, graphics=boxes), META)
    f = sec(t, "figure-p2")
    assert f["area"]["bottom"] >= 300  # cut to the drawing's ink, not only its words
    # A letter's address block: the same short scattered lines, no drawn shapes. Not a figure.
    t = build_tree(drawn_doc(lines), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]


def test_page_of_short_lines_in_a_ruled_table_is_a_table_not_a_figure():
    lines = _flow_chart_page()
    tables = [{"page": 2, "top": 120.0, "bottom": 300.0, "x0": 40.0, "x1": 560.0, "rows": [["Is the work removal?"] * 4]}]
    t = build_tree(drawn_doc(lines, tables=tables), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]
    tab = sec(t, "table-p2")
    assert tab["type"] == "table" and tab["title"] == "Decision flow chart" and tab["grid"]


def test_short_small_print_lines_without_drawn_shapes_are_not_a_drawing():
    lines = [ln(2, 98, "1 Labelling", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "1 The label must look like this, and it must be printed so that it can be read.", x0=180)]
    lines += [ln(2, 700 + 12 * i, t, 8.0, x0=60) for i, t in
              enumerate(["Ministry of Housing", "Fry Building", "2 Marsham Street", "London SW1P 4DF"])]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "graphics": [], "pages": PAGES}, META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]
    assert "Fry Building" in all_text(t)
    # The same lines among the strokes of a drawing are its labels.
    strokes = [_shape(2, 100 + 10 * i, 705, 110 + 10 * i, 740, "curve") for i in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "graphics": strokes,
                    "pages": PAGES}, META)
    assert sec(t, "chapter-1-figure-1")["labels"][0] == "Ministry of Housing"


def test_signature_and_letterhead_logo_are_not_photos():
    lines = [ln(1, 400, "Yours faithfully", 11.0, x0=72),
             ln(1, 470, "John Smith", 11.0, "Arial-Bold", x0=72),
             ln(1, 484, "Deputy Director", 11.0, x0=72),
             ln(1, 100, "To: The Chief Executive", 11.0, x0=72)]
    images = [{"page": 1, "top": 415.0, "bottom": 466.0, "x0": 72.0, "x1": 170.0},  # signature
              {"page": 1, "top": 40.0, "bottom": 95.0, "x0": 72.0, "x1": 200.0}]   # crest at the top of page 1
    t = build_tree(drawn_doc(lines, images=images), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]
    assert "John Smith" in all_text(t)


BODY = "This is a line of running text in the body of the guide about safe work."


def _page_with_body(page, tops, x0=180.0):
    return [ln(page, t, BODY, 10.0, x0=x0) for t in tops]


def test_drawing_without_labels_is_cut_from_its_shapes_in_the_caption_column():
    # Running text on the left (x 60), a drawing on the right (x 330-520), its caption under it.
    lines = [ln(1, 98, "1 Planning", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174])  # full-width text above
    lines += [ln(1, 300 + 12 * i, "Short column text beside the drawing goes on here.", 10.0, x0=60) for i in range(15)]
    lines += [ln(1, 482, "Figure 2 Hierarchy for work at height", 8.0, "HelveticaNeue", x0=340)]
    shapes = [_shape(1, 330, 300, 520, 470, "curve"), _shape(1, 360, 400, 500, 402, "line")]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2, "graphics": shapes,
                    "pages": PAGES}, META)
    a = sec(t, "figure-2")["area"]
    assert a["top"] <= 300 and a["bottom"] >= 490  # the whole drawing and its caption
    assert a["x0"] >= 320  # not the text column beside it
    assert a["top"] >= 186  # not the running text above


def test_captions_above_figures_take_the_drawing_below():
    lines = [ln(1, 98, "1 Enclosures", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [130, 142])
    lines += [ln(1, 160, "Figure 1.1 Schematic of an enclosure", 9.0, "HelveticaNeue", x0=60)]
    lines += _page_with_body(1, [400, 412])
    lines += [ln(1, 430, "Figure 1.2 The airlock", 9.0, "HelveticaNeue", x0=60)]
    lines += _page_with_body(1, [700, 712])
    shapes = [_shape(1, 140, 175, 420, 380), _shape(1, 140, 445, 420, 680)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2, "graphics": shapes,
                    "pages": PAGES}, META)
    a1, a2 = sec(t, "figure-1-1")["area"], sec(t, "figure-1-2")["area"]
    assert a1["top"] <= 160 and 380 <= a1["bottom"] < 400
    assert a2["top"] <= 430 and 680 <= a2["bottom"] < 700


def test_photos_stacked_over_one_caption_are_one_figure():
    lines = [ln(1, 98, "1 Dust", 28.0, "HelveticaNeue-Medium")]
    lines += [ln(1, 455, "Figure 2 Examples of captor hoods", 9.0, "HelveticaNeue", x0=60)]
    lines += _page_with_body(1, [500, 512, 524], x0=60)
    images = [{"page": 1, "top": 100.0, "bottom": 270.0, "x0": 55.0, "x1": 290.0},
              {"page": 1, "top": 278.0, "bottom": 450.0, "x0": 55.0, "x1": 290.0}]
    t = build_tree({"lines": lines, "rects": [], "images": images, "page_count": 2, "graphics": [],
                    "pages": PAGES}, META)
    f = sec(t, "figure-2")
    assert f["area"]["top"] == 100.0 and f["area"]["bottom"] == 450.0 and not f.get("image_bbox")


# ---------------------------------------------------------------- real files: S2c sources

def _real(source_id, title):
    pytest.importorskip("pdfplumber")
    r = _record(source_id)
    return build_tree(read_guidance(ROOT / r["raw_path"]), {**r, "title": title}, fixes=load_fixes(source_id))


@pytest.fixture(scope="module")
def l143():
    return _real("hse-l143", "L143 Managing and working with asbestos")


def test_real_l143_structure(l143):
    secs = l143["sections"]
    main = [int(s["number"]) for s in secs if s["type"] == "paragraph" and s["id"].startswith("para-")]
    assert main == list(range(1, 538))
    regs = [s for s in secs if s["type"] == "chapter" and s["id"].startswith("regulation-")]
    assert len(regs) == 35
    assert sorted(int(s["number"]) for s in secs if s["type"] == "table" and s["number"]) == list(range(1, 8))
    tabs = [s for s in secs if s["type"] == "table" and not s["number"]]  # Schedule 3 runs on to page 113 (S118)
    assert [s["id"] for s in tabs] == ["schedule-3-table-p112"] and sorted(tabs[0]["spans"]) == ["112", "113"]
    S = {s["id"]: s for s in secs}
    assert S["para-46"]["status"] == "guidance" and S["para-36"]["status"] == "acop"
    assert S["para-46"]["text"].startswith("Licensable work does not meet")
    assert len({s["id"] for s in secs}) == len(secs)
    assert not [s for s in secs if s["type"] == "note" and s["text"].startswith(("ACOP", "Guidance", "Regulation"))]


def test_real_l143_all_checks_settled_by_saved_fixes(l143):
    assert l143["checks"] == []
    S = {s["id"]: s for s in l143["sections"]}
    assert S["table-5"]["grid_source"] == "model" and len(S["table-5"]["row_sentences"]) == 24
    assert S["schedule-2-figure-1"]["description_source"] == "model"


@pytest.fixture(scope="module")
def a0():
    return _real("hse-asbestos-a0", "Asbestos essentials a0")


def test_real_a0_sidebars_photos_and_diagrams(a0):
    S = {s["id"]: s for s in a0["sections"]}
    assert S["note-3"]["title"] == "Safety checklist" and "Class H" not in S["note-3"]["text"]
    assert [S[f"photo-{n}"]["title"] for n in (1, 2, 3)] == ["Broken asbestos insulating board", "Asbestos lagging",
                                                            "Sprayed asbestos (limpet)"]
    assert S["figure-p6"]["title"] == "Decision flow chart"
    assert S["figure-p7"]["title"].startswith("Where asbestos materials can be found")
    assert a0["checks"] == [] and not a0["issues"]


@pytest.fixture(scope="module")
def em1():
    return _real("hse-asbestos-em1", "Asbestos essentials em1")


def test_real_em1(em1):
    S = {s["id"]: s for s in em1["sections"]}
    assert {"document-unexpected-discovery-of-asbestos", "document-accidental-release-of-asbestos",
            "document-emergency-procedures"} <= set(S)
    assert S["photo-1"]["title"].startswith("Top row:") and S["figure-p3"]["title"] == "Flow chart"
    assert em1["checks"] == []


def test_real_cis80_two_columns():
    t = _real("hse-cis80", "CIS80")
    titles = [s["title"] for s in t["sections"] if s["type"] == "note"]
    assert {"Plan", "Working together", "Organise"} <= set(titles)
    assert t["checks"] == []


def test_real_awaab_consolidated_regulations():
    t = _real("awaab-consolidated", "Awaab's law regulations")
    paras = [int(s["number"]) for s in t["sections"] if s["type"] == "paragraph"]
    assert paras == list(range(1, 24))
    # The enacting words before Part 1 are kept in "Front matter" (S105), with the end of the contents list
    # above them on the same page (parking lot).
    assert [s["id"] for s in t["sections"] if s["type"] == "chapter"] == ["front-matter"] + [f"part-{n}" for n in range(1, 8)]
    assert "The Secretary of State makes the following regulations" in sec(t, "front-matter-text-1")["text"]
    assert t["checks"] == [] and not t["issues"]


def test_decimal_paragraphs_and_appendix_numbers_follow_their_chapter():
    lines = [ln(2, 98, "2 Accreditation", 28.0, "HelveticaNeue-Medium", x0=57),
             ln(2, 150, "2.1 Organisations must be accredited by UKAS for this work.", x0=57),
             ln(2, 180, "2.2 The assessment covers 5.6 m of documents and more.", x0=57),
             ln(3, 98, "Appendix 1 Fibres in air", 28.0, "HelveticaNeue-Medium", x0=57),
             ln(3, 150, "A1.1 This method is used to count fibres in air samples.", x0=176),
             ln(3, 180, "A1.2 Use a phase contrast microscope for the count.", x0=176)]
    lines += [ln(2, 300 + 12 * i, "running text of the chapter goes on here for a while and more", x0=57) for i in range(6)]
    lines += [ln(3, 300 + 12 * i, "running text of the appendix goes on here for a while and more", x0=176) for i in range(6)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 4}, META)
    assert sec(t, "para-2-2")["number"] == "2.2" and sec(t, "para-2-2")["text"].startswith("The assessment")
    assert sec(t, "para-a1-2")["parent_id"] == "appendix-1"


def test_lettered_and_appendix_captions():
    lines = [ln(2, 98, "1 Gas", 28.0, "HelveticaNeue-Medium"), ln(2, 150, "1 Gas fittings must be safe.", x0=180),
             ln(2, 300, "Figure 11(a) LPG systems – cylinder installation", 9.0, "HelveticaNeue"),
             ln(2, 400, "Table A1.2 Sampling rates", 9.0, "HelveticaNeue"),
             ln(2, 420, "Rate 1 litre per minute", 8.0, x0=180)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    assert sec(t, "figure-11a")["number"] == "11(a)"
    assert sec(t, "table-a1-2")["title"] == "Sampling rates"


def test_margin_labels_with_paragraph_references_and_letter_parts():
    lines = [ln(2, 98, "PART B Gas fittings", 16.0, "HelveticaNeueLTStd-HvCn"),
             wl(2, 150, [(57, "ACOP", 11.0, "HelveticaNeueLTStd-Bd", True)]),
             wl(2, 150, [(143, "3(1)–(2)", 11.0, "HelveticaNeueLTStd-Bd", True)]),
             ln(2, 152, "1 No one shall carry out work on a gas fitting unless competent.", x0=180)]
    lines += [ln(2, 200 + 12 * i, "guidance text about competence goes on and on here", x0=180) for i in range(5)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    assert sec(t, "part-b")["title"] == "Gas fittings"
    assert sec(t, "para-1")["status"] == "acop" and not [s for s in t["sections"] if s["type"] == "note"]


@pytest.fixture(scope="module")
def hsg150():
    return _real("hse-hsg150", "HSG150 Health and safety in construction")


def test_real_hsg150(hsg150):
    paras = [int(s["number"]) for s in hsg150["sections"] if s["type"] == "paragraph" and s["id"].startswith("para-")]
    assert paras == list(range(1, 682))
    ids = {s["id"] for s in hsg150["sections"]}
    assert {"figure-12a", "figure-48d", "figure-54"} <= ids and len(ids) == len(hsg150["sections"])
    assert hsg150["checks"] == []


def test_real_l153():
    t = _real("hse-l153", "L153 Managing health and safety in construction")
    main = [int(s["number"]) for s in t["sections"] if s["type"] == "paragraph" and s["id"].startswith("para-")]
    assert main[:30] == list(range(1, 31)) and main[-1] == 186 and len(main) >= 180
    assert len([s for s in t["sections"] if s["id"].startswith("regulation-") and s["type"] == "chapter"]) == 39
    assert t["checks"] == []


def test_real_hsg248_decimal_paragraphs():
    t = _real("hse-hsg248", "HSG248 Asbestos: The analysts' guide")
    S = {s["id"]: s for s in t["sections"]}
    assert S["para-2-14"]["text"].startswith("These site issues arose")
    assert len([s for s in t["sections"] if s["type"] == "paragraph"]) >= 580
    assert {"table-2-1", "table-a1-2", "appendix-2-annex-1"} <= set(S)
    assert len(S) == len(t["sections"])


def test_real_l56_labels_and_paragraphs():
    t = _real("hse-l56", "L56 Safety in the installation and use of gas systems and appliances")
    main = [int(s["number"]) for s in t["sections"] if s["type"] == "paragraph" and s["id"].startswith("para-")]
    assert main[0] == 1 and main[-1] >= 340 and len(main) >= 335
    assert len([s for s in t["sections"] if s["type"] == "note"]) <= 2
    assert {"figure-7a", "figure-11c"} <= {s["id"] for s in t["sections"]}


def _doc(lines, images=(), shapes=(), tables=()):
    return {"lines": lines, "rects": [], "images": list(images), "page_count": 2, "graphics": list(shapes),
            "pages": PAGES, "tables": list(tables)}


def test_leaflet_cover_thumbnail_is_not_a_photo():
    lines = [ln(1, 300, "This is a web-friendly", 8.0, x0=60), ln(1, 310, "version of leaflet INDG463", 8.0, x0=60)]
    lines += _page_with_body(1, [400, 412, 424], x0=60)
    images = [{"page": 1, "top": 200.0, "bottom": 296.0, "x0": 60.0, "x1": 140.0}]
    t = build_tree(drawn_doc(lines, images=images), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]


def test_caption_saying_left_or_above_takes_that_photo():
    lines = [ln(1, 98, "1 Roofs", 28.0, "HelveticaNeue-Medium")]
    lines += [ln(1, 590, "Figure 37 (left) Permanent walkway", 8.0, "HelveticaNeue", x0=303),
              ln(1, 626, "Figure 38 (above) Lighting panels", 8.0, "HelveticaNeue", x0=303)]
    lines += _page_with_body(1, [700, 712, 724, 736, 748], x0=60)
    images = [{"page": 1, "top": 438.0, "bottom": 748.0, "x0": 56.0, "x1": 292.0},
              {"page": 1, "top": 438.0, "bottom": 580.0, "x0": 303.0, "x1": 538.0}]
    t = build_tree(_doc(lines, images), META)
    assert sec(t, "figure-37")["area"]["x0"] == 56.0 and sec(t, "figure-38")["area"]["x0"] == 303.0


def test_flow_chart_box_as_wide_as_the_text_column_does_not_end_the_figure():
    lines = [ln(1, 98, "1 Control", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=180)
    lines += [ln(1, 200, "Figure 1 Route map for adequate control", 10.0, "HelveticaNeue-Bold", x0=180)]
    lines += [ln(1, 360, BODY, 10.0, x0=180)]  # running text inside the wide box
    shapes = [_shape(1, 180, 220, 360, 320), _shape(1, 270, 320, 272, 348, "line"),
              _shape(1, 178, 348, 540, 416), _shape(1, 270, 416, 272, 444, "line"), _shape(1, 180, 444, 360, 500)]
    t = build_tree(_doc(lines, shapes=shapes), META)
    assert sec(t, "figure-1")["area"]["bottom"] >= 500


def test_note_line_under_a_drawing_and_a_side_panel_belong_to_it():
    lines = [ln(1, 98, "1 Lifting", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=60)
    lines += [ln(1, 200, "Figure 1 Flow of the checks", 10.0, "HelveticaNeue-Bold", x0=60)]
    lines += [ln(1, 505, "Note: LGA Guide see Fire safety in purpose-built blocks of flats", 10.0, x0=60)]
    shapes = [_shape(1, 60, 220, 300, 500), _shape(1, 320, 260, 420, 460)]
    t = build_tree(_doc(lines, shapes=shapes), META)
    a = sec(t, "figure-1")["area"]
    assert a["bottom"] >= 515 and a["x1"] >= 420


def test_large_picture_on_its_own_keeps_all_its_parts():
    lines = [ln(1, 98, "1 Filters", 28.0, "HelveticaNeue-Medium"),
             ln(1, 767, "Figure A1.5 Cowl being loaded", 8.0, "HelveticaNeue", x0=176)]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=176)
    images = [{"page": 1, "top": 518.0, "bottom": 760.0, "x0": 176.0, "x1": 538.0}]
    t = build_tree(_doc(lines, images), META)
    assert sec(t, "figure-a1-5")["photo_whole"]


def test_medium_weight_caption_with_ink_above_is_a_caption():
    lines = [ln(1, 98, "1 Noise", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=60)
    lines += [ln(1, 420, "Figure 9 The direct noise path is blocked", 10.0, "HelveticaNeueLTStd-MdCn", x0=60)]
    lines += [ln(1, 450 + 12 * i, BODY, 10.0, x0=60) for i in range(3)]
    shapes = [_shape(1, 60, 200, 400, 410, "curve")]
    t = build_tree(_doc(lines, shapes=shapes), META)
    f = sec(t, "figure-9")
    assert f["area"]["top"] <= 200 and f["area"]["bottom"] < 450  # the drawing and caption, not the text below


def test_caption_like_line_in_another_font_still_ends_the_figure_above_it():
    lines = [ln(1, 98, "1 Fibres", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=60)
    lines += [ln(1, 400, "Figure A1.10 g–h Examples of counting rules", 10.0, "HelveticaNeueLTStd-MdCn", x0=60),
              ln(1, 700, "Figure A1.10i Example of counting rules", 9.0, "HelveticaNeue-Bold", x0=60)]
    shapes = [_shape(1, 80, 200, 300, 390, "curve"), _shape(1, 80, 420, 300, 690, "curve")]
    t = build_tree(_doc(lines, shapes=shapes), META)
    assert sec(t, "figure-a1-10i")["area"]["top"] >= 405


def test_labels_beside_a_drawing_join_it_but_text_in_the_next_column_does_not():
    lines = [ln(1, 98, "1 Charts", 28.0, "HelveticaNeue-Medium")]
    lines += _page_with_body(1, [114, 126, 138, 150, 162, 174], x0=60)
    lines += [wl(1, 250, [(80, "Falls from a height", 8.0, "Light", False), (330, "97", 8.0, "Light", False)])]
    lines += [ln(1, 420, "Figure 1 Falls are the biggest killer", 8.0, "HelveticaNeue", x0=60)]
    shapes = [_shape(1, 160, 245, 320, 260)]
    t = build_tree(_doc(lines, shapes=shapes), META)
    assert sec(t, "figure-1")["area"]["x1"] >= 340


# Sources whose model checks were all answered through packets (22 Nov 2026). Rebuilding some of them from the raw
# file takes over half an hour (supplier-information), so this reads the parsed trees; it skips where none exist.
SETTLED_SOURCES = """awaab-collection awaab-tenants bc-changes-2023 br-circulars circ-adb-2024 fser-page fso-s156 hhsrs-operating
hse-cis36 hse-cis54 hse-cis62 hse-cis65 hse-cis78 hse-cis79 hse-hsg141 hse-hsg247 hse-hsg248 hse-hsg33 hse-hsg47 hse-hsg85
hse-hsr25 hse-indg136 hse-indg231 hse-indg236 hse-indg344 hse-indg411 hse-indg463 hse-l108 hse-l140 hse-l5
manual-br pd-householder-guide supplier-information""".split()


@pytest.mark.parametrize("source_id", SETTLED_SOURCES)
def test_real_parsed_guidance_trees_have_no_open_checks(source_id):
    trees = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "parsed" / source_id).glob("*.json")]
    trees = [t for t in trees if str(t.get("parser", "")).startswith("guidance-pdf")]
    from system.rag.corpus import version_in_scope
    trees = [t for t in trees if version_in_scope(source_id, t["version_id"])]  # ADR 0016: old versions stay open
    if not trees:
        pytest.skip(f"{source_id} not parsed on this machine")
    open_checks = {t["version_id"]: len(t["checks"]) for t in trees if t["checks"]}
    assert open_checks == {}


def test_chapter_titles_found_from_the_contents_page_when_only_contents_is_large():
    """HHSRS Parts 1-2 and Procurement Act short guides: "Contents" is the only line large enough to be a chapter
    title, so the whole document used to be skipped as front matter (S103). Chapter titles are then the largest
    later lines whose text is a contents entry, and every line in that style."""
    lines = [ln(1, 200, "Demo guide title", 24.0, "ArialMT"),
             ln(2, 100, "Contents", 16.0, "Calibri-Light"),
             ln(2, 140, "Introduction ........................ 3", 11.0, "Calibri"),
             ln(2, 160, "Assessing hazards ................... 4", 11.0, "Calibri"),
             ln(3, 80, "Introduction", 16.0, "Calibri-Light"),
             ln(3, 110, "Housing is a key factor of both physical and mental health for people.", 11.0, "Calibri"),
             ln(4, 80, "Assessing hazards", 16.0, "Calibri-Light"),
             ln(4, 110, "Inspect the whole dwelling before you score any hazard at all.", 11.0, "Calibri"),
             ln(5, 80, "Annex", 16.0, "Calibri-Light"),  # not listed, but in the same style
             ln(5, 110, "Further notes for assessors on how to record what they found.", 11.0, "Calibri")]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 5}, META)
    chapters = [s["title"] for s in t["sections"] if s["type"] == "chapter"]
    assert chapters == ["Introduction", "Assessing hazards", "Annex"]
    assert any("Housing is a key factor" in (s.get("text") or "") for s in t["sections"])
    assert not any("...." in (s.get("text") or "") for s in t["sections"])  # the contents page stays skipped


BLURB = ["This book contains the Approved Code of Practice and guidance on the Regulations for",
         "employers and the self-employed who carry out work with hazardous substances at work and",
         "it explains what the law requires and what you must do to protect your employees and others",
         "who may be affected by the work, with practical advice on control measures and records."]


def test_content_before_the_first_chapter_is_kept_but_not_the_imprint_or_contents():
    """Coverage S105: everything before the first chapter title was skipped as front matter, so a cover blurb
    (HSE ACOPs), a key-facts page after the contents (HSG227) or a whole leaflet (INDG285) was lost. Content
    pages (40+ words of body-size running text) are kept in a "Front matter" chapter; the imprint and the
    contents page are still skipped."""
    lines = [ln(1, 100, "Control of demo substances", 37.0, "HelveticaNeue-BoldCond", 54),
             ln(1, 184, "Approved Code of Practice and guidance", 18.0, "HelveticaNeue-Light", 54),
             *[ln(1, 273 + 12 * k, t) for k, t in enumerate(BLURB)],
             ln(1, 300, "Cover thumbnail words", 1.6, "HelveticaNeue-Bold", 143),
             ln(2, 100, "© Crown copyright 2013. First published 2005. ISBN 978 0 7176 6582 2"),
             *[ln(2, 120 + 12 * k, t) for k, t in enumerate(BLURB)],
             ln(3, 98, "Contents", 28.0, "HelveticaNeue-Medium"), ln(3, 140, "Introduction 5"),
             ln(4, 100, "The key facts", 11.0, "HelveticaNeue-Bold"),
             *[ln(4, 120 + 12 * k, t.replace("book", "page")) for k, t in enumerate(BLURB)],
             ln(4, 180, "Approved Document B Volume 1 (2006 Edition, ISBN: 978 185946 261 4) is now available."),
             ln(5, 98, "Introduction", 28.0, "HelveticaNeue-Medium"),
             ln(5, 150, "1 The Regulations apply to employers."),
             ln(6, 98, "Duties", 28.0, "HelveticaNeue-Medium"),
             ln(6, 150, "2 Employers must assess the risk.")]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 6}, META)
    front = sec(t, "front-matter")
    assert front["file_page"] == 1 and front["title"] == "Front matter"
    kept = all_text(t)
    assert "This book contains the Approved Code" in kept and "This page contains the Approved Code" in kept
    assert sec(t, "front-matter-the-key-facts")["file_page"] == 4
    assert "2006 Edition, ISBN" in kept  # an ISBN in running text does not make the page an imprint
    assert "ISBN 978 0 7176" not in kept and "Introduction 5" not in kept and "thumbnail" not in kept
    assert [s["title"] for s in t["sections"] if s["type"] == "chapter"] == ["Front matter", "Introduction", "Duties"]


def test_a_chapter_title_on_page_one_with_text_under_it_is_a_chapter():
    """MS34 and DETR circulars: "Introduction" on page 1 under the document's title, with paragraphs under it,
    was taken for part of the cover and skipped. A later large title on page 1 is a chapter when running text
    follows it; one without (a subtitle such as "Part 1: An introductory guide") is not."""
    lines = [ln(1, 100, "Guidance for doctors on medical", 36.0, "HelveticaNeueLT-BoldCond", 54),
             ln(1, 135, "surveillance of demo workers", 36.0, "HelveticaNeueLT-BoldCond", 54),
             ln(1, 230, "Introduction", 30.0, "HelveticaNeueLT-Condensed"),
             ln(1, 280, "1 This document provides guidance for doctors on medical surveillance."),
             ln(1, 294, "It updates the earlier version following a review by the regulator."),
             ln(1, 308, "There is no change to the frequency of medical surveillance."),
             ln(1, 600, "Related diseases", 30.0, "HelveticaNeueLT-Condensed"),
             ln(1, 650, "2 Most deaths are associated with very high past exposures at work."),
             ln(1, 664, "Many buildings still contain the material in walls and ceilings."),
             ln(1, 678, "Those now most at risk are maintenance workers and tradespeople."),
             ln(2, 100, "Who can do it", 30.0, "HelveticaNeueLT-Condensed"),
             ln(2, 150, "3 Any registered medical practitioner can do the surveillance.")]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2}, META)
    assert [s["title"] for s in t["sections"] if s["type"] == "chapter"] == ["Introduction", "Related diseases", "Who can do it"]
    assert sec(t, "para-1")["file_page"] == 1 and sec(t, "para-2")["file_page"] == 1
    cover = [ln(1, 230, "Demo rating system", 24.0, "ArialMT", 72), ln(1, 311, "Part 1: An introductory guide", 18.0, "ArialMT", 72),
             ln(1, 390, "Presented to Parliament", 14.0, "ArialMT", 72), ln(2, 76, "Contents", 16.0, "Calibri-Light"),
             ln(3, 76, "Introduction", 24.0, "ArialMT"), ln(3, 110, "Housing is a key factor of health.", 11.0, "Calibri")]
    t = build_tree({"lines": cover, "rects": [], "images": [], "page_count": 3}, META)
    assert [s["title"] for s in t["sections"] if s["type"] == "chapter"] == ["Introduction"]


def test_a_phone_number_or_a_schedule_named_in_running_text_is_not_a_chapter():
    """INDG285: "Tel: 0800 300 363" in 21pt on the back page was the only chapter title, so pages 1-4 were skipped
    as front matter. Circular 01/2015: a body line "Schedule 3 to the Building Regulations 2010 ..." set a little
    larger was taken for a SCHEDULE heading. Neither is a chapter: the document is one chapter from page 1."""
    for big in (ln(3, 273, "Tel: 0800 300 363", 21.0, "HelveticaNeueLTPro-Bd"),
                ln(3, 197, "Schedule 3 to the Building Regulations 2010 (S.I. 2010/2214):", 11.0, "GoudyOldStyleBT-Roman")):
        lines = [ln(1, 97, "Landlords", 37.0, "HelveticaNeueLTStd-BdC", 54),
                 ln(1, 531, "What type of property is covered?", 12.0, "HelveticaNeueLTPro-Bd"),
                 ln(1, 556, "The duties generally apply to appliances and flues provided for tenants."),
                 ln(2, 100, "Any lease under seven years is covered by the duties in the Regulations."),
                 ln(2, 112, "Landlords must keep the record of the safety check for two years."), big,
                 ln(3, 300, "This guidance is issued by the regulator and is not compulsory.")]
        t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
        assert [s["id"] for s in t["sections"] if s["type"] == "chapter"] == ["document"]
        assert "The duties generally apply" in all_text(t)


def test_cover_thumbnail_is_not_a_photo_and_its_caption_is_text():
    """HSE leaflets and books print a small picture of their own cover with the publication's name under it
    ("This is a web-friendly version of leaflet INDG231(rev1)", read on the same line as the text column beside
    it; "HSG85 (Third edition) Published 2013"). It is not a figure, and the lines under it are text, not a
    table. The same rule is used by the coverage check (S107)."""
    two_col = [{"x0": 54.0, "x1": 160.0, "text": w} for w in "This is a web-friendly version".split()]
    two_col += [{"x0": 179.0 + 6 * i, "x1": 183.0 + 6 * i, "text": w} for i, w in enumerate("also cause death or".split())]
    lines = [ln(1, 100, "Electrical safety", 37.0, "HelveticaNeue-BoldCond", 54),
             ln(1, 388, "This is a web-friendly version also cause death or", 9.0, x0=54, words=two_col),
             ln(1, 400, "of leaflet INDG231(rev1), careful planning", 9.0, x0=54),
             ln(1, 412, "published 04/12", 9.0, x0=54),
             ln(1, 300, "Text on the thumbnail", 3.8, x0=60),
             ln(1, 500, "Electricity can kill or severely injure people and cause damage to property.")]
    images = [{"page": 1, "top": 229.0, "bottom": 378.0, "x0": 54.0, "x1": 168.0}]
    t = build_tree(drawn_doc(lines, images=images), META)
    assert not [s for s in t["sections"] if s["type"] in ("figure", "table")]
    assert "web-friendly version" in all_text(t) and "thumbnail" not in all_text(t)
    lines = [ln(1, 100, "Safe working practices", 37.0, "HelveticaNeue-BoldCond", 54),
             ln(1, 405, "HSG85 (Third edition)", 10.0, x0=54), ln(1, 417, "Published 2013", 10.0, x0=54),
             ln(1, 500, "The guidance covers the key elements to consider when devising safe working practices.")]
    images = [{"page": 1, "top": 236.0, "bottom": 396.0, "x0": 54.0, "x1": 167.0}]
    t = build_tree(drawn_doc(lines, images=images), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]


def test_a_contents_page_with_its_page_numbers_in_a_column_stays_skipped():
    """HSG33: the contents run on to a second page with no "Contents" title, the page numbers set as a column
    of their own lines. That page is not front content; the 12pt cover blurb on page 1 is."""
    entries = ["Training and competence for roof workers", "The role of the client", "The role of the designer",
               "The role of the principal contractor", "The role of the contractor", "Issues for method statements",
               "Further reading and useful contacts", "Glossary of terms used in this book"]
    lines = [ln(1, 197, "Health and safety in roof work", 30.0, "HelveticaNeueLTStd-XBl", 57),
             *[ln(1, 316 + 14 * k, t, 12.0, "HelveticaNeueLTStd-LtC") for k, t in enumerate(BLURB)],
             ln(2, 100, "CONTENTS", 30.0, "HelveticaNeueLTStd-BdC"), ln(2, 176, "Preface"), ln(2, 176, "5", x0=531),
             *[ln(3, 100 + 14 * k, t) for k, t in enumerate(entries)],
             *[ln(3, 100 + 14 * k, str(40 + 2 * k), x0=526) for k in range(len(entries))],
             ln(4, 100, "PREFACE", 30.0, "HelveticaNeueLTStd-BdC"),
             ln(4, 150, "Every year many construction site workers are killed or injured at work.")]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 4}, META)
    kept = all_text(t)
    assert "This book contains the Approved Code" in kept and "The role of the client" not in kept


def test_running_text_without_numbers_is_cut_at_page_breaks_so_citations_name_the_page():
    """bc-changes-2023 (a 25-page letter) and Procurement Act short guides were one text section each, cited as
    page 1. Unnumbered text starts a new section on a new page when the last page ended a sentence, and always on
    its third page; a sentence running over one page break stays whole."""
    lines = [ln(1, 300, "Dear Sir or Madam, I am writing about the changes to building control.", x0=43),
             ln(2, 100, "The new rules apply from 1 October 2023 to all building work in", x0=43),
             ln(3, 100, "England. Applications must be made to the regulator before work starts", x0=43),
             ln(4, 100, "and the regulator will decide them within twelve weeks of receipt", x0=43),
             ln(5, 100, "Enquiries should be sent to the department by email.", x0=43)]
    t = build_tree({"lines": [ln(1, 80, "Building control letter", 30.0, "Arial-Bold", 43)] + lines, "rects": [],
                    "images": [], "page_count": 5}, META)
    texts = [(s["file_page"], s["text"][:20]) for s in t["sections"] if s["type"] == "text"]
    assert texts == [(1, "Dear Sir or Madam, I"), (2, "The new rules apply "), (4, "and the regulator wi")]


def test_small_print_pages_apart_is_not_one_table_and_a_box_round_text_is_not_a_grid():
    """bc-changes-2023: a one-line web address on page 1 and the legal text of Annex A on page 17, both small
    print under the same chapter, were joined into one 'table' cited as page 1; the Annex is set in a ruled box
    (a one-column 'table'), which made its sentences look tabular. Now: the address is text, the Annex is text."""
    annex = ["(a) the name, address, telephone number and email address of the applicant;",
             "(b) where the applicant is not the client, the name and address of the client;",
             "(c) where known, the name and address of the principal contractor and designer;",
             "(d) a statement that the application is for building control approval."]
    lines = [ln(1, 80, "Building control letter", 30.0, "Arial-Bold", 43),
             ln(1, 210, "www.gov.uk/dluhc", 8.0, "Arial-BoldMT", 326),
             *[ln(p, 300 + 14 * k, "Dear Sir or Madam, I am writing to you about the changes to building control.", x0=43)
               for p in (1, 2, 3) for k in range(8)],
             *[ln(17, 200 + 24 * k, t, 8.0, x0=71) for k, t in enumerate(annex)]]
    box = {"page": 17, "top": 173.0, "bottom": 772.0, "x0": 40.0, "x1": 560.0, "rows": [[a] for a in annex]}
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 17, "tables": [box]}, META)
    assert not [s for s in t["sections"] if s["type"] == "table"]
    assert {s["file_page"] for s in t["sections"] if s.get("small_print")} == {1, 17}


def test_a_frame_round_the_whole_page_does_not_stop_two_columns_being_split():
    """Procurement Act short guides draw a border round each page; pdfplumber reads it as a 'table' holding the
    whole page, and lines inside ruled tables are never cut into columns, so both columns were read across
    ("What is Find a Tender, the What will this mean for"). A table as large as the page is a frame."""
    rows = [("Find a Tender, the central digital", "Find a Tender is the central place for"),
            ("platform, is where all UK contracting", "the contracting authority to register"),
            ("authorities publish information relating", "their organisation initially and then"),
            ("to procurement. It is also the place", "publish their procurement notices.")]
    lines = []
    for k, (a, b) in enumerate(rows):
        words = [{"x0": 44.0 + 6 * i, "x1": 48.0 + 6 * i, "text": w} for i, w in enumerate(a.split())]
        words += [{"x0": 314.0 + 6 * i, "x1": 318.0 + 6 * i, "text": w} for i, w in enumerate(b.split())]
        lines.append(ln(2, 120 + 17 * k, f"{a} {b}", 13.0, x0=44, words=words))
    frame = {"page": 2, "top": -7.8, "bottom": 860.9, "x0": 0.0, "x1": 596.5, "rows": [["...", ""], ["", "..."]]}
    out = split_columns(lines, 13.0, 595.0, [frame], 842.0)
    assert [l["text"] for l in out if l["col"] == 0][0] == "Find a Tender, the central digital"
    assert len(out) == 8


def test_narrow_text_columns_inside_a_page_frame_are_not_a_picture():
    """CDP short guide page 5: once the page frame no longer stops the columns being cut, two narrow columns of
    short lines (five or six words each) and a few drawn panels looked like a flow chart and became one figure.
    On a page inside a frame, four or more body lines one under the other at the same left edge are running text."""
    left = ["Public procurement will always be", "possible. The Procurement Act and", "the Regulations allow for contingency",
            "arrangements to be enacted by the", "contracting authority, if a supplier", "cannot access Find a Tender."]
    right = ["Sign up for the newsletter", "Any queries: contact us at", "For more information", "Knowledge Drop videos",
             "Factsheets", "Technical Guidance", "E-learning manual"]
    lines = [ln(1, 80, "Find a Tender factsheet", 40.0, "HelveticaNowText-Bold", 44)]
    for p in (1, 2, 3, 4):
        lines += [ln(p + 1, 116 + 17 * k, t, 13.0, x0=51) for k, t in enumerate(left)]
        lines += [ln(p + 1, 116 + 23 * k, t, 13.0, x0=321) for k, t in enumerate(right)]
        lines += [ln(p + 1, 40, "What happens if a", 13.3, x0=110), ln(p + 1, 60, "11", 24.3, x0=56),
                  ln(p + 1, 300, "procurement.reform@cabinetoffice.gov.uk", 13.0, x0=371),
              ln(p + 1, 480, "Contracting Authorities", 13.0, x0=200)]
    frame = [{"page": p, "top": -8.0, "bottom": 861.0, "x0": 0.0, "x1": 596.0, "rows": [["...", ""]]} for p in range(1, 6)]
    shapes = [_shape(p, 310, 100 + 25 * i, 560, 120 + 25 * i) for p in range(2, 6) for i in range(12)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 5, "tables": frame, "graphics": shapes,
                    "pages": {str(p): {"width": 596.0, "height": 842.0} for p in range(1, 6)}}, META)
    assert not [s for s in t["sections"] if s["type"] in ("figure", "table")]


def _grid(page, top, bottom, rows, x0=60.0, x1=540.0):
    return {"page": page, "top": float(top), "bottom": float(bottom), "x0": x0, "x1": x1, "rows": rows}


def test_a_ruled_table_with_no_caption_in_running_text_is_a_table_per_page():
    """EH40 Table 1 (13 pages of workplace exposure limits under a chapter title, no "Table N" caption) and the
    Annex tables of circulars were kept as running text (S105). A ruled grid with data (two or more filled columns
    in two or more rows, short cells) is now a table section, one per page, titled from its chapter."""
    rows = [["Substance", "CAS number", "Long-term limit ppm"], ["Acetone", "67-64-1", "500"], ["Ammonia", "7664-41-7", "25"]]
    lines = [ln(2, 98, "Table 1: List of approved limits", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "15 This list is legally binding and reproduces the limits approved by the Executive."),
             ln(2, 300, "Substance CAS number Long-term limit ppm", x0=61), ln(2, 314, "Acetone 67-64-1 500", x0=61),
             ln(2, 328, "Ammonia 7664-41-7 25", x0=61),
             ln(3, 102, "Substance CAS number Long-term limit ppm", x0=61), ln(3, 116, "Benzene 71-43-2 1", x0=61),
             ln(3, 130, "Bromine 7726-95-6 0.1", x0=61)]
    tables = [_grid(2, 296, 340, rows), _grid(3, 98, 142, [rows[0], ["Benzene", "71-43-2", "1"], ["Bromine", "7726-95-6", "0.1"]])]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "tables": tables}, META)
    tabs = [s for s in t["sections"] if s["type"] == "table"]
    assert [(s["id"], s["file_page"]) for s in tabs] == [("table-1-list-of-approved-limits-table-p2", 2),
                                                          ("table-1-list-of-approved-limits-table-p3", 3)]
    assert tabs[0]["grid"] == rows and "Acetone" not in sec(t, "table-1-list-of-approved-limits-text-1")["text"]
    assert {s["title"] for s in tabs} == {"Table 1: List of approved limits"} and len(t["checks"]) == 2


def test_paragraphs_in_a_ruled_frame_stay_text_and_a_caption_just_above_takes_the_grid_rows():
    """Two paragraphs set side by side in ruled boxes are layout, not data: they stay text. L108 prints table
    captions above its tables (figure captions below), so "Table 1" looked up for its rows and found none: the
    grid just under the caption gives them."""
    long1 = "Find a Tender is the central place for the contracting authority to register its organisation and publish notices about each procurement it runs"
    long2 = "Many buyers use a third party to publish their notices and will never need to visit the platform other than to register and to use the data"
    lines = [ln(2, 98, "1 Introduction", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "1 The platform is where notices are published."),
             ln(2, 300, long1[:60], x0=61), ln(2, 314, long2[:60], x0=300),
             ln(2, 400, "Table 1 Simple tests to see if a noise risk assessment is needed", 10.0, "HelveticaNeueLTStd-MdC"),
             ln(2, 421, "Test Probable noise level", 10.0, "HelveticaNeueLTStd-MdC", x0=61),
             ln(2, 435, "Shout to talk 1 m away 90 dB(A)", x0=61), ln(2, 449, "Normal conversation 80 dB(A)", x0=61),
             ln(2, 480, "2 For peak noise, some sources may lead to exposure above the lower action value.")]
    tables = [_grid(2, 296, 360, [[long1, long2], [long2, long1]]),
              _grid(2, 417, 462, [["Test", "Probable noise level"], ["Shout to talk 1 m away", "90 dB(A)"],
                                  ["Normal conversation", "80 dB(A)"]])]
    shade = [{"page": 2, "top": 417.0, "bottom": 431.0, "x0": 60.0, "x1": 540.0, "colour": (0.8, 0.8, 0.8)}]
    t = build_tree({"lines": lines, "rects": shade, "images": [], "page_count": 2, "tables": tables}, META)
    assert [s["id"] for s in t["sections"] if s["type"] == "table"] == ["table-1"]
    assert "Shout to talk" in sec(t, "table-1")["text"] and sec(t, "table-1")["grid"][1][1] == "90 dB(A)"


def test_a_ruled_table_run_on_without_its_header_stays_a_table():
    """Circular 03/2001: the last rows of a regulations table run on to the next page with no header row, the first
    of them with only its last cell filled. A grid with the same columns and edges as a data grid on the page
    before is that table's continuation."""
    head = ["SI 2000/2532 Regulation", "SI 2001/3336 Regulation", "Action"]
    p2 = [head, ["3", "2(2)", "Amends the definition of building work"], ["4", "2(3)", "Adds a requirement to consult"]]
    p3 = [["", "", "the introduction of the new requirement to consult the sewerage undertaker and the revision of ground"],
          ["Schedules 3, 4, 6, 7, 8", "8", "Grounds for rejecting notices and certificates amended to reflect the repeal of section 18"]]
    lines = [ln(2, 98, "Annex A", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "The following table lists the changes made by the Regulations to the earlier ones."),
             ln(2, 300, " ".join(head), x0=61), ln(2, 314, " ".join(p2[1]), x0=61), ln(2, 328, " ".join(p2[2]), x0=61),
             ln(3, 60, p3[0][2][:50], x0=330), ln(3, 120, " ".join(p3[1])[:70], x0=61),
             ln(3, 300, "Enquiries about this circular should be sent to the department by email please.")]
    tables = [_grid(2, 296, 340, p2, 58, 554), _grid(3, 54, 277, p3, 58, 554)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3, "tables": tables}, META)
    assert [s["file_page"] for s in t["sections"] if s["type"] == "table"] == [2, 3]


def test_a_photo_on_a_content_page_one_with_no_caption_is_a_figure():
    """CIS54, CIS78, CIS79 and RO-CIS59: a real photo on page 1 with no caption was left out of the tree (page 1
    pictures were taken for cover art). On a page 1 that is content (40+ words near body size), a photo below the
    title, 4% of the page or more and not a wide thin band, is a figure named by its place. A coloured box with
    lines of text set on it (a callout) is not; nor is the picture on a cover with only a title."""
    body = [ln(1, 520 + 12 * k, t, x0=55) for k, t in enumerate(BLURB * 2)]
    lines = [ln(1, 92, "Dust control on cut-off saws", 25.0, "HelveticaNeue-BoldCond", 54), *body,
             ln(1, 120, "Making it easier to bid", 10.0, x0=60), ln(1, 132, "in partnership", 10.0, x0=60)]
    images = [{"page": 1, "top": 226.0, "bottom": 495.0, "x0": 300.0, "x1": 541.0},  # the photo
              {"page": 1, "top": 115.0, "bottom": 150.0, "x0": 55.0, "x1": 260.0},   # callout box under text
              {"page": 1, "top": 790.0, "bottom": 830.0, "x0": 0.0, "x1": 595.0}]    # band at the foot
    t = build_tree(drawn_doc(lines, images=images), META)
    figs = [s for s in t["sections"] if s["type"] == "figure"]
    assert [s["id"] for s in figs] == ["photo-p1-300-226"] and figs[0]["images_bbox"]["bottom"] == 495.0
    cover = drawn_doc([ln(1, 92, "Dust control on cut-off saws", 25.0, "HelveticaNeue-BoldCond", 54),
                       ln(2, 100, "Some text on page two of the sheet.")], images=images[:1])
    assert not [s for s in build_tree(cover, META)["sections"] if s["type"] == "figure"]


def test_a_signature_beside_signed_by_on_the_left_is_not_a_photo():
    """Circulars and impact assessments print "Signed by authority of the Secretary of State" in the cell to the
    left of the signature, not above it. The rule is shared with the coverage check (S107)."""
    two = [{"x0": 72.0, "x1": 200.0, "text": "Signed"}, {"x0": 205.0, "x1": 240.0, "text": "by"},
           {"x0": 420.0, "x1": 460.0, "text": "Date:"}]
    lines = [ln(1, 100, "Building Act 1984", 20.0, "Arial-Bold", 72),
             ln(1, 650, "Signed by Date:", 11.0, x0=72, words=two), ln(1, 695, "4 October 2022", 11.0, x0=290),
             *[ln(1, 200 + 14 * k, t, 11.0, x0=72) for k, t in enumerate(BLURB)]]
    images = [{"page": 1, "top": 640.0, "bottom": 690.0, "x0": 280.0, "x1": 400.0}]
    t = build_tree(drawn_doc(lines, images=images), META)
    assert not [s for s in t["sections"] if s["type"] == "figure"]


# ---------------------------------------------------------------- ligature glyphs mapped to a bare "f" (semantic check)

def test_ligature_glyph_mapped_to_a_bare_f_is_read_by_its_glyph_name():
    """HSG33, AD G: the font names the glyph "fi" but the PDF's ToUnicode table says "f" ("frst-aid", "foor")."""
    from pdfminer import pdffont

    from system.rag.parse_pdf import ligature_glyphs, ligature_text

    assert ligature_text("ﬁ", "f") == "fi" and ligature_text("ﬂ", "f") == "fl" and ligature_text("ﬃ", "ff") == "ffi"
    assert ligature_text("ﬁ", "fi") == "fi" and ligature_text("ﬁ", "ﬁ") == "ﬁ"  # a right table is left alone
    assert ligature_text("ﬁ", "x") == "x" and ligature_text(None, "f") == "f" and ligature_text("f", "f") == "f"

    class Table:
        def get_unichr(self, cid):
            return {31: "f", 102: "f", 65: "A"}[cid]

    font = object.__new__(pdffont.PDFSimpleFont)
    font.cid2unicode = {31: "ﬁ", 30: "ﬂ", 102: "f", 65: "A"}
    font.unicode_map = Table()
    plain = pdffont.PDFSimpleFont.to_unichr
    assert [font.to_unichr(c) for c in (31, 102, 65)] == ["f", "f", "A"]  # the fault: "first" would read "frst"
    with ligature_glyphs():
        assert [font.to_unichr(c) for c in (31, 102, 65)] == ["fi", "f", "A"]
    assert pdffont.PDFSimpleFont.to_unichr is plain  # the reader is put back


def test_annex_title_set_larger_than_body_text_starts_an_annex():
    # Building regulations circulars (AD J 2022, circular 03/2022): "ANNEX A" in 20pt over "Building Act 1984" in
    # 18pt, on 12pt body text, used to be read as the end of the last numbered paragraph ("ENQUIRIES"), so the
    # notice of approval sat under ENQUIRIES.
    T, B = "TimesNewRomanPSMT", "TimesNewRomanPS-BoldMT"
    lines = [ln(2, 75, "ENQUIRIES", 12.0, B, x0=72),
             ln(2, 98, "9. All enquiries on matters covered by this Circular should be addressed to the Department.", 12.0, T, x0=72),
             ln(2, 113, "Technical Policy Division, Fry Building, 2 Marsham Street, London and more words here", 12.0, T, x0=72),
             ln(3, 99, "ANNEX A", 20.0, T, x0=72), ln(3, 132, "Building Act 1984", 18.0, T, x0=72),
             ln(3, 240, "The Secretary of State hereby gives notice under section 6 of the Building Act 1984.", 12.0, T, x0=72)]
    lines += [ln(2, 140 + 14 * i, "words of the circular run on here for a while longer", 12.0, T, x0=72) for i in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    a = sec(t, "annex-a")
    assert a["type"] == "appendix" and a["title"] == "Building Act 1984"
    assert not [s for s in t["sections"] if "ANNEX" in (s["text"] or "")]
    assert any("All enquiries" in (s["text"] or "") for s in t["sections"])  # the letter before the annex is kept
    assert any(s["parent_id"] == "annex-a" and "Secretary of State" in s["text"] for s in t["sections"])


def test_part_or_annex_entry_with_dot_leaders_is_a_contents_line_not_a_chapter():
    # Awaab's Law phase 2 impact assessment: "Annex A Policy Landscape ........ 2" on the contents page became an
    # annex holding the whole document.
    T = "ArialMT"
    lines = [ln(2, 100, "Annex A Policy Landscape ................................ 2", 14.0, T, x0=72),
             ln(3, 99, "1. Introduction and problem under consideration of the document here", 11.0, T, x0=72)]
    lines += [ln(3, 120 + 14 * i, "words of the assessment run on here for a while longer", 11.0, T, x0=72) for i in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    assert not [s for s in t["sections"] if s["id"].startswith("annex-")]


def test_annex_titles_in_small_capitals_or_without_a_space_or_a_point_smaller():
    # Circular 02/2011: "Annex c", "Annex d" (small capitals read as lower case) were missed while "Annex B" was
    # found, so Annex C's notice sat under Annex B. Circular 08/2004 (a scan): "AnnexA" at 16pt, "Annex B" at 17pt.
    T = "GoudyOldStyleBT-Roman"
    lines = []
    for p, title, size in ((3, "Annex B", 17.0), (4, "Annex c", 17.0), (5, "AnnexA", 16.0)):
        lines += [ln(p, 79, title, size, T, x0=79)]
        lines += [ln(p, 120 + 14 * i, "The Secretary of State gives notice of approval of these documents.", 11.0, T, x0=79)
                  for i in range(5)]
    lines += [ln(2, 100 + 14 * i, "words of the circular letter run on here for a while longer", 11.0, T, x0=79) for i in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 5}, META)
    assert {s["id"] for s in t["sections"] if s["type"] == "appendix"} == {"annex-a", "annex-b", "annex-c"}


def test_signature_over_a_signed_by_line_is_not_a_figure():
    from system.rag.parse_pdf import signature_or_logo
    im = {"page": 4, "top": 473.3, "bottom": 535.2, "x0": 126.3, "x1": 291.2}
    lines = [{"text": "Signed by authority of the First Secretary of State,", "top": 547, "bottom": 558, "x0": 128, "x1": 400},
             {"text": "Anne Hemming", "top": 561, "bottom": 572, "x0": 128, "x1": 200}]
    assert signature_or_logo(im, 4, lines)


def _runon_doc():
    """HSG248-like pages: Table 3.2 ends at the foot of page 2 and runs on at the top of page 3 under a
    "Table 3.2 continued" label, on a page with other margins (the grid is shifted right); Table 3.3 follows
    with its own grid. Page 4 ends a third table whose last cell runs on to page 5 as one row with one cell."""
    B, L = "HelveticaNeueLTStd-MdCn", "HelveticaNeueLTStd-LtCn"
    lines = [ln(2, 98, "3 Competence", 28.0, "HelveticaNeue-Medium"),
             ln(2, 150, "3.1 Analysts need training in the topics listed in the tables of this chapter here.", 10.0, L, x0=57),
             ln(2, 400, "Table 3.2 Core competences", 10.0, B, x0=57),
             ln(2, 425, "Module Core competences", 8.0, B, x0=61),
             *[ln(2, 440 + 20 * k, f"Module {k} Know the risk number {k}", 8.0, L, x0=61) for k in range(16)],
             ln(3, 101, "Table 3.2 continued", 10.0, B, x0=176),
             ln(3, 125, "Module Core competences", 8.0, B, x0=180),
             ln(3, 140, "Air sampling Count fibres accurately", 8.0, L, x0=180),
             ln(3, 160, "Clearance Carry out clearance for reoccupation", 8.0, L, x0=180),
             ln(3, 400, "Table 3.3 Examples of modules", 10.0, B, x0=176),
             ln(3, 425, "Module code Module title", 8.0, B, x0=180),
             ln(3, 440, "P401 Identification of asbestos", 8.0, L, x0=180),
             ln(3, 460, "P402 Surveying and sampling", 8.0, L, x0=180),
             ln(3, 600, "3.2 Proficiency modules are offered by several course providers in this country.", 10.0, L, x0=176),
             *[ln(3, 612 + 12 * k, "and the analyst should keep a record of the training done and its results.", 10.0, L, x0=176)
               for k in range(14)],
             *[ln(2, 162 + 12 * k, "and the employer should plan the training of each analyst against these lists.", 10.0, L, x0=57)
               for k in range(14)]]
    tables = [_grid(2, 420, 790, [["Module", "Core competences"]] + [[f"Module {k}", f"Know the risk number {k}"] for k in range(16)], 57, 419),
              _grid(3, 121, 180, [["Module", "Core competences"], ["Air sampling", "Count fibres accurately"],
                                  ["Clearance", "Carry out clearance for reoccupation"]], 176, 538),
              _grid(3, 420, 480, [["Module code", "Module title"], ["P401", "Identification of asbestos"],
                                  ["P402", "Surveying and sampling"]], 176, 538)]
    return {"lines": lines, "rects": [], "images": [], "page_count": 3, "tables": tables}


def test_a_table_run_on_to_the_next_page_is_one_table_section():
    """S118: the rows of a table that runs on at the top of the next page were a table of their own, named after
    the heading above (HSG248 Table 4.1), or were swallowed by the next table's caption (Table 3.2 into Table 3.3).
    Now a ruled grid at the top of a page, with the same columns and width as the grid at the foot of the page
    before and nothing above it but a "continued" label, is more rows of that table: one section, spans on both
    pages, its rows from both grids (the repeated header row once)."""
    t = build_tree(_runon_doc(), META)
    tabs = [s for s in t["sections"] if s["type"] == "table"]
    assert [s["id"] for s in tabs] == ["table-3-2", "table-3-3"]
    t32, t33 = tabs
    assert set(t32["spans"]) == {"2", "3"} and set(t33["spans"]) == {"3"}
    assert ["Air sampling", "Count fibres accurately"] in t32["grid"] and t32["grid"].count(["Module", "Core competences"]) == 1
    assert "Air sampling" not in t33["text"] and "P401" in t33["text"] and "Air sampling" in t32["text"]
    assert "Table 3.2 continued" in t32["text"]
    assert not any("continued" in (s["text"] or "") for s in t["sections"] if s["type"] != "table")
    assert len(t["checks"]) == 2


def test_the_last_cell_of_a_table_run_on_to_the_next_page_stays_in_the_table():
    """Awaab's Law tenant guides: the last cell of a table ends on the next page, in a ruled row with only that
    cell filled. It was running text, glued to the paragraph before the table. Now it is in the table."""
    T = "ArialMT"
    lines = [ln(1, 80, "Investigations", 20.0, T, x0=72),
             ln(1, 120, "Your landlord must investigate the hazard within the time set out below in the table.", 12.0, T, x0=72),
             ln(1, 300, "Type Description", 12.0, T, x0=75),
             ln(1, 320, "Visual Your landlord looks at the problem", 12.0, T, x0=75),
             ln(1, 740, "Further Your landlord must still act to keep you safe,", 12.0, T, x0=75),
             ln(2, 75, "such as treating visible mould.", 12.0, T, x0=170),
             ln(2, 200, "After the investigation your landlord must write to you within three working days.", 12.0, T, x0=72)]
    tables = [_grid(1, 296, 760, [["Type", "Description"], ["Visual", "Your landlord looks at the problem"],
                                  ["Further", "Your landlord must still act to keep you safe,"]], 72, 540),
              _grid(2, 72, 106, [["", "such as treating visible mould."]], 72, 540)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2, "tables": tables}, META)
    tab = next(s for s in t["sections"] if s["type"] == "table")
    assert set(tab["spans"]) == {"1", "2"} and "treating visible mould" in tab["text"]
    assert not any("treating visible mould" in (s["text"] or "") for s in t["sections"] if s["type"] != "table")


def test_hse_headings_over_a_column_and_medium_sub_headings_are_headings():
    """S128 (HSG248): "Records and reporting of sampling" (13pt bold) starts at the left edge of a text column
    beside the figures, not at the page's margin, and "Video evidence" is set in 11pt medium condensed oblique:
    both were read as body text, so the paragraphs under them sat under the heading before."""
    L, Bd, Md = "HelveticaNeueLTStd-LtCn", "HelveticaNeueLTStd-BdCn", "HelveticaNeueLTStd-MdCnO"
    lines = [ln(2, 98, "4 Bulk sampling", 28.0, "HelveticaNeue-Medium", x0=57)]
    lines += [ln(2, 140 + 12 * k, "4.1 Samples should be taken by trained people using the right tools for the job." if k == 0 else
                 "and sealed in a labelled container before they leave the room where they were taken.", 10.0, L, x0=57)
              for k in range(10)]
    lines += [ln(2, 300, "Records and reporting of sampling", 13.0, Bd, x0=176),
              ln(2, 326, "4.2 The sampling records and report should include the following as a minimum:", 10.0, L, x0=320),
              *[ln(2, 338 + 12 * k, "the name and address of the sampling organisation and the site sampled here", 10.0, L, x0=320)
                for k in range(6)],
              ln(2, 430, "Video evidence", 11.0, Md, x0=57),
              ln(2, 450, "4.3 Videos may also be taken of the areas that are the reason for any failure of the work.", 10.0, L, x0=57),
              *[ln(2, 462 + 12 * k, "and kept with the report so that the client can see what the analyst saw on site.", 10.0, L, x0=57)
                for k in range(6)],
              ln(2, 560, "These new requirements come into", 12.0, "HelveticaNeueLTStd-Md", x0=57),
              ln(2, 577, "Force on 1 October 2023 for all", 12.0, "HelveticaNeueLTStd-Md", x0=57),
              ln(2, 594, "Responsible Persons in England", 12.0, "HelveticaNeueLTStd-Md", x0=57)]
    lines += [ln(3, 140 + 12 * k, "4.4 Labels must show the sample number, the date and the name of the person who took it" if k == 0 else
                 "so that the laboratory can match each sample to the record made on site by the analyst.", 10.0, L, x0=176)
              for k in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    heads = {s["title"] for s in t["sections"] if s["type"] == "heading"}
    assert {"Records and reporting of sampling", "Video evidence"} <= heads
    assert sec(t, "para-4-2")["heading_path"][-2] == "Records and reporting of sampling"
    assert sec(t, "para-4-3")["heading_path"][-2] == "Video evidence"
    assert not any(h.startswith(("These new", "Force on", "Responsible")) for h in heads)  # three lines set large: a lead-in, not headings


def test_body_text_after_a_ruled_table_is_not_kept_in_the_table():
    """S128 (HSG248): under a body-size table caption the rows ran on until a numbered paragraph "12. ...";
    paragraphs numbered "3.6 ..." and body text printed under the ruled table were kept in the table's text (as if
    they were notes). Now they end the table; a note under it ("Note: ...") stays."""
    L, M = "HelveticaNeueLTStd-LtCn", "HelveticaNeueLTStd-MdCn"
    lines = [ln(2, 98, "3 Competence", 28.0, "HelveticaNeue-Medium", x0=57)]
    lines += [ln(2, 140 + 12 * k, "3.5 Relevant topics are listed in Table 3.1 and might be run in house or outsourced." if k == 0 else
                 "and the employer should keep a record of the training each analyst has completed.", 10.0, L, x0=57)
              for k in range(8)]
    lines += [ln(2, 300, "Table 3.1 Topics to be covered in analyst development programmes", 10.0, M, x0=57),
              ln(2, 325, "All staff Field staff", 10.0, M, x0=61),
              ln(2, 339, "Awareness training for asbestos Working in confined spaces", 10.0, L, x0=61),
              ln(2, 353, "Safe handling of chemicals Working at heights", 10.0, L, x0=61),
              ln(2, 380, "Note: Field staff also need the all staff topics.", 10.0, L, x0=57),
              ln(2, 400, "3.6 Analysts who will have to enter enclosures must complete practical training on RPE.", 10.0, L, x0=57),
              ln(2, 412, "The training should include the full decontamination process in a unit on site.", 10.0, L, x0=57)]
    tables = [_grid(2, 320, 365, [["All staff", "Field staff"], ["Awareness training for asbestos", "Working in confined spaces"],
                                  ["Safe handling of chemicals", "Working at heights"]], 57, 419)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2, "tables": tables}, META)
    tab = sec(t, "table-3-1")
    assert "Working at heights" in tab["text"] and "Note: Field staff" in tab["text"]
    assert "3.6" not in tab["text"] and "decontamination" not in tab["text"]
    assert "decontamination" in sec(t, "para-3-6")["text"]


def test_a_table_longer_than_four_pages_is_cut_into_parts_that_keep_its_title_and_headings():
    """S132 (Florin, 23 Nov 2026): a table over pages is joined into parts of at most four pages. A later part says
    which table it continues ("Table 3.2 ... (continued)", same number), starts its text with the first part's
    header row, and takes the first part's column names when its model check had none to read."""
    B, L = "HelveticaNeueLTStd-MdCn", "HelveticaNeueLTStd-LtCn"
    lines = [ln(2, 98, "3 Competence", 28.0, "HelveticaNeue-Medium", x0=57),
             *[ln(2, 140 + 12 * k, "3.1 Analysts need training in the topics listed in the tables of this chapter here." if k == 0 else
                  "and the employer should plan the training of each analyst against these lists.", 10.0, L, x0=57)
               for k in range(14)],
             ln(2, 400, "Table 3.2 Core competences", 10.0, B, x0=57), ln(2, 425, "Module Core competences", 8.0, B, x0=61)]
    tables = [_grid(2, 420, 790, [["Module", "Core competences"], ["Module 1", "Know the risk"]], 57, 419)]
    for p in range(3, 8):
        lines += [ln(p, 105, "Module Core competences", 8.0, B, x0=61), ln(p, 120, f"Module {p} Know the risk on page {p}", 8.0, L, x0=61)]
        tables.append(_grid(p, 100, 790, [["Module", "Core competences"], [f"Module {p}", f"Know the risk on page {p}"]], 57, 419))
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 7, "tables": tables}, META)
    tabs = [s for s in t["sections"] if s["type"] == "table"]
    assert [sorted(s["spans"], key=int) for s in tabs] == [["2", "3", "4", "5"], ["6", "7"]]
    part = tabs[1]
    assert part["continues"] == "table-3-2" and part["number"] == "3.2" and part["title"] == "Core competences (continued)"
    assert part["text"].startswith("Module Core competences")
    key = next(c["key"] for c in t["checks"] if c["section_id"] == part["id"])
    fix = {"key": key, "kind": "table", "reason": "test",
           "value": {"columns": ["Topic", "Column 2"], "rows": [["Module 6", "Know the risk on page 6"]], "sentences": ["x."]}}
    key1 = next(c["key"] for c in t["checks"] if c["section_id"] == "table-3-2")
    fix1 = {"key": key1, "kind": "table", "reason": "test",
            "value": {"columns": ["Module", "Core competences"], "rows": [["Module 1", "Know the risk"]], "sentences": ["x."]}}
    t2 = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 7, "tables": tables}, META, fixes=[fix, fix1])
    assert sec(t2, part["id"])["columns"] == ["Module", "Core competences"]
