"""Coverage audit (system/rag/coverage.py): which parser fits a source, and what is in scope."""

from system.rag import coverage as C


def test_fitting_parser_by_fetch_method_and_file_type():
    assert C.fitting_parser({"fetch": {"method": "legislation"}}, {"application/xml"}) == "parse_legislation"
    assert C.fitting_parser({"fetch": {"method": "govuk"}}, {"text/html"}) == "parse_html"
    assert C.fitting_parser({"kind": "approved-document", "fetch": {"method": "govuk"}}, {"application/pdf"}) == "parse_adoc"
    assert C.fitting_parser({"kind": "hse-guidance", "fetch": {"method": "url"}}, {"application/pdf"}) == "parse_pdf"
    assert C.fitting_parser({"fetch": {"method": "govuk"}}, {"application/pdf", "text/html"}) == "parse_pdf"
    assert C.fitting_parser({"fetch": {"method": "url"}}, set()) == "unknown"


def test_scope_is_ingest_and_fetched_only():
    assert C.in_scope({"mode": "ingest", "fetch": {"method": "url"}})
    assert not C.in_scope({"mode": "restricted", "fetch": {"method": "url"}})
    assert not C.in_scope({"mode": "link_only", "fetch": {"method": "none"}})
    assert not C.in_scope({"mode": "ingest", "fetch": {"method": "none"}})


# ---------------------------------------------------------------- content check: raw file against parsed tree
# Synthetic raw documents (pages of words as read_pdf_raw returns them) and hand-made trees; the last test runs
# on the real trees and raw files where this machine has them.

import pytest

A4 = (595.0, 842.0)


def W(text, x0, top, upright=1, size=10):
    """A raw word as read_pdf_raw stores it: [text, x0, top, x1, bottom, upright]."""
    return [text, x0, top, x0 + 6 * len(text), top + size, upright]


def line(text, top, x0=72.0):
    out, x = [], x0
    for t in text.split():
        out.append(W(t, x, top))
        x += 6 * len(t) + 4
    return out


def page(n, *lines_, images=(), tables=()):
    words = [w for l in lines_ for w in l]
    return {"n": n, "width": A4[0], "height": A4[1], "words": words, "images": list(images), "tables": list(tables)}


BODY = ("The client must make sure the building work is planned and managed so that it can be done safely and "
        "without risks to health. This applies to every project, small or large, and to every contractor on site.")


def page_text(n):
    """BODY plus words only this page has, so a lost page cannot be covered by its neighbour."""
    return BODY + " " + " ".join(f"item{n}x{k}" for k in range(20))


def body_lines(start=120, text=BODY, per=12):
    ws = text.split()
    return [line(" ".join(ws[i:i + per]), start + 14 * k) for k, i in enumerate(range(0, len(ws), per))]


def sec(id_, page_, text="", type_="paragraph", title=None, **kw):
    return {"id": id_, "type": type_, "title": title, "heading_path": ["Doc"] + ([title] if title else []),
            "text": text, "number": None, "file_page": page_, "footnotes": [], **kw}


def test_tokens_normalise_case_ligatures_punctuation_and_bullets():
    assert C.tokens("ﬁre safety") == ["fire", "safety"]
    assert C.tokens("Area 12 m²") == ["area", "12", "m2"]
    assert C.tokens("Don’t ■ use (cid:2) it") == ["dont", "use", "it"]
    assert C.tokens("Contents .......... 12") == ["contents", "12"]
    assert C.tokens("pre-") + C.tokens("vention") == C.tokens("pre-vention")  # line-end hyphen, same both sides
    assert C.tokens("Order¹") == ["order1"]


def test_match_split_words_and_ligatures():
    from collections import Counter
    # the tree split a word ("W hat"), the PDF did not
    assert all(C.match(["what", "to", "do"], Counter(["w", "hat", "to", "do"]), ["w", "hat", "to", "do"]))
    # the PDF split a word, the tree did not
    assert all(C.match(["sur", "vey", "plan"], Counter(["survey", "plan"]), ["survey", "plan"]))
    # the PDF font dropped "fi" (parse_adoc puts it back) or doubled it
    assert all(C.match(["nd", "the", "fifire"], Counter(["find", "the", "fire"]), []))
    assert C.match(["asbestos"], Counter(["lead"]), ["lead"]) == [False]


def test_section_pages_runs_on_to_the_next_section_and_uses_spans():
    sections = [sec("a", 3, "x"), sec("b", 5, "y"), sec("t", 5, type_="table", spans={"5": [1, 2], "6": [3, 4]}),
                sec("c", 7, "z")]
    pages = C.section_pages(sections)
    assert pages[0] == {3, 4, 5}       # a paragraph from page 3 may run on to page 5, where the next one starts
    assert pages[2] == {5, 6}          # spans say exactly
    assert pages[3] == {7}


def _doc(n_pages=6, header="Health and Safety Executive", contents=True):
    pages = [page(1, line("Managing asbestos", 300), line("A guide for clients", 340))]
    for n in range(2, n_pages + 1):
        ls = [line(header, 40), line(str(n), 820, x0=290)]
        if n == 2 and contents:
            ls += [line("Contents", 120), line("Introduction 3", 160), line("Duties 4", 180)]
        else:
            ls += body_lines(text=page_text(n))
        pages.append(page(n, *ls))
    return {"pages": pages}


def _tree(raw, skip=(1, 2), drop_pages=()):
    secs = []
    for p in raw["pages"]:
        if p["n"] in skip or p["n"] in drop_pages:
            continue
        secs.append(sec(f"p{p['n']}", p["n"], page_text(p["n"])))
    return {"title": "Managing asbestos", "parser": "guidance-pdf/0.3", "sections": secs, "issues": []}


def test_reasons_name_header_page_number_cover_contents_and_sideways():
    raw = _doc()
    raw["pages"][3]["words"].append(W("DRAFT", 10, 400, upright=0))
    reasons, facts = C.word_reasons(raw, _tree(raw))
    by = {}
    for p, rs in zip(raw["pages"], reasons):
        for w, r in zip(p["words"], rs):
            by.setdefault(r, set()).add(w[0])
    assert {"Managing", "guide"} <= by["cover"]
    assert {"Contents", "Introduction"} <= by["contents"]
    assert {"Health", "Executive"} <= by["furniture"]
    assert {"3", "4", "5"} <= by["page-number"]
    assert by["sideways"] == {"DRAFT"}
    assert "client" in by[None]


def test_contents_lines_and_tree_issue_pages_are_reasons():
    raw = _doc()
    raw["pages"][4]["words"] += line("Duties of the client ........... 12", 600)
    tree = _tree(raw)
    tree["issues"] = ["file page 4: picture made of text with no caption, 12 lines skipped"]
    reasons, _ = C.word_reasons(raw, tree)
    assert set(reasons[3]) == {"issue"}
    assert reasons[4][-1] == "contents"


def test_approved_document_top_band_and_footer_are_furniture():
    raw = {"pages": [page(1, line("Cover", 300)), page(2, line("Section 3 tab", 50), *body_lines(), line("ONE", 800))]}
    tree = {"title": "AD", "parser": "approved-document-pdf/0.1", "sections": [sec("a", 2, BODY)], "issues": []}
    reasons, _ = C.word_reasons(raw, tree)
    assert reasons[1][0] == "furniture" and reasons[1][-1] == "furniture"


def test_full_tree_covers_everything_and_flags_nothing():
    raw = _doc()
    r = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, _tree(raw), raw)
    assert r["text"]["unexplained"] == 0 and r["text"]["coverage"] == 1.0
    assert r["items"] == []


def test_a_lost_page_is_flagged_and_the_document_too():
    raw = _doc(n_pages=8)
    lost_text = "The client must make sure " + " ".join(f"lost{k}" for k in range(60))
    raw["pages"][4]["words"] = line("Health and Safety Executive", 40) + [w for l in body_lines(text=lost_text) for w in l]
    r = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, _tree(raw, drop_pages=(5,)), raw)
    kinds = {(i["kind"], i["page"]) for i in r["items"]}
    assert ("page", 5) in kinds  # lost, not misplaced
    assert r["text"]["unexplained_share"] > 0
    lost = next(i for i in r["items"] if i["kind"] == "page")
    assert lost["key"] == "abababab:p5:text" and "lost0 lost1" in lost["detail"]


def test_empty_tree_for_a_non_empty_pdf_is_flagged():
    raw = _doc(n_pages=8)
    tree = {"title": "Managing asbestos", "parser": "guidance-pdf/0.3", "sections": [], "issues": []}
    r = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, tree, raw)
    kinds = {i["kind"] for i in r["items"]}
    assert {"empty", "doc", "page"} <= kinds
    assert r["text"]["unexplained_share"] > 0.9  # no front-matter excuse for a whole document


def test_reverse_check_reports_tree_words_not_in_the_pdf_by_origin():
    raw = _doc()
    tree = _tree(raw)
    tree["sections"].append(sec("t1", 3, "", type_="table", grid=[["Duty", "Who"], ["Plan", "Client"]],
                                grid_source="model", columns=["Duty", "Responsible person"]))
    tree["sections"][0]["text"] += " invented"
    t = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, tree, raw)["text"]
    assert "invented" in t["extra_pdf_words"]
    assert {"duty", "responsible", "person", "plan", "who"} <= set(t["extra_model_words"])


def test_images_in_a_crop_are_fine_others_explained_or_flagged():
    raw = _doc()
    p3 = raw["pages"][2]
    p3["images"] = [[100, 300, 400, 500],    # photo in the figure crop
                    [100, 600, 300, 700],    # photo in no crop: flagged
                    [0, 0, 595, 10],         # thin band
                    [100, 760, 102, 762]]    # a speck under 1% of the page: ignored
    raw["pages"][4]["images"] = [[0, 0, 595, 842]]  # background behind a page of text
    tree = _tree(raw)
    tree["sections"].append(sec("figure-1", 3, type_="figure", title="Lagging",
                                area={"page": 3, "x0": 95, "x1": 405, "top": 295, "bottom": 505}))
    im = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, tree, raw)["images"]
    assert im["images"] == 4 and im["in_crop"] == 1
    assert im["explained"] == {"band": 1, "background": 1}
    assert [i["key"] for i in im["items"]] == ["abababab:p3:image@100,600"]


def test_signature_image_is_explained():
    raw = _doc()
    raw["pages"][2]["words"] += line("Yours faithfully", 560)
    raw["pages"][2]["images"] = [[72, 580, 250, 640]]
    raw["pages"][2]["words"] += line("Jane Smith", 650) + line("Deputy Director", 664)
    im = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, _tree(raw), raw)["images"]
    assert im["explained"] == {"signature": 1} and not im["items"]


def test_ruled_tables_must_have_a_section_and_their_words():
    raw = _doc()
    rows = [["Material", "Score"], ["Lagging", "3"], ["Board", "2"]]
    raw["pages"][2]["tables"] = [{"bbox": [72, 400, 500, 480], "rows": rows}]
    raw["pages"][3]["tables"] = [{"bbox": [72, 400, 500, 480], "rows": [["Tile", "Ceiling"], ["Pipe", "Boiler"]]}]
    raw["pages"][4]["tables"] = [{"bbox": [72, 400, 500, 480], "rows": [["client", "safely"], ["project", "site"]]}]
    tree = _tree(raw)
    tree["sections"].append(sec("table-1", 3, "Material Score Lagging 3 Board 2", type_="table", title="Scores",
                                spans={"3": [390, 485]}))
    tb = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, tree, raw)["tables"]
    assert tb["tables"] == 3 and tb["found"] == 1
    kinds = {i["page"]: i["table"] for i in tb["items"]}
    assert kinds == {4: "missing", 5: "as text"}


def test_accept_records_a_flagged_item(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "CORPUS_DIR", tmp_path)
    raw = _doc(n_pages=8)
    rec = {"source_id": "x", "version_id": "v", "sha256": "ab" * 32}
    item = C.check_version(rec, {"title": "", "sections": [], "issues": []}, raw)["items"][0]
    monkeypatch.setattr(C, "versions_in_scope", lambda ids: [])
    monkeypatch.setattr(C, "check_source", lambda sid, vs: [{"version_id": "v", "items": [item]}])
    assert C.accept("x", "nope", "r", "me") == 1
    assert C.accept("x", item["key"], "page is a blank form", "Florin", today="2026-11-22") == 0
    saved = C.load_accepted("x")["accepted"][item["key"]]
    assert saved["reason"] == "page is a blank form" and saved["by"] == "Florin" and saved["date"] == "2026-11-22"


def test_real_trees_have_no_open_coverage_items():
    """Every current PDF tree on this machine against its raw file: no flagged item that is not accepted.
    Skips where no raw file or tree is on this machine. Raw words are cached, so a second run is quick."""
    pytest.importorskip("pdfplumber")
    versions = [v for v in C.versions_in_scope() if (C.ROOT / v[0]["raw_path"]).exists()]
    if not versions:
        pytest.skip("no parsed PDF trees with raw files on this machine")
    C.fill_caches(versions)
    by_src = {}
    for v in versions:
        by_src.setdefault(v[0]["source_id"], []).append(v)
    open_items = [f"{r['source_id']} {i['key']}: {i['detail'][:120]}"
                  for sid, vs in sorted(by_src.items()) for r in C.check_source(sid, vs) for i in r["open"]]
    assert not open_items, f"{len(open_items)} open coverage items:\n" + "\n".join(open_items[:40])


def test_running_text_runs_on_past_figures_and_notes_placed_inside_it():
    sections = [sec("t", 11, "long text"), sec("f", 11, type_="figure", spans={"11": [1, 2]}),
                sec("n", 12, "note", type_="note"), sec("h", 14, type_="heading", title="Next")]
    pages = C.section_pages(sections)
    assert pages[0] == {11, 12, 13, 14}
    assert pages[2] == {12, 13, 14}


def test_the_last_running_text_runs_on_to_the_end_of_the_file():
    pages = C.section_pages([sec("h", 1, type_="heading", title="Q and A"), sec("t", 2, "long answers"),
                             sec("f", 3, type_="figure", spans={"3": [1, 2]})], last_page=7)
    assert pages[1] == {2, 3, 4, 5, 6, 7}
    assert pages[2] == {3}


def test_a_full_page_before_the_first_section_is_not_excused_as_front_matter():
    raw = _doc(n_pages=8)
    intro = " ".join(f"intro{k}" for k in range(150))
    raw["pages"][2]["words"] = [w for l in body_lines(text=intro) for w in l]   # page 3: real text, no imprint
    raw["pages"][1]["words"] = line("© Crown copyright 2013 First published 1995", 300)  # page 2: the imprint
    tree = _tree(raw, skip=(1, 2, 3))
    reasons, _ = C.word_reasons(raw, tree)
    assert set(reasons[1]) == {"front"}
    assert set(reasons[2]) == {None}
    r = C.check_version({"source_id": "x", "version_id": "v", "sha256": "ab" * 32}, tree, raw)
    assert ("page", 3) in {(i["kind"], i["page"]) for i in r["items"]}


def test_a_table_text_and_its_grid_count_once():
    s = sec("t", 1, "Job Fibres\nWet stripping 0.1", type_="table", grid=[["Job", "Fibres"], ["Wet stripping", "0.1"]],
            grid_source="model", columns=["Job", "Fibre level"])
    from collections import Counter
    pool = Counter(t for t, o in C.section_words(s) if o != "model-copy")
    assert pool["job"] == 1 and pool["stripping"] == 1 and pool["level"] == 1


def test_bullet_letters_margin_labels_and_form_boxes_are_reasons():
    raw = {"pages": [page(1, line("n Wear a mask", 200), line("ACOP 3 The employer must", 230, x0=60),
                          line("Yes No N/A", 260))]}
    tree = {"title": "", "parser": "guidance-pdf/0.3", "issues": [],
            "sections": [sec("a", 1, "Wear a mask", status="acop")]}
    rs = C.word_reasons(raw, tree)[0][0]
    assert rs[0] == "bullet" and rs[4:6] == ["margin-label", "margin-label"] and rs[-1] is None
    tree["parser"] = "home-office-booklet-pdf/0.1"
    assert C.word_reasons(raw, tree)[0][0][-3:] == ["form", "form", "form"]
