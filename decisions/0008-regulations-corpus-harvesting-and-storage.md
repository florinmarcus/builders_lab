# 0008: Regulations corpus: versioned harvesting, raw files in S3, restricted documents for the prototype

Date: 19 Nov 2026. Status: accepted.
Changed by: 0016 (only versions in force from 1 January 2025).

## Context

ADR 0004 puts shared rules and guidance in one store. Users need the current text, and sometimes the text that applied when a job started, because old editions keep applying for a transition period. We checked which documents we need and their licences (`research/domain/corpus-inventory/`). Most are under the Open Government Licence (OGL). Standards, warranty manuals and contracts are copyrighted, and their website terms forbid storing even their contents pages in a database or AI system. Florin decided that a private prototype may hold a few legally free copies of such documents (free previews and free downloads), to test the technology with friendly builders.

## Decision

- **Catalogue in git, files outside git.** `corpus/sources.yaml` lists every document. `corpus/versions/` holds one small JSON record per fetched version (hash, dates, S3 key). Raw files (PDF, HTML, XML) are never committed: `corpus/raw/` locally and a private S3 bucket in London (eu-west-2). The bucket name and credentials are never written to the repo.
- **Three modes.** `ingest`: OGL, store and quote with attribution. `restricted`: copyrighted but legally free copies, prototype only, private storage only, deleted before any commercial use. `link_only`: number, title, edition, date and link, written in our own words; no text and no contents pages.
- **Keep every version.** Files are named by SHA-256, so nothing is overwritten. A new hash for the same document closes the old record's `valid_to`. That is the only change to an old record.
- **How far back.** *Changed 22 Nov 2026 by ADR 0016: search and checking keep only versions in force at any time from 1 January 2025 (with the editions in force on that day); older raw files stay in S3.* Originally: Legislation: every point-in-time version from 1 Oct 2010 (start of the Building Regulations 2010), plus the version in force on that date. GOV.UK and HSE: the current edition from now on. Older editions only where the publisher keeps them (AD B back to 2006; AD L and F 2021 beside 2026). The National Archives web archive blocks automated downloads: a later manual step if evals show we need older editions.
- **Harvesting only for now.** Parsing, chunking, embeddings and search come after the evals, which will decide reranking and hybrid search.

## Options considered

- Commit raw files to git: simple, but large binary files, and wrong for restricted documents even in a private repo.
- Link only for every copyrighted document: safest, but the prototype could not show how the system handles them.
- Store contents pages of standards: their terms forbid it (BSI, JCT, NEC). Rejected.
- Fetch old editions from the National Archives web archive now: blocked for bots; manual work with unclear value before evals.

## Consequences

- The repo should be private while restricted documents are in use. Restricted records carry `mode: restricted`, so they can be found and removed in one step.
- Get legal advice before any commercial use, and before ingesting AD A and AD C in full (their PDFs still carry the old Click-Use licence wording).
- S3 upload needs working AWS credentials in the session. Until then, raw files exist only on the harvesting machine.
- Re-running the harvester is safe and finds changes by hash. A weekly run would catch new editions.

## Update, 20 Nov 2026: two fingerprints

Every record has two hashes. `sha256` is the exact file: it checks downloads and S3 copies. `content_hash` is the content and decides whether a file is a new version, so noise does not fire false updates.

- Legislation: a new version is a new point-in-time date. Fetching a known date again never makes a new version.
- HTML: the visible text only.
- XML (new from 20 Nov 2026): canonical XML without the legislation metadata block, so attribute order and metadata dates do not count. Older records keep their old `content_hash` (the file's hash); all of them are legislation, decided by date, so nothing fires.
- PDF and other files: still the exact bytes. A text fingerprint for PDFs comes with the parser.

Why: re-fetching on 20 Nov 2026 gave different bytes for 17 files (16 the same size, legislation metadata in no fixed order). They are left out for now; see `corpus/README.md`.
