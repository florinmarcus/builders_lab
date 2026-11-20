"""Demo inbox tool (ADR 0005): load, reset and the live email simulator, on the builder's own Gmail.

Only touches messages with the label `marcus-limited`, demo drafts (to *.example.com), and emails from
the allowed simulator senders. Nothing else in the inbox is read or changed.

Set up once (see README.md, "Gmail set-up"):
  pip install -e ".[gmail]"
  export BUILDER_INBOX=you@gmail.com SIMULATOR_SENDERS=you@mail.com
  python system/data/mock/gmail_demo.py auth --client-secret ~/Downloads/client_secret.json

Commands:
  load              import the 17 past emails (skips ones already there)
  today [eNN ...]   import the demo-day emails (all, or the ones named)
  reset             trash all demo emails and demo drafts, then load again
  simulate          watch for emails from SIMULATOR_SENDERS to BUILDER_INBOX+<persona>, re-import them
                    as that persona, trash the original. Ctrl+C to stop.
  status            count demo emails and drafts
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import email
import hashlib
import io
import os
import re
import sys
import time
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, parseaddr
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from generate import build_email  # noqa: E402
from scenario import EMAILS, FIRM, PERSONAS  # noqa: E402

LABEL = "marcus-limited"
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = Path(os.environ.get("GMAIL_TOKEN_FILE", Path.home() / ".config" / "builders-lab" / "gmail-token.json"))
DEMO_DOMAIN = "example.com"


# ------------------------------------------------------------------ Gmail access


def gmail_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if not TOKEN_FILE.exists():
        raise SystemExit(f"No Gmail login yet. Run: python {Path(__file__).name} auth --client-secret <file>")
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        try:
            TOKEN_FILE.write_text(creds.to_json())
        except OSError:
            pass  # read-only on the server: the refreshed token lives in memory
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def auth(client_secret: Path) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())
    TOKEN_FILE.chmod(0o600)
    print(f"Logged in. Token saved to {TOKEN_FILE} (keep it private).")


def label_id(svc) -> str:
    labels = svc.users().labels().list(userId="me").execute().get("labels", [])
    for lab in labels:
        if lab["name"] == LABEL:
            return lab["id"]
    created = svc.users().labels().create(
        userId="me", body={"name": LABEL, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
    ).execute()
    return created["id"]


def _search(svc, q: str) -> list[str]:
    ids, token = [], None
    while True:
        resp = svc.users().messages().list(userId="me", q=q, pageToken=token, maxResults=100).execute()
        ids += [m["id"] for m in resp.get("messages", [])]
        token = resp.get("nextPageToken")
        if not token:
            return ids


def import_raw(svc, raw: bytes, labels: list[str]) -> str:
    from googleapiclient.http import MediaIoBaseUpload

    media = MediaIoBaseUpload(io.BytesIO(raw), mimetype="message/rfc822", resumable=False)
    resp = svc.users().messages().import_(
        userId="me", body={"labelIds": labels}, media_body=media,
        internalDateSource="dateHeader", neverMarkSpam=True, processForCalendar=False,
    ).execute()
    return resp["id"]


# ------------------------------------------------------------------ scenario emails


def _inbox() -> str:
    inbox = os.environ.get("BUILDER_INBOX", "").strip()
    if not inbox:
        raise SystemExit("Set BUILDER_INBOX to the builder's Gmail address.")
    return inbox


def scenario_raw(e: dict, today: dt.date, inbox: str) -> bytes:
    """The scenario email with the real inbox as Florin's address, so Gmail shows it as received or sent."""
    msg = build_email(e, today)
    dan = formataddr((FIRM["owner"], inbox))
    if e["from"] == "florin":
        msg.replace_header("From", dan)
    else:
        msg.replace_header("To", dan)
    return bytes(msg)


def load_emails(svc, which: list[dict], today: dt.date) -> int:
    inbox, lab, added = _inbox(), label_id(svc), 0
    for e in which:
        msgid = f"{e['id']}.mail@marcus-ltd.example.com"
        if _search(svc, f"rfc822msgid:{msgid}"):
            continue
        labels = [lab, "SENT"] if e["from"] == "florin" else [lab, "INBOX", "UNREAD"]
        import_raw(svc, scenario_raw(e, today, inbox), labels)
        added += 1
        print(f"  {e['id']}  {e['subject']}")
    return added


def history() -> list[dict]:
    return [e for e in EMAILS if not e["when"].startswith("today ")]


def todays(ids: list[str] | None = None) -> list[dict]:
    out = [e for e in EMAILS if e["when"].startswith("today ")]
    return [e for e in out if not ids or e["id"] in ids]


def demo_drafts(svc) -> list[str]:
    """Drafts addressed only to demo people (*.example.com). Real drafts are never touched."""
    found, token = [], None
    while True:
        resp = svc.users().drafts().list(userId="me", pageToken=token, maxResults=100).execute()
        for d in resp.get("drafts", []):
            full = svc.users().drafts().get(userId="me", id=d["id"], format="metadata").execute()
            headers = {h["name"].lower(): h["value"] for h in full["message"]["payload"].get("headers", [])}
            rcpts = [parseaddr(a)[1] for a in re.split(r",", headers.get("to", "") + "," + headers.get("cc", "")) if a.strip()]
            if rcpts and all(r.lower().endswith("." + DEMO_DOMAIN) or r.lower().endswith("@" + DEMO_DOMAIN) for r in rcpts):
                found.append(d["id"])
        token = resp.get("nextPageToken")
        if not token:
            return found


def reset(svc, today: dt.date) -> None:
    ids = _search(svc, f"label:{LABEL}")
    for mid in ids:
        svc.users().messages().trash(userId="me", id=mid).execute()
    drafts = demo_drafts(svc)
    for did in drafts:
        svc.users().drafts().delete(userId="me", id=did).execute()
    print(f"trashed {len(ids)} demo emails, deleted {len(drafts)} demo drafts")
    print(f"loaded {load_emails(svc, history(), today)} past emails")


# ------------------------------------------------------------------ live simulator


def persona_from_recipient(addresses: str, inbox: str) -> str | None:
    """'you+council@gmail.com' -> 'council' (only for the builder's own inbox)."""
    local, _, domain = inbox.lower().partition("@")
    for addr in re.findall(r"[\w.+-]+@[\w.-]+", addresses.lower()):
        m = re.fullmatch(rf"{re.escape(local)}\+([a-z0-9]+)@{re.escape(domain)}", addr)
        if m and m.group(1) in PERSONAS:
            return m.group(1)
    return None


def rewrite_as_persona(raw: bytes, persona: str, inbox: str, now: dt.datetime) -> bytes:
    """New message: same subject, text and attachments; From = persona; To = the builder."""
    src = email.message_from_bytes(raw, policy=policy.default)
    name, addr = PERSONAS[persona]
    msg = EmailMessage()
    msg["From"] = formataddr((name, addr))
    msg["To"] = formataddr((FIRM["owner"], inbox))
    msg["Subject"] = src.get("Subject", "")
    msg["Date"] = format_datetime(now)
    original_id = (src.get("Message-ID") or "").strip("<> ") or f"{now.timestamp()}"
    digest = hashlib.sha1(original_id.encode()).hexdigest()[:16]
    msg["Message-ID"] = f"<sim-{digest}.mail@marcus-ltd.example.com>"
    msg["X-Marcus-Mail-Id"] = f"sim-{persona}"
    body = src.get_body(preferencelist=("plain", "html"))
    msg.set_content(body.get_content() if body else "")
    for part in src.iter_attachments():
        data = part.get_content()
        maintype, subtype = part.get_content_type().split("/", 1)
        if isinstance(data, str):
            msg.add_attachment(data, subtype=subtype, filename=part.get_filename())
        else:
            msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=part.get_filename())
    return bytes(msg)


def simulate_once(svc, inbox: str, senders: list[str]) -> int:
    if not senders:
        raise SystemExit("Set SIMULATOR_SENDERS (comma-separated addresses allowed to send as personas).")
    local, _, domain = inbox.partition("@")
    q = f"from:({' OR '.join(senders)}) to:{local}+*@{domain} -label:{LABEL} newer_than:1d"
    lab, done = label_id(svc), 0
    for mid in _search(svc, q):
        full = svc.users().messages().get(userId="me", id=mid, format="raw").execute()
        raw = base64.urlsafe_b64decode(full["raw"])
        src = email.message_from_bytes(raw, policy=policy.default)
        sender = parseaddr(src.get("From", ""))[1].lower()
        persona = persona_from_recipient(" ".join(filter(None, [src.get("To", ""), src.get("Delivered-To", ""),
                                                                src.get("Cc", "")])), inbox)
        if sender not in [s.lower() for s in senders] or not persona:
            continue  # not ours: leave it alone
        import_raw(svc, rewrite_as_persona(raw, persona, inbox, dt.datetime.now(dt.timezone.utc)),
                   [lab, "INBOX", "UNREAD"])
        svc.users().messages().trash(userId="me", id=mid).execute()
        done += 1
        print(f"  {dt.datetime.now():%H:%M:%S}  now from {PERSONAS[persona][0]}: {src.get('Subject', '')}")
    return done


def simulate(svc, every: int = 10) -> None:
    inbox = _inbox()
    senders = [s.strip() for s in os.environ.get("SIMULATOR_SENDERS", "").split(",") if s.strip()]
    local, _, domain = inbox.partition("@")
    print("Simulator running. Send to one of:")
    for alias, (name, _) in PERSONAS.items():
        if alias != "florin":
            print(f"  {local}+{alias}@{domain:<20}  -> {name}")
    while True:
        try:
            simulate_once(svc, inbox, senders)
        except Exception as exc:  # noqa: BLE001 - keep running on network blips
            print(f"  (retrying after error: {type(exc).__name__})")
        time.sleep(every)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="gmail_demo")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("auth")
    a.add_argument("--client-secret", type=Path, required=True)
    sub.add_parser("load")
    t = sub.add_parser("today")
    t.add_argument("ids", nargs="*")
    sub.add_parser("reset")
    s = sub.add_parser("simulate")
    s.add_argument("--every", type=int, default=10)
    sub.add_parser("status")
    args = p.parse_args(argv)
    today = dt.date.today()

    if args.cmd == "auth":
        return auth(args.client_secret)
    svc = gmail_service()
    if args.cmd == "load":
        print(f"loaded {load_emails(svc, history(), today)} past emails")
    elif args.cmd == "today":
        print(f"sent {load_emails(svc, todays(args.ids), today)} demo-day emails")
    elif args.cmd == "reset":
        reset(svc, today)
    elif args.cmd == "simulate":
        simulate(svc, args.every)
    elif args.cmd == "status":
        print(f"demo emails: {len(_search(svc, f'label:{LABEL}'))}, demo drafts: {len(demo_drafts(svc))}")


if __name__ == "__main__":
    main()
