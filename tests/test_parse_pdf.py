"""Tests for the guidance PDF parser (ADR 0010). The tree builder works on simple "lines", so most tests
use hand-made lines (mock text) and need no PDF. Real-file tests skip where raw files are missing."""

import json
from pathlib import Path

import pytest

from system.rag.fixes import load_fixes
from system.rag.parse_pdf import build_tree, photo_box, read_pdf

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
    return build_tree(read_pdf(ROOT / r["raw_path"]), {**r, "title": "HSG264 Asbestos: The survey guide"},
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
    a4 = S["appendix-4-table-1"]["grid"]
    assert any(r and r[0].startswith("Product type") for r in a4)
    a2 = S["appendix-2-table-1"]
    assert a2["columns"][0] == "Asbestos product"
    assert not [r for r in a2["grid"] if r and r[0] == "Asbestos product"]  # header not repeated across 5 pages


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
    return build_tree(read_pdf(ROOT / r["raw_path"]), {**r, "title": "HSG227 A comprehensive guide to managing asbestos"},
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


# ---------------------------------------------------------------- real files: S2c sources

def _real(source_id, title):
    pytest.importorskip("pdfplumber")
    r = _record(source_id)
    return build_tree(read_pdf(ROOT / r["raw_path"]), {**r, "title": title}, fixes=load_fixes(source_id))


@pytest.fixture(scope="module")
def l143():
    return _real("hse-l143", "L143 Managing and working with asbestos")


def test_real_l143_structure(l143):
    secs = l143["sections"]
    main = [int(s["number"]) for s in secs if s["type"] == "paragraph" and s["id"].startswith("para-")]
    assert main == list(range(1, 538))
    regs = [s for s in secs if s["type"] == "chapter" and s["id"].startswith("regulation-")]
    assert len(regs) == 35
    assert sorted(int(s["number"]) for s in secs if s["type"] == "table") == list(range(1, 8))
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
    assert [s["id"] for s in t["sections"] if s["type"] == "chapter"] == [f"part-{n}" for n in range(1, 8)]
    assert t["checks"] == [] and not t["issues"]
