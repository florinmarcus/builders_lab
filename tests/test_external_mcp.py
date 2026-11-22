"""External government MCP servers: id mapping, reply parsing and scoring (offline), plus live runtime checks.

The live checks call third-party servers, so they run only with BUILDERS_LIVE_MCP=1:
    BUILDERS_LIVE_MCP=1 pytest -q tests/test_external_mcp.py -k live
"""
import os

import pytest

from evals import external_mcp as X

LEG = {"br2010": "uksi/2010/2214", "car2012": "uksi/2012/632", "hgcra1996-p2": "ukpga/1996/53"}
GOV = {"vat-notice-708": "/guidance/buildings-and-construction-vat-notice-708",
       "hmrc-cis-340": "/government/publications/construction-industry-scheme-cis-340"}


def test_law_paths_and_provisions():
    assert X.law_path("ukpga/1996/53/part/II") == "ukpga/1996/53"
    assert X.law_path("https://www.legislation.gov.uk/uksi/2026/1153") == "uksi/2026/1153"
    assert X.our_provision("regulation-12-6") == ("regulation", "12")
    assert X.our_provision("regulation-12-6A") == ("regulation", "12")
    assert X.our_provision("schedule-1-K4") == ("schedule", "1")
    assert X.our_provision("article-9-3") == ("article", "9")
    assert X.our_provision("top-text-2") is None and X.our_provision("part-2") is None
    assert X.lex_provision("http://www.legislation.gov.uk/id/uksi/2010/2214/regulation/12/6") == (
        "uksi/2010/2214", ("regulation", "12"))
    assert X.lex_provision("http://www.legislation.gov.uk/id/nisr/1988/74") == ("nisr/1988/74", None)


def test_source_maps_use_fetch_settings():
    leg, gov = X.source_maps([
        {"id": "br2010", "fetch": {"method": "legislation", "path": "uksi/2010/2214"}},
        {"id": "hgcra1996-p2", "fetch": {"method": "legislation", "path": "ukpga/1996/53/part/II"}},
        {"id": "vat-notice-708", "fetch": {"method": "govuk", "page": "/guidance/buildings-and-construction-vat-notice-708"}},
        {"id": "hse-nnlw", "fetch": {"method": "url"}},  # HSE pages are not on GOV.UK
    ])
    assert leg == {"br2010": "uksi/2010/2214", "hgcra1996-p2": "ukpga/1996/53"}
    assert gov == {"vat-notice-708": "/guidance/buildings-and-construction-vat-notice-708"}


def test_gold_keeps_only_legislation_and_govuk_labels():
    q = {"expected_sections": ["br2010:regulation-12-6", "car2012:regulation-5", "adb:para-2.5",
                               "hmrc-cis-340:chapter-2-text-1"]}
    g = X.gold(q, LEG, GOV)
    assert g["laws"] == {"uksi/2010/2214", "uksi/2012/632"}
    assert g["provs"] == {("uksi/2010/2214", "regulation", "12"), ("uksi/2012/632", "regulation", "5")}
    assert g["pages"] == {GOV["hmrc-cis-340"]}


def test_page_match_counts_parts_and_attachments_only():
    page = GOV["hmrc-cis-340"]
    assert X.page_match("https://www.gov.uk/government/publications/construction-industry-scheme-cis-340", page)
    assert X.page_match(page + "/construction-industry-scheme-cis-340-chapter-2", page)
    assert not X.page_match("/government/publications/construction-industry-scheme-cis-3400", page)
    assert not X.page_match("/universal-credit", page)


def test_parse_body_plain_json_and_sse():
    assert X.parse_body('{"jsonrpc":"2.0","id":1,"result":{}}')["id"] == 1
    sse = 'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"x":1}}\n\n'
    assert X.parse_body(sse)["result"] == {"x": 1}
    assert X.parse_body("") is None


def test_payload_prefers_structured_content():
    assert X.payload({"structuredContent": {"results": [1]}, "content": []}) == {"results": [1]}
    assert X.payload({"content": [{"type": "text", "text": '{"result": []}'}]}) == {"result": []}
    assert X.payload({"content": [{"type": "text", "text": "not json"}]}) == {"text": "not json"}


def test_normalise_each_server_shape():
    lex = {"result": [{"uri": "http://www.legislation.gov.uk/id/uksi/2012/632/regulation/9",
                       "title": "Notification of work with asbestos", "legislation_type": "uksi"}]}
    assert X.normalise("lex", lex) == [{"law": "uksi/2012/632", "prov": ["regulation", "9"],
                                       "title": "Notification of work with asbestos", "type": "uksi"}]
    ukl = {"results": [{"title": "CAR (NI) 2012", "url": "https://www.legislation.gov.uk/nisr/2012/179"}]}
    assert X.normalise("uklegal", ukl)[0]["law"] == "nisr/2012/179"
    gv = {"results": [{"title": "VAT Notice 708", "link": GOV["vat-notice-708"], "format": "guide"}]}
    assert X.normalise("govuk", gv)[0]["page"] == GOV["vat-notice-708"]


def test_score_question_law_provision_page_and_flags():
    q = {"expected_sections": ["car2012:regulation-9-1", "vat-notice-708:para-3-1"]}
    g = X.gold(q, LEG, GOV)
    results = [{"law": "nisr/2012/179", "prov": ["regulation", "9"], "type": "nisr"},
               {"law": "uksi/2012/632", "prov": ["regulation", "9"], "type": "uksi"},
               {"page": GOV["vat-notice-708"] + "/part-3"}]
    s = X.score_question(q, g, results, LEG, GOV, k=5)
    assert s["law"] and s["prov"] and s["page"]
    assert s["not_england"] == 1 and s["outside_corpus"] == 1
    s1 = X.score_question(q, g, results, LEG, GOV, k=1)  # only the Northern Ireland copy in the top 1
    assert not s1["law"] and not s1["prov"] and not s1["page"]


def test_ours_scored_with_the_same_rules():
    keys = ["adb:para-2.5", "car2012:regulation-9-1#row-2", "vat-notice-708:para-3-1"]
    res = X.ours_as_results(keys, LEG, GOV)
    assert res[1] == {"law": "uksi/2012/632", "prov": ["regulation", "9"], "type": "uksi"}
    assert res[2] == {"page": GOV["vat-notice-708"]}
    row = {"top5": ["a:1", "b:2"], "candidates": ["b:2", "c:3", "a:1", "d:4"]}
    assert X.ours_ranked(row, 3) == ["a:1", "b:2", "c:3"]  # the re-ranked top 5 first, then the rest
    assert X.ours_ranked(row, 3, only={"a", "c"}) == ["a:1", "c:3"]  # like for like: one source type only


# ---------------------------------------------------------------- live runtime checks (third-party servers)

live = pytest.mark.skipif(os.environ.get("BUILDERS_LIVE_MCP") != "1", reason="set BUILDERS_LIVE_MCP=1 to call live servers")


@live
@pytest.mark.parametrize("system", list(X.SERVERS))
def test_live_server_up_and_offers_its_search_tool(system):
    url, tool, _ = X.SERVERS[system]
    assert tool in X.Client(url).tools()


@live
def test_live_lex_finds_the_asbestos_notification_regulation():
    url, tool, args = X.SERVERS["lex"]
    res = X.normalise("lex", X.payload(X.Client(url).call(tool, args("notification of work with asbestos", 5))))
    assert {"law": "uksi/2012/632", "prov": ["regulation", "9"]}.items() <= next(
        (r for r in res if r["law"] == "uksi/2012/632"), {}).items()


@live
def test_live_uklegal_finds_a_law_by_title():
    url, tool, _ = X.SERVERS["uklegal"]
    res = X.normalise("uklegal", X.payload(X.Client(url).call(tool, {"query": "Building Regulations 2010", "limit": 5})))
    assert any(r["law"] == "uksi/2010/2214" for r in res)


@live
def test_live_govuk_finds_vat_notice_708():
    url, tool, args = X.SERVERS["govuk"]
    res = X.normalise("govuk", X.payload(X.Client(url).call(tool, args("VAT Notice 708 buildings and construction", 5))))
    assert any(X.page_match(r["page"], GOV["vat-notice-708"]) for r in res)
