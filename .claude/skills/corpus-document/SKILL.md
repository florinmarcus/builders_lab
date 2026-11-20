---
name: corpus-document
description: Parse one regulations corpus document (legislation XML or guidance PDF) into a checked document tree, the same way every time - raw file, parse, model checks through packets, saved fixes, review, tests, commit. Use when asked to parse, re-parse or finish a corpus document (e.g. Approved Document B, HSG264), or to redo its model checks.
---

# Parse a corpus document

Same steps, same order, for every document. Design: `architecture/design/regulations-corpus.md`, ADR 0010. Run everything from the repo root.

Never edit `corpus/fixes/*.json` by hand. Fixes come from `checks save`. A bulk change to saved fixes is a script, and its reason is added to each fix it touches.

## 0. Set up

```
pip install -e ".[dev,corpus]"
```

## 1. Raw file

The raw file must match its version record. Get it one of these two ways only:

```
CORPUS_BUCKET=<bucket> python -m system.rag.upload_s3 --download   # from S3, hash checked
python -m system.rag.harvest --only <source_id> --no-report         # from the source, saved only if the SHA-256 matches
```

If the source now gives different bytes, stop and ask Florin. Do not parse a file that has no record.

## 2. Parse

```
python -m system.rag.parse_pdf --source <source_id>                  # HSE-style guidance PDFs
python -m system.rag.parse_adoc --source <source_id> --part <part>     # Approved Documents (2019 layout)
python -m system.rag.parse_html --source <source_id>                 # GOV.UK and HSE web pages (no model checks)
python -m system.rag.parse_legislation --source <source_id> --current   # legislation XML
```

The parser for a source is named in `sources.yaml` (`parser:`). Read the `issues` and, for Approved Documents, the `repairs` (letters put back into words) in the tree. Structure problems (paragraph numbers, headings, captions, crops) are fixed in the parser code, with a test, then parse again. Never patch them with fixes.

## 3. Model checks, through packets

```
python -m system.rag.checks export --source <source_id>
```

This writes one packet per open check to `corpus/parsed/<source_id>/checks/`. Split the packet file names into batches of up to 6 (in name order) and start one subagent per batch, up to 8 at a time, with exactly this prompt (fill in the source, packet names and batch number):

> You are doing model checks for a regulations corpus. Work in the repo at `<repo>`. Do not change any file except the one answers file named below.
>
> For EACH packet below, separately and in order:
> 1. Read the JSON packet at `<repo>/corpus/parsed/<source_id>/checks/<name>`.
> 2. Open every image listed in its `images` (paths are relative to `<repo>`) with the Read tool.
> 3. Follow the packet's `instructions` exactly, and use `template` if there is one.
> 4. Produce one line of JSON in the shape of `answer_format` (copy `key` and `kind` exactly from the packet; `value` as the format shows; `reason`, `evidence`, `confidence`).
>
> Packets: `<names>`
>
> Write all answers, one JSON object per line, in packet order, to `<repo>/corpus/parsed/<source_id>/answers/batch_<NN>.jsonl` with the Write tool. Each line must be valid JSON on a single line. Then reply only with "done" and the number of lines written.

When all batches are done:

```
cat corpus/parsed/<source_id>/answers/batch_*.jsonl > corpus/parsed/<source_id>/answers.jsonl
python -m system.rag.checks save --source <source_id> --answers corpus/parsed/<source_id>/answers.jsonl --by "model check, Claude Code subagent (packet)"
```

`save` refuses answers that break the rules (row and sentence counts, heading rows, a family's columns, unknown keys). Re-run a refused packet's subagent once, adding the refusal reason to the prompt. If it is refused again, check it yourself against the page image.

Then parse again (the tree only drops a check once it is parsed with the saved fix) and run `export` again. Tables held back because they belong to a family now get the first one as their template, and refused packets come back. Repeat until export says `0 packets`.

## 4. Parse again and review

```
python -m system.rag.parse_pdf --source <source_id>     # or parse_adoc; must say "0 model checks"
python -m system.rag.checks review --source <source_id>
```

Look at the review sheet (`corpus/parsed/<source_id>/<version>-figures.png`). A crop that is cut short or shows a neighbour is a parser bug: fix the code and add a test (step 2).

## 5. Tests

```
python -m system.rag.checks lint
python -m pytest -q
```

Add real-file tests for the document in `tests/test_parse_pdf.py` (or `test_parse_legislation.py`): counts taken from the document itself (numbered paragraphs, tables, figures, appendices), and "all checks settled by saved fixes". These tests skip where the raw file is missing.

## 5b. Chunks, vectors and the search index

```
python -m system.rag.chunk            # corpus/chunks/ and corpus/chunk-report.md
python -m system.rag.embed            # only new or changed chunks cost money
python -m system.rag.search --build
python -m system.rag.search "a builder question about this document"
```

## 6. Record and commit

- Any shortcut or known flaw goes into `requirements/parking-lot.md`.
- Gaps found in the source go under "Known gaps" in `corpus/README.md`.
- If the parser or the check rules changed, update `architecture/design/regulations-corpus.md`.
- Commit to `main` with the counts in the message: sections by type, fixes saved, checks open (should be 0). Then push.

## Changing the instructions or rules

The instructions and answer formats live in `system/rag/checks.py` (`INSTRUCTIONS`, `ANSWER_FORMAT`, `lint_fixes`). Change them between documents, not halfway through one. After a change, run `checks lint` on all sources and bring older fixes up to date with a script.
