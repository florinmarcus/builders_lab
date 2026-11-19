# Goal: harvest the shared regulations corpus

Set: 19 Nov 2026. Owner: Florin. Worked on autonomously by Claude Code.

## Goal

Every document in `sources.yaml` that we may store is downloaded, hashed and recorded with its version dates. Latest versions first, then older versions where the publisher keeps them. Parsing, chunking, embeddings and search are out of scope. Evals come later and drive those choices.

## Definition of done

1. `corpus/sources.yaml` lists every document from the inventory (`research/domain/corpus-inventory/`). Each entry has a mode: `ingest` (open licence), `restricted` (prototype only, see ADR 0005) or `link_only`. The file passes the schema check in the tests.
2. `python -m system.rag.harvest` runs from start to end without crashing.
3. Every `ingest` or `restricted` source with a fetch method has at least one version record in `corpus/versions/` and a raw file in `corpus/raw/` whose SHA-256 matches the record.
4. Legislation: every point-in-time version from `history_from` (default 1 Oct 2010) to today. The `valid_from` and `valid_to` dates form an unbroken chain, and only the newest version has `valid_to: null`.
5. Running the harvester a second time adds no new records (nothing changed, so nothing new).
6. Failed fetches are retried with backoff (3 tries). Whatever still fails is listed in `corpus/harvest-report.md` with the reason. Known blocks (the National Archives web archive, Gas Safe) are recorded as gaps, not hidden.
7. `pytest tests/` passes offline: hashing, versioning, closing `valid_to`, and the schema check.
8. `python -m system.rag.upload_s3 --dry-run` lists what would go to S3 (eu-west-2). The real upload runs once AWS credentials work in the session.
9. ADR 0005, `corpus/README.md`, `.gitignore` (`corpus/raw/`) and the AGENTS.md layout are updated. No secrets anywhere in the repo.
10. Committed and pushed.

## Loop

Run the harvester, read the report, fix the cause (wrong URL, parser, rate limit), run it again. Stop when only known, recorded gaps remain.
