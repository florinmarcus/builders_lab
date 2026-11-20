# 0010: Parsing: library first, model checks and fills gaps, chunk by document structure

Date: 20 Nov 2026. Status: accepted for the parser pilot. Design and diagrams: `architecture/design/regulations-corpus.md`.

## Context

The corpus is harvested (ADR 0008). Next is turning raw files into chunks for search. Profiling the pilot files showed hard cases for any parser: legislation XML with Wales-only text in a separate block and duplicated Schedule 1 Parts without extent markers; an Approved Document with two dated versions of two appendices in one PDF, diagram labels mixed into the text, a watermark, a font that drops "fi", and tables that neither pdfplumber nor PyMuPDF extracts cleanly. Florin expects the parser to need constant improvement as new cases appear, and a purely rule-based parser would grow hard to manage. Ingestion runs on Florin's PC in Claude Code, so model checks cost no extra money.

## Decision

- **Two steps.** The parser writes a document tree (JSON) to `corpus/parsed/`, out of git, rebuilt from raw files. The chunker reads the tree.
- **Library first, model second.** lxml for legislation XML; pdfplumber (MIT licence) for PDF text and tables, pypdfium2 for page images. PyMuPDF is not used: it is AGPL, which could bind us if the software is distributed or offered as a service (decided 20 Nov 2026). A model (Claude Code) checks every table and every diagram, and decides cases the code cannot (unclear "fi" repairs, which duplicate Schedule 1 Part is England's). Tests and experiments will move the line between the two.
- **Model fixes are saved** in git (`corpus/fixes/<source_id>.json`) and reused on later runs, so parsing is repeatable and fixes can be counted. Each fix is linked to a fingerprint of the content it is about (for a table: its text), so it carries over to later versions where that content is unchanged, and comes back as a check when the content changes. The parser lists open decisions as `checks` in the tree. (Updated 20 Nov 2026; first written as "file hash and page".)
- **Keep everything, mark it.** Wales-only text is kept with `applies_to`; search shows England by default. Amendment markers leave the text; amendment notes stay as metadata.
- **Dates on every chunk**, including two dated versions inside one document (AD B appendices B and C: until 1 Sep 2029, from 2 Sep 2029).
- **Chunk by structure**: regulation (split at sub-paragraphs only when long, splits counted), Schedule 1 requirement, definition, numbered paragraph, box, table plus a sentence per row, figure, change note. Every chunk links to its parent section; full section text is stored for a `get_section` tool.
- **Figures and photos** are saved as original images cut from the PDF, with caption, labels and a model description. No Mermaid redraw, because a wrong redraw of a safety drawing is worse than none.
- **Links** use the documents' own marks for definitions (legislation `Term`, AD B green links), each scoped to its own document. Cross-references are found by pattern; unresolved ones are logged, not guessed.
- **Citations** use the printed page number.
- **Every chunk carries its filter fields**: source, `kind`, `legal_weight` (law, statutory guidance, approved code, guidance), version, dates, `applies_to`, breadcrumb, section, printed page, URL. The breadcrumb is also put in front of the text that is embedded. Cross-references are their own records (from chunk, to section, original words, resolved or not).
- **Keyword search column from the start** (Postgres full-text, codes like "7.6.3" kept whole), so hybrid search needs no re-load. Search takes a country, England by default.
- **Pilot:** Building Regulations 2010 (current and the four 2026 versions), AD B volume 1, HSG264 and HSG227 (for the asbestos priority assessment). Done when a checklist of counts taken from the documents passes as automatic tests.

## Options considered

- Library only: free and repeatable, but the AD B tables and the duplicated Parts need judgement; rules for every case would pile up.
- Model only (page images to a model): handles tables well, but varies between runs, is slow on 200-page documents, and makes every result depend on the model.
- Mermaid redraws of diagrams: renderable and light, but most AD B diagrams are measured drawings Mermaid cannot draw, and redraw errors are a safety risk.
- Chunk by size (fixed tokens): simple, but cuts clauses in half and makes evals by section id impossible.

## Consequences

- The parser needs a fix store and a step that runs model checks in Claude Code; both must log what they did.
- Update 20 Nov 2026: the check step is built (`system/rag/checks.py`, runbook `.claude/skills/corpus-document/SKILL.md`). Checks go out as packets with fixed instructions and answer formats; answers are saved only if they pass rules, and every fix file is linted as a test. Reason: two helpers given a one-line question produced two layouts for the same kind of table (HSG227), and some HSG264 rows had no sentence.
- Asbestos as the demo scenario rests on one builder's view so far (a guess to test with more builders).
- A `country` argument, `get_section` and new passage keys (`section_id`, `applies_to`, `kind`, `legal_weight`, `printed_page`, `image_url`) change the contract in `system/rag/README.md`; agree them with the server session first.
- Embedding model, hybrid search and re-ranking stay open until the evals.
