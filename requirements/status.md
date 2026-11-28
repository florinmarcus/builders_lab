# Status

Where the project is now. The one place for live figures and status (ADR 0020); AGENTS.md and ADRs link here.
Update this file in the same change as the work. Updated 26 Nov 2026.

## Branch

Work in progress is on branch `claude/wonderful-wright-rd0v80`: main plus the corpus work (ligature-glyph fix for
`parse_pdf` and `parse_adoc`, `CORPUS_REDO`, the table instruction for group headings, with tests), the eval work
(rule coverage, gate, answer-set judge) and the docs rebuild (ADR 0020). Main is the live, deployed state. The branch
goes into main only when its work is finished, its tests pass and Florin says yes.

## Live

- Two MCP servers on AWS London behind the same API keys (ADR 0015): firm data at `/mcp/<secret>` (12 tools; `show_today` opens a card in the chat; each firm gets its own client file with the instructions; both on the branch until merged) and
  regulations at `/mcp/<secret>/regulations` (3 tools). Tool list: `system/api/README.md`. Deploy: `deploy/README.md`.
- The same gateway also serves the separate planning-harvest MCP server at `/planning/mcp/<key>` (ADR 0024).
- Mock firm "Marcus Limited" (`system/data/mock/`), ingestion of demo email, plain-code answer checks
  (`verify_answer`).
- Regulations search on the London server since 24 Nov 2026: `corpus-db` container, 58,032 chunks from 197 sources,
  about 1.3 s per search with re-rank.

## Built, tried by Florin only

- The Builders plugin (`plugin/`): skills and rules; Haiku sub-agents only for big jobs (ADR 0019).
- The demo Gmail tool.

## Regulations corpus

- Parsing done for PDFs, web pages and legislation in scope (versions in force from 1 Jan 2025, ADR 0016). Coverage
  check 0 open items, crop check clean, model checks 0 open in scope. English only (S130).
- The five laws (car2012, fso2005, housing-act-2004-p1, ess2020, awaab-regs-2025) are parsed, 9 versions in scope.
  Their raw files are not in git or S3; a new session fetches them again with
  `python -m system.rag.harvest --only car2012 fso2005 housing-act-2004-p1 ess2020 awaab-regs-2025 --accept-refetch`
  (S126).
- Semantic check (a model judges raw against parse, judge Opus 5.5, 23 Nov 2026), pages with a serious finding:
  Approved Documents 12% (tables 13%), guidance PDFs 14% (tables 12%), fire guides 4%, legislation 1%, web pages 0%.
  Judge noise 1.4%. Smaller causes parked in S128; S131 open. Details: `evals/experiments/P-semantic-validation.md`.

## Evals

Plan and step status: [evals/PLAN.md](../evals/PLAN.md). Rule coverage is the main score since 25 Nov 2026; no
baseline is set yet (S151, S153).
Answer judge: design agreed 26 Nov 2026 (ADR 0021); reference answers cleaned (S146); the first Sonnet run on dev stopped at 17 of 342 on the demo firm's daily limit; next, the eval key (S161), then the run.

## Next, in order

1. Florin's spot check of the corpus and a sample of rules and verdicts.
2. Merge the branch into main.
3. Chunk, embed, load and switch the live index.
4. Set the eval baseline (S151) and measure.
5. The ADR 0016 retrieval work: lanes, "too broad", `get_section`, `read_document`.

Gaps and shortcuts: [parking-lot.md](parking-lot.md).
