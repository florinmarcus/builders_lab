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
          ln(2, 520, ["Fire", "fire", "fire", "Fire", "the", "end."]),
          ln(2, 540, ["defnition", "defnition", "defnition", "definition", "often", "oftn", "often"])]
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


def test_broken_word_more_common_than_the_good_one_is_repaired_after_a_rare_f_pair(tree):
    # "fn" almost never occurs in English: "defnition" is fixed although it outnumbers "definition" here.
    assert tree["repairs"]["defnition -> definition"] == 3
    # "ft" is a normal pair: "often" is never touched, and "oftn" (no fi/fl candidate in the text) stays.
    assert not [k for k in tree["repairs"] if k.startswith(("often", "oftn"))]


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


# ---------------------------------------------------------------- 2019 layout: more rules (AD F, L, P)

def test_a_ligature_printed_twice_is_repaired_and_counted():
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "1:", "Heat"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, [("1.1", B), "The", "specifification", "of", "the", "flfloor", "and",
                                              "effiffifficiency."], font="Agenda-Semibold")]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    assert sec(t, "para-1.1")["text"] == "The specification of the floor and efficiency."
    assert t["repairs"]["specifification -> specification"] == 1 and t["repairs"]["effiffifficiency. -> efficiency."] == 1


def test_a_line_printed_twice_over_is_repaired_and_counted():
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "2:", "Scope"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, [("2.5", B), "Notifiable", "work", "is", "set", "out", "below."], font="Agenda-Semibold"),
                                  ln(1, 154, ["1122..——((66AA))", "AA", "ppeerrssoonn", "iinntteennddiinngg", "ttoo", "ccaarrrryy", "oouutt"]),
                                  ln(1, 168, ["Ladders", "need", "a", "well", "lit", "room."])]  # "ll" alone: not doubled
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    assert sec(t, "para-2.5")["text"] == ("Notifiable work is set out below. 12.—(6A) A person intending to carry out "
                                          "Ladders need a well lit room.")
    assert t["repairs"]["ppeerrssoonn -> person"] == 1 and t["repairs"]["1122..——((66AA)) -> 12.—(6A)"] == 1


def test_ruled_table_without_caption_in_body_type_is_a_table():
    L = page_furniture(1, "1") + [ln(1, 84, bold("Which", "edition", "applies?"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, ["The", "table", "below", "shows", "which", "edition", "applies."]),
                                  ln(1, 212, ["Work", "started", "Edition"], x0=98),
                                  ln(1, 266, ["Before", "1", "October", "2015", "2010", "edition"], x0=98),
                                  ln(1, 300, ["After", "1", "October", "2015", "2015", "edition"], x0=98),
                                  ln(1, 366, ["Note:", "a", "later", "edition", "may", "be", "used."])]
    grid = {"page": 1, "top": 206.8, "bottom": 350.8, "x0": 90.0, "x1": 500.0,
            "rows": [["Work started", "Edition"], ["Before 1 October 2015", "2010 edition"], ["After 1 October 2015", "2015 edition"]]}
    quote = {"page": 1, "top": 360.0, "bottom": 380.0, "x0": 50.0, "x1": 500.0,  # one filled row: not a grid
             "rows": [["Note:", "a later edition may be used."], ["", ""], ["", ""]]}
    t = build_tree({"lines": L, "tables": [grid, quote], "page_width": 595.0}, META)
    tab = [s for s in t["sections"] if s["type"] == "table"]
    assert len(tab) == 1 and tab[0]["id"] == "which-edition-applies-table-1"
    assert tab[0]["text"].split("\n") == ["Work started Edition", "Before 1 October 2015 2010 edition", "After 1 October 2015 2015 edition"]
    assert tab[0]["grid"] == grid["rows"] and t["checks"][0]["section_id"] == tab[0]["id"]
    texts = [s["text"] for s in t["sections"] if s["type"] == "text"]
    assert texts == ["The table below shows which edition applies. Note: a later edition may be used."]


def test_text_below_the_caption_of_a_page_picture_is_kept():
    # AD P page 14: a drawing made of many tiny words, its caption, then a heading and paragraph 2.5 below it.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "2:", "Scope"), 26.0, "Agenda-Bold")]
    L += [ln(1, 120 + 8 * k, ["label", str(k)], 8.0, "Agenda-Medium") for k in range(12)]
    L += [ln(1, 400, [("Diagram", {"c": WHITE}), ("1", {"c": WHITE}), ("Scope", {"c": WHITE})]),
          ln(1, 445, bold("Notifiable", "work"), 15.0, "Agenda-Bold"),
          ln(1, 464, [("2.5", B), "Notifiable", "work", "is", "set", "out."], font="Agenda-Semibold")]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    assert sec(t, "para-2.5")["text"] == "Notifiable work is set out."
    assert len(sec(t, "diagram-1")["labels"]) == 12


def test_diagram_labels_a_little_larger_than_small_print_stay_in_the_drawing():
    # AD K Diagram 10.2: the labels are 10.9pt, and the whole page above the caption is the drawing.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "10:", "Doors"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, [("10.1", B), "Doors", "text."], font="Agenda-Semibold")]
    L += page_furniture(2, "2") + [ln(2, 105, ["See", "para", "10.2"]),
                                   ln(2, 194, ["Guarding", "with"], 10.9), ln(2, 206, ["cane", "detection"], 10.9),
                                   ln(2, 316, bold("Plan"), 10.9, "Agenda-Bold"),
                                   ln(2, 651, [("Diagram", {"c": WHITE}), ("10.2", {"c": WHITE}), ("Avoiding", {"c": WHITE}),
                                               ("doors", {"c": WHITE})])]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    assert sec(t, "diagram-10.2")["labels"] == ["See para 10.2", "Guarding with", "cane detection", "Plan"]
    assert sec(t, "para-10.1")["text"] == "Doors text."


def test_an_11pt_list_inside_a_table_does_not_make_the_page_two_columns():
    # AD L 2026 vol 2 Table 5.6: an 11pt list of conversion factors starts at x=329 inside the table; the page title
    # and its table caption must not be cut at a "gutter" there.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "5:", "Services"), 26.0, "Agenda-Bold"),
                                  ln(1, 120, [("5.1", B), "Some", "text."], font="Agenda-Semibold"),
                                  ln(1, 150, bold("Table", "5.6", "Minimum", "thermal", "efficiencies", "for", "domestic", "hot",
                                                  "water", "systems"), 12.0, "Agenda-Bold")]
    L += [ln(1, 165, ["Indirect-fired", "Natural", "gas", "91%"], 10.0)]
    L += [ln(1, 180 + 13 * k, [f"Fuel{k}", f"0.9{k}"], 11.0, x0=329.0) for k in range(6)]
    L += [ln(1, 270, ["Electrically-heated", "100%", "assumed"], 10.0)]
    L += [ln(1, 300, [("5.2", B), "More", "text."], font="Agenda-Semibold")]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    tab = sec(t, "table-5.6")
    assert tab["title"] == "Minimum thermal efficiencies for domestic hot water systems"
    assert "Fuel5 0.95" in tab["text"] and tab["text"].endswith("Electrically-heated 100% assumed")
    assert sec(t, "para-5.2")["text"] == "More text."


def test_key_terms_in_the_accent_colour_on_their_own_line():
    # AD P 2013: the term is printed in a spot colour, its meaning on the lines below; "*" marks a term from the
    # Building Regulations.
    spot = {"c": [1.0]}
    L = page_furniture(1, "11") + [ln(1, 86, bold("Appendix", "A:", "Key", "terms"), 26.0, "Agenda-Bold"),
                                   ln(1, 190, [("Building", spot), ("control", spot), ("body", spot)]),
                                   ln(1, 204, ["A", "local", "authority", "or", "approved"]),
                                   ln(1, 218, ["inspector"]),
                                   ln(1, 238, [("Electrical", spot), ("installation*", spot)]),
                                   ln(1, 252, ["Fixed", "electric", "cables"])]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    d = {x["term"]: x for x in t["definitions"]}
    assert set(d) == {"Building control body", "Electrical installation"}
    assert sec(t, d["Building control body"]["section_id"])["text"] == "A local authority or approved inspector"
    assert d["Electrical installation"]["from_building_regulations"] is True


def test_chapters_with_the_same_code_or_title_get_distinct_ids():
    L = page_furniture(1, "1") + [ln(1, 84, bold("Regulation", "23(2):", "New", "elements"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, ["Text", "one."])]
    L += page_furniture(2, "2") + [ln(2, 84, bold("Regulation", "23(1):", "Renovation"), 26.0, "Agenda-Bold"),
                                   ln(2, 140, ["Text", "two."])]
    L += page_furniture(3, "3") + [ln(3, 84, bold("Guidance"), 26.0, "Agenda-Bold"), ln(3, 140, ["Three."])]
    L += page_furniture(4, "4") + [ln(4, 84, bold("Guidance"), 26.0, "Agenda-Bold"), ln(4, 140, ["Four."])]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    ids = [s["id"] for s in t["sections"] if s["type"] == "chapter"]
    assert ids == ["regulation-23", "regulation-23-1", "guidance", "guidance-2"] and not t["issues"][:-1]


# ---------------------------------------------------------------- classic layout (2004-2016 editions: A, C, G, J)

def classic_doc():
    """Two pages of the older two-column layout: 10.5pt body, 23pt chapter titles, 14pt headings, a gutter at 292
    (even pages) or 326 (odd pages), captions in 12pt roman type above the drawing or table."""
    def cl(page, top, words, size=10.5, font="HelveticaNeue-Roman", x0=36.9):
        return ln(page, top, words, size, font, x0)

    def both(page, top, left, right, size=10.5, g=292.0, x0=36.9):
        a, b = cl(page, top, left, size, x0=x0), cl(page, top, right, size, x0=g)
        a["words"] += b["words"]
        a["text"] += " " + b["text"]
        return a

    L = []
    for p in (1, 2, 3):
        L += [cl(p, 16, list("ONLINE"), 20.0, "HelveticaNeue-Bold", 188.9), cl(p, 24.1, ["A1/2"], 18.0, x0=519.4),
              cl(p, 27.1, ["RUNNING", "HEADER"], 14.0, x0=70.9),
              cl(p, 814.9, ["O", "N", "L", "I", "N", "E", "V", "E", "R", "S", "I", "O", "N", str(p + 10)], 20.0, x0=188.9)]
    L += [cl(1, 45.4, bold("The", "Requirements"), 23.0, "HelveticaNeue-Bold"),
          cl(1, 160, ["Requirement", "Limits", "on", "application"], 8.5, "TimesNewRomanPS-Italic", 90.7),
          cl(1, 189, [("A1.", B), "The", "building", "shall", "be", "constructed", "so", "that", "loads", "are"], 8.5, "TimesNewRomanPS", 90.7),
          cl(1, 199, ["sustained", "and", "transmitted", "to", "the", "ground."], 8.5, "TimesNewRomanPS", 90.7)]
    L += [cl(2, 45.4, bold("Section", "2C:", "Thickness", "of", "walls"), 23.0, "HelveticaNeue-Bold"),
          both(2, 106, [("Application", {"b": True, "s": 14.0})], [(w, {"s": 10.5}) for w in ("e.", "the", "guidance", "is", "based")], 14.0),
          both(2, 125, [("2C1", B), "This", "section", "applies", "to"], ["on", "compressive", "strengths."]),
          cl(2, 136, ["the", "following", "buildings:"]),
          cl(2, 141.5, [("2C4", B), "This", "section", "applies", "only"], x0=292.0),
          both(2, 152.5, ["a.", "houses", "(see", "paragraphs"], ["to", "small", "buildings."]),
          cl(2, 163.5, [("2C14", B), "to", "2C16);", "and"], x0=53.9),
          cl(2, 180, [("2C2", B), "Only", "the", "wall", "types", "in"]),
          cl(2, 191, [("Table", B), ("2", B), ("are", B), ("considered", B)]),
          both(2, 202, ["here."], ["Continued", "on", "page", "3"], g=450.0),
          cl(2, 400, ["Table", "2", "Wall", "types", "considered"], 12.0, x0=42.5),
          cl(2, 420, bold("Residential", "buildings", "of", "up", "to", "three", "storeys"), 8.0, "HelveticaNeue-Bold", 42.5),
          cl(2, 437, ["External", "walls", "Internal", "load-bearing", "walls", "across", "the", "gutter", "too"], 8.0, x0=42.5),
          cl(2, 700, ["Next", "column", "text."], x0=292.0),
          cl(2, 760, [("7", {"s": 3.8}), ("National", {"s": 6.5}), ("Planning", {"s": 6.5}), ("Policy", {"s": 6.5})], 3.8, x0=306.1),
          cl(2, 768, ["Framework,", "2012."], 6.5, x0=320.3)]
    L += [cl(3, 60, ["Diagram", "1", "Size", "and", "proportion"], 12.0, x0=76.5),
          cl(3, 83, ["See", "para", "2C4"], 6.0, x0=77.4),
          cl(3, 300, ["H", "W1", "W2"], 7.0, x0=150.0),
          cl(3, 440, bold("Thickness", "of", "walls"), 14.0, "HelveticaNeue-Bold", 70.9),
          cl(3, 460, [("2C5", B), "General", "wall", "thickness."], x0=70.9)]
    return {"lines": L, "tables": [], "page_width": 595.0}


@pytest.fixture(scope="module")
def ctree():
    return build_tree(classic_doc(), META)


def test_classic_page_furniture_and_printed_page(ctree):
    text = " ".join(s["text"] + " " + (s["title"] or "") for s in ctree["sections"])
    assert "RUNNING" not in text and "A1/2" not in text and "Continued on page" not in text
    assert sec(ctree, "para-2c1")["printed_page"] == "12"


def test_classic_requirement_box(ctree):
    box = [s for s in ctree["sections"] if s["type"] == "requirement"]
    assert len(box) == 1 and box[0]["text"].startswith("Requirement Limits on application\nA1. The building")


def test_classic_two_columns_are_read_left_then_right(ctree):
    assert sec(ctree, "para-2c1")["text"] == "This section applies to the following buildings:\na. houses (see paragraphs 2C14 to 2C16); and"
    assert sec(ctree, "para-2c4")["text"] == "This section applies only to small buildings. Next column text."
    assert sec(ctree, "section-2c-application")["level"] == 2


def test_classic_bold_run_on_line_and_cross_reference_are_not_new_sections(ctree):
    assert "para-2c14" not in {s["id"] for s in ctree["sections"]}
    # the right column's first line carries on the last paragraph of the left column
    assert sec(ctree, "para-2c2")["text"] == "Only the wall types in Table 2 are considered here.\ne. the guidance is based on compressive strengths."
    assert not [s for s in ctree["sections"] if s["type"] == "heading" and s["title"].startswith("Table 2")]


def test_classic_caption_above_its_table_and_drawing(ctree):
    t = sec(ctree, "table-2")
    assert t["title"] == "Wall types considered" and t["text"].startswith("Residential buildings of up to three storeys\nExternal walls")
    d = sec(ctree, "diagram-1")
    assert d["title"] == "Size and proportion" and d["labels"] == ["See para 2C4", "H W1 W2"]
    assert d["area"]["top"] < 60 and 300 < d["area"]["bottom"] < 440
    assert sec(ctree, "para-2c5")["text"] == "General wall thickness."


def test_classic_footnotes_are_kept_on_the_section(ctree):
    notes = [f for s in ctree["sections"] for f in s["footnotes"]]
    assert notes == ["7 National Planning Policy Framework, 2012."]


def test_classic_main_changes_page_before_the_first_chapter_is_kept_and_its_repeat_skipped():
    def cl(page, top, words, size=10.5, font="HelveticaNeue-Roman", x0=36.9):
        return ln(page, top, words, size, font, x0)
    L = []
    for p in range(1, 6):
        L += [cl(p, 814.9, ["O", "N", "L", "I", "N", "E", "V", "E", "R", "S", "I", "O", "N", str(p)], 20.0, x0=188.9)]
    L += [cl(1, 300, bold("APPROVED", "DOCUMENT"), 30.0, "HelveticaNeue-Bold")]
    mc = [cl(2, 53, bold("MAIN", "CHANGES", "MADE", "BY", "THE"), 14.0, "HelveticaNeue-Bold"),
          cl(2, 70, bold("2010", "AMENDMENTS"), 14.0, "HelveticaNeue-Bold"),
          cl(2, 95, ["The", "2010", "amendments", "reflect", "the", "new", "regulations."]),
          cl(2, 107, ["They", "were", "mainly", "number", "changes."])]
    L += mc
    for p in (3, 4):
        L += [cl(p, 45.4, bold("Section", str(p - 2) + ":", "Toxic", "substances"), 23.0, "HelveticaNeue-Bold"),
              cl(p, 100, [(f"{p - 2}.1", B), "Cavity", "walls", "should", "be", "checked."]),
              cl(p, 112, ["More", "words", "here."]), cl(p, 124, ["And", "more", "words."])]
    L += [{**l, "page": 5} for l in mc] + [cl(5, 400, ["Cover", "spread", "junk."])]
    t = build_tree({"lines": L, "tables": [], "page_width": 595.0}, META)
    chaps = [s for s in t["sections"] if s["type"] == "chapter"]
    assert [c["id"] for c in chaps] == ["main-changes", "section-1", "section-2"] and chaps[0]["file_page"] == 2
    head = next(s for s in t["sections"] if s["parent_id"] == "main-changes")
    assert head["type"] == "heading" and head["title"] == "MAIN CHANGES MADE BY THE 2010 AMENDMENTS"
    texts = [s["text"] for s in t["sections"] if s["type"] == "text"]
    assert texts == ["The 2010 amendments reflect the new regulations. They were mainly number changes."]
    assert "Cover spread junk." not in " ".join(s["text"] for s in t["sections"])
    assert any("file page 5: a repeat of the Main changes page (file page 2)" in i for i in t["issues"])


def test_classic_requirement_box_in_body_type_inside_a_ruled_frame_is_a_requirement():
    def cl(page, top, words, size=10.5, font="HelveticaNeue-Roman", x0=56.7):
        return ln(2, top, words, size, font, x0)  # page 1 is the cover
    L = [ln(1, 300, bold("APPROVED", "DOCUMENT"), 30.0, "HelveticaNeue-Bold"),
         cl(1, 814.9, ["O", "N", "L", "I", "N", "E", "V", "E", "R", "S", "I", "O", "N", "12"], 20.0, x0=188.9),
         cl(1, 45.4, bold("The", "Requirement"), 23.0, "HelveticaNeue-Bold", 36.9),
         cl(1, 100, ["This", "Approved", "Document", "deals", "with", "the", "following", "Requirement."], x0=36.9),
         cl(1, 154, ["Requirement", "Limits", "on", "application"], 10.0, "TimesNewRomanPS-Italic"),
         cl(1, 184, bold("Means", "of", "warning", "and", "escape"), 10.0, "TimesNewRomanPS-Bold"),
         cl(1, 201, [("B1.", B), "The", "building", "shall", "be", "designed", "and", "constructed."], 10.0, "TimesNewRomanPS"),
         cl(1, 330, [("1.1", B), "Guidance", "text", "after", "the", "box."], x0=36.9)]
    frame = {"page": 2, "top": 133.5, "bottom": 312.5, "x0": 36.9, "x1": 522.7,
             "rows": [["Requirement Limits on application", ""], ["Means of warning and escape B1. The building ...", ""]]}
    t = build_tree({"lines": L, "tables": [frame], "page_width": 595.0}, META)
    req = [s for s in t["sections"] if s["type"] == "requirement"]
    assert len(req) == 1 and req[0]["id"] == "the-requirement-box-1"
    assert req[0]["text"] == ("Requirement Limits on application\nMeans of warning and escape\n"
                              "B1. The building shall be designed and constructed.")
    assert req[0]["grid"][0] == ["Requirement Limits on application", ""]  # the frame goes to the model check
    intro = next(s for s in t["sections"] if s["id"] == "the-requirement-text-1")
    assert intro["text"] == "This Approved Document deals with the following Requirement."
    assert not [s for s in t["sections"] if s["type"] == "heading"]


# ---------------------------------------------------------------- booklets and notes without chapter titles

def booklet():
    L = [ln(1, 270, bold("Amendments", "to", "the"), 36.0, "Agenda-Bold"), ln(1, 785, ["For", "use", "in", "England"], 26.0)]
    L += page_furniture(2, "2") + [ln(2, 83, bold("Introduction"), 15.0, "Agenda-Bold"),
                                   ln(2, 107, ["These", "changes", "take", "effect", "on", "2", "February", "2023."])]
    for p, vol in ((3, "1"), (4, "2")):
        L += page_furniture(p, str(p)) + [
            ln(p, 83, ["The", "Building", "Regulations", "2010"], 20.0),
            ln(p, 107, bold("Approved", "Document", "L"), 20.0, "Agenda-Bold"),
            ln(p, 128, bold("Volume", vol), 20.0, "Agenda-Bold"),
            ln(p, 150, ["2021", "edition"], 20.0),
            ln(p, 188, bold("List", "of", "amendments"), 20.0, "Agenda-Bold"),
            ln(p, 296, bold("Page", "15", "Replace", "paragraph", "2.10."), 12.0, "Agenda-Bold"),
            ln(p, 316, [("2.10", B), "New", "text", "for", "volume", vol + "."], font="Agenda-Semibold")]
    L += [ln(5, 24, bold("List", "of", "Approved", "Documents"), 26.0, "Agenda-Bold"), ln(5, 120, ["Approved", "Document", "A"])]
    return {"lines": L, "tables": [], "page_width": 595.0}


def test_booklet_without_chapter_titles():
    t = build_tree(booklet(), META)
    chaps = [s for s in t["sections"] if s["type"] == "chapter"]
    assert [c["title"] for c in chaps] == ["Introduction", "Approved Document L Volume 1 2021 edition List of amendments",
                                           "Approved Document L Volume 2 2021 edition List of amendments"]
    paras = [s for s in t["sections"] if s["type"] == "paragraph"]
    assert [p["text"] for p in paras] == ["New text for volume 1.", "New text for volume 2."]
    assert len({p["id"] for p in paras}) == 2 and not t["issues"]
    assert "Approved Document A" not in " ".join(s["text"] for s in t["sections"])  # the back page list


def test_booklet_replacement_row_in_small_print_is_kept():
    d = booklet()
    d["lines"].append(ln(3, 340, ["17.", "Cavity", "barrier", "E", "30", "and", "I", "15", "Not", "applicable"], 8.0))
    t = build_tree(d, META)
    assert "17. Cavity barrier E 30 and I 15 Not applicable" in [s["text"] for s in t["sections"] if s["type"] == "text"]
    assert not [i for i in t["issues"] if "very small print skipped" in i]


def booklet_with_a_reprinted_section():
    """A two-volume booklet that reprints a whole section in the 2019 layout (June 2022 AD B): the reprinted
    section has a 26pt chapter title, which used to make the parser skip everything before it."""
    L = [ln(1, 270, bold("Amendments", "to", "the"), 36.0, "Agenda-Bold")]
    L += page_furniture(2, "2") + [ln(2, 83, bold("Introduction"), 15.0, "Agenda-Bold"),
                                   ln(2, 107, ["These", "changes", "take", "effect", "on", "1", "December", "2022."])]
    p = 3
    for vol in ("1", "2"):
        L += page_furniture(p, str(p)) + [
            ln(p, 107, bold("Approved", "Document", "B"), 20.0, "Agenda-Bold"),
            ln(p, 128, bold("Volume", vol), 20.0, "Agenda-Bold"),
            ln(p, 152, ["2019", "edition"], 20.0),
            ln(p, 190, bold("List", "of", "amendments"), 20.0, "Agenda-Bold"),
            ln(p, 300, bold("Section", "3:", "Means", "of", "escape"), 20.0, "Agenda-Bold", 100),
            ln(p, 330, bold("Page", "21") + ["Replace", "paragraph", "3.14."]),
            ln(p, 350, [("3.14", B), "Escape", "text", "for", "volume", vol + "."], font="Agenda-Semibold", x0=100)]
        p += 1
        L += page_furniture(p, str(p)) + [
            ln(p, 83, bold("Section", "10:", "External", "walls"), 20.0, "Agenda-Bold", 100),
            ln(p, 111, bold("Pages", "79") + ["Replace", "Section", "10", "with", "the", "following."]),
            ln(p, 150, bold("Section", "10:", "Resisting", "fire", "spread", "over"), 26.0, "Agenda-Bold"),
            ln(p, 180, bold("external", "walls"), 26.0, "Agenda-Bold"),
            ln(p, 263, bold("Introduction"), 20.0, "Agenda-Bold"),
            ln(p, 291, [("10.1", B), "Walls", "for", "volume", vol + "."], font="Agenda-Semibold")]
        p += 1
    L += [ln(p, 24, bold("List", "of", "Approved", "Documents"), 26.0, "Agenda-Bold"), ln(p, 120, ["Approved", "Document", "A"])]
    return {"lines": L, "tables": [], "page_width": 595.0}


def test_booklet_that_reprints_a_section_keeps_both_volumes_apart():
    t = build_tree(booklet_with_a_reprinted_section(), META)
    paras = {s["id"]: s["text"] for s in t["sections"] if s["type"] == "paragraph"}
    # Volume 1 is kept (it was skipped up to the first 26pt title), and Volume 2 does not take Volume 1's ids.
    assert sorted(paras.values()) == ["Escape text for volume 1.", "Escape text for volume 2.",
                                      "Walls for volume 1.", "Walls for volume 2."]
    chaps = [s["id"] for s in t["sections"] if s["type"] == "chapter"]
    assert "section-3" in chaps and "v2-section-3" in chaps and "section-10" in chaps and "v2-section-10" in chaps
    assert paras["v2-section-3-para-3.14"] == "Escape text for volume 2."
    # the reprinted 26pt title is one heading, joined over its two lines
    heads = [s["title"] for s in t["sections"] if s["type"] == "heading" and s["title"].startswith("Section 10")]
    assert heads == ["Section 10: Resisting fire spread over external walls"] * 2
    assert not [i for i in t["issues"] if "duplicate" in i]
    assert "Approved Document A" not in " ".join(s["text"] for s in t["sections"])


def test_part_prefix_rule_and_ids():
    from system.rag.parse_adoc import part_prefix
    parts = ["approved-document-l-volume-1", "approved-document-l-volume-2", "february-2023-amendments-to-approved-document-l",
             "frequently-asked-questions", "corrections-to-approved-document-g", "approved-document-g-sanitation"]
    assert [part_prefix(p, parts) for p in parts] == ["v1-", "v2-", "amendments-february-2023-", "faq-", "corrections-", ""]
    assert part_prefix("approved-document-b-volume-1", ["approved-document-b-volume-1"]) == ""
    t = build_tree(booklet(), {**META, "id_prefix": "v2-"})
    assert all(s["id"].startswith("v2-") for s in t["sections"])
    assert all(s["parent_id"] is None or s["parent_id"].startswith("v2-") for s in t["sections"])


# ---------------------------------------------------------------- real files: the other Approved Documents

REAL = [  # source, part (start of the part name), counts from the parsed document, checked by eye against the PDF
    ("adl", "approved-document-l-conservation-of-fuel-and-power-volume-1", {"paragraph": 246, "figure": 3, "table": 22, "definition": 63}),
    ("adl", "approved-document-l-conservation-of-fuel-and-power-volume-2", {"paragraph": 264, "figure": 3, "table": 34, "definition": 74}),
    ("adf", "approved-document-f-volume-1", {"paragraph": 182, "figure": 5, "table": 16, "definition": 36}),
    ("adf", "approved-document-f-volume-2", {"paragraph": 93, "figure": 1, "table": 5, "definition": 33}),
    ("adp", "approved-document-p", {"paragraph": 32, "figure": 2, "requirement": 1, "definition": 7}),
    ("ada", "approved-document-a", {"paragraph": 89, "figure": 25, "table": 11, "requirement": 2}),
    ("adc", "approved-document-c", {"paragraph": 139, "figure": 14, "table": 4, "requirement": 1}),
    ("adg", "approved-document-g-sanitation", {"paragraph": 153, "figure": 3, "table": 23, "requirement": 6}),
    ("adj", "approved-document-j", {"paragraph": 248, "figure": 45, "table": 16, "requirement": 2}),
    ("ad7", "approved-document-7", {"paragraph": 42, "requirement": 1}),
    ("adk", "approved-document-k", {"paragraph": 91, "figure": 32, "table": 1, "requirement": 9, "definition": 26}),
    ("adl", "february-2023-amendments", {"chapter": 3, "paragraph": 3}),
]


def _real_tree(source, part):
    pytest.importorskip("pdfplumber")
    import yaml
    from system.rag.parse_adoc import part_prefix, read_adoc_pdf
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / source).glob("*.json")]
    cur = [r for r in recs if r["valid_to"] is None and r["part"].startswith(part)]
    if not cur or not (ROOT / cur[0]["raw_path"]).exists():
        pytest.skip(f"{source} {part} raw file not on this machine")
    r = cur[0]
    srcs = yaml.safe_load((ROOT / "corpus" / "sources.yaml").read_text(encoding="utf-8"))["sources"]
    parts = next(s for s in srcs if s["id"] == source)["parser"]["parts"]
    meta = {**r, "title": r.get("part_title") or source, "id_prefix": part_prefix(r["part"], parts)}
    return build_tree(read_adoc_pdf(ROOT / r["raw_path"]), meta, fixes=load_fixes(source))


@pytest.mark.parametrize("source,part,counts", REAL, ids=[f"{s}-{p[:30]}" for s, p, _ in REAL])
def test_real_approved_documents_counts_and_all_checks_settled(source, part, counts):
    t = _real_tree(source, part)
    got = {k: sum(1 for s in t["sections"] if s["type"] == k) for k in counts}
    assert got == counts
    assert not t["checks"]  # every model check settled by a saved fix
    assert not [i for i in t["issues"] if "duplicate" in i]
    ids = [s["id"] for s in t["sections"]]
    assert len(ids) == len(set(ids))
    for s in t["sections"]:
        assert "O N L I N E" not in s["text"] and "specifification" not in s["text"] and "flfl" not in s["text"]


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
    from system.rag.parse_adoc import read_adoc_pdf as read_pdf
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
        for bad in ("O N L I N E", "Approved Document B Volume 1, 2019 edition", " fre ", "T he ", "defnition", "specifc"):
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


# ---------------------------------------------------------------- figure frames (the crop is the drawn frame)

def _shape(page, top, bottom, x0, x1, fill=False):
    return {"page": page, "top": float(top), "bottom": float(bottom), "x0": float(x0), "x1": float(x1), "fill": fill}


def test_modern_frame_gives_the_crop_and_its_lines_are_labels():
    # AD K Diagram 1.1: the frame starts with a "See paras 1.2–1.3" note in body size, above the highest label;
    # the caption band is at the bottom of the frame. Body text above the frame stays out.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "1:", "Stairs"), 26.0, "Agenda-Bold"),
                                  ln(1, 140, [("1.2", B), "Measure", "the", "rise."], font="Agenda-Semibold"),
                                  ln(1, 352, ["See", "paras", "1.2–1.3"], x0=75.0),
                                  ln(1, 367, ["Open", "riser"], 8.0, "Agenda-Medium", 240),
                                  ln(1, 744, [("Diagram", {"c": WHITE}), ("1.1", {"c": WHITE}), ("Rise", {"c": WHITE})], x0=65.0)]
    shapes = [_shape(1, 735, 761, 57, 538, fill=True), _shape(1, 346, 736, 57, 538, fill=True)]  # band, frame
    t = build_tree({"lines": L, "tables": [], "shapes": shapes, "page_width": 595.0}, META)
    d = sec(t, "diagram-1.1")
    assert d["area"]["top"] == 343.0 and d["area"]["bottom"] >= 761 and d["area"]["x0"] == 54.0 and d["area"]["x1"] == 541.0
    assert d["labels"] == ["See paras 1.2–1.3", "Open riser"]
    assert sec(t, "para-1.2")["text"] == "Measure the rise."


def test_modern_frame_sides_drawn_in_pieces_are_joined():
    # AD L 2026 Diagram B1: rows of a little table at the top of the frame, its sides drawn row by row.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "1:", "Heat"), 26.0, "Agenda-Bold"),
                                  ln(1, 334, ["Foundation", "area"], 9.0, x0=86),
                                  ln(1, 608, [("Diagram", {"c": WHITE}), ("B1", {"c": WHITE}), ("Roof", {"c": WHITE})], x0=89.0)]
    shapes = [_shape(1, 601, 626, 79, 561, fill=True)]
    for a, b in ((330.8, 347.7), (347.7, 364.8), (364.8, 382.0), (382.0, 600.6)):
        shapes += [_shape(1, a, b, 79.1, 79.1), _shape(1, a, b, 561.0, 561.0)]
    t = build_tree({"lines": L, "tables": [], "shapes": shapes, "page_width": 595.0}, META)
    assert sec(t, "diagram-b1")["area"]["top"] < 330


def test_a_band_with_no_frame_keeps_the_text_rule():
    # AD F Diagram 3.1: the chart above the band has no frame of the band's width; the old rule stands.
    L = page_furniture(1, "1") + [ln(1, 84, bold("Section", "3:", "Work"), 26.0, "Agenda-Bold"),
                                  ln(1, 300, [("3.9", B), "Text."], font="Agenda-Semibold"),
                                  ln(1, 400, ["Category", "A"], 8.0, "Agenda-Medium", 200),
                                  ln(1, 647, [("Diagram", {"c": WHITE}), ("3.1", {"c": WHITE}), ("Chart", {"c": WHITE})], x0=88.0)]
    shapes = [_shape(1, 639, 676, 80, 561, fill=True), _shape(1, 380, 630, 90, 550)]
    t = build_tree({"lines": L, "tables": [], "shapes": shapes, "page_width": 595.0}, META)
    d = sec(t, "diagram-3.1")
    assert d["area"]["x0"] == 28.0 and d["area"]["top"] == 316.0 and d["labels"] == ["Category A"]


def test_a_band_of_the_same_width_stops_the_frame():
    # Two framed diagrams stacked close together (AD E Diagrams 2.10 and 2.11 in the classic layout): the lower
    # diagram's band stops the upper frame.
    def cl(top, words, size=10.5, x0=303.0):
        return ln(4, top, words, size, "HelveticaNeue-Roman", x0)
    L = classic_doc()["lines"] + [cl(16, list("ONLINE"), 20.0, 188.9), cl(27.1, ["RUNNING", "HEADER"], 14.0, 70.9),
                                  cl(100, ["Left", "column", "words."], x0=36.9),
                                  cl(814.9, ["O", "N", "L", "I", "N", "E", "V", "E", "R", "S", "I", "O", "N", "14"], 20.0, 188.9),
                                  cl(60, ["Diagram", "2.10", "Wall", "type"], 12.0), cl(150, ["Hanger"], 7.0, 330),
                                  cl(262.5, ["Diagram", "2.11", "Concrete", "floor"], 12.0), cl(350, ["SECTION"], 7.0, 330)]
    shapes = [_shape(4, 54, 91, 292, 524, fill=True), _shape(4, 91, 259, 292, 524),
              _shape(4, 259.5, 290, 292, 524, fill=True), _shape(4, 290, 517, 292, 524)]
    t = build_tree({"lines": L, "tables": [], "shapes": shapes, "page_width": 595.0}, META)
    a, b = sec(t, "diagram-2.10"), sec(t, "diagram-2.11")
    assert a["area"]["bottom"] == 262.0 and a["labels"] == ["Hanger"]
    assert b["area"]["top"] <= 260 and b["area"]["bottom"] == 520.0 and b["labels"] == ["SECTION"]


def test_classic_frame_gives_the_crop_and_takes_the_notes_under_it():
    # AD H Diagram 2 (requirement H2 guidance): caption band at the top, the drawing in a ruled box, then small
    # notes straight under the box; body text further down and the next column stay out.
    def cl(top, words, size=10.5, x0=76.5):
        return ln(3, top, words, size, "HelveticaNeue-Roman", x0)
    L = [l for l in classic_doc()["lines"] if l["page"] != 3 or l["top"] < 50 or l["top"] > 800]
    L += [cl(60, ["Diagram", "2", "Drainage", "mound"], 12.0), cl(150, ["Filter", "sand"], 7.0, 200),
          cl(244, ["Notes:"], 5.0, 72), cl(252, ["1.", "To", "provide", "venting."], 5.0, 72),
          cl(300, ["Right", "column", "words", "here."], 7.0, 330),
          cl(440, bold("Thickness", "of", "walls"), 14.0, 70.9),
          cl(460, [("2C5", B), "General", "wall", "thickness."], x0=70.9)]
    L[-2]["font"] = "HelveticaNeue-Bold"
    shapes = [_shape(3, 54, 72, 71, 303, fill=True), _shape(3, 72, 238, 71, 303)]
    t = build_tree({"lines": L, "tables": [], "shapes": shapes, "page_width": 595.0}, META)
    d = sec(t, "diagram-2")
    assert d["labels"] == ["Filter sand", "Notes:", "1. To provide venting."]
    assert d["area"]["x0"] == 68.0 and d["area"]["x1"] == 306.0 and 255 < d["area"]["bottom"] < 270


@pytest.mark.parametrize("source,part,fid,frame_top,caption_top", [
    ("adk", "approved-document-k", "diagram-1.1", 345.6, 744),       # "See paras 1.2–1.3" at the frame top
    ("adk", "approved-document-k", "diagram-5.2", 382, 647),
    ("ads", "approved-document-s", "diagram-6.3", 86, 302),
    ("adm", "approved-document-m-access-to-and-use-of-buildings-volume-1", "v1-diagram-3.11", 154, 743),
])
def test_real_modern_crops_hold_the_frame_top(source, part, fid, frame_top, caption_top):
    t = _real_tree(source, part)
    a = next(s for s in t["sections"] if s["id"] == fid)["area"]
    assert frame_top - 8 < a["top"] <= frame_top and a["bottom"] > caption_top + 14


def test_real_classic_crops_hold_the_drawing_under_the_caption_band():
    t = _real_tree("adm", "approved-document-m-access-to-and-use-of-buildings-volume-2")
    a = next(s for s in t["sections"] if s["id"] == "v2-diagram-1")["area"]
    assert a["top"] < 59 and a["bottom"] > 540 and a["x0"] > 300  # the whole tactile paving drawing, one column
    t = _real_tree("ade", "approved-document-e")
    a = next(s for s in t["sections"] if s["id"] == "diagram-2.9")["area"]
    assert a["bottom"] > 317 and a["x1"] < 280  # down to PLAN, and not Diagram 2.10 in the next column
    t = _real_tree("adh", "approved-document-h")
    d = next(s for s in t["sections"] if s["id"] == "the-requirement-2-diagram-2")
    assert d["area"]["bottom"] > 290 and any(l.startswith("3.") for l in d["labels"])  # Notes 1-3 under the frame


def test_real_adb_historical_trees_in_scope_have_no_open_checks():
    """ADR 0016: only the AD B files in force from 1 January 2025 are checked (the 2019 edition with the 2020 and
    2022 amendments, and the text collated with the 2025, 2026 and 2029 amendments, both volumes). Older files keep
    their checks open. Reads the parsed trees; skips where none exist."""
    from system.rag.corpus import version_in_scope
    trees = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "parsed" / "adb-historical").glob("*.json")]
    trees = [t for t in trees if version_in_scope("adb-historical", t["version_id"])]
    if not trees:
        pytest.skip("adb-historical not parsed on this machine")
    assert len(trees) == 4
    assert {t["version_id"]: len(t["checks"]) for t in trees if t["checks"]} == {}
    for t in trees:
        S = t["sections"]
        assert all(s.get("description_source") == "model" for s in S if s["type"] == "figure")
        assert all(s.get("grid_source") == "model" and s.get("row_sentences") for s in S if s["type"] == "table")
