# corpus/

The shared regulations corpus: public rules and guidance that every customer uses. This folder holds only lists and version records. Raw files (PDF, HTML, XML) are never committed. They live in `corpus/raw/` (git-ignored) and in a private S3 bucket in eu-west-2 (ADR 0005).

- `GOAL.md`: the harvesting goal and definition of done.
- `sources.yaml`: one entry per document.
- `versions/<source_id>/<version_id>.json`: one record per fetched version.
- `harvest-report.md`: what the last run fetched, what failed and why.
- Inventory and licence research: `research/domain/corpus-inventory/`.

Code: `system/rag/harvest.py` (fetch and record), `system/rag/upload_s3.py` (copy raw files to S3). Run from the repo root: `python -m system.rag.harvest [--only ID ...]`.

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
- `govuk`: a GOV.UK page, read through the Content API. `page` is the path, e.g. `/government/publications/fire-safety-approved-document-b`. `attachments: pdf | html | all | none` picks the files. `match` is an optional regex on the attachment title. `body: true` also stores the page text, for guidance pages without attachments.
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
- `valid_to: null` means current. A new hash for the same part closes the old record's `valid_to`. That is the only edit ever made to an old record. Raw files are named by hash, so nothing is overwritten.
