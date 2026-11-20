"""Terminology layer and bilingual answer checks (ADR 0012)."""

import json

import pytest

from builders_api import terminology
from builders_api.service import jobs, verify


def test_glossary_json_is_current():
    data = json.loads(terminology.JSON_FILE.read_text())["entries"]
    assert data == terminology.build(), "Run: python -m builders_api.terminology --build (from system/api)"


@pytest.mark.parametrize("question, english", [
    ("Trebuie aviz ca să scot peretele portant din bucătărie?", "load-bearing wall"),
    ("Când trebuie să dau notificarea de plată la Fenwick?", "payment notice"),
    ("Ce lucrări suplimentare a aprobat clientul?", "variations / extras"),
    ("Ce zice studiul de azbest?", "asbestos survey"),
])
def test_romanian_words_with_endings(question, english):
    assert any(t["english"].startswith(english) for t in terminology.lookup(question)["terms"])


def test_mismatch_terms_are_flagged():
    terms = terminology.lookup("Am nevoie de autorizație de construire?")["terms"]
    assert terms[0]["mismatch"] and "Building Regulations" in terms[0]["english"]


def test_english_to_romanian():
    assert terminology.lookup("remove a load-bearing wall")["terms"][0]["romanian"].startswith("perete portant")


def test_romanian_answer_checks(seeded):
    firm = jobs.firm_id("oakline")
    ok = verify.verify_answer(firm, "Notificarea de plată până pe 30 noiembrie.", [])
    codes = {p["code"] for p in ok["problems"]}
    assert "NO_CLAIMS" in codes  # the date needs a claim
    bad = verify.verify_answer(firm, "Dormitorul 2 este fără azbest. Am trimis factura.", [])
    codes = [p["code"] for p in bad["problems"]]
    assert codes.count("BANNED_PHRASE") == 2
