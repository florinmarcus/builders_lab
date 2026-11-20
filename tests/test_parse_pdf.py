"""Tests for the guidance PDF parser (ADR 0010). The tree builder works on simple "lines", so most tests
use hand-made lines (mock text) and need no PDF. Real-file tests skip where raw files are missing."""

import json
from pathlib import Path

import pytest

from system.rag.parse_pdf import build_tree, read_pdf

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
    return build_tree(read_pdf(ROOT / r["raw_path"]), {**r, "title": "HSG264 Asbestos: The survey guide"})


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


def test_real_text_is_clean(hsg264):
    for s in hsg264["sections"]:
        for bad in ("Health and Safety\nExecutive", "Page 1", "■", "Asbestos: The survey guide Page"):
            assert bad not in s["text"], (s["id"], bad)
    p14 = next(s for s in hsg264["sections"] if s["id"] == "para-14")
    assert p14["text"].startswith("To help comply with the legal requirements")
    assert p14["heading_path"][-2:] == ["Appointed person", "Paragraph 14"]
    assert p14["printed_page"] == "10"
