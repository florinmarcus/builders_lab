"""Embed corpus chunks with Amazon Titan Text Embeddings V2 (ADR 0013).

    python -m system.rag.embed                 # every corpus/chunks/*/*.jsonl
    python -m system.rag.embed --source adb    # one source

For each chunk file corpus/chunks/<source>/<version>.jsonl it writes corpus/vectors/<source>/<version>.npy
(float32, one row per chunk, 1,024 numbers, normalised) and <version>.ids.json (chunk id and a fingerprint of
the embedded text, row by row). Not in git: rebuilt from the chunks. A re-run only embeds chunks whose text
changed, so it costs nothing when nothing changed. The text embedded is embed_text (breadcrumb + text).

Settings (environment): RAG_EMBED_REGION (default eu-west-2, London), RAG_EMBED_MODEL
(default amazon.titan-embed-text-v2:0), RAG_EMBED_WORKERS (default 8).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from system.rag.corpus import CORPUS_DIR

ROOT = CORPUS_DIR.parent
DIMS = 1024
MAX_CHARS = 40_000  # Titan V2 takes up to 50,000 characters; our longest chunk is about 8,000


def settings() -> dict:
    return {"region": os.environ.get("RAG_EMBED_REGION", "eu-west-2"),
            "model": os.environ.get("RAG_EMBED_MODEL", "amazon.titan-embed-text-v2:0"),
            "workers": int(os.environ.get("RAG_EMBED_WORKERS", "8"))}


def fingerprint(text: str, model: str) -> str:
    return hashlib.sha256(f"{model}\n{DIMS}\n{text}".encode("utf-8")).hexdigest()[:16]


_client = None


def client():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config

        _client = boto3.client("bedrock-runtime", region_name=settings()["region"],
                               config=Config(retries={"max_attempts": 10, "mode": "adaptive"}))
    return _client


TRUNCATED: list[tuple[int, int]] = []  # (original length, length sent) for inputs over Titan's token limit


def embed_text(text: str) -> tuple[list[float], int]:
    """One Titan call. Returns the normalised vector and the token count Bedrock reports.

    Titan V2 refuses more than 8,192 tokens; dense tables can pass the character cap, so on that error the
    text is halved and sent again (recorded in TRUNCATED; the chunk check in S3 should split such chunks)."""
    send = text[:MAX_CHARS]
    while True:
        body = json.dumps({"inputText": send, "dimensions": DIMS, "normalize": True})
        try:
            r = client().invoke_model(modelId=settings()["model"], body=body)
        except Exception as e:  # botocore ValidationException: "Too many input tokens"
            if "too many input tokens" in str(e).lower() and len(send) > 1000:
                send = send[: len(send) // 2]
                continue
            raise
        if len(send) < len(text):
            TRUNCATED.append((len(text), len(send)))
        out = json.loads(r["body"].read())
        return out["embedding"], out.get("inputTextTokenCount", 0)


def vector_paths(chunk_file: Path) -> tuple[Path, Path]:
    rel = chunk_file.relative_to(CORPUS_DIR / "chunks")
    base = CORPUS_DIR / "vectors" / rel.parent / rel.stem
    return base.with_suffix(".npy"), base.with_suffix(".ids.json")


def embed_file(chunk_file: Path, embed=embed_text) -> dict:
    """Embed one chunk file, reusing vectors whose text has not changed. Returns counts."""
    import numpy as np

    model = settings()["model"]
    chunks = [json.loads(l) for l in chunk_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    npy, ids_path = vector_paths(chunk_file)
    old: dict[str, list[float]] = {}
    if npy.exists() and ids_path.exists():
        prev = json.loads(ids_path.read_text(encoding="utf-8"))
        mat = np.load(npy)
        old = {p["fp"]: mat[i] for i, p in enumerate(prev)}
    fps = [fingerprint(c["embed_text"], model) for c in chunks]
    todo = [i for i, fp in enumerate(fps) if fp not in old]
    results: dict[int, list[float]] = {}
    tokens = 0
    with ThreadPoolExecutor(max_workers=settings()["workers"]) as pool:
        for i, (vec, n) in zip(todo, pool.map(lambda i: embed(chunks[i]["embed_text"]), todo)):
            results[i] = vec
            tokens += n
    mat = np.zeros((len(chunks), DIMS), dtype=np.float32)
    for i, fp in enumerate(fps):
        mat[i] = results[i] if i in results else old[fp]
    npy.parent.mkdir(parents=True, exist_ok=True)
    np.save(npy, mat)
    ids_path.write_text(json.dumps([{"id": c["id"], "fp": fp} for c, fp in zip(chunks, fps)]), encoding="utf-8")
    return {"chunks": len(chunks), "embedded": len(todo), "reused": len(chunks) - len(todo), "tokens": tokens}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", nargs="*")
    a = ap.parse_args(argv)
    total = {"chunks": 0, "embedded": 0, "reused": 0, "tokens": 0}
    start = time.time()
    for f in sorted((CORPUS_DIR / "chunks").glob("*/*.jsonl")):
        if a.source and f.parent.name not in a.source:
            continue
        r = embed_file(f)
        for k in total:
            total[k] += r[k]
        print(f"{f.relative_to(ROOT)}: {r['embedded']} embedded, {r['reused']} reused, {r['tokens']} tokens")
    print(f"total: {total['chunks']} chunks, {total['embedded']} embedded, {total['tokens']} tokens, "
          f"about ${total['tokens'] / 1000 * 0.0001:.3f} at the London price checked 20 Nov 2026 "
          f"({time.time() - start:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
