"""Versioned texts: prompts, MCP server instructions, tool descriptions.

Files are named `<name>.v<N>.md` under `prompts/`, `server/` or `tools/`. The highest N is active.
Never edit a file once committed: add the next version. `versions.lock.json` holds each file's hash;
tests fail and the server refuses to start if a locked file changed.

Lock new files: python -m builders_api.versions --lock
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

ROOT = Path(__file__).parent
LOCK_FILE = ROOT / "versions.lock.json"
KINDS = {"prompts": "prompt", "server": "server_instructions", "tools": "tool_description"}
_NAME = re.compile(r"^(?P<name>[a-z0-9_]+)\.v(?P<n>\d+)\.md$")


class VersionEditedError(RuntimeError):
    """A locked version file changed. Add a new version instead of editing."""


@dataclass(frozen=True)
class Version:
    id: str  # e.g. tools/list_jobs.v1
    kind: str
    name: str
    number: int
    text: str
    sha256: str


def _scan() -> list[Version]:
    out = []
    for folder, kind in KINDS.items():
        for path in sorted((ROOT / folder).glob("*.md")):
            m = _NAME.match(path.name)
            if not m:
                continue
            text = path.read_text()
            out.append(
                Version(
                    id=f"{folder}/{path.name[:-3]}",
                    kind=kind,
                    name=m["name"],
                    number=int(m["n"]),
                    text=text.strip(),
                    sha256=hashlib.sha256(text.encode()).hexdigest(),
                )
            )
    return out


def _lock() -> dict[str, str]:
    return json.loads(LOCK_FILE.read_text()) if LOCK_FILE.exists() else {}


def check_lock() -> list[str]:
    """Return problems: edited locked files, or files missing from the lock."""
    lock, problems = _lock(), []
    for v in _scan():
        if v.id not in lock:
            problems.append(f"{v.id}: not locked (run python -m builders_api.versions --lock)")
        elif lock[v.id] != v.sha256:
            problems.append(f"{v.id}: edited after locking; add a new version instead")
    return problems


@cache
def active() -> dict[tuple[str, str], Version]:
    """Highest version per (kind, name). Raises if any locked file was edited."""
    edited = [p for p in check_lock() if "edited" in p]
    if edited:
        raise VersionEditedError("; ".join(edited))
    best: dict[tuple[str, str], Version] = {}
    for v in _scan():
        key = (v.kind, v.name)
        if key not in best or v.number > best[key].number:
            best[key] = v
    return best


def get(kind: str, name: str) -> Version:
    return active()[(kind, name)]


def register(conn) -> None:
    """Write all versions into the versions table. Same id with a different hash is refused."""
    for v in _scan():
        row = conn.execute("select sha256 from versions where id = %s", (v.id,)).fetchone()
        if row is None:
            conn.execute(
                "insert into versions (id, kind, name, sha256) values (%s, %s, %s, %s)",
                (v.id, v.kind, v.name, v.sha256),
            )
        elif (row["sha256"] if isinstance(row, dict) else row[0]) != v.sha256:
            raise VersionEditedError(f"{v.id} differs from the copy registered in the database")


def lock_new() -> list[str]:
    lock = _lock()
    added = [v.id for v in _scan() if v.id not in lock]
    for v in _scan():
        lock.setdefault(v.id, v.sha256)
    LOCK_FILE.write_text(json.dumps(dict(sorted(lock.items())), indent=2) + "\n")
    return added

