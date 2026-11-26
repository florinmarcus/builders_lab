# builders_lab

An AI assistant for UK building firms, first for Romanian-run firms. Claude, on the user's own plan, does the
thinking; our MCP servers hold firm data, the regulations library, rules and checks. A demo with mock data is live.

**Status, live figures and what is next:** [requirements/status.md](requirements/status.md).
**Gaps and shortcuts:** [requirements/parking-lot.md](requirements/parking-lot.md). Read both before starting.

## Branches and deploy

Every push to `main` runs the tests and deploys to the live server (`.github/workflows/ci-deploy.yml`). So work on a
branch, and merge into `main` only when the work is finished, its tests pass and Florin says yes. Pull before you
push.

## Read first, by task

| If you are... | Read |
|---|---|
| Starting any work | [status](requirements/status.md), [parking lot](requirements/parking-lot.md), [architecture](architecture/ARCHITECTURE.md) |
| Changing a server tool or the service layer | [runtime design](architecture/design/runtime/design.md), `system/api/README.md` |
| Adding or changing an MCP tool | `.claude/skills/add-mcp-tool/SKILL.md` (runbook) |
| Changing agents, skills or answer flow | [runtime design](architecture/design/runtime/design.md), `plugin/README.md` |
| Changing JSON passed between agents | `system/api/builders_api/contracts.py` (source of truth), then the runtime design |
| Changing the database | [data design](architecture/design/data/design.md), then `system/api/builders_api/db/migrations/` |
| Changing security | `decisions/0007-mcp-server-security.md`, [tool-call flow](architecture/design/runtime/flows/tool-call.md) |
| Deploying, upgrading, keys, kill switch | `deploy/README.md`, `decisions/0009-...md` |
| Mock data, demo emails, Gmail demo | `system/data/mock/README.md`, `decisions/0005-...md` |
| Regulations corpus: harvest, parse, checks, load | [ingest design](architecture/design/ingest/design.md), `corpus/README.md`, `.claude/skills/corpus-document/` |
| Regulations search | `system/rag/README.md` (contract), [search flow](architecture/design/runtime/flows/search-regulations.md) |
| Evals, judges, retrieval tuning | [eval design](architecture/design/eval/design.md), `evals/PLAN.md`, `evals/knowledge/README.md` |
| Research or requirements | `research/summary.md`, `requirements/prototype.md` |
| Business plan, prices, pilot | `requirements/business-plan.md`, `decisions/0014-pilot-business-model.md` |
| Language, Romanian terms, spoken answers | `decisions/0012-language-and-voice.md`, `research/domain/glossary.md` (then `python -m builders_api.terminology --build`) |
| Docs layout | `decisions/0020-*.md` |
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

No local Postgres? Any throwaway Postgres 16 works; CI starts one.

## Definition of done (every change)

1. Tests pass (`pytest -q`) and `python -m builders_api.versions` passes.
2. Prompt, server instruction or tool description changed: add a new `.vN.md`, run `--lock`. Never edit a locked file.
3. Schema changed: add a new migration file. Never edit an applied one.
4. New or renamed tool: follow `.claude/skills/add-mcp-tool/SKILL.md`, then reconnect the connector in the Claude app.
5. Agent JSON changed: change `contracts.py`, bump the contract version, keep the examples in `plugin/agents/*.md`
   valid (`tests/test_contracts.py` checks them).
6. Docs in `architecture/` and [status](requirements/status.md) updated in the same commit. Diagrams first
   (Mermaid), little text, link to the source of truth instead of copying lists (ADR 0020).
7. Every shortcut goes into `requirements/parking-lot.md` with a new, unique ID, in the same commit.
8. A decision made or changed: add an ADR. Never rewrite an accepted one.

## Rules

1. **Never invent facts about the domain.** Every claim in `research/` needs a source in `research/sources/`. Mark
   guesses as guesses.
2. **Mock data only.** No real customer, personal or company data in this repo. Mock data lives in `system/data/mock/`.
3. **Cost first.** Cheapest hosting and models that do the job. Prices dated, in `research/hosting-costs/` and
   `research/models/`.
4. **No model on our server** (ADR 0006). Model work runs in Claude on the user's plan. Server checks are plain code.
5. **Secrets never in Git.** They live in AWS Parameter Store; never print them in chat or logs.
6. **Record decisions** as short ADRs in `decisions/` (`NNNN-title.md`: context, decision, options considered,
   consequences). Check the next free number first.
7. **Plain English.** Short sentences, common words, no marketing language.
8. **Documents stay outside the system.** `research/`, `requirements/`, `presentation/`, `architecture/` are
   documents. `system/` is code only.
9. **Not related to LSEG.** Nothing from Florin's employer goes here.

## How Florin works

- Small steps. Before each step, say in a few short lines what you will do and why, then wait for his yes.
- He often listens to replies: short spoken sentences, small chunks, few tables.
- For design questions, the `grill-me` skill in `.claude/skills/` helps.

## Layout

```
AGENTS.md       this file (CLAUDE.md imports it)
research/       domain, pain points, market, costs, sources
requirements/   status.md, prototype.md, parking-lot.md, business plan
presentation/   the deck and its notes
decisions/      ADRs
architecture/   ARCHITECTURE.md and design/ (runtime, data, ingest, eval)
corpus/         regulations corpus records (raw files in S3, not git)
plugin/         the Builders Claude plugin: skills, agents, shared rules, connectors, Claude app instructions
deploy/         CloudFormation, Docker Compose, install/upgrade/rollback scripts, IAM policy
system/
  api/          builders_api: MCP servers, service layer, ingestion, security, versions, migrations
  rag/          regulations harvesting, parsing, chunking, search
  data/mock/    mock scenario, email generator, demo Gmail tool, seed SQL
tests/          tests for system/
evals/          golden set, retrieval and answer evals, judges, gate
.claude/skills/ runbooks for Claude Code
.github/        CI and deploy pipeline
```

Open questions and answered ones: `requirements/README.md`.
