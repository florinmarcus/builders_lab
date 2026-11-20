# corpus/

The shared regulations corpus: public rules and guidance that every customer uses. This folder holds only lists and version records. Raw files (PDF, HTML, XML) are never committed. They live in `corpus/raw/` (git-ignored) and in a private S3 bucket in eu-west-2 (ADR 0008).

- `GOAL.md`: the harvesting goal and definition of done.
- `sources.yaml`: one entry per document.
- `versions/<source_id>/<version_id>.json`: one record per fetched version.
- `harvest-report.md`: what the last run fetched, what failed and why.
- Inventory and licence research: `research/domain/corpus-inventory/`.

Code: `system/rag/harvest.py` (fetch and record), `system/rag/upload_s3.py` (copy raw files to S3). Run from the repo root: `python -m system.rag.harvest [--only ID ...]`. Parse legislation into document trees (`corpus/parsed/`, not in git): `python -m system.rag.parse_legislation --source br2010 --current [--since YYYY-MM-DD]` (ADR 0010; Schedules not yet).

On a new machine, `corpus/raw/` is empty. Get the files with `CORPUS_BUCKET=<bucket> python -m system.rag.upload_s3 --download`. If S3 lacks them, run the harvester: when a record exists but its file is missing, it fetches the file again and saves it only if the SHA-256 matches the record. Files whose source now gives different bytes are listed as mismatches and not saved. Two old GOV.UK versions cannot be fetched again this way, because GOV.UK only serves the current file.

## sources.yaml

```yaml
- id: br2010                      # lowercase, letters, digits and hyphens. Never reused
  title: The Building Regulations 2010 (SI 2010/2214)
  publisher: legislation.gov.uk (The National Archives)
  url: https://www.legislation.gov.uk/uksi/2010/2214/contents   # page a person would open
  kind: legislation               # legislation | approved-document | guidance | hse-guidance | tax-guidance | standard | contract
  nation: england-wales           # england | england-wales | gb | uk
  licence: OGL-3.0                # OGL-3.0 | proprietary | unclear
  mode: ingest                    # ingest | restricted | link_only
  priority: 1                     # 1 must have, 2 useful, 3 nice to have
  topics: [building-regs]
  why: Legal duties behind every Approved Document.
  in_force: 2010-10-01            # optional: in-force date of the current edition
  status: current                 # current | out-of-date | withdrawn | coming
  notes: ...                      # optional
  checked: 2026-11-19
  fetch:
    method: legislation           # legislation | govuk | url | none
    path: uksi/2010/2214
    history: all                  # all | current | made
```

Fetch methods:

- `legislation`: legislation.gov.uk. `path` like `uksi/2010/2214` or `ukpga/2022/30`. `history: all` takes every point-in-time version from `history_from` (default 2010-10-01). `current` takes today's version only. `made` takes the original version only, for amending instruments.
- `govuk`: a GOV.UK page, read through the Content API. `page` is the path, e.g. `/government/publications/fire-safety-approved-document-b`. `attachments: pdf | html | all | none` picks the files. `match` is an optional regex on the attachment title. `body: true` also stores the page text, for guidance pages without attachments. `parts` maps a part name to a title regex, for stable part names. `keep_titles: true` makes each attachment its own part (pages that list old editions side by side). Redirects to moved pages are followed.
- `url`: one file at `url` (HSE PDFs and pages, BSI previews).
- `none`: nothing is fetched (`link_only`).

Attribution is added from the publisher: OGL for GOV.UK and legislation.gov.uk, the HSE wording for HSE.

## Version record

```json
{
  "source_id": "br2010",
  "part": "main",
  "part_title": "The Building Regulations 2010",
  "version_id": "main@2023-10-01",
  "edition_date": "2023-10-01",
  "valid_from": "2023-10-01",
  "valid_from_basis": "point_in_time",
  "valid_to": "2024-04-06",
  "fetched_at": "2026-11-19T21:00:00Z",
  "fetched_url": "https://www.legislation.gov.uk/uksi/2010/2214/2023-10-01/data.xml",
  "sha256": "...",
  "bytes": 2400000,
  "media_type": "application/xml",
  "raw_path": "corpus/raw/br2010/main/<sha256 first 16>.xml",
  "s3_key": "corpus/raw/br2010/main/<sha256 first 16>.xml",
  "mode": "ingest"
}
```

- A source can have several parts, e.g. volume 1 and volume 2 of an Approved Document. Each part has its own chain of versions.
- `valid_from_basis`: `point_in_time` (legislation version date), `in_force` (stated in-force date), `published` (GOV.UK publish or update date) or `first_seen` (the date we first fetched it, when nothing better exists).
- `sha256` is the exact file (checks downloads and S3). `content_hash` decides new versions: visible text for HTML, canonical XML without legislation metadata for XML, bytes for the rest (ADR 0008).
- `valid_to: null` means current. A new hash for the same part closes the old record's `valid_to`. That is the only edit ever made to an old record. Raw files are named by hash, so nothing is overwritten.

## Known gaps (19 Nov 2026)

- **17 raw files missing** (20 Nov 2026). The first harvest ran in a cloud session and its raw files were lost with it. On Florin's PC the harvester restored 815 of 832 files with matching SHA-256, and all 815 are in the S3 bucket (checked: size, hash, encryption). The other 17 now come back with different bytes, so they were not saved (list in `harvest-report.md`). 16 are exactly the same size as before, mostly legislation XML whose metadata attributes come in no fixed order. One (ess2020, 1 May 2026) is 35 KB bigger. Open: keep today's bytes with a note in the record, or leave them missing; and hash legislation XML with attributes sorted so reordering is not a change.
- **Old editions of GOV.UK documents.** GOV.UK keeps only the current file, except AD B (back to 2006), AD L and F 2021 next to 2026, and the building regulations circulars (back to 2003). The National Archives web archive blocks automated downloads (HTTP 405). Older editions need a manual step, only if evals show we need them.
- **HSE keeps only current editions** (L143 2013, HSG264 2012, L153 2015 and others). From now on our own records keep every change.
- **Pending legislation changes.** legislation.gov.uk has not yet applied SI 2026/1153 (asbestos, reg 20 from 25 Nov 2027) or SI 2026/1195 (Awaab's Law phase 2, 30 Nov 2026) to the main texts. We hold the amending SIs as made. Re-run the harvester after they are applied.
- **England and Wales in one text.** The Building Regulations 2010 XML includes Welsh changes with extent markers. Filter to England when parsing.
- **Licence checks.** AD A and AD C PDFs still carry the old Click-Use wording. Get legal confirmation before quoting them in full.
- **Withdrawn or blocked.** HSE INDG223, INDG188 and INDG289 return 404. Gas Safe Register returned 403 (link only anyway).
