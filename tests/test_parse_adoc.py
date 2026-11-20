"""Tests for the Approved Document parser (system/rag/parse_adoc.py). Hand-made lines (mock text) for each
layout rule; real-file counts for AD B volume 1 where the raw file is on this machine."""

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

from system.rag.fixes import load_fixes
from system.rag.parse_adoc import build_tree

ROOT = Path(__file__).parent.parent
META = {"source_id": "demo-ad", "version_id": "main@1", "valid_from": "2026-01-01", "valid_to": None, "title": "Demo AD"}
WHITE, GREEN = [1.0, 1.0, 1.0], [0.0, 0.52, 0.25]


def ln(page, top, words, size=12.0, font="Agenda-Light", x0=56.7):
    """A line as read_pdf gives it. words: list of text, or (text, {"b": True, "c": [...]}) pairs."""
    out, x = [], x0
    for w in words:
        text, extra = (w, {}) if isinstance(w, str) else w
        out.append({"x0": round(x, 1), "x1": round(x + 5 * len(text), 1), "text": text, **extra})
        x += 5 * (len(text) + 1)
    return {"page": page, "top": float(top), "x0": float(x0), "size": size, "font": font,
            "text": " ".join(o["text"] for o in out), "words": out}


B = {"b": True}


def bold(*ws):
    return [(w, B) for w in ws]


def page_furniture(page, label):
    return [ln(page, 16, list("ONLINE"), 20.0, "Agenda-Bold", 198.6), ln(page, 804.7, [label], 14.0, "Agenda-Bold", 540),
            ln(page, 807.7, ["Approved", "Document", "Demo"], 8.0)]


def doc():
    L = []
    L += page_furniture(1, "i")  # cover: skipped until the first chapter
    L += [ln(1, 300, ["Cover", "words"], 28.0, "Agenda-Bold")]
    L += page_furniture(2, "1")
    L += [ln(2, 84, bold("Section", "2:", "Means", "of", "escape"), 26.0, "Agenda-Bold"),
          ln(2, 114, bold("dwellinghouses"), 26.0, "Agenda-Bold"),
          ln(2, 166, bold("Escape", "from", "upper", "storeys"), 20.0, "Agenda-Bold"),
          ln(2, 187, bold("above", "ground", "level"), 20.0, "Agenda-Bold"),
          ln(2, 220, [("2.5", B), "Every", ("storey", {"c": GREEN}), "should", "have", "a", "fre", "alarm."], font="Agenda-Semibold"),
          ln(2, 234, ["a.", "First", "item", "of", "the", "list."], x0=79.4),
          ln(2, 254, [("2.10Doors", B), "should", "open", "with", "fre", "resisting", "hinges."], font="Agenda-Semibold"),
          ln(2, 300, ["See", "para", "2.5"], 8.0, "Agenda-Medium", 80),
          ln(2, 320, ["Final", "exit"], 8.0, "Agenda-Medium", 200),
          ln(2, 400, [("Diagram", {"c": WHITE}), ("2.2", {"c": WHITE}), ("Final", {"c": WHITE}), ("exits", {"c": WHITE})]),
          ln(2, 450, bold("Table", "2.1", "Limits", "on"), 12.0, "Agenda-Bold"),
          ln(2, 464, bold("travel", "distance"), 12.0, "Agenda-Bold"),
          ln(2, 480, ["Escape", "in", "one", "direction"], 10.0),
          ln(2, 494, ["7.5m"], 10.0),
          ln(2, 520, ["Fire", "fire", "fire", "Fire", "the", "end."])]
    L += page_furniture(3, "2")
    L += [ln(3, 73.7, bold("Effective", "until", "1", "September", "2029", "–", "see", "2029", "amendment"), 12.0, "Agenda-Bold"),
          ln(3, 94, bold("Appendix", "B:", "Performance"), 26.0, "Agenda-Bold"),
          ln(3, 200, [("B1", B), "Old", "text."], font="Agenda-Semibold")]
    L += page_furniture(4, "3")
    L += [ln(4, 73.7, bold("2029", "amendment", "–", "effective", "from", "2", "September", "2029"), 12.0, "Agenda-Bold"),
          ln(4, 94, bold("Appendix", "B:", "Performance"), 26.0, "Agenda-Bold"),
          ln(4, 200, [("B1", B), "New", "text."], font="Agenda-Semibold")]
    L += page_furniture(5, "4")
    L += [ln(5, 84, bold("Appendix", "A:", "Key", "terms"), 26.0, "Agenda-Bold")]
    for k, (left, right) in enumerate([(bold("Access", "room") + ["A", "room", "on", "the", "route."],
                                        bold("Basement") + ["A", "storey", "below", "ground."]),
                                       (["passed", "through."], ["More", "words."]),
                                       (bold("Alternative", "exit") + ["One", "of", "two", "exits."], ["Even", "more."])]):
        l = ln(5, 160 + 20 * k, left)
        r = ln(5, 160 + 20 * k, right, x0=314.6)
        l["words"] += r["words"]
        l["text"] += "   " + r["text"]
        L.append(l)
    L += [ln(5, 260, ["Final", "words", "left."]), ln(5, 280, ["Right", "column", "only."], x0=314.6),
          ln(5, 300, ["Left", "again."]), ln(5, 320, ["Right", "again."], x0=314.6),
          ln(5, 340, ["Right", "last."], x0=314.6)]
    L += page_furniture(6, "5")
    L += [ln(6, 84, bold("Index"), 26.0, "Agenda-Bold"), ln(6, 120, ["Means", "of", "escape", "2.5"])]
    return {"lines": L, "tables": [], "images": [], "rects": [], "page_count": 6, "page_width": 595.0}


@pytest.fixture(scope="module")
def tree():
    return build_tree(doc(), META)


def sec(tree, sid):
    return next(s for s in tree["sections"] if s["id"] == sid)


def test_furniture_cover_and_index_are_dropped(tree):
    text = " ".join(s["text"] + " " + (s["title"] or "") for s in tree["sections"])
    assert "ONLINE" not in text and "Cover" not in text and "Approved Document Demo" not in text
    assert "Means of escape 2.5" not in text  # index
    assert sec(tree, "para-2.5")["printed_page"] == "1"


def test_chapter_and_heading_titles_join_their_wrapped_lines(tree):
    assert sec(tree, "section-2")["title"] == "Section 2: Means of escape dwellinghouses"
    h = [s for s in tree["sections"] if s["type"] == "heading"]
    assert [s["title"] for s in h] == ["Escape from upper storeys above ground level"]


def test_numbered_paragraphs_lists_and_marked_terms(tree):
    p = sec(tree, "para-2.5")
    assert p["text"].startswith("Every storey should have a fire alarm.\na. First item")
    assert p["marked_terms"] == ["storey"]
    assert p["heading_path"][-2:] == ["Escape from upper storeys above ground level", "Paragraph 2.5"]


def test_a_long_number_touching_its_first_word_is_split(tree):
    assert sec(tree, "para-2.10")["text"].startswith("Doors should open")


def test_dropped_letters_of_fi_are_put_back_and_counted(tree):
    assert "fire alarm" in sec(tree, "para-2.5")["text"]
    assert tree["repairs"]["fre -> fire"] >= 2


def test_diagram_caption_labels_and_area(tree):
    d = sec(tree, "diagram-2.2")
    assert d["type"] == "figure" and d["title"] == "Final exits" and d["labels"] == ["See para 2.5", "Final exit"]
    assert d["area"]["top"] < 300 and d["area"]["bottom"] > 400
    assert "Final exit" not in sec(tree, "para-2.10")["text"]


def test_table_caption_wraps_and_small_text_goes_to_the_table(tree):
    t = sec(tree, "table-2.1")
    assert t["title"] == "Limits on travel distance"
    assert t["text"] == "Escape in one direction\n7.5m"
    assert any(c["section_id"] == "table-2.1" for c in tree["checks"])


def test_two_dated_copies_of_an_appendix(tree):
    old, new = sec(tree, "para-b1-until-2029-09-01"), sec(tree, "para-b1-from-2029-09-02")
    assert old["text"] == "Old text." and old["valid_to"] == "2029-09-01" and "valid_from" not in old
    assert new["text"] == "New text." and new["valid_from"] == "2029-09-02"
    assert sec(tree, "appendix-b-until-2029-09-01")["type"] == "appendix"


def test_key_terms_in_two_columns(tree):
    d = {x["term"]: x["section_id"] for x in tree["definitions"]}
    assert set(d) == {"Access room", "Basement", "Alternative exit"}
    assert sec(tree, d["Access room"])["text"] == "A room on the route. passed through."
    assert sec(tree, d["Basement"])["text"].startswith("A storey below ground. More words. Even more. Right column")
    assert sec(tree, d["Alternative exit"])["text"] == "One of two exits. Final words left. Left again."


def test_tree_is_json(tree):
    json.dumps(tree)


# ---------------------------------------------------------------- real file

def _vol1():
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / "adb").glob("*.json")]
    cur = [r for r in recs if r["valid_to"] is None and r["part"] == "approved-document-b-fire-safety-volume-1-dwellings"]
    if not cur or not (ROOT / cur[0]["raw_path"]).exists():
        pytest.skip("AD B volume 1 raw file not on this machine")
    return cur[0]


@pytest.fixture(scope="module")
def adb1():
    pytest.importorskip("pdfplumber")
    from system.rag.parse_pdf import read_pdf
    r = _vol1()
    return build_tree(read_pdf(ROOT / r["raw_path"]), {**r, "title": r["part_title"]}, fixes=load_fixes("adb"))


def test_real_adb1_paragraph_numbers_are_complete(adb1):
    by = defaultdict(list)
    for s in adb1["sections"]:
        if s["type"] == "paragraph":
            m = re.match(r"^(\d+)\.(\d+)$", s["number"]) or re.match(r"^([A-G])(\d+)$", s["number"])
            by[(m.group(1), s.get("valid_from") or s.get("valid_to") or "")].append(int(m.group(2)))
    for k, nums in by.items():
        assert sorted(nums) == list(range(1, max(nums) + 1)), k
    assert len(by[("3", "")]) == 112 and sum(len(v) for v in by.values()) == 490
    assert len(by[("B", "2029-09-01")]) == 26 and len(by[("B", "2029-09-02")]) == 27


def test_real_adb1_chapters_diagrams_tables_terms(adb1):
    S = adb1["sections"]
    sections = sorted(int(s["number"]) for s in S if s["type"] == "chapter" and s["id"].startswith("section-"))
    assert sections == list(range(0, 18))
    assert {s["id"] for s in S if s["type"] == "appendix"} >= {
        "appendix-a", "appendix-b-until-2029-09-01", "appendix-b-from-2029-09-02", "appendix-c-until-2029-09-01",
        "appendix-c-from-2029-09-02", "appendix-d", "appendix-e", "appendix-f", "appendix-g"}
    assert len([s for s in S if s["type"] == "figure"]) == 57
    tables = [s["number"] for s in S if s["type"] == "table" and s["number"]]
    assert sorted(set(tables)) == sorted(["0.1", "3.1", "4.1", "4.2", "9.1", "10.1", "11.1", "12.1", "12.2", "12.3",
                                          "13.1", "B1", "B2", "B3", "C1", "D1"])
    assert len([s for s in S if s["type"] == "requirement"]) == 8
    assert len(adb1["definitions"]) == 83
    assert not [i for i in adb1["issues"] if "duplicate" in i]


def test_real_adb1_text_is_clean(adb1):
    for s in adb1["sections"]:
        for bad in ("O N L I N E", "Approved Document B Volume 1, 2019 edition", " fre ", "T he "):
            assert bad not in s["text"], (s["id"], bad)
    S = {s["id"]: s for s in adb1["sections"]}
    assert S["para-2.6"]["text"].startswith("See Diagram 2.1d.")
    assert "protected stairway" in S["para-2.6"]["marked_terms"]


def test_real_adb1_all_checks_settled_by_saved_fixes(adb1):
    assert adb1["checks"] == []
    S = adb1["sections"]
    assert all(s.get("description_source") == "model" for s in S if s["type"] == "figure")
    assert all(s.get("grid_source") == "model" and s.get("row_sentences") for s in S if s["type"] == "table")
    old = next(s for s in S if s["id"] == "table-b1-until-2029-09-01")
    new = next(s for s in S if s["id"] == "table-b1-from-2029-09-02")
    assert old["columns"] == new["columns"]  # one family, one layout
