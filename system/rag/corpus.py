"""Corpus catalogue and version store.

sources.yaml lists the documents. Each fetched version gets a small JSON record
in corpus/versions/ and a raw file in corpus/raw/ named by its hash. Records are
never rewritten, except to close valid_to when a newer version arrives.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "corpus"

MODES = {"ingest", "restricted", "link_only"}
METHODS = {"legislation", "govuk", "url", "none"}
LICENCES = {"OGL-3.0", "proprietary", "unclear"}
REQUIRED = ["id", "title", "publisher", "url", "kind", "licence", "mode", "priority", "why", "checked", "fetch"]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
BASES = {"point_in_time", "in_force", "published", "first_seen"}

EXT_BY_TYPE = {
    "application/pdf": "pdf",
    "application/xml": "xml",
    "text/xml": "xml",
    "text/html": "html",
    "application/xhtml+xml": "html",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
    "application/vnd.oasis.opendocument.text": "odt",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


LEG_META_NS = "http://www.legislation.gov.uk/namespaces/metadata"


def content_hash(data: bytes, media_type: str) -> str:
    """Hash used to detect real changes. For HTML it hashes the visible text only,
    so random ids, tokens and markup changes do not count as a new version. For XML
    it hashes canonical XML without legislation metadata, so attribute order and
    metadata updates do not count either. Other files: the exact bytes."""
    if media_type.split(";")[0].strip().lower() in ("text/html", "application/xhtml+xml"):
        try:
            import lxml.html

            doc = lxml.html.fromstring(data)
            for bad in doc.xpath("//script|//style|//noscript"):
                bad.drop_tree()
            text = " ".join(doc.text_content().split())
            return hashlib.sha256(text.encode("utf-8")).hexdigest()
        except Exception:  # unparsable HTML: fall back to the bytes
            pass
    if media_type.split(";")[0].strip().lower() in ("application/xml", "text/xml"):
        try:
            from lxml import etree

            root = etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))
            # legislation.gov.uk metadata (modified dates, unapplied effects) changes without
            # the law text changing, and its attributes come in no fixed order. Drop it.
            for meta in root.findall(f".//{{{LEG_META_NS}}}Metadata"):
                meta.getparent().remove(meta)
            # Canonical XML (C14N) writes attributes in a fixed order.
            return sha256(etree.tostring(root, method="c14n"))
        except Exception:  # unparsable XML: fall back to the bytes
            pass
    return sha256(data)


def slugify(text: str, max_len: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:max_len].rstrip("-") or "main"


def part_key(title: str) -> str:
    """Stable part name from an attachment title. Drops edition text such as
    "2019 edition incorporating 2020 amendments" so a new edition becomes a new
    version of the same part. Years elsewhere (e.g. "2026 amendments to ...")
    are kept, because those are different documents."""
    t = re.sub(r"\([^)]*\bedition\b[^)]*\)", " ", title, flags=re.I)
    t = re.sub(r",?\s*\b(19|20)\d\d\s+edition\b.*$", " ", t, flags=re.I)
    t = re.sub(r"\((no longer current|revised|updated)[^)]*\)", " ", t, flags=re.I)
    return slugify(t)


def ext_for(media_type: str) -> str:
    return EXT_BY_TYPE.get(media_type.split(";")[0].strip().lower(), "bin")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------- catalogue


def load_sources(path: Path | None = None) -> dict:
    path = path or CORPUS_DIR / "sources.yaml"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_sources(doc: dict) -> list[str]:
    """Return a list of problems. Empty list means the file is valid."""
    errors: list[str] = []
    sources = doc.get("sources")
    if not isinstance(sources, list) or not sources:
        return ["no 'sources' list"]
    seen: set[str] = set()
    for i, s in enumerate(sources):
        sid = s.get("id", f"#{i}")
        for key in REQUIRED:
            if key not in s or s[key] in (None, ""):
                errors.append(f"{sid}: missing {key}")
        if not ID_RE.match(str(sid)):
            errors.append(f"{sid}: bad id")
        if sid in seen:
            errors.append(f"{sid}: duplicate id")
        seen.add(sid)
        if s.get("mode") not in MODES:
            errors.append(f"{sid}: bad mode {s.get('mode')}")
        if s.get("licence") not in LICENCES:
            errors.append(f"{sid}: bad licence {s.get('licence')}")
        fetch = s.get("fetch") or {}
        method = fetch.get("method")
        if method not in METHODS:
            errors.append(f"{sid}: bad fetch.method {method}")
        if s.get("mode") == "link_only" and method != "none":
            errors.append(f"{sid}: link_only must not be fetched")
        if s.get("mode") == "ingest" and s.get("licence") != "OGL-3.0":
            errors.append(f"{sid}: ingest needs OGL-3.0")
        if method == "legislation" and not fetch.get("path"):
            errors.append(f"{sid}: legislation needs fetch.path")
        if method == "legislation" and fetch.get("history", "current") not in {"all", "current", "made"}:
            errors.append(f"{sid}: bad fetch.history")
        if method == "govuk" and not str(fetch.get("page", "")).startswith("/"):
            errors.append(f"{sid}: govuk needs fetch.page starting with /")
        if method == "url" and not str(fetch.get("url", s.get("url", ""))).startswith("http"):
            errors.append(f"{sid}: url method needs a URL")
    return errors


# ---------------------------------------------------------------- versions


@dataclass
class Fetched:
    """One file as fetched, before it is stored."""

    part: str
    part_title: str
    content: bytes
    media_type: str
    fetched_url: str
    edition_date: str | None
    valid_from: str
    valid_from_basis: str
    # Legislation history is fixed per date: skip if this date is already stored.
    dedupe_on_date: bool = False


def chain_order(r: dict) -> tuple:
    """Sort versions oldest first. On the same start date, closed versions come first."""
    return (r["valid_from"], r.get("valid_to") is None, r.get("valid_to") or "", r["fetched_at"])


class Store:
    def __init__(self, corpus_dir: Path | None = None):
        self.corpus_dir = corpus_dir or CORPUS_DIR
        self.versions_dir = self.corpus_dir / "versions"
        self.raw_dir = self.corpus_dir / "raw"
        # raw_path in records is relative to the repo root, e.g. corpus/raw/...
        self.rel_base = self.corpus_dir.parent
        # Raw files written again for records whose file was missing (this run).
        self.restored: list[str] = []
        # Records whose file is missing, where the source now gives different bytes.
        self.mismatched: list[str] = []

    def _source_dir(self, source_id: str) -> Path:
        return self.versions_dir / source_id

    def records(self, source_id: str, part: str | None = None) -> list[dict]:
        d = self._source_dir(source_id)
        if not d.exists():
            return []
        out = []
        for p in sorted(d.glob("*.json")):
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec["_file"] = p
            if part is None or rec["part"] == part:
                out.append(rec)
        out.sort(key=chain_order)
        return out

    def has_date(self, source_id: str, part: str, edition_date: str) -> bool:
        return any(r.get("edition_date") == edition_date for r in self.records(source_id, part))

    def _raw_exists(self, rec: dict) -> bool:
        return (self.rel_base / rec["raw_path"]).exists()

    def needs_date(self, source_id: str, part: str, edition_date: str) -> bool:
        """True if this dated version is not stored, or its raw file is missing."""
        recs = [r for r in self.records(source_id, part) if r.get("edition_date") == edition_date]
        return not recs or not all(self._raw_exists(r) for r in recs)

    def _restore(self, existing: list[dict], f: Fetched, digest: str, chash: str) -> bool:
        """Write back a missing raw file if the fetched bytes match a record exactly.

        Returns True if the fetch was handled here (restored or listed as a mismatch).
        """
        same = [r for r in existing if r["sha256"] == digest]
        if same:
            for r in same:
                if not self._raw_exists(r):
                    raw = self.rel_base / r["raw_path"]
                    raw.parent.mkdir(parents=True, exist_ok=True)
                    raw.write_bytes(f.content)
                    self.restored.append(r["raw_path"])
            return True
        # Same version by date or by content, but different bytes: never overwrite a record.
        like = [r for r in existing
                if (f.dedupe_on_date and f.edition_date and r.get("edition_date") == f.edition_date)
                or (not f.dedupe_on_date and chash == r.get("content_hash"))]
        missing = [r for r in like if not self._raw_exists(r)]
        for r in missing:
            self.mismatched.append(r["raw_path"])
        return bool(missing)

    def _write(self, rec: dict) -> None:
        path = rec.pop("_file", None) or (self._source_dir(rec["source_id"]) / f"{rec['version_id']}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def add(self, source: dict, f: Fetched) -> dict | None:
        """Store a fetched file. Return the new record, or None if nothing changed."""
        sid = source["id"]
        existing = self.records(sid, f.part)
        digest = sha256(f.content)
        chash = content_hash(f.content, f.media_type)
        if self._restore(existing, f, digest, chash):
            return None

        if f.dedupe_on_date and f.edition_date and any(r.get("edition_date") == f.edition_date for r in existing):
            return None
        if not f.dedupe_on_date:
            current = [r for r in existing if r.get("valid_to") is None]
            latest = current[-1] if current else (existing[-1] if existing else None)
            if latest and chash in (latest.get("content_hash"), latest["sha256"]):
                return None
            # The same content seen before under an older version: nothing new.
            if any(chash in (r.get("content_hash"), r["sha256"]) for r in existing):
                return None

        valid_from = f.valid_from
        # A new version of a changing document cannot start before the one it replaces.
        if not f.dedupe_on_date and existing:
            last_from = existing[-1]["valid_from"]
            if valid_from <= last_from:
                valid_from = max(date.today().isoformat(), last_from)
                f.valid_from_basis = "first_seen"

        ext = ext_for(f.media_type)
        raw = self.raw_dir / sid / f.part / f"{digest[:16]}.{ext}"
        raw.parent.mkdir(parents=True, exist_ok=True)
        if not raw.exists():
            raw.write_bytes(f.content)
        rel = raw.relative_to(self.rel_base).as_posix()

        later = [r for r in existing if r["valid_from"] > valid_from]
        valid_to = later[0]["valid_from"] if later else None

        label = f.edition_date or valid_from
        version_id = f"{f.part}@{label}-{digest[:8]}"
        rec = {
            "source_id": sid,
            "part": f.part,
            "part_title": f.part_title,
            "version_id": version_id,
            "edition_date": f.edition_date,
            "valid_from": valid_from,
            "valid_from_basis": f.valid_from_basis,
            "valid_to": valid_to,
            "fetched_at": now_utc(),
            "fetched_url": f.fetched_url,
            "sha256": digest,
            "content_hash": chash,
            "bytes": len(f.content),
            "media_type": f.media_type.split(";")[0].strip(),
            "raw_path": rel,
            "s3_key": rel,
            "mode": source["mode"],
            "licence": source["licence"],
        }
        self._write(rec)

        # Close the version this one follows. That is the only edit to an old record.
        # A version replaced on the day it started gets an empty range [d, d).
        earlier = [r for r in existing if r["valid_from"] < valid_from
                   or (not f.dedupe_on_date and r["valid_from"] == valid_from)]
        if earlier:
            prev = next((r for r in reversed(earlier) if r.get("valid_to") is None), earlier[-1])
            if prev.get("valid_to") is None or prev["valid_to"] > valid_from:
                prev["valid_to"] = valid_from
                self._write(prev)
        return rec


def check_chain(records: list[dict]) -> list[str]:
    """Check one part's records form an unbroken chain. Return problems."""
    problems = []
    recs = sorted(records, key=chain_order)
    for a, b in zip(recs, recs[1:]):
        if a.get("valid_to") != b["valid_from"]:
            problems.append(f"{a['version_id']} valid_to {a.get('valid_to')} != next valid_from {b['valid_from']}")
    if recs and recs[-1].get("valid_to") is not None:
        problems.append(f"{recs[-1]['version_id']}: newest version is closed")
    return problems
