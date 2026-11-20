"""Demo Gmail tool against a fake Gmail service: labels, idempotent load, reset scope, simulator rewrite."""

import base64
import email
import sys
from email import policy
from email.message import EmailMessage
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("googleapiclient")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "system" / "data" / "mock"))
import gmail_demo as g  # noqa: E402

INBOX = "builder.demo@gmail.com"


class Req:
    def __init__(self, fn):
        self.fn = fn

    def execute(self):
        return self.fn()


class FakeGmail:
    """Just enough of the Gmail API for gmail_demo."""

    def __init__(self):
        self.labels_ = [{"id": "INBOX", "name": "INBOX"}]
        self.msgs = {}      # id -> {"raw": bytes, "labels": [...], "trashed": bool}
        self.drafts_ = {}   # id -> to header
        self.n = 0

    # users().labels() / messages() / drafts() all return self
    def users(self): return self
    def labels(self): return self
    def messages(self): return self
    def drafts(self): return self

    def list(self, userId, q=None, pageToken=None, maxResults=None):
        if q is None:  # labels().list or drafts().list
            if self._ctx == "drafts":
                return Req(lambda: {"drafts": [{"id": d} for d in self.drafts_]})
            return Req(lambda: {"labels": self.labels_})
        return Req(lambda: {"messages": [{"id": i} for i in self._match(q)]})

    def _match(self, q):
        out = []
        for i, m in self.msgs.items():
            if m["trashed"]:
                continue
            parsed = email.message_from_bytes(m["raw"], policy=policy.default)
            if q.startswith("rfc822msgid:") and parsed["Message-ID"].strip("<>") != q.split(":", 1)[1]:
                continue
            if q.startswith("label:") and g.LABEL not in [self._name(x) for x in m["labels"]]:
                continue
            if q.startswith("from:"):
                if g.LABEL in [self._name(x) for x in m["labels"]]:
                    continue
            out.append(i)
        return out

    def _name(self, lid):
        return next((lab["name"] for lab in self.labels_ if lab["id"] == lid), lid)

    def create(self, userId, body):
        lab = {"id": f"L{len(self.labels_)}", "name": body["name"]}
        self.labels_.append(lab)
        return Req(lambda: lab)

    def import_(self, userId, body, media_body, **kw):
        def run():
            self.n += 1
            mid = f"m{self.n}"
            self.msgs[mid] = {"raw": media_body.getbytes(0, media_body.size()), "labels": body["labelIds"], "trashed": False}
            return {"id": mid}
        return Req(run)

    def trash(self, userId, id):
        return Req(lambda: self.msgs[id].update(trashed=True))

    def get(self, userId, id, format=None):
        if self._ctx == "drafts":
            return Req(lambda: {"message": {"payload": {"headers": [{"name": "To", "value": self.drafts_[id]}]}}})
        return Req(lambda: {"raw": base64.urlsafe_b64encode(self.msgs[id]["raw"]).decode()})

    def delete(self, userId, id):
        return Req(lambda: self.drafts_.pop(id))

    _ctx = "messages"


@pytest.fixture()
def svc(monkeypatch):
    monkeypatch.setenv("BUILDER_INBOX", INBOX)
    fake = FakeGmail()
    orig = FakeGmail.drafts
    def drafts(self):
        self._ctx = "drafts"; return self
    def messages(self):
        self._ctx = "messages"; return self
    def labels(self):
        self._ctx = "labels"; return self
    monkeypatch.setattr(FakeGmail, "drafts", drafts)
    monkeypatch.setattr(FakeGmail, "messages", messages)
    monkeypatch.setattr(FakeGmail, "labels", labels)
    return fake


def test_load_is_idempotent_and_labels(svc):
    import datetime as dt
    assert g.load_emails(svc, g.history(), dt.date(2026, 11, 21)) == 21
    assert g.load_emails(svc, g.history(), dt.date(2026, 11, 21)) == 0
    sent = [m for m in svc.msgs.values() if "SENT" in m["labels"]]
    assert len(sent) == 4  # our own emails go to Sent, not Inbox
    first = email.message_from_bytes(next(iter(svc.msgs.values()))["raw"], policy=policy.default)
    assert INBOX in first["To"]


def test_reset_touches_only_demo_items(svc):
    import datetime as dt
    real = EmailMessage(); real["From"] = "friend@gmail.com"; real["Subject"] = "Real"; real["Message-ID"] = "<real@x>"
    real.set_content("hi")
    svc.msgs["real"] = {"raw": bytes(real), "labels": ["INBOX"], "trashed": False}
    svc.drafts_ = {"d1": "Victoria Hartley <victoria.hartley@mail.example.com>", "d2": "mum@gmail.com"}
    g.load_emails(svc, g.history(), dt.date(2026, 11, 21))
    g.reset(svc, dt.date(2026, 11, 21))
    assert svc.msgs["real"]["trashed"] is False
    assert list(svc.drafts_) == ["d2"]
    assert sum(not m["trashed"] for m in svc.msgs.values()) == 22  # real + 21 reloaded


def test_persona_from_plus_address():
    assert g.persona_from_recipient("Builder <builder.demo+council@gmail.com>", INBOX) == "council"
    assert g.persona_from_recipient("builder.demo+nobody@gmail.com", INBOX) is None
    assert g.persona_from_recipient("someone+council@gmail.com", INBOX) is None


def test_simulator_rewrites_only_allowed_senders(svc):
    def raw(sender, to, subject):
        m = EmailMessage(); m["From"] = sender; m["To"] = to; m["Subject"] = subject; m["Message-ID"] = f"<{subject}@x>"
        m.set_content("Please confirm the finish date."); m.add_attachment(b"%PDF-1.4 x", maintype="application", subtype="pdf", filename="note.pdf")
        return bytes(m)
    svc.msgs["s1"] = {"raw": raw("me@mail.com", "builder.demo+council@gmail.com", "Finish date"), "labels": ["INBOX"], "trashed": False}
    svc.msgs["s2"] = {"raw": raw("stranger@evil.com", "builder.demo+council@gmail.com", "Phish"), "labels": ["INBOX"], "trashed": False}
    assert g.simulate_once(svc, INBOX, ["me@mail.com"]) == 1
    assert svc.msgs["s1"]["trashed"] and not svc.msgs["s2"]["trashed"]
    new = [m for k, m in svc.msgs.items() if k not in ("s1", "s2")][0]
    parsed = email.message_from_bytes(new["raw"], policy=policy.default)
    assert "Hollowell Council Repairs" in parsed["From"] and parsed["Subject"] == "Finish date"
    assert next(parsed.iter_attachments()).get_filename() == "note.pdf"


def test_calendar_entries_are_marked_and_timed():
    from scenario import CALENDAR
    bodies = [g.event_body(e) for e in CALENDAR]
    assert all(b["extendedProperties"]["private"]["marcus_sample"] for b in bodies)
    assert all(b["start"]["timeZone"] == "Europe/London" and b["start"]["dateTime"] < b["end"]["dateTime"] for b in bodies)
    assert any("payment notice" in b["summary"].lower() for b in bodies)
