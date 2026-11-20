"""Where new emails come from. Plain code, no model (ADR 0006).

MAIL_SOURCE settings (comma-separated for several, e.g. "eml:/data/mail,gmail"):
  eml:<folder>   .eml files in a folder (demo feed; tests)
  gmail          the builder's Gmail, label `oakline-demo` only (token file in GMAIL_TOKEN_FILE).
                 With several sources, a missing or empty Gmail login is skipped, not an error.
"""

from __future__ import annotations

import base64
import json
import logging
import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from builders_api.errors import NotConfiguredError, UpstreamError
from builders_api.retry import with_retries

GMAIL_LABEL = "oakline-demo"
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawMail:
    source_id: str   # file name or Gmail id, for error messages
    raw: bytes       # RFC 822 message


class EmlFolder:
    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def fetch(self) -> Iterator[RawMail]:
        if not self.folder.is_dir():
            return
        for path in sorted(self.folder.rglob("*.eml")):
            yield RawMail(path.name, path.read_bytes())


class GmailLabel:
    """Reads only messages with the demo label. Not yet run against a real inbox (parking lot N3)."""

    def __init__(self, token_file: Path, label: str = GMAIL_LABEL) -> None:
        self.token_file = token_file
        self.label = label

    def configured(self) -> bool:
        try:
            return bool(json.loads(self.token_file.read_text()).get("refresh_token"))
        except (OSError, ValueError):
            return False

    def _service(self):
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise NotConfiguredError("Gmail libraries are not installed on the server.") from exc
        if not self.token_file.exists():
            raise NotConfiguredError("No Gmail login on the server yet.")
        creds = Credentials.from_authorized_user_file(str(self.token_file))
        if not creds.valid:
            creds.refresh(Request())
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def fetch(self) -> Iterator[RawMail]:
        svc = self._service()

        def call(req):
            try:
                return with_retries(req.execute)
            except Exception as exc:  # noqa: BLE001
                status = getattr(getattr(exc, "resp", None), "status", 0)
                raise UpstreamError("Gmail did not answer.", retryable=status in (429, 500, 502, 503, 504)) from exc

        token = None
        while True:
            resp = call(svc.users().messages().list(userId="me", q=f"label:{self.label}", pageToken=token, maxResults=100))
            for m in resp.get("messages", []):
                full = call(svc.users().messages().get(userId="me", id=m["id"], format="raw"))
                yield RawMail(m["id"], base64.urlsafe_b64decode(full["raw"]))
            token = resp.get("nextPageToken")
            if not token:
                return


class Several:
    def __init__(self, sources: list) -> None:
        self.sources = sources

    def fetch(self) -> Iterator[RawMail]:
        for src in self.sources:
            if isinstance(src, GmailLabel) and not src.configured():
                log.info("Gmail source skipped: no Gmail login on the server")
                continue
            yield from src.fetch()


def _one(setting: str):
    if setting.startswith("eml:"):
        return EmlFolder(Path(setting[4:]))
    if setting == "gmail":
        return GmailLabel(Path(os.environ.get("GMAIL_TOKEN_FILE", "/run/secrets/gmail-token.json")))
    raise NotConfiguredError(f"Unknown mail source '{setting}'.")


def from_env():
    settings = [s.strip() for s in os.environ.get("MAIL_SOURCE", "").split(",") if s.strip()]
    if not settings:
        raise NotConfiguredError("No mail source is set on the server (MAIL_SOURCE).")
    if len(settings) == 1:
        return _one(settings[0])
    return Several([_one(s) for s in settings])
