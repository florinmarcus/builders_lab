# M1: library map and outside references (25 Nov 2026)

Question (Florin): can a table of contents of the library, plus the links between documents, tell us when a topic is
held but the detail sits in a document we do not hold? Plain code only, no model.
Code: `evals/experiments/library-map/build.py`. Counts: `library-map/outside-refs.csv` (names and counts, no corpus text).

## Library map

- 58,059 chunks in scope, 396 document versions, 197 sources.
- A map with chapter headings is about 34,000 tokens. That's too big for every Haiku call.
- Titles only (one line per source and title) is about 4,600 tokens. That fits in a prompt.
- The deeper contents belong behind a tool (ADR 0016 get_section, read_document).

## Outside references

How each citation is used is a guess from its wording:
- list: a reading list or a standards appendix;
- mention: "see ...", "for more information";
- binding: everything else in body text, for example "tested to BS 476-22" or "should comply with BS 5839-1".

| | chunks | share |
|---|---|---|
| cite a document we do not hold | 1,994 | 3.4% |
| at least one binding citation | 1,575 | 2.7% |
| reading lists only | 231 | 0.4% |

- 548 different outside documents are cited, 473 of them standards.
- Only 45 of the 548 are in `corpus/sources.yaml`, so we don't know the edition or status of the other 503.
- The most cited are fire standards: BS 476, BS EN 13501, BS 5839, BS 9999. "Manufacturer's instructions" is cited
  in 34 sources, and BS 7671 in 17.
- Hand check of 40 random citations: all 12 "list" and the 1 "mention" were right. 24 of the 27 "binding" were right.
  The wrong ones were a history note (L127 merged into L143), an optional template (PAS 79) and an index edit in an
  amendment booklet. That's about 9 in 10 on a small sample.

## Tune questions (60)

- 4 have an expected section with a binding outside citation: fire-safety-013 (BS 476), -016 (BS 4514, BS 5255),
  -027 (manufacturer's instructions) and -032 (BS 5839).
- Of the 7 out_of_scope questions, two need BS 7671 (housing-repairs-058, site-safety-065). Our library cites BS 7671
  as binding in 40 chunks, so a pointer exists. The other five need things no held text points to: steel sizing,
  worker cards, Right to Repair 1994, insurance, and planning (a stale label, S146).
- The gold set has few "held but the detail is outside" questions. The questions were labelled against what we hold,
  so such cases tend to end up as out_of_scope with no expected sections (S150).

## What this allows

When search returns a chunk with a binding citation to a document we don't hold, plain code can add a note:
"the detail is in BS 5839, which our library does not hold". The answer then says so, citing the official text.
That's not built yet; it would be a field on the search result. Parked as S149.
