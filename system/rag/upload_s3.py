"""Copy raw corpus files to S3 (private bucket, London, eu-west-2).

    python -m system.rag.upload_s3 --dry-run
    CORPUS_BUCKET=<bucket> python -m system.rag.upload_s3
    CORPUS_BUCKET=<bucket> python -m system.rag.upload_s3 --download   # fill corpus/raw from S3

The bucket name comes from the CORPUS_BUCKET environment variable and is never
written to the repo. Files are stored under their record's s3_key with
server-side encryption. Files already in the bucket are skipped.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from system.rag.corpus import CORPUS_DIR

REGION = "eu-west-2"


def records() -> list[dict]:
    out = []
    for p in sorted((CORPUS_DIR / "versions").glob("*/*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="list what would be uploaded")
    ap.add_argument("--download", action="store_true", help="download missing raw files from S3 and check their hashes")
    a = ap.parse_args(argv)
    if a.download:
        return download()

    recs = records()
    root = CORPUS_DIR.parent
    missing = [r for r in recs if not (root / r["raw_path"]).exists()]
    todo = [r for r in recs if (root / r["raw_path"]).exists()]
    size = sum(r["bytes"] for r in todo)
    print(f"{len(recs)} records, {len(todo)} raw files present ({size / 1e6:.1f} MB), {len(missing)} missing locally")

    if a.dry_run:
        for r in todo[:20]:
            print(f"  would upload {r['raw_path']} -> s3://$CORPUS_BUCKET/{r['s3_key']}")
        if len(todo) > 20:
            print(f"  ... and {len(todo) - 20} more")
        return 0

    bucket = os.environ.get("CORPUS_BUCKET")
    if not bucket:
        print("Set CORPUS_BUCKET to the bucket name.")
        return 2
    import boto3  # only needed for a real upload

    s3 = boto3.client("s3", region_name=REGION)
    uploaded = skipped = 0
    for r in todo:
        key = r["s3_key"]
        try:
            s3.head_object(Bucket=bucket, Key=key)
            skipped += 1
            continue
        except s3.exceptions.ClientError:
            pass
        s3.upload_file(
            str(root / r["raw_path"]), bucket, key,
            ExtraArgs={
                "ServerSideEncryption": "AES256",
                "ContentType": r["media_type"],
                "Metadata": {"sha256": r["sha256"], "source-id": r["source_id"], "mode": r["mode"]},
            },
        )
        uploaded += 1
    print(f"uploaded {uploaded}, already there {skipped}")
    return 0


def download() -> int:
    """Fetch raw files that are missing locally, and check each SHA-256 against its record."""
    bucket = os.environ.get("CORPUS_BUCKET")
    if not bucket:
        print("Set CORPUS_BUCKET to the bucket name.")
        return 2
    import hashlib

    import boto3

    s3 = boto3.client("s3", region_name=REGION)
    root = CORPUS_DIR.parent
    got = have = bad = missing = 0
    for r in records():
        path = root / r["raw_path"]
        if path.exists():
            have += 1
            continue
        try:
            body = s3.get_object(Bucket=bucket, Key=r["s3_key"])["Body"].read()
        except s3.exceptions.NoSuchKey:
            missing += 1
            print(f"  not in S3: {r['s3_key']}")
            continue
        if hashlib.sha256(body).hexdigest() != r["sha256"]:
            bad += 1
            print(f"  hash mismatch, not saved: {r['s3_key']}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        got += 1
    print(f"downloaded {got}, already here {have}, not in S3 {missing}, hash mismatch {bad}")
    return 0 if not (bad or missing) else 1


if __name__ == "__main__":
    sys.exit(main())
