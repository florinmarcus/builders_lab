# S128 work in progress (23 Nov 2026)

Saved here so it survives the container. Fable's usage limit stopped the work; it resets 25 Nov 01:00 UTC.

- Fix 1 (tables over pages, S118) is done: commits 028fa8d, 5ad3a21.
- Fix 2 (HSE headings, text after tables) is committed as work in progress: built and tested, not yet judged.
  Three L108 page-85 model checks are pending, so the local real-file "all checks settled" test fails until they are done.
- Fix 3 (two columns) is only a draft: `parse_pdf.fix3-draft.py` (a whole copy of parse_pdf.py).
- `status-before2.json.gz`: semantic-check status before fix 2, for the paired table (`paired.py`).
  The scripts expected it at `corpus/parsed/_s128/status-before2.json`.

To resume fix 2: `CORPUS_REDO=ebaf75cce21f180b`, re-parse L108, export (3 packets), run them with Fable, save,
re-parse without the variable, export shows 0 packets; crop check and coverage on the fix-2 sources;
`semcheck export` and `run` on the changed sources; paired table against status-before2; check broken units; tests; commit.
