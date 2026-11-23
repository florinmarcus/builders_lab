# P: semantic validation of the parsed corpus (partial, 23 Nov 2026)

**Status: stopped part-way.** 890 of 3,022 sampled units are judged. The run was paused to save usage (Florin).
The Approved Documents are fully judged; the other families are only started. No finding is settled yet and no
parser fix from this check is committed.

## Question

Code checks pass (coverage 0 open, crops 0 bad, model checks 0 open). Does each tree also say what its source
says? A model reads the source next to the tree and names differences.

## Method

Tool: `system/rag/semcheck.py` (design: [regulations-corpus.md](../../architecture/design/regulations-corpus.md),
"Semantic check"). Model: Fable 5.2 only, headless Claude Code, 6 packets a batch, 4 batches at a time.

- PDF: one page. The page image against the page's tree content in reading order.
- Web page: one part of a page, cut at headings. The visible text (dropped text named) against the tree sections.
- Legislation: one provision. The raw XML against its tree sections.

Each answer is `ok` or findings of kind missing, garbled, order, structure, table, figure, extra, each with a
problem, quoted evidence and a severity. High = changes meaning or loses a rule, number or limit. Verdicts are in
`corpus/semchecks/<source>.json`, keyed by a hash of the source side and the tree content.

## Sample (seed 20261122, `corpus/semchecks/sample.json`)

| Kind | Population in scope | Sampled | How |
|---|---|---|---|
| PDF pages | 9,336 pages in 244 documents | 2,478 | per document a random 10%, at least 3 (base: 1,266); plus every other page with a table (1,212) |
| Web pages | 111 pages | 111 pages, 218 parts | all |
| Legislation | 3,876 provisions in 47 laws (140 have no element id in the XML and cannot be drawn) | 326 | in proportion to each law, at least 2 per law |

What I chose: the brief asked for every table page, and for half the figure-only pages only if the total stayed
near 1,500. Base plus tables is already 2,478, so the 668 extra figure pages were left out. All 1,397 table pages
are in the sample. Figure pages are covered only as far as the random base pages hit them.

## Judged so far

"High" = units with at least one high-severity finding. Interval: 95% Wilson.

| Family | Sampled | Judged | ok | Low only | High | High rate | 95% |
|---|---|---|---|---|---|---|---|
| Approved Documents (parse_adoc) | 786 | 786 | 341 | 259 | 186 | 23.7% | 20.8 to 26.8% |
| Guidance PDFs (parse_pdf) | 1,306 | 78 | 4 | 39 | 35 | 44.9% | 34.3 to 55.9% |
| Fire risk guides (parse_guide) | 349 | 0 | | | | | |
| Flats guide (parse_flats) | 21 | 0 | | | | | |
| Home Office booklets (parse_booklet) | 16 | 0 | | | | | |
| Web pages (parse_html) | 218 | 24 | 23 | 1 | 0 | 0% | 0 to 13.8% |
| Legislation (parse_legislation) | 326 | 2 | 2 | 0 | 0 | | |
| **Total** | 3,022 | 890 | 370 | 299 | 221 | | |

Table pages and other pages apart. The random base pages give the fair rate for ordinary pages; table pages are
all picked, so their rate is a count, not an estimate.

| Family | Pages | Judged | ok | Low only | High | High rate | 95% |
|---|---|---|---|---|---|---|---|
| Approved Documents, random base pages | 319 | 319 | 165 | 102 | 52 | 16.3% | 12.7 to 20.8% |
| Approved Documents, other table pages | 467 | 467 | 176 | 157 | 134 | 28.7% | 24.8 to 33.0% |
| Guidance PDFs, random base pages | 726 | 34 | 3 | 16 | 15 | 44.1% | 28.9 to 60.5% |
| Guidance PDFs, other table pages | 580 | 44 | 1 | 23 | 20 | 45.5% | 31.7 to 59.9% |

Findings by kind and severity (Approved Documents): table 94 high and 129 low; structure 74 and 220; garbled 30
and 83; missing 15 and 23; order 11 and 24; extra 4 and 15; figure 1 and 20.

**Read these numbers with care.**
- The guidance PDF numbers are not a sample of that family. The 78 judged pages are the first sources in name
  order, mostly `awaab-collection` and `awaab-tenants`: tenant guides in Bengali, Urdu, Arabic and Polish and
  impact assessments, which parse badly. HSE guidance is not judged yet.
- The Approved Document rate is pulled up by two sources: `adb-historical` (76 high findings) and
  `adb-amendments` (50). Amendment booklets and the collated AD B are the hardest layouts.
- The model's own error rate is not measured yet. I checked only a handful of findings against the page or the
  file (below). The plan was to check a sample of about 50; that is still to do. Until then the rates are an
  upper bound: "what the model flagged", not "what is wrong".

## Checked by hand so far

- Table group headings dropped: confirmed on AD B volume 1 pages 139 and 153 (page images).
- "fi" and "fl" lost in HSG33: confirmed in the PDF itself. The font names the glyph "fi" but the file's text
  table says "f". A scan of all PDFs in scope finds this in 15 documents.
- One false alarm that was mine, not the model's: the first packets showed tables as grid only, so the model
  reported the notes under tables as missing. The notes are in the table's text. Packets now show the text too,
  and those answers were thrown away before saving.

## Main causes (high-severity findings, rough grouping by keyword)

1. **Table grids drop group headings over several columns** (73 pages in Approved Documents). The model-check
   instruction asked for "the lowest header row". Examples: AD B Table B1 loses "Alternative minimum provisions
   when tested to the relevant part of BS 476"; AD B volume 2 Table B4 loses "basement depth" against "height of
   top floor"; Table B3 has two "Walls" and two "Door leaf" columns with nothing to tell single stair from more
   than one stair.
2. **Other table faults** (28 pages in Approved Documents, 12 in guidance): AD F 2026 Table 1.2 has three printed
   columns and two in the tree; AD B 2029 booklet Table B3 row 8 reads 1100mm where the page prints 100mm; a
   table row cut at a page break with its end in the running text (Awaab tenant guides).
3. **Provisions merged or split** (25 pages): amendment booklets join "Replace paragraph ..." instructions and the
   new text to the paragraph before (AD B March 2024: new 3.56(b) sits inside 3.54); closing sentences of a
   paragraph joined to its last list item (AD B 15.8).
4. **Wrong parent or validity** (20 pages): collated AD B puts text printed after an amendment box under the
   box's "effective from" heading (3.36, 3.37); Table C1 has valid_to 2029-09-01 where the page says until
   29 September 2026; the 2025 booklet files Volume 2 amendments under a Volume 1 chapter.
5. **Headings and body text confused** (13 pages in Approved Documents, 7 in guidance): a heading printed on two
   lines becomes two headings (AD M Table 3 title, AD A "Construction materials and workmanship"); FAQ documents
   parsed with the Approved Document parser lose question headings (AD A, AD G, AD M FAQs).
6. **Notes under tables in the wrong place or scrambled** (15 pages): AD G Table A2.7's footnote sits in Table
   A2.5; AD J Table 10 note 2 has its words interleaved.
7. **Garbled text**: "fi" and "fl" lost (HSG33, AD G, 13 more documents); formulas flattened so a fraction loses
   its division (AD L U-value, AD L 2026 equation 5.4); Bengali, Urdu and Arabic guides with broken characters,
   and one of them kept as a single "Paragraph 8" for the whole document.
8. **Figures** (6 pages): words inside older diagrams (AD A Diagrams 5, 10, 14) are not in `labels`, only in the
   model's description; AD E Diagram A.1 and AD K Diagram 9.1 are not figures at all.

Web pages and legislation look clean so far (25 of 26 ok, one low finding), but too few are judged to say more.

## What this implies

- For Approved Documents the high rate on random pages is 16% (13 to 21%), far above the 2% line. Judging every
  page would not change the decision; fixing the causes would. Widening was not done.
- For unsampled Approved Document pages: about 2,000 pages, so roughly 250 to 420 more pages with a finding the
  model would call high, before any fix and before the model's own errors are taken off.
- Nothing can be said yet about HSE guidance, the fire guides, web pages or legislation.

## Left to do

1. Judge the other 2,132 units: `semcheck export`, then `semcheck run --by "..."` (answers are saved after every
   batch; only units with no verdict are exported).
2. Check about 50 high findings against the page images, settle them (`accept --as model-wrong` or leave open),
   and give the model's error rate.
3. Fix causes, biggest first. Started and not committed (kept in a local git stash, not pushed):
   - the reader takes ligature glyphs by glyph name (`parse_pdf`, `parse_adoc`); with it 17 trees in 9 sources
     change and 55 model checks reopen; all other trees stay byte-identical;
   - `CORPUS_REDO` so a saved fix can be done again without a hand edit;
   - the table instruction joins group headings into the column names; the flagged tables then need redoing.
4. Run the report again; table pages and base pages apart.

## Limits

- One model, one pass, no second opinion. A finding is a claim until someone checks it.
- A PDF page's tree content is worked out by code (which sections are on the page). A section that ends on the
  page with fewer than five words there is left out and may be reported as missing.
- Row sentences of tables are not shown to the model, only grids, columns and printed text.
- Web pages are checked as text, not as rendered pages. Pictures count only by their alt text.
- 140 legislation units (tables inside Schedules, Schedule 1 requirements of the Building Regulations, copies
  for other nations) have no element id in the XML and are outside the sample.
