# P: semantic validation of the parsed corpus (23 Nov 2026)

**Status (23 Nov 2026): sample fully judged, 50 findings checked by hand, judge noise measured, six fixes made
and judged again.** Approved Documents: high rate on random pages 16.3% before, 10.3% after; on table pages 28.7%
before, 13.1% after. Guidance PDFs are almost unchanged (23.3% on random pages): their main causes are still open.

## Question

Code checks pass (coverage 0 open, crops 0 bad, model checks 0 open). Does each tree also say what its source
says? A model reads the source next to the tree and names differences.

## Method

Tool: `system/rag/semcheck.py` (design: [regulations-corpus.md](../../architecture/design/regulations-corpus.md),
"Semantic check"). Model: Fable 5.2 only, headless Claude Code, 6 packets a batch, 4 to 8 batches at a time.

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

## Checked by hand: how often is the model wrong?

I checked 50 units with a high finding against the page image (or the XML or web text), drawn at random within
each family and kind of finding (seed 20261123 and 20261124): 24 Approved Document pages (table 8, structure 7,
garbled 4, missing 2, order 2, figure 1) and 26 others (guidance PDFs 18, fire guides 3, legislation 3, web 1,
booklet 1).

| Result | Units |
|---|---|
| Finding real and high | 45 |
| Finding real, but the explanation partly off (still high) | 2 |
| Finding real, but low, not high (a label or a title page; no rule lost) | 2 |
| Finding wrong | 1 |

- **Precision of a "high" unit: 47 of 50 = 94% (95% interval 84 to 98%).** Outright wrong: 1 of 50 (2%).
- The one wrong finding was the tool's fault, not the model's: HSWA 1974 section 43A is printed twice with one id
  (for E+W+S and for N.I.); the packet showed the N.I. text and the tree holds the E+W+S text. `semcheck` now picks
  the version by the tree's extent; the finding is settled as model-wrong.
- The model's quotes were exact every time I looked them up in the tree.
- Not measured: findings the model missed (pages it called ok). The rates below are what is wrong among what the
  model saw, not a full error rate.

Corrected high rates (rate times 0.94; intervals scaled the same way, so they leave out the doubt in the 0.94):

| Family | Flagged | Corrected |
|---|---|---|
| Approved Documents, random pages | 16.3% | about 15% (12 to 20%) |
| Approved Documents, table pages | 28.7% | about 27% (23 to 31%) |
| Guidance PDFs, random pages | 23.3% | about 22% (19 to 25%) |
| Guidance PDFs, table pages | 29.0% | about 27% (24 to 31%) |
| Fire guides, random pages | 1.1% | about 1% |
| Legislation | 2.8% | about 3% |
| Web pages | 0.5% | under 1% |

## Main causes (before the fixes)

1. **Table grids drop group headings over several columns** (73 Approved Document pages, more in guidance): the
   model-check instruction asked for "the lowest header row". AD B Table B1 lost "Alternative minimum provisions
   when tested to the relevant part of BS 476"; Table B4 "basement depth" against "height of top floor"; Table B5
   two "Walls" and two "Door leaf" columns; AD L Table 4.3 was forced into the two columns of its "family".
2. **Amendment booklets**: "Replace paragraph ..." instructions joined to the paragraph before (AD B March 2024:
   new 3.56(b) inside 3.54); margin page references ("to 128") read as headings; "Page 115 Insert" as a key term.
3. **Collated AD B edition boxes**: text printed after a box filed under the box's heading (3.36, 3.37) and no
   box dates on the sections.
4. **Circular annex titles**: "ANNEX A" (20pt over 12pt body) read as the end of the last paragraph, so notices
   of approval sat under "ENQUIRIES" (58 high findings in circulars).
5. **"fi" and "fl" lost** where the PDF maps the ligature glyph to "f" (HSG33, AD B, AD G, AD M, L108, HSG248).
6. **Classic headings on two lines** read as two headings (AD A "Construction materials and" / "workmanship").
7. Not fixed (still open, see the end): tables over pages not joined; text after a table held in the table's text
   (HSG248); headings read as body text in HSE guides; two columns mixed (leaflets, short guides); formulas
   flattened; Bengali, Urdu and Arabic tenant guides with broken characters; FAQ PDFs without question headings;
   shading in tables not recorded; footnote markers joined to numbers.

## Judge noise: how often does a fresh run change the verdict?

150 unchanged units, drawn by family (seed 20261125), were judged again by Fable in fresh runs and kept apart
(`evals/experiments/data/semcheck-noise-2026-11-23.json`; the saved verdicts were not touched). A batch run that
picked up stale packets judged 281 more unchanged units again by mistake; those answers are kept in the same file
as extra noise data and the saved verdicts were put back.

| Set | Units | Class flips (ok / low only / high) | High-flag flips | High to not high | Not high to high |
|---|---|---|---|---|---|
| Designed (150) | 150 | 17 (11%) | 5 (3.3%; 1.4 to 7.6%) | 3 of 21 (14%) | 2 of 129 (1.6%) |
| Extra (batch) | 281 | 50 (18%) | 18 (6.4%; 4.1 to 9.9%) | 12 of 91 (13%) | 6 of 190 (3.2%) |
| **All** | 431 | 67 (16%) | 23 (5.3%; 3.6 to 7.9%) | **15 of 112 (13%; 8 to 21%)** | **8 of 319 (2.5%; 1.3 to 4.9%)** |

By family (designed set): Approved Documents 2 of 40 high flips, guidance PDFs 3 of 50, fire guides, web pages,
legislation, flats guide and booklets 0. The extra set: guidance PDFs 10 of 168, legislation 8 of 71, web 0 of 42.

So a unit flagged high loses the flag on a fresh run about one time in eight, and an unflagged unit gains one about
one time in forty. A fix is read against that: on n units that were high before, about 0.13 n "fixed" are noise;
on m units that were not high, about 0.025 m "broken" are noise.

## Fixes and their effect (paired, on the units each fix changed)

Each fix was made in the parser with a synthetic test that fails on the old code, then every PDF and Approved
Document tree was parsed again. Byte identity: the ligature fix changed 17 trees, all other 240 trees stayed
byte-identical; the structure fixes changed 68 trees (189 identical); saving the re-done and re-keyed model fixes
changed 90 (167 identical, all in the sources whose fixes changed); the two refinements changed 37 (circulars
only) and 15 (220 and 242 identical). In all, 111 of the 257 PDF and Approved Document trees changed and 146 are
byte-identical to before.
Model checks (re-done or new), crop check and coverage were run for every changed tree and end at 0 open, 0 bad,
0 not judged, coverage 0 open items. Then every sampled unit whose content changed was judged again.

"Fixed" = high before, not high after; "broken" = not high before, high after. McNemar exact test on the two.
"Noise" = what the noise rates above would give on the same units.

| Fix | Units changed | High before / after | Fixed | Broken | McNemar p | Noise would give (fixed / broken) |
|---|---|---|---|---|---|---|
| Table group headings (instruction + 198 table fixes re-done with CORPUS_REDO) | 236 | 113 / 32 | 86 | 5 | 4e-20 | 15 / 3 |
| Circular annex titles (parse_pdf) | 159 | 37 / 22 | 21 | 6 | 0.006 | 5 / 3 |
| AD structure: edition boxes, booklet instructions, classic headings (parse_adoc) | 29 | 17 / 10 | 10 | 3 | 0.09 | 2 / 0.3 |
| Ligature and AD structure in the same tree (AD B, AD M) | 29 | 11 / 4 | 7 | 0 | 0.016 | 1.4 / 0.5 |
| Ligature alone ("fi", "fl" from the glyph name) | 35 | 11 / 8 | 3 | 0 | 0.25 | 1.4 / 0.6 |
| semcheck picks the provision version by extent | 2 | 2 / 0 | 2 | 0 | 0.5 | 0.3 / 0 |

Reading:
- The table instruction is the clear win: 86 fixed against 15 expected from noise.
- Annex titles and the AD structure fixes fix clearly more than noise would, with small numbers.
- The ligature fix alone cannot be told apart from judge noise on the sample (3 fixed, 1.4 expected). It stays
  because it is checked by code: the tree's words now match the PDF's glyph names (17 trees, synthetic test).

**Every broken unit was looked at (14).** None is caused by a fix: in each the fault the model names was already
in the tree before (same table grid, same text, or a parser behaviour the fix does not touch), and the earlier run
did not flag it. They are: may-2020 booklet paragraph 13.5 read as headings (the whole booklet is bold, as before);
AD C footnote mark run into "No. 27"; AD M corrections Diagram 3.17 labels; an Awaab impact assessment table cut at
a page break (S118); two circular notice tables whose grids are unchanged; a circular flowchart and a two-column
table read as text; a circular paragraph with no spaces in the PDF itself; AD B volume 2 Table 14.2 in a version
the re-do did not reach; HSE L5 biohazard sign not a figure; manual-br Table A2 caption kept as a note; two
supplier-information pages with headings and order faults. Their count (5, 6, 3) is close to what noise gives.

Three breaks found on the way were real and were fixed before the final run: headings printed inside an edition
box lost the box date and stayed the parent after the box (AD B pages 38, 145, 147: headings inside a box now
end with it); "Annex c" in small capitals and "AnnexA" were missed, so Annex C sat under Annex B; a signature over
"Signed by authority ..." became a figure and took another circular's figure description (figure keys of empty
figures can collide, S129).

## Results after the fixes

| Family | Units | ok | Low only | High | High rate | 95% | Before |
|---|---|---|---|---|---|---|---|
| Approved Documents, random pages | 319 | 189 | 97 | 33 | 10.3% | 7.5 to 14.2% | 16.3% |
| Approved Documents, table pages | 467 | 276 | 130 | 61 | 13.1% | 10.3 to 16.4% | 28.7% |
| Guidance PDFs, random pages | 726 | 194 | 363 | 169 | 23.3% | 20.3 to 26.5% | 23.3% |
| Guidance PDFs, table pages | 580 | 188 | 245 | 147 | 25.3% | 22.0 to 29.0% | 29.0% |
| Fire guides, random pages | 188 | 149 | 37 | 2 | 1.1% | 0.3 to 3.8% | 1.1% |
| Fire guides, table pages | 161 | 111 | 37 | 13 | 8.1% | 4.8 to 13.3% | 8.1% |
| Flats guide | 21 | 12 | 9 | 0 | 0% | 0 to 15.5% | 0% |
| Home Office booklets | 16 | 9 | 6 | 1 | 6.2% | 1.1 to 28.3% | 6.2% |
| Web pages (parts) | 218 | 191 | 26 | 1 | 0.5% | 0.1 to 2.6% | 0.5% |
| Legislation (provisions) | 326 | 258 | 61 | 7 | 2.1% | 1.0 to 4.4% | 2.8% |

High findings by kind after, Approved Documents: structure 48, garbled 30, table 17, missing 13, order 12, extra 3,
figure 1 (before: table 94, structure 74). Guidance PDFs: structure 216, order 78, garbled 73, table 35, missing 29.
The hand check (94% of high units real) and the noise above apply to these numbers too.

## What is left

- Approved Documents are still well above the 2% line on random pages (10%). Remaining causes: formulas flattened
  (AD L), FAQ PDFs read with the Approved Document parser, notes under tables misplaced in the classic layout
  (AD H, AD J), diagram words only in the model description (AD A), headings read as body text.
- Guidance PDFs are unchanged on random pages (23%): HSE guides keep text after a table inside the table's text
  (HSG248), read some headings as body text (HSG33, HSG248, L5), mix two columns (CIS54, leaflets, short guides);
  tables over pages are not joined (S118); the Awaab tenant guides in Bengali, Urdu and Arabic have broken
  characters (S130).
- Legislation: provisions marked prospective in the XML are given as in force (RRA 2025, S131; parse_legislation,
  not changed here).
- Open findings are left open; none was accepted to make the report pass (one tool fault settled as model-wrong).

## Round 2 (S128, 23 Nov 2026): guidance PDF causes

Counted first on the 316 guidance units with a high finding (keyword classes, a unit can have several): headings
read as body text 63, tables over pages 46, non-Latin scripts 40 (S130), table rows also kept as running text 33,
two columns mixed 33, paragraphs merged 27, text after a table 24, formulas 16, footnote numbers joined 2.

| Fix | Units changed | High before / after | Fixed | Broken | McNemar p | Noise would give (fixed / broken) |
|---|---|---|---|---|---|---|
| 1. Tables over pages joined (S118) | 246 | 67 / 42 | 28 | 3 | 4.6e-6 | 8.7 / 4.5 |

Fix 1: 36 trees changed, 388 byte-identical; 107 model checks (Fable), 0 open; crops 0 bad; coverage 0 open. The
three broken units were looked at: all three faults were in the tree before (Awaab phase 2 IA annex titles in
paragraph 10, a one-row table read as a note in the learning manual). A fourth break, found on the way (an annex
title printed inside the next ruled table let Annex B's table join Annex A's), was fixed before the final run.
Guidance PDFs over all sampled units: 24.2% high before, 22.3% after.

### Judge from fix 2 on: Opus 5.5 (Florin, 23 Nov 2026)

The judge is a setting now (`semcheck --model`, default Opus 5.5). Each judge has its own store; a paired table uses
one judge on both sides (before = trees from the code before the fix, after = new trees), so Fable and Opus verdicts
are never mixed.

Opus judge noise: the 145 designed noise units still in scope (5 were non-English), judged twice by Opus in fresh
runs (`evals/experiments/data/semcheck-noise-opus-2026-11-23.json`):

| Set | Units | Class flips | High-flag flips | High to not high | Not high to high |
|---|---|---|---|---|---|
| Opus run 1 vs run 2 | 145 | 17 (12%) | 2 (1.4%; 0.4 to 4.9%) | 0 of 10 | 2 of 135 (1.5%) |

Opus against Fable on the 137 of them whose content is unchanged: the high flag agrees on 132 (96.4%). Both high 9,
Opus only 1, Fable only 4: Opus flags fewer units high (7.3% against Fable's 9.5% on these units), mostly in
guidance PDFs (Opus 6, Fable 12 of 45). So Opus is steadier than Fable (1.4% flips against 5.3%) and a little more
lenient; its rates are not comparable with Fable's.

| Fix (judge) | Units changed | High before / after | Fixed | Broken | McNemar p | Noise would give (fixed / broken) |
|---|---|---|---|---|---|---|
| 2. HSE headings, table rows stop at body text (Opus 5.5) | 252 | 54 / 33 | 25 | 4 | 0.0001 | 0 / 3 |

Fix 2: 30 trees changed against the fix-1 trees, 395 byte-identical; model checks (Fable, then Opus for the last
tables) 0 open; crops 0 bad (one crop of a go-live slide kept with a named defect: the same cut was there before);
coverage 0 open. The first Opus run found 7 breaks; 4 came from the fix (a heading found above, the next heading
missed, so text sat under the wrong sub-heading; a heading at the top of a whole-page table swallowed by the table)
and were fixed before the final run. The 4 final breaks: three faults that were in the tree before (HSG248 A5.41
bullet, L108 Box 4 order, a learning manual footnote section), and Scenario 7/8 in the learning manual, headings in
the right column of a two-column page (fix 3).

### English only (S130, Florin, 23 Nov 2026)

97 sampled units in translated or Romanian documents left the sample (95 guidance pages, 2 web parts). On the Fable
verdicts of the fix-1 trees this alone moves guidance PDFs from 22.9% to 20.1% (random pages) and 21.6% to 20.1%
(table pages). This is a change of scope, not a fix.

## Limits

- One model judges, with the noise measured above; a finding is a claim until checked. The hand check covers 50
  units; findings the model missed (pages called ok) are not measured.
- A PDF page's tree content is worked out by code (which sections are on the page). A section that ends on the
  page with fewer than five words there is left out and may be reported as missing.
- Row sentences of tables are not shown to the model, only grids, columns and printed text.
- Web pages are checked as text, not as rendered pages. Pictures count only by their alt text.
- 140 legislation units (tables inside Schedules, Schedule 1 requirements of the Building Regulations, copies
  for other nations) have no element id in the XML and are outside the sample.
- Two pages printed the same in two versions share one key and one verdict.
- Fix attribution is by tree and page: a page with a re-done table counts under the table fix even when another
  fix changed the same tree.
