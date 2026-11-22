"""Tests for the GOV.UK and HSE web page parser (ADR 0010). Most tests use small hand-made pages (mock
text). Real-file tests skip where the raw files are missing."""

import json
from pathlib import Path

import pytest

from system.rag.parse_html import parse_html

ROOT = Path(__file__).parent.parent
META = {"source_id": "demo-page", "version_id": "page@2024-01-01-abc", "valid_from": "2024-01-01",
        "valid_to": None, "sha256": "abc", "title": "Demo source", "fetched_url": "https://example.org/fetched"}


def govuk(body: str, title: str = "Demo guide") -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>'
            f'<link rel="canonical" href="https://www.gov.uk/demo"></head><body><h1>{title}</h1>'
            f'<div class="govspeak">{body}</div></body></html>')


def by_id(tree: dict) -> dict:
    return {s["id"]: s for s in tree["sections"]}


def test_govuk_headings_and_grouping():
    tree = parse_html(govuk(
        "<p>Opening words.</p>"
        '<h2 id="about">About the scheme</h2><p>First point.</p><p>Second   point&nbsp;here.</p>'
        '<h3 id="who">Who it covers</h3><p>Builders.</p>'
        '<h4>Small firms</h4><p>Sole traders too.</p>'
        '<h2 id="more">More help</h2><div class="call-to-action"><p>Call us.</p></div>'), META)
    s = by_id(tree)
    assert tree["title"] == "Demo guide" and tree["parser"] == "html/0.1"
    assert tree["definitions"] == [] and tree["checks"] == []
    assert s["top-text-1"]["text"] == "Opening words." and s["top-text-1"]["parent_id"] is None
    ch, h3, h4 = s["about-the-scheme"], s["about-the-scheme-who-it-covers"], s["about-the-scheme-who-it-covers-small-firms"]
    assert ch["type"] == "chapter"
    assert s["about-the-scheme-text-1"]["text"] == "First point.\nSecond point here."
    assert h3["type"] == "heading" and h3["parent_id"] == "about-the-scheme" and h3["level"] == 3
    assert h4["parent_id"] == h3["id"] and h4["level"] == 4
    assert h4["heading_path"] == ["Demo guide", "About the scheme", "Who it covers",
                                                          "Small firms"]
    assert s["more-help-text-1"]["text"] == "Call us."
    assert ch["url"] == "https://www.gov.uk/demo#about"
    assert h4["url"] == "https://www.gov.uk/demo"  # no id on the heading
    for sec in tree["sections"]:
        assert sec["heading_path"][0] == "Demo guide"
        assert sec["printed_page"] is None and sec["file_page"] is None and sec["footnotes"] == []


def test_text_sections_split_at_about_1500_characters():
    para = "<p>" + "word " * 100 + "</p>"  # about 500 characters each
    tree = parse_html(govuk('<h2 id="a">A</h2>' + para * 7), META)
    texts = [s for s in tree["sections"] if s["type"] == "text"]
    assert len(texts) == 3
    assert all(len(t["text"]) <= 1500 for t in texts)
    assert [t["id"] for t in texts] == ["a-text-1", "a-text-2", "a-text-3"]


def test_numbered_paragraphs_from_headings_and_paragraphs():
    tree = parse_html(govuk(
        '<h2 id="intro">1. Introduction</h2><p>Lead in.</p>'
        '<h3 id="types">1.1 Types of work</h3><p>The scheme covers:</p><ul><li>repairs</li></ul>'
        '<h4 id="extra">Extra notes</h4><p>Under a heading.</p>'
        '<h3 id="t2">1.2 Businesses</h3><p>Companies.</p>'
        '<h2 id="two">2. Terms</h2><p>2.1. A paragraph that starts with a number.</p><p>More of 2.1.</p>'
        '<p>2.10 Another one.</p><p>3.1 Wrong chapter, so plain text.</p>'
        '<h2 id="appendix-a">Appendix A</h2><h3>A.1 Scope</h3><p>In scope.</p>'), META)
    s = by_id(tree)
    assert s["chapter-1"]["number"] == "1" and s["chapter-2"]["number"] == "2"
    p = s["para-1.1"]
    assert p["type"] == "paragraph" and p["number"] == "1.1" and p["title"] == "Types of work"
    assert p["text"] == "The scheme covers:\n• repairs"  # stops at the next heading
    assert p["url"].endswith("#types") and p["parent_id"] == "chapter-1"
    assert s["para-1.1-extra-notes"]["parent_id"] == "para-1.1"
    assert s["para-1.2"]["text"] == "Companies."
    assert s["para-2.1"]["text"] == "A paragraph that starts with a number.\nMore of 2.1."
    assert s["para-2.1"]["title"] is None and s["para-2.1"]["heading_path"][-1] == "Paragraph 2.1"
    assert s["para-2.10"]["text"] == "Another one.\n3.1 Wrong chapter, so plain text."
    assert s["appendix-a"]["number"] == "A" and s["para-A.1"]["text"] == "In scope."


def test_numbers_in_plain_pages_are_not_paragraphs():
    tree = parse_html(govuk('<h2 id="h">Heights</h2><p>2.5 metres is the limit.</p>'), META)
    assert [s["type"] for s in tree["sections"]] == ["chapter", "text"]


def test_lists():
    tree = parse_html(govuk(
        '<h2 id="l">Lists</h2><p>Bring:</p><ul><li>a hat</li><li>boots<ul><li>steel toe</li></ul></li></ul>'
        '<p>Steps:</p><ol><li>Check</li><li>Record<br>and sign</li></ol>'
        '<ol start="4"><li>Fourth</li></ol>'), META)
    text = by_id(tree)["lists-text-1"]["text"]
    assert text.split("\n") == ["Bring:", "• a hat", "• boots", "  • steel toe", "Steps:", "1. Check",
                                "2. Record", "and sign", "4. Fourth"]


def test_table_with_colspan_and_rowspan():
    tree = parse_html(govuk(
        '<h3 id="rates">Rates</h3><table><thead><tr><th>Who</th><th>Rate</th><th>Notes</th></tr></thead><tbody>'
        '<tr><td>Registered</td><td>20%</td><td rowspan="2">Standard</td></tr>'
        '<tr><td>Not registered</td><td>30%</td></tr>'
        '<tr><td colspan="3">Gross status: no deduction</td></tr>'
        '</tbody></table>'), META)
    t = next(s for s in tree["sections"] if s["type"] == "table")
    assert t["columns"] == ["Who", "Rate", "Notes"]
    assert t["grid"] == [["Registered", "20%", "Standard"], ["Not registered", "30%", "Standard"],
                         ["Gross status: no deduction"] * 3]
    assert t["grid_source"] == "html" and t["title"] == "Rates" and t["parent_id"] == "rates"
    assert t["text"].split("\n")[0] == "Who | Rate | Notes"
    assert "Registered | 20% | Standard" in t["text"]
    assert all(len(r) == len(t["columns"]) for r in t["grid"])


def test_table_caption_and_no_header():
    tree = parse_html(govuk('<h2 id="x">X</h2><table><caption>Table 2: Sizes</caption>'
                            '<tr><td>a</td><td>b</td></tr><tr><td>c</td></tr></table>'), META)
    t = by_id(tree)["table-2"]
    assert t["number"] == "2" and t["title"] == "Sizes" and t["columns"] == []
    assert t["grid"] == [["a", "b"], ["c", ""]]


def test_images_keep_only_long_alt_text():
    tree = parse_html(govuk('<h2 id="d">Doors</h2><div class="img"><img src="a.jpg" alt="Door"></div>'
                            '<figure><img src="b.jpg" alt="A fire door with a self-closing device fitted"></figure>'
                            '<p>Text.</p>'), META)
    figs = [s for s in tree["sections"] if s["type"] == "figure"]
    assert len(figs) == 1 and figs[0]["text"] == "A fire door with a self-closing device fitted"


HSE = """<!DOCTYPE html><html><head><title>Domestic work - HSE</title><script>var x = 1;</script></head>
<body><section id="top"><a class="skip" href="#c">Skip to content</a></section>
<header id="headerContainer"><nav id="main-menu"><ul><li><a>Guidance</a></li><li><a>News</a></li></ul></nav>
<div class="cookie-banner"><p>We use Cookies to improve the site.</p></div></header>
<nav id="breadCrumb" class="hse-breadcrumb"><ol><li><a>Home</a></li><li><a>Construction</a></li></ol></nav>
<main id="contentContainer"><div class="hse-page-header"><h1>Domestic  work</h1></div>
<div id="page-contents"><h2>Who is a client</h2><p>A domestic client has work done on their home.</p>
<ul><li>the contractor</li><li>the principal contractor</li></ul>
<aside id="contentAside"><h2>Related content</h2><ul><li><a>Other page</a></li></ul></aside>
<div class="hse-back-to-top"><a>Back to top</a></div></div>
<div class="hse-sidebar"><aside><p>Sidebar menu</p></aside></div></main>
<div class="feedback-container"><p>Is this page useful?</p><button>Yes</button></div>
<footer id="footerContainer"><nav><a href="/cookies.htm">Cookies</a><a>Accessibility</a></nav></footer>
<script>Cookies.get('x');</script></body></html>"""


def test_hse_page_keeps_only_main_content():
    tree = parse_html(HSE, META)
    assert tree["title"] == "Domestic work"
    all_text = json.dumps(tree["sections"])
    for junk in ("Cookies", "Skip to content", "Guidance", "Home", "Related content", "Back to top",
                 "Sidebar", "useful", "Accessibility", "var x"):
        assert junk not in all_text, junk
    s = by_id(tree)
    assert s["who-is-a-client"]["type"] == "chapter"
    assert s["who-is-a-client-text-1"]["text"] == ("A domestic client has work done on their home.\n"
                                                   "• the contractor\n• the principal contractor")
    assert s["who-is-a-client"]["url"] == "https://example.org/fetched"  # no canonical link, no heading id
    assert tree["issues"] == []


def test_unique_ids():
    tree = parse_html(govuk('<h2 id="a">Example</h2><p>One.</p><h2 id="b">Example</h2><p>Two.</p>'
                            '<h3>Notes</h3><p>x</p><h3>Notes</h3><p>y</p>'), META)
    ids = [s["id"] for s in tree["sections"]]
    assert len(ids) == len(set(ids))
    assert "example" in ids and "example-2" in ids and "example-2-notes-2" in ids


def test_empty_page_and_title_fallback():
    tree = parse_html("<html><head><title>Only a title - GOV.UK</title></head><body></body></html>", META)
    assert tree["title"] == "Only a title"
    assert tree["sections"] == []
    assert any("no <h1>" in i for i in tree["issues"])
    assert any("empty page" in i for i in tree["issues"])


def test_empty_sections_dropped():
    tree = parse_html(govuk('<h2 id="a">A</h2><p> </p><h2 id="b">B</h2><p>Text.</p>'), META)
    assert [s["id"] for s in tree["sections"]] == ["b", "b-text-1"]


def test_tree_is_json_serialisable_and_has_all_keys():
    tree = parse_html(govuk('<h2 id="a">1. A</h2><h3>1.1 B</h3><p>x</p><table><tr><th>h</th></tr>'
                            '<tr><td>v</td></tr></table>'), META)
    back = json.loads(json.dumps(tree))
    assert back == tree
    assert set(tree) == {"source_id", "version_id", "valid_from", "valid_to", "sha256", "title", "parser",
                         "sections", "definitions", "issues", "checks"}
    keys = {"id", "parent_id", "type", "number", "title", "heading_path", "text", "printed_page", "file_page",
            "applies_to", "footnotes", "url"}
    for s in tree["sections"]:
        assert keys <= set(s)


def test_chunker_accepts_the_tree():
    from system.rag.chunk import chunk_tree

    tree = parse_html(govuk('<h2 id="a">1. A</h2><h3 id="b">1.1 B</h3><p>See paragraph 1.2.</p>'
                            '<h3 id="c">1.2 C</h3><p>y</p>'), META)
    chunks, _ = chunk_tree(tree, {"id": "demo-page", "kind": "guidance"}, META)
    assert [c["section_id"] for c in chunks] == ["para-1.1", "para-1.2"]
    assert chunks[0]["url"] == "https://www.gov.uk/demo#b"
    assert chunks[0]["references"][0]["to_section"] == "para-1.2"


# ---------------------------------------------------------------- real files (skip when missing)

def _real(source_id: str) -> list[dict]:
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "corpus" / "versions" / source_id).glob("*.json")]
    trees = []
    for r in recs:
        if r.get("valid_to") is not None or r.get("media_type") != "text/html":
            continue
        raw = ROOT / r["raw_path"]
        if not raw.exists():
            pytest.skip(f"{source_id} raw file not on this machine")
        trees.append(parse_html(raw.read_bytes(), {**r, "title": source_id}))
    if not trees:
        pytest.skip(f"{source_id} has no current HTML version")
    return trees


def test_real_cis_340():
    (tree,) = _real("hmrc-cis-340")
    types = [s["type"] for s in tree["sections"]]
    assert tree["title"].startswith("Construction Industry Scheme")
    assert types.count("table") == 3
    assert types.count("paragraph") > 100
    assert types.count("chapter") >= 6
    s = by_id(tree)
    assert s["para-1.1"]["title"] == "Types of work that are covered by the scheme"
    assert "• site preparation" in s["para-1.1"]["text"]
    assert "para-A.1" in s and "para-B.1" in s
    assert s["para-2.1-terms-used-under-the-scheme-table-1"]["columns"] == ["Term used", "Paragraph"]
    ids = [x["id"] for x in tree["sections"]]
    assert len(ids) == len(set(ids)) and tree["issues"] == []


def test_real_hse_cdm_domestic_clients():
    (tree,) = _real("hse-cdm-domestic-clients")
    text = json.dumps(tree["sections"])
    assert tree["title"].startswith("Domestic clients")
    for junk in ("Cookies", "Related content", "Is this page useful", "Skip to content", "Back to top"):
        assert junk not in text, junk
    assert 1 <= len([s for s in tree["sections"] if s["type"] == "text"]) <= 5
    assert "principal contractor" in text


def test_pages_of_a_multi_page_source_get_their_page_in_every_id():
    html = govuk("<p>Intro text before any heading.</p><h2>Who pays</h2><p>The customer accounts for the VAT.</p>")
    plain = parse_html(html, META)
    multi = parse_html(html, {**META, "id_prefix": "vatrevcon05000"})
    assert all(s["id"].startswith("vatrevcon05000-") for s in multi["sections"])
    assert [s["id"] for s in multi["sections"]] == ["vatrevcon05000-" + s["id"] for s in plain["sections"]]
    ids = {s["id"] for s in multi["sections"]}
    assert all(s["parent_id"] is None or s["parent_id"] in ids for s in multi["sections"])


# ---------------------------------------------------------------- S106: losses the coverage check found

def test_furniture_marks_match_whole_name_parts_not_substrings():
    """A heading id is a slug of its text: "searching-for-opportunities" holds "search" and "declare-and-share"
    holds "share", and both headings (with their chapter) were dropped as page furniture."""
    tree = parse_html(govuk(
        '<h2 id="searching-for-opportunities">Searching for opportunities</h2><p>Use the search tools.</p>'
        '<h2 id="declare-and-share">Declare and Share</h2><p>You are now bid ready.</p>'
        '<div class="hse-back-to-top__container"><a>Back to top</a></div><p class="research-note">Kept.</p>'), META)
    s = by_id(tree)
    assert s["searching-for-opportunities"]["type"] == "chapter"
    assert s["searching-for-opportunities-text-1"]["text"] == "Use the search tools."
    assert s["declare-and-share-text-1"]["text"] == "You are now bid ready.\nKept."
    assert "Back to top" not in json.dumps(tree["sections"])


def test_hse_next_page_links_and_printable_version_are_dropped():
    tree = parse_html(govuk(
        '<h2 id="v">Video</h2><p>The following video sets out the steps.</p>'
        '<div id="pagination" role="navigation"><ul><li class="next-page"><a><span class="pagination-icon">Next'
        '<span class="hide">page</span></span> <span class="pagination-text">Check your duty</span></a></li></ul></div>'
        '<div role="note" class="printable-version"><p><a>View a printable version of the whole guide</a></p></div>'),
        META)
    assert by_id(tree)["video-text-1"]["text"] == "The following video sets out the steps."


def test_text_left_inside_a_list_joins_the_item_before_it():
    """HSE wood dust: "<li>... over a representative time</li> period</ul>" lost "period"."""
    tree = parse_html(govuk('<h2 id="h">Health</h2><ul><li>Lead in<ul><li>over a representative time</li> period'
                            '</ul></li><li>next</li></ul>'), META)
    assert by_id(tree)["health-text-1"]["text"].split("\n") == ["• Lead in", "  • over a representative time period",
                                                          "• next"]


def test_a_group_label_heading_holds_the_next_heading_and_ids_stay():
    """AD B FAQ: an h3 topic label with an h3 question straight after it. The label was dropped as an empty
    heading; now it holds the question (one level down). The question keeps its id (evals point to it), and the
    next question after it is not moved: the page does not say where the group ends."""
    html = govuk('<h2 id="scope">The scope</h2><h3 id="named">Named standards</h3>'
                 '<h3 id="q25">25. Should I use the newer version?</h3><p>Answer 25.</p><h4>Note</h4><p>A note.</p>'
                 '<h3 id="q26">26. Another question?</h3><p>Answer 26.</p>')
    s = by_id(parse_html(html, META))
    label, q25, q26 = (s["the-scope-named-standards"], s["the-scope-25-should-i-use-the-newer-version"],
                       s["the-scope-26-another-question"])
    assert label["type"] == "heading" and label["parent_id"] == "the-scope" and label["level"] == 3
    assert q25["parent_id"] == label["id"] and q25["level"] == 4
    assert q25["heading_path"] == ["Demo guide", "The scope", "Named standards", "25. Should I use the newer version?"]
    assert s["the-scope-25-should-i-use-the-newer-version-note"]["level"] == 5
    assert s["the-scope-25-should-i-use-the-newer-version-note-text-1"]["text"] == "A note."
    assert q26["parent_id"] == "the-scope" and q26["level"] == 3
    assert s["the-scope-26-another-question-text-1"]["text"] == "Answer 26."
