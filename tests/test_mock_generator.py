"""Mock email generator: 20 emails, 3 for today, attachments readable, stable ids."""

import datetime as dt
import email
import io
import sys
from email import policy
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
pypdf = pytest.importorskip("pypdf")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system" / "data" / "mock"))
from generate import generate  # noqa: E402


def _load(path: Path):
    return email.message_from_bytes(path.read_bytes(), policy=policy.default)


def test_generates_scenario(tmp_path):
    written = generate(tmp_path, dt.date(2026, 11, 21))
    assert len(written["history"]) == 17 and len(written["today"]) == 3
    ids = {_load(p)["X-Oakline-Demo-Id"] for p in written["history"] + written["today"]}
    assert len(ids) == 20
    today = _load(tmp_path / "today" / "e15.eml")
    assert today["Date"].datetime.date() == dt.date(2026, 11, 21)


def test_attachments_are_readable(tmp_path):
    generate(tmp_path, dt.date(2026, 11, 21))
    survey = _load(tmp_path / "history" / "e17.eml")
    pdf = next(survey.iter_attachments())
    text = pypdf.PdfReader(io.BytesIO(pdf.get_content())).pages[0].extract_text()
    assert "Chrysotile detected" in text and "kitchen and bathroom only" in text
    chat = next(_load(tmp_path / "history" / "e06.eml").iter_attachments())
    assert "Approved, thanks. Pocket door it is." in chat.get_content()


def test_output_is_stable(tmp_path):
    a = generate(tmp_path / "a", dt.date(2026, 11, 21))
    b = generate(tmp_path / "b", dt.date(2026, 11, 21))
    assert [p.read_bytes() for p in a["history"]] == [p.read_bytes() for p in b["history"]]
