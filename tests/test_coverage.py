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
