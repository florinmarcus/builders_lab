"""Semantic check (system/rag/semcheck.py): what goes into a packet, the hash, the sample, save rules, the report."""
import json
import random

from system.rag import coverage as C
from system.rag import semcheck as S


def _sec(id_, type_, page, text="", **kw):
    return {"id": id_, "type": type_, "number": None, "title": None, "heading_path": ["Doc", id_], "text": text,
            "file_page": page, "footnotes": [], **kw}


def _raw_page(text):
    return {"words": [[w, 0, 0, 0, 0, 1] for w in text.split()]}


LONG = " ".join(f"word{i}" for i in range(900))


def test_page_content_keeps_what_is_on_the_page_in_tree_order():
    tree = {"title": "Doc", "sections": [
        _sec("p1", "paragraph", 1, "Alpha beta gamma delta epsilon zeta eta theta. Tail runs on to the next page here."),
        _sec("gone", "paragraph", 1, "Nothing of this one is printed on page two at all."),
        _sec("fig-1", "figure", 1, title="Figure 1", area={"page": 1, "top": 0, "bottom": 9, "x0": 0, "x1": 9},
             labels=["A"], description="A photo."),
        _sec("h", "heading", 2, title="Second"),
        _sec("p2", "paragraph", 2, "Second page text with a limit of 30 minutes.", footnotes=[{"text": "Note one."}]),
        _sec("t", "table", 2, "a b", grid=[["a", "b"]], columns=["x", "y"], spans={"2": [0, 9], "3": [0, 9]}),
        _sec("p3", "paragraph", 3, "Third page.")]}
    page2 = _raw_page("Tail runs on to the next page here. Second Second page text with a limit of 30 minutes. a b")
    got = S.pdf_page_content(tree, 2, page2, last_page=3)
    assert [e["id"] for e in got] == ["p1", "h", "p2", "t"]  # "gone" and the page 1 figure are not on page 2
    assert got[0]["from_earlier_page"] == 1 and "text_cut" not in got[0]
    assert got[1] == {"id": "h", "type": "heading", "title": "Second", "heading_path": "h"}  # document title dropped
    assert got[2]["footnotes"] == ["Note one."] and got[2]["may_run_on"] is True
    assert got[3]["grid"] == [["a", "b"]] and got[3]["columns"] == ["x", "y"] and got[3]["table_pages"] == [2, 3]
    assert got[3]["text"] == ["a b"]  # the printed words too: the notes under a table are only there
    assert [e["id"] for e in S.pdf_page_content(tree, 1, _raw_page("x"), last_page=3)][:3] == ["p1", "gone", "fig-1"]


def test_long_section_from_an_earlier_page_is_cut_to_the_part_on_the_page():
    tree = {"title": "Doc", "sections": [_sec("long", "paragraph", 1, LONG), _sec("next", "paragraph", 3, "End.")]}
    page2 = _raw_page(" ".join(f"word{i}" for i in range(400, 500)))
    e = S.pdf_page_content(tree, 2, page2, last_page=3)[0]
    text = " ".join(e["text"])
    assert e["text_cut"] is True and text.startswith("[...] word360 ") and text.endswith(" word539 [...]")
    # one shared phrase of three words is not enough to put a section on a page; five words in a row are
    assert S.page_part("see Table B2 for more", S._grams(["see", "table", "b2", "and", "so"]))[2] is False
    assert S.page_part("one two three four five six", S._grams("one two three four five".split()))[2] is True


def test_lines_and_packet_dump_stay_under_the_read_tools_line_limit():
    assert S.lines("a\n\n b ") == ["a", "b"]
    assert all(len(x) <= S.LINE for x in S.lines("word " * 2000)) and "".join(S.lines("x" * 4000)) == "x" * 4000
    pk = {"key": "k", "instructions": S.INSTRUCTIONS["pdf"].split("\n"),
          "content": [{"id": "t", "grid": [["a", "b"], ["c" * 3000, "d"]], "text": S.lines("long " * 900)}]}
    out = S.dump_packet(pk)
    assert max(len(ln) for ln in out.split("\n")) <= S.LINE + 20
    back = json.loads(out)
    assert back["content"][0]["grid"][0] == ["a", "b"] and '["a", "b"]' in out  # a row is one line
    assert "".join(back["content"][0]["grid"][1]) == "c" * 3000 + "d"  # an over-long row is wrapped, nothing lost


def test_key_changes_with_the_image_and_with_the_tree_content():
    content = [{"id": "p", "text": ["a"]}]
    k = S._sha(b"image-1", S._canon(content))
    assert k == S._sha(b"image-1", S._canon([{"text": ["a"], "id": "p"}])) and len(k) == 16  # key order does not matter
    assert k != S._sha(b"image-2", S._canon(content))
    assert k != S._sha(b"image-1", S._canon([{"id": "p", "text": ["b"]}]))


def test_html_parts_cut_at_shared_headings_and_show_dropped_text():
    def bl(tag, text, reason=None):
        return {"tag": tag, "parts": [[text, reason]]}
    raw = {"blocks": [bl("nav", "Home", "navigation"), bl("h1", "Title"), bl("p", "one " * 30),
                      bl("h2", "First part"), bl("p", "two " * 30), bl("td", "Cell A"), bl("td", "9"),
                      bl("h2", "Second part"), bl("p", "three " * 30)],
           "images": [{"alt": "A flow chart", "block": 8, "reason": None}],
           "tables": [{"rows": [["Cell A", "9"]], "reason": None}]}
    tree = {"title": "Title", "sections": [
        _sec("t0", "text", None, "one " * 30), _sec("c1", "chapter", None, title="First part"),
        _sec("t1", "text", None, "two " * 30), _sec("tb", "table", None, grid=[["Cell A", "9"]], columns=["a", "b"]),
        _sec("c2", "chapter", None, title="Second part"), _sec("t2", "text", None, "three " * 30)]}
    one = S.html_parts(raw, tree)
    assert len(one) == 1 and one[0]["source"][0] == "[dropped: navigation] Home" and one[0]["source"][1] == "<h1> Title"
    parts = S.html_parts(raw, tree, max_words=40)
    assert [p["part"] for p in parts] == [1, 2, 3] and all(p["of"] == 3 for p in parts)
    assert [[e["id"] for e in p["content"]] for p in parts] == [["t0"], ["c1", "t1", "tb"], ["c2", "t2"]]
    assert parts[1]["source"][0] == "<h2> First part" and parts[1]["source_tables"] == [[["Cell A", "9"]]]
    assert parts[2]["source_images"] == ["A flow chart"] and not parts[0]["source_tables"]


def test_legislation_units_are_provisions_with_everything_under_them():
    def s(id_, type_, parent, text=""):
        return {"id": id_, "type": type_, "parent_id": parent, "number": None, "title": None, "heading_path": [],
                "text": text, "status": "in_force", "applies_to": "E+W"}
    tree = {"sections": [s("part-1", "part", None), s("regulation-1", "regulation", "part-1", "(1) A.\n(a) b"),
                         s("regulation-1-1", "paragraph", "regulation-1", "(1) A.\n(a) b"),
                         s("regulation-1-1-a", "paragraph", "regulation-1-1", "(a) b"),
                         s("schedule-1", "schedule", None), s("schedule-1-paragraph-1", "schedule-paragraph", "schedule-1", "X")]}
    assert [u["id"] for u in S.leg_units(tree)] == ["regulation-1", "schedule-1-paragraph-1"]
    got = S.leg_content(tree, "regulation-1")
    assert [e["id"] for e in got] == ["regulation-1", "regulation-1-1", "regulation-1-1-a"]
    assert got[0]["text"] == ["(1) A.", "(a) b"] and got[0]["applies_to"] == "E+W"
    cut = S.leg_content(tree, "regulation-1", limit=5)
    assert cut[-1] == {"note": "[cut] more sections under this provision are not shown"} and len(cut) == 2


def test_xml_snippet_puts_the_group_title_first_and_cuts():
    from lxml import etree
    ns = "http://www.legislation.gov.uk/namespaces/legislation"
    root = etree.fromstring(f'<Body xmlns="{ns}"><P1group><Title>Notification</Title><P1 id="regulation-6">'
                            f'<Pnumber>6</Pnumber><Text>A project is notifiable.</Text></P1></P1group></Body>')
    el = next(e for e in root.iter() if e.get("id") == "regulation-6")
    got = S.xml_snippet(el)
    assert got[0].startswith("<Title>Notification</Title>") and got[1] == '<P1 id="regulation-6">'
    assert "<Text>A project is notifiable.</Text>" in got and not any("xmlns" in ln for ln in got)
    assert S.xml_snippet(el, limit=20)[-1] == "[cut]"


def test_sample_pages_base_tables_and_half_the_figures():
    rng = random.Random("seed|doc")
    got = S.sample_pages(100, tables={5, 6, 7}, figures={20, 21, 22, 23, 24, 25}, rng=rng)
    again = S.sample_pages(100, tables={5, 6, 7}, figures={20, 21, 22, 23, 24, 25}, rng=random.Random("seed|doc"))
    assert got == again  # the same seed gives the same pages
    base = [p for p, s in got.items() if s == "base"]
    assert len(base) == 10 and {5, 6, 7} <= set(got)  # 10% of 100, and every table page
    fig_left = [p for p in (20, 21, 22, 23, 24, 25) if p not in base]
    assert sum(1 for s in got.values() if s == "figure") == len(fig_left) // 2
    assert S.sample_pages(2, set(), set(), random.Random(1)) == {1: "base", 2: "base"}  # a short document: all pages
    assert len(S.sample_pages(12, set(), set(), random.Random(1))) == 3  # at least 3
    docs = {("a", "v"): dict(got)}
    kept = S.fit_cap(docs, cap=13)  # over the cap: extra figure pages go, base and table pages stay
    assert "figure" not in kept[("a", "v")].values() and {5, 6, 7} <= set(kept[("a", "v")]) and set(base) <= set(kept[("a", "v")])
    assert "figure" in S.fit_cap({("a", "v"): dict(got)}, cap=500)[("a", "v")].values()


def test_legislation_allocation_is_proportional_with_a_floor():
    got = S.leg_allocation({"big": 3000, "mid": 800, "tiny": 1, "small": 30}, target=300, least=2)
    assert got == {"big": 235, "mid": 63, "tiny": 1, "small": 2}


def test_check_answer_rules():
    f = {"kind": "table", "problem": "A value is in the wrong column.", "evidence": 'source: "30" / tree: "60"', "severity": "high"}
    assert S.check_answer({"verdict": "ok", "findings": []}) is None
    assert S.check_answer({"verdict": "table", "findings": [f]}) is None
    assert S.check_answer({"verdict": "ok", "findings": [f]}) == "verdict ok with findings"
    assert "needs at least one finding" in S.check_answer({"verdict": "table", "findings": []})
    assert "unknown verdict" in S.check_answer({"verdict": "fine"})
    assert "severity" in S.check_answer({"verdict": "table", "findings": [{**f, "severity": "medium"}]})
    assert "problem or evidence" in S.check_answer({"verdict": "table", "findings": [{**f, "evidence": " "}]})
    assert "unknown kind" in S.check_answer({"verdict": "table", "findings": [{**f, "kind": "typo"}]})
    assert "not the kind" in S.check_answer({"verdict": "missing", "findings": [f]})


def _setup(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(S, "CORPUS_DIR", corpus)
    monkeypatch.setattr(S, "ROOT", tmp_path)
    d = corpus / "parsed" / "demo" / "semcheck"
    d.mkdir(parents=True)
    for key, unit in (("a" * 16, "p1"), ("b" * 16, "p2"), ("c" * 16, "p3")):
        (d / f"pdf-{unit}-{key}.json").write_text(json.dumps(
            {"source_id": "demo", "version_id": "v1", "key": key, "kind": "semcheck-pdf", "unit": unit,
             "family": "guidance-pdf", "stratum": "base"}))
    return corpus


def test_save_keeps_good_answers_and_refuses_the_rest(tmp_path, monkeypatch):
    corpus = _setup(tmp_path, monkeypatch)
    f = {"kind": "missing", "problem": "A line is lost.", "evidence": "source: \"not more than 9 m\"", "severity": "high"}
    answers = tmp_path / "answers"
    answers.mkdir()
    (answers / "batch_0001.jsonl").write_text("\n".join([
        json.dumps({"key": "a" * 16, "kind": "semcheck-pdf", "verdict": "ok", "findings": [], "confidence": "high"}),
        json.dumps({"key": "b" * 16, "kind": "semcheck-pdf", "verdict": "missing", "findings": [f, {**f, "kind": "garbled", "severity": "low"}]}),
        json.dumps({"key": "c" * 16, "kind": "semcheck-pdf", "verdict": "ok", "findings": [f]}),   # ok with findings
        json.dumps({"key": "z" * 16, "kind": "semcheck-pdf", "verdict": "ok", "findings": []}),    # unknown key
        json.dumps({"key": "a" * 16, "kind": "semcheck-xml", "verdict": "ok", "findings": []}),    # wrong kind
        "not json"]))
    assert S.save(answers, "test model", today="2026-11-22") == 1
    saved = json.loads((corpus / "semchecks" / "demo.json").read_text())["verdicts"]
    assert set(saved) == {"a" * 16, "b" * 16}
    b = saved["b" * 16]
    assert b["verdict"] == "missing" and b["unit"] == "p2" and b["family"] == "guidance-pdf" and b["by"] == "test model"
    assert [x["severity"] for x in b["findings"]] == ["high", "low"] and b["confidence"] == "medium"


def _rows(verdicts):
    return [{"source_id": "demo", "version_id": "v1", "unit": f"p{i}", "key": str(i), "kind": "semcheck-pdf",
             "family": "guidance-pdf", "stratum": "base", "verdict": v} for i, v in enumerate(verdicts)]


def test_summary_counts_units_with_a_high_finding_and_gives_the_interval():
    hi = {"kind": "table", "severity": "high", "problem": "p", "evidence": "e"}
    lo = {"kind": "garbled", "severity": "low", "problem": "p", "evidence": "e"}
    wrong = {**hi, "settled": {"as": "model-wrong", "reason": "the page shows 30", "by": "me"}}
    kept = {**hi, "settled": {"as": "kept", "reason": "known limit S1", "by": "me"}}
    ok = {"verdict": "ok", "findings": []}
    rows = _rows([ok] * 94 + [{"verdict": "table", "findings": [hi, lo]}, {"verdict": "garbled", "findings": [lo]},
                              {"verdict": "table", "findings": [wrong]}, {"verdict": "table", "findings": [kept]},
                              {"verdict": "table", "findings": [wrong, lo]}, None])
    s = S.summarise(rows)
    assert (s["units"], s["judged"], s["not_judged"]) == (100, 99, 1)
    assert s["high"] == 2 and s["low_only"] == 2 and s["ok"] == 95  # a unit whose only finding was the model's mistake is ok
    assert s["open"] == 3 and s["open_high"] == 1 and s["model_wrong"] == 2 and s["kept"] == 1
    assert s["findings"] == {"table/high": 2, "garbled/low": 3}
    assert abs(s["high_rate"] - 2 / 99) < 1e-9 and 0.005 < s["high_low"] < 0.006 and 0.070 < s["high_high"] < 0.072
    assert S.wilson(0, 0) == (0.0, 1.0) and S.wilson(0, 50)[0] == 0.0 and 0.07 < S.wilson(0, 50)[1] < 0.072


def test_accept_settles_one_finding_or_all_and_needs_a_reason(tmp_path, monkeypatch):
    corpus = _setup(tmp_path, monkeypatch)
    f = {"kind": "table", "problem": "p", "evidence": "e", "severity": "high"}
    (tmp_path / "a.jsonl").write_text(json.dumps({"key": "b" * 16, "kind": "semcheck-pdf", "verdict": "table",
                                                  "findings": [f, {**f, "severity": "low"}]}))
    assert S.save(tmp_path / "a.jsonl", "m", today="2026-11-22") == 0
    assert S.accept("demo", "b" * 16, "model-wrong", " ", "me") == 1  # no reason
    assert S.accept("demo", "nope", "kept", "r", "me") == 1
    assert S.accept("demo", "b" * 16, "kept", "r", "me", finding=3) == 1
    assert S.accept("demo", "b" * 16, "model-wrong", "the page shows 30 under Integrity", "me", finding=1, today="2026-11-22") == 0
    v = json.loads((corpus / "semchecks" / "demo.json").read_text())["verdicts"]["b" * 16]
    assert v["findings"][0]["settled"]["as"] == "model-wrong" and "settled" not in v["findings"][1]
    assert len(S.open_findings(v)) == 1 and len(S.real_findings(v)) == 1
    assert S.accept("demo", "b" * 16, "kept", "known limit", "me") == 0  # all findings
    v = json.loads((corpus / "semchecks" / "demo.json").read_text())["verdicts"]["b" * 16]
    assert not S.open_findings(v) and len(S.real_findings(v)) == 2


def test_batches_and_prompt():
    files = [S.ROOT / f"corpus/parsed/x/semcheck/{i}.json" for i in range(14)]
    assert [len(b) for b in S.batches(files)] == [6, 6, 2]
    p = S.PROMPT.format(root="/repo", answers="a.jsonl", packets="- `x`")
    assert "Do not change any file except" in p and "/repo/a.jsonl" in p
    assert S.MODEL == "claude-fable-5-2"
    assert C.PDF == "application/pdf"


def test_xml_ids_keep_every_version_and_the_tree_extent_picks_one(tmp_path):
    # HSWA 1974 s.43A is printed twice under one id: for E+W+S and for N.I. The checked version must be the one the
    # tree holds; the last one in the file used to win, so the model compared the tree with the N.I. text.
    p = tmp_path / "law.xml"
    p.write_text('<Legislation><P1group><P1 id="section-43A" RestrictExtent="E+W+S"><Text>ORR</Text></P1></P1group>'
                 '<P1group><P1 id="section-43A" RestrictExtent="N.I."><Text>Executive</Text></P1></P1group></Legislation>')
    ids = S.xml_ids(p)
    assert len(ids["section-43A"]) == 2
    assert S.pick_version(ids["section-43A"], "E+W+S").get("RestrictExtent") == "E+W+S"
    assert S.pick_version(ids["section-43A"], "N.I.").get("RestrictExtent") == "N.I."
    assert S.pick_version(ids["section-43A"], None).get("RestrictExtent") == "E+W+S"
