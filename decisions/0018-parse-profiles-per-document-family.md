# 0018: Parse profiles per document family

Date: 24 Nov 2026. Status: proposed (Florin, 24 Nov). To pick up after the firm visits (28 Nov and 5 Dec). Renumbered from 0017 on 25 Nov 2026: 0017 is the workflow-control decision.
Not started.

## Context

Parsing is plain code: the same file always gives the same tree. Models come in only outside the parser: model
checks propose per-page fixes, saved as data in `corpus/fixes/` and applied the same way every run; the semantic
check (`system/rag/semcheck.py`) judges raw against parse.

Some parsers already follow the kind of document: `parse_adoc` (Approved Documents), `parse_guide` (fire guides),
`parse_booklet`, `parse_flats`, `parse_legislation`, `parse_html`. But `parse_pdf` has grown into one general
parser for every other PDF: about 3,300 lines on 24 Nov 2026 (all parsers about 11,600).

Each semantic-check round (S128) fixes many pages and breaks a few: a rule added for one layout also fires on
another. Fix 4 (leaflet headings) fixed 47 units and really broke 3. Tests cover only the cases we wrote; there
is no answer key for the whole corpus. As rules pile up, each new rule costs more and risks more. Pages with a
serious finding are still 12% (Approved Documents) and 14% (guidance PDFs); the target is 2%.

## Decision

1. **Profiles per document family, not per file type.** A family is a set of documents with the same layout
   and meaning: HSE guides, BR circulars, Procurement Act supplier guides, leaflets, and so on.
2. **Strategies.** Each parsing step becomes a small swappable piece: finding headings, reading tables, two
   columns, notes and boxes, figures, footnotes.
3. **A registry of profiles.** Each profile names the strategies a family uses and their settings. A builder
   (factory) puts the parser together from the profile.
4. **The model proposes, the choice is stored.** For a new document, a model looks at sample pages and proposes
   a profile (an existing one, or a new mix of strategies). We parse, run the semantic check and keep the profile
   that passes. The choice is saved as data (for example in `corpus/sources.yaml`) and then runs the same way
   every time. The model never picks a strategy afresh on each run, so the same file always gives the same tree
   and regressions can be traced.
5. **Page fixes stay a last resort**, stored as data in `corpus/fixes/`, never as `if page == 5` in code.
6. **Move over step by step.** Pull one family at a time out of `parse_pdf` into a profile, starting with the
   worst sources in the semantic check. Each move uses the S128 regression method: untouched trees stay
   byte-identical, a synthetic test per strategy, model, crop and coverage checks at 0 open, and a paired
   before/after with the same judge.

## Options considered

- **Keep adding rules to one general parser.** Cheapest per fix today, but each rule can break other layouts,
  and the cost grows with each round. Rejected as the long-term path.
- **A model parses each page at run time.** Handles odd layouts, but output changes from run to run, costs
  tokens on every parse, and breaks ADR 0006 if run on our server. Rejected.
- **Per-page hard-coding in the parser.** Precise but fragile and unreadable. Kept only as stored fixes (item 5).
- **Profiles and strategies with a stored, model-proposed choice (chosen).** Changes stay local to one family;
  new documents reuse existing strategies.

## Consequences

- A rule change can only affect documents whose profile uses that strategy, so breakage stays inside one
  family and is easier to check.
- New documents start from a model proposal plus a judge run, not new code, when existing strategies fit.
- Work: splitting `parse_pdf` into strategies, a profile registry and a proposal step. Not before the visits.
- The parser label on each tree (S99) should name the profile and its version.
- Parking-lot item S134 tracks it.
