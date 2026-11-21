# Golden set: re-label pass brief (after new parses)

The first labelling pass (`LABEL-BRIEF.md`) could not label clauses in documents that had no usable tree yet; it
listed them in `missing`. Those documents are now parsed (L143, HSG150, L153, HSG248, INDG453, Asbestos
Essentials A0/EM1, CIS80, Awaab consolidated, L56, Approved Documents A, C, G, J, K, L-2026, F-2026 and more).

## What to do

For your role file `evals/golden/labelled/<role>.jsonl`, for each row with a non-empty `missing` list:

1. Read the matching business row (`evals/golden/business/<role>.jsonl`: question, reference answer, cited clauses).
2. For each `missing` entry, find the section in the current trees (`evals/tools/find_sections.py`, current trees
   only) and check its text says it.
3. Add the found keys to `expected_sections`. Keep the existing keys and their order, except: if a newly found
   section answers the question better than the current first key (e.g. the L143 paragraph the reference answer
   rests on), move it to the front.
4. Remove the entry from `missing` once labelled; keep it if the document still has no section for it.
5. Raise `label_confidence` if the row is now fully labelled; update `label_note` briefly ("relabel: added ...").
6. Rows with `expected_sections: []` that are answerable get keys too when their source is now parsed.

Also check every existing key still exists (some ids changed in the re-parse: L143/HSG150/L153 paragraphs are
`para-N`; HSG248 is `para-<chapter>-<n>`; multi-volume Approved Documents use `v1-`/`v2-`). Fix a missing key to
the section with the same text.

## Rules

Same as `LABEL-BRIEF.md`: no search, embeddings or eval results; touch only your one labelled file; every key must
exist (`python evals/golden/build.py` fails otherwise). Report: rows changed, keys added, rows still with `missing`
and which sources.
