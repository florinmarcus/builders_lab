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
python -m system.rag.parse_pdf --source <source_id>                  # guidance PDFs
python -m system.rag.parse_legislation --source <source_id> --current   # legislation XML
```

Read the `issues` in the tree. Structure problems (paragraph numbers, headings, captions, crops) are fixed in the parser code, with a test, then parse again. Never patch them with fixes.

## 3. Model checks, through packets

```
python -m system.rag.checks export --source <source_id>
```

This writes one packet per open check to `corpus/parsed/<source_id>/checks/`. For each packet, start one subagent with exactly this prompt (fill in the path):

> Read the JSON packet at `<path>`. Open every image listed in `images`. Follow `instructions` exactly, and use `template` if there is one. Reply with one line of JSON in the shape of `answer_format`, and nothing else.

Up to 8 subagents at a time. Put every reply, one per line, into `corpus/parsed/<source_id>/answers.jsonl`. Then:

```
python -m system.rag.checks save --source <source_id> --answers corpus/parsed/<source_id>/answers.jsonl --by "model check, Claude Code subagent (packet)"
```

`save` refuses answers that break the rules (row and sentence counts, heading rows, a family's columns, unknown keys). Re-run a refused packet's subagent once, adding the refusal reason to the prompt. If it is refused again, check it yourself against the page image.

Run `export` again. Tables held back because they belong to a family now get the first one as their template. Repeat until export says `0 packets`.

## 4. Parse again and review

```
python -m system.rag.parse_pdf --source <source_id>     # must say "0 model checks"
python -m system.rag.checks review --source <source_id>
```

Look at the review sheet (`corpus/parsed/<source_id>/<version>-figures.png`). A crop that is cut short or shows a neighbour is a parser bug: fix the code and add a test (step 2).

## 5. Tests

```
python -m system.rag.checks lint
python -m pytest -q
```

Add real-file tests for the document in `tests/test_parse_pdf.py` (or `test_parse_legislation.py`): counts taken from the document itself (numbered paragraphs, tables, figures, appendices), and "all checks settled by saved fixes". These tests skip where the raw file is missing.

## 6. Record and commit

- Any shortcut or known flaw goes into `requirements/parking-lot.md`.
- Gaps found in the source go under "Known gaps" in `corpus/README.md`.
- If the parser or the check rules changed, update `architecture/design/regulations-corpus.md`.
- Commit to `main` with the counts in the message: sections by type, fixes saved, checks open (should be 0). Then push.

## Changing the instructions or rules

The instructions and answer formats live in `system/rag/checks.py` (`INSTRUCTIONS`, `ANSWER_FORMAT`, `lint_fixes`). Change them between documents, not halfway through one. After a change, run `checks lint` on all sources and bring older fixes up to date with a script.
