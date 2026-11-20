"""Titan V2 refuses inputs over 8,192 tokens; dense tables can pass the character cap. embed_text halves and retries."""

import json

import pytest

from system.rag import embed as E


class TooMany(Exception):
    pass


class FakeClient:
    def __init__(self, limit_chars):
        self.limit, self.sent = limit_chars, []

    def invoke_model(self, modelId, body):
        text = json.loads(body)["inputText"]
        self.sent.append(len(text))
        if len(text) > self.limit:
            raise TooMany("ValidationException: 400 Bad Request: Too many input tokens. Max input tokens: 8192")

        class Body:
            def read(self_inner):
                return json.dumps({"embedding": [0.0] * 4, "inputTextTokenCount": len(text) // 4})
        return {"body": Body()}


def test_too_long_input_is_halved_until_titan_accepts_it(monkeypatch):
    fake = FakeClient(limit_chars=9000)
    monkeypatch.setattr(E, "client", lambda: fake)
    vec, tokens = E.embed_text("x" * 30000)
    assert vec == [0.0] * 4 and fake.sent[-1] <= 9000 and len(fake.sent) >= 2
    assert E.TRUNCATED and E.TRUNCATED[-1][1] <= 9000


def test_other_errors_are_not_swallowed(monkeypatch):
    class Broken:
        def invoke_model(self, modelId, body):
            raise RuntimeError("throttled")
    monkeypatch.setattr(E, "client", lambda: Broken())
    with pytest.raises(RuntimeError):
        E.embed_text("short text")
