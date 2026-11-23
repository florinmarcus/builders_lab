# P: semantic validation of the parsed corpus (23 Nov 2026)

**Status: sample fully judged (3,022 of 3,022 units).** Findings are model-flagged; a hand check of a sample of
them, the fixes and the numbers after the fixes follow below.
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

## Results: the whole sample (before any fix)

"High" = units with at least one high-severity finding. Interval: 95% Wilson. Random pages are the per-document
random 10% (the fair rate for ordinary pages); table pages are all the other pages with a table (picked, not drawn).

| Family | Units | ok | Low only | High | High rate | 95% |
|---|---|---|---|---|---|---|
| Approved Documents, random pages | 319 | 165 | 102 | 52 | 16.3% | 12.7 to 20.8% |
| Approved Documents, table pages | 467 | 176 | 157 | 134 | 28.7% | 24.8 to 33.0% |
| Guidance PDFs (parse_pdf), random pages | 726 | 184 | 373 | 169 | 23.3% | 20.3 to 26.5% |
| Guidance PDFs (parse_pdf), table pages | 580 | 158 | 254 | 168 | 29.0% | 25.4 to 32.8% |
| Fire risk guides (parse_guide), random pages | 188 | 150 | 36 | 2 | 1.1% | 0.3 to 3.8% |
| Fire risk guides (parse_guide), table pages | 161 | 103 | 45 | 13 | 8.1% | 4.8 to 13.3% |
| Flats guide (parse_flats), all pages | 21 | 11 | 10 | 0 | 0% | 0 to 15.5% |
| Home Office booklets (parse_booklet), all pages | 16 | 9 | 6 | 1 | 6.2% | 1.1 to 28.3% |
| Web pages (parse_html), parts | 218 | 191 | 26 | 1 | 0.5% | 0.1 to 2.6% |
| Legislation (parse_legislation), provisions | 326 | 256 | 61 | 9 | 2.8% | 1.5 to 5.2% |
| **Total** | 3,022 | 1,403 | 1,070 | 549 | | |

Guidance PDFs by group (random pages): HSE 22.8% (54 of 237; 17.9 to 28.5%), building regulations circulars and
manual 16.1% (42 of 261), other government PDFs 25.3% (44 of 174), Awaab's Law PDFs 53.7% (29 of 54).

High findings by kind: Approved Documents table 94, structure 74, garbled 30, missing 15, order 11, extra 4,
figure 1. Guidance PDFs structure 236, order 77, garbled 75, table 43, missing 26, extra 5. Legislation structure
8, garbled 5. Fire guides table 10, garbled 5, structure 4.

Two pages printed the same in two versions (nine circular pages) get one key and one verdict; they count once per
version above. Eight packets came back without an answer in the batch run and were judged again on their own.

**Read these numbers with care.**
- The Approved Document rate is pulled up by `adb-historical` (76 high findings) and `adb-amendments` (50):
  amendment booklets and the collated AD B are the hardest layouts.
- Building regulations circulars give 58 high "structure" findings, nearly all one cause: "ANNEX A" titles read as
  the end of the last paragraph.
- Awaab's Law PDFs (tenant guides in Bengali, Urdu, Arabic and Polish, impact assessments) are the worst group.
- Until the hand check below, the rates are "what the model flagged", not "what is wrong".

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

Web pages (0.5%), legislation (2.8%) and the fire guides' random pages (1.1%) are close to clean.

## What this implies

- For Approved Documents the high rate on random pages is 16% (13 to 21%), far above the 2% line. Judging every
  page would not change the decision; fixing the causes would. Widening was not done.
- For unsampled Approved Document pages: about 2,000 pages, so roughly 250 to 420 more pages with a finding the
  model would call high, before any fix and before the model's own errors are taken off.
- HSE guidance random pages: 22.8% (17.9 to 28.5%). Fire guides, web pages and legislation are near or under the
  2% line on ordinary pages.

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
