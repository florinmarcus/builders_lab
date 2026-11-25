# builders_lab

An AI assistant for UK building firms, first for Romanian-run firms: Claude (the user's own plan) does the thinking; our MCP server holds firm data, rules and guardrails. Research and requirements came first; a working demo with mock data is live.

## Where we are (23 Nov 2026, late evening)

**Start here: branch `claude/wonderful-wright-rd0v80`.** It holds main plus the unfinished corpus work: the ligature-glyph
fix for parse_pdf and parse_adoc, `CORPUS_REDO` and the table instruction for group headings (with tests). Fetch it and continue there. Main is the live, deployed state: merge the
branch into main only when its work is finished and its tests pass, because every push to main deploys.

- **Live:** two MCP servers on AWS London behind the same API keys (ADR 0015, since 25 Nov): firm data at `/mcp/<secret>` (11 tools) and regulations at `/mcp/<secret>/regulations` (search_regulations, lookup_terms) (`deploy/README.md`), mock firm "Marcus Limited" (`system/data/mock/`), ingestion of demo email, deterministic answer checks (`verify_answer`). Regulations search runs on the London server since 24 Nov: `corpus-db` container, 58,032 chunks from 197 sources, about 1.3 s per search with re-rank (Frankfurt RDS no longer used; Florin deletes it).
- **Built, not yet tried by users:** the Builders plugin (`plugin/`: skills, Haiku specialist agents, rules), the demo Gmail tool.
- **Regulations corpus:** parsing done for PDFs, web pages and legislation in scope (versions in force from 1 Jan 2025, ADR 0016); coverage check 0 open items, crop check clean, model checks 0 open in scope. The five laws (car2012, fso2005, housing-act-2004-p1, ess2020, awaab-regs-2025) are parsed, 9 versions in scope, coverage 0 open; their raw files are not in git or S3, so a new session fetches them again with `python -m system.rag.harvest --only car2012 fso2005 housing-act-2004-p1 ess2020 awaab-regs-2025 --accept-refetch` (S126). Semantic check (a model judges raw against parse) done on the whole sample; round 2 (S128) joined tables over pages, found HSE and leaflet headings and read two columns apart; the corpus is English only now (S130). Pages with a serious finding (judge Opus 5.5, 23 Nov): Approved Documents 12% (tables 13%), guidance PDFs 14% (tables 12%), fire guides 4%, legislation 1%, web pages 0%. Opus judge noise 1.4%. Smaller causes parked in S128 for after chunking; S131 open (`evals/experiments/P-semantic-validation.md`).
- **Next, in order:** Florin's spot check; merge this branch into main; chunk, embed, load and switch the live index; fix the gold labels (S116) and measure the baseline; then the ADR 0016 retrieval work (lanes, "too broad", get_section, read_document) and the two-server split (ADR 0015).
- **Gaps and shortcuts:** `requirements/parking-lot.md`. Read it before starting anything.

## Read first, by task

| If you are... | Read |
|---|---|
| Starting any work | this file, `requirements/parking-lot.md`, `architecture/ARCHITECTURE.md` |
| Changing a server tool or the service layer | `architecture/design/server.md`, `system/api/README.md` |
| Adding or changing an MCP tool | `.claude/skills/add-mcp-tool/SKILL.md` (runbook) |
| Changing agents, skills or answer flow | `architecture/design/agents.md`, `architecture/design/agent-contracts.md`, `plugin/README.md` |
| Changing JSON passed between agents | `system/api/builders_api/contracts.py` (source of truth), then the design doc |
| Changing the database | `system/api/builders_api/db/migrations/` (add a file, never edit one) |
| Changing security | `decisions/0007-mcp-server-security.md`, `architecture/design/server.md` |
| Deploying, upgrading, keys, kill switch | `deploy/README.md`, `decisions/0009-...md` |
| Mock data, demo emails, Gmail demo | `system/data/mock/README.md`, `decisions/0005-...md` |
| Regulations corpus or search | `system/rag/README.md` (contract), `corpus/README.md`, `.claude/skills/corpus-document/` |
| Evals, judges, prompt or retrieval tuning, graph vs vector | `evals/README.md`, `evals/knowledge/README.md` (eval knowledge base: terminology, actions, ADR seeds) |
| Research or requirements | `research/summary.md`, `requirements/prototype.md` |
| Business plan, prices, pilot | `requirements/business-plan.md`, `decisions/0014-pilot-business-model.md` |
| Language, Romanian terms, spoken answers | `decisions/0012-language-and-voice.md`, `research/domain/glossary.md` (then `python -m builders_api.terminology --build`) |
| Making a decision | `decisions/` (add an ADR) |

## Commands

```
pip install -e ".[dev]"                                   # from the repo root
TEST_DATABASE_URL=postgresql://postgres@localhost:5433/builders_test pytest -q   # that database is wiped
python -m builders_api.versions                           # fails if a locked text was edited
python -m builders_api.versions --lock                    # lock new .vN.md files
python -m builders_api.db.migrate                         # needs DATABASE_URL
python -m builders_api.mcp_server                         # local server, settings in .env.example
claude plugin validate ./plugin                           # plugin check
python system/data/mock/generate.py --today 2026-11-21    # demo emails as .eml
```

No local Postgres? Any throwaway Postgres 16 works; CI starts one (`.github/workflows/ci-deploy.yml`). Every push to `main` runs the tests and then deploys to the live server.

## Definition of done (every code change)

1. Tests pass (`pytest -q`) and `python -m builders_api.versions` passes.
2. Prompt, server instruction or tool description changed: add a new `.vN.md`, run `--lock`. Never edit a locked file.
3. Schema changed: add a new migration file. Never edit an applied one.
4. New or renamed tool: service function, `versions/tools/<name>.v1.md`, registration in `mcp_server/server.py`, the tool-name set in `tests/test_mcp_http.py`, the specialist in `plugin/agents/` and skill that use it, tool tables in `architecture/design/server.md` and `system/api/README.md`. Then reconnect the connector in the Claude app.
5. Agent JSON changed: change `contracts.py`, bump the contract version, keep the examples in `plugin/agents/*.md` valid (`tests/test_contracts.py` checks them).
6. Diagrams in `architecture/` updated in the same commit.
7. Every shortcut goes into `requirements/parking-lot.md` with a new, unique ID.
8. A decision changed: add or update an ADR.

## Rules

1. **Never invent facts about the domain.** Every claim in `research/` needs a source in `research/sources/`. Mark guesses as guesses.
2. **Mock data only.** No real customer, personal or company data in this repo. Mock data lives in `system/data/mock/`.
3. **Cost first.** Cheapest hosting and models that do the job. Prices dated, in `research/hosting-costs/` and `research/models/`.
4. **No model on our server** (ADR 0006). Model work runs in Claude on the user's plan. Server checks are plain code.
5. **Secrets never in Git.** They live in AWS Parameter Store; never print them in chat or logs.
6. **Record decisions** as short ADRs in `decisions/` (`NNNN-title.md`: context, decision, options considered, consequences). Check the next free number first.
7. **Plain English.** Short sentences, common words, no marketing language.
8. **Documents stay outside the system.** `research/`, `requirements/`, `presentation/`, `architecture/` are documents. `system/` is code only.
9. **Not related to LSEG.** Nothing from Florin's employer goes here.
10. **Keep the architecture docs current.** Diagrams first (Mermaid), little text. Link to the source of truth instead of copying lists.
11. **Park every shortcut** in `requirements/parking-lot.md` in the same commit.

## How Florin works

- Small steps. Before each step, say in a few short lines what you will do and why, then wait for his yes.
- He often listens to replies: short spoken sentences, small chunks, few tables.
- For design questions, the `grill-me` skill in `.claude/skills/` helps.

## Layout

```
AGENTS.md       this file (CLAUDE.md imports it)
research/       domain, pain points, market, costs, sources
requirements/   prototype.md (what we build), parking-lot.md (gaps and shortcuts)
presentation/   the deck and its notes
decisions/      ADRs
architecture/   ARCHITECTURE.md, design/ (server, agents, agent contracts, corpus), sequences/
corpus/         regulations corpus records (raw files in S3, not git)
plugin/         the Builders Claude plugin: skills, agents, shared rules, connectors, Claude app instructions
deploy/         CloudFormation, Docker Compose, install/upgrade/rollback scripts, IAM policy
system/
  api/          builders_api: MCP server, service layer, ingestion, security, versions, migrations
  rag/          regulations harvesting, parsing, search (other session)
  data/mock/    mock scenario, email generator, demo Gmail tool, seed SQL
tests/          tests for system/
evals/          answer quality evals (not started; parking lot N9)
.claude/skills/ runbooks for Claude Code (add-mcp-tool, corpus-document, grill-me)
.github/        CI and deploy pipeline
```

## Open questions

- Romanian answers: when, and for which users (ADR 0001)?

Answered questions are in `requirements/README.md`.

## Commits

Work on `main` and push to `main`. Pull before you push. Keep research, requirements, decisions and architecture up to date in the same change as the work.
