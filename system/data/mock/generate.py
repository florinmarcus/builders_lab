"""Build the demo emails as .eml files (with PDF and text attachments) from scenario.py.

Usage (from the repo root):
  python system/data/mock/generate.py [--out system/data/mock/out] [--today 2026-11-21]

Output: out/history/eNN.eml (past emails) and out/today/eNN.eml (sent on demo day).
Every email carries `X-Marcus-Mail-Id: eNN` so loading is idempotent, and a stable Message-ID.
Re-running gives the same files (except today's dates).
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import sys
from email.message import EmailMessage
from email.utils import format_datetime, formataddr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from scenario import ATTACHMENTS, EMAILS, FIRM, PERSONAS  # noqa: E402

LONDON = dt.timezone(dt.timedelta(hours=0))  # GMT in late November


def render_pdf(spec: dict) -> bytes:
    """A plain one-page PDF: title, paragraphs, optional table, mock-data footer."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=spec["title"], author="Builders Lab mock data",
                            creator="builders_lab generate.py", invariant=1)  # invariant: same bytes every run
    styles = getSampleStyleSheet()
    story = [Paragraph(spec["title"], styles["Title"]), Spacer(1, 8)]
    for para in spec.get("paras", []):
        story += [Paragraph(para, styles["BodyText"]), Spacer(1, 6)]
    if spec.get("table"):
        table = Table(spec["table"], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        story += [Spacer(1, 6), table]
    story += [Spacer(1, 18), Paragraph("Mock document for a demo. All names, firms and figures are invented.",
                                       styles["Italic"])]
    doc.build(story)
    return buf.getvalue()


def _when(value: str, today: dt.date) -> dt.datetime:
    if value.startswith("today "):
        hh, mm = map(int, value.split()[1].split(":"))
        return dt.datetime.combine(today, dt.time(hh, mm), tzinfo=LONDON)
    return dt.datetime.fromisoformat(value)


def build_email(e: dict, today: dt.date) -> EmailMessage:
    sender_name, sender_addr = PERSONAS[e["from"]]
    to_name, to_addr = PERSONAS[e["to"]] if e.get("to") else (FIRM["owner"], FIRM["address"])
    msg = EmailMessage()
    msg["From"] = formataddr((sender_name, sender_addr))
    msg["To"] = formataddr((to_name, to_addr))
    msg["Subject"] = e["subject"]
    msg["Date"] = format_datetime(_when(e["when"], today))
    msg["Message-ID"] = f"<{e['id']}.mail@marcus-ltd.example.com>"
    msg["X-Marcus-Mail-Id"] = e["id"]
    msg.set_content(e["body"] + "\n")
    for key in e.get("attach", []):
        spec = ATTACHMENTS[key]
        if spec["kind"] == "pdf":
            msg.add_attachment(render_pdf(spec), maintype="application", subtype="pdf", filename=spec["filename"])
        else:
            msg.add_attachment(spec["text"], subtype="plain", filename=spec["filename"])
    if msg.is_multipart():
        msg.set_boundary(f"==marcus-limited-{e['id']}==")  # fixed boundary: same bytes every run
    return msg


def generate(out: Path, today: dt.date) -> dict[str, list[Path]]:
    written: dict[str, list[Path]] = {"history": [], "today": []}
    for group in written:
        (out / group).mkdir(parents=True, exist_ok=True)
        for old in (out / group).glob("*.eml"):
            old.unlink()
    for e in EMAILS:
        group = "today" if e["when"].startswith("today ") else "history"
        path = out / group / f"{e['id']}.eml"
        path.write_bytes(bytes(build_email(e, today)))
        written[group].append(path)
    return written


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path(__file__).parent / "out")
    p.add_argument("--today", type=dt.date.fromisoformat, default=dt.date.today())
    a = p.parse_args()
    written = generate(a.out, a.today)
    print(f"history: {len(written['history'])} emails, today: {len(written['today'])} emails -> {a.out}")


if __name__ == "__main__":
    main()
