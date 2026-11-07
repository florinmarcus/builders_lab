# builders_lab

A research lab that may become a product: an AI assistant (agentic RAG) for building and construction businesses, aimed first at the Romanian community.

We don't know the domain yet. Research and requirements come first, then a presentation, then a cheap technical solution with mock data.

## Phases

1. **Research** (`research/`): learn the business domain, find the pain points, look at the market and competitors.
2. **Requirements** (`requirements/`): who the users are, what problems we solve, what's in and out of scope.
3. **Presentation** (`presentation/`): the first deliverable. It explains the domain, the pain points, the proposed solution and the costs.
4. **Technical solution** (`system/`, `tests/`, `evals/`): a website (not a mobile app) with a backend, agentic RAG and mock data.

Don't start building in `system/` before the research and requirements that justify it exist.

## Open questions (answer before going deep)

- Which businesses exactly? Construction and renovation firms, sole-trader tradespeople, suppliers, or building management?
- Where? Romanian-run businesses in the UK, businesses in Romania, or both?
- Which language should users see: Romanian, English or both?
- Who pays, and how much would they pay?

When one is answered, move it into `requirements/` and delete it here.

## Rules

1. **Never invent facts about the domain.** Every claim in `research/` needs a source (link, document or interview note) in `research/sources/`. Mark guesses as guesses.
2. **Mock data only.** No real customer, personal or company data in this repo. Mock data lives in `system/data/mock/`.
3. **Cost first.** Choose the cheapest hosting and models that do the job. Compare options in `research/hosting-costs/` (AWS, Azure AI Foundry, Google Cloud, others) and `research/models/`, with prices and the date checked. Prices change, so always date them.
4. **We must be able to run models.** We already have model access. The hosting choice has to support it.
5. **Website, not an app.** Assume a mobile-friendly website unless research shows a strong reason for an app.
6. **Record decisions** as short ADRs in `decisions/` (`NNNN-title.md`: context, decision, options considered, consequences).
7. **Plain English.** Short sentences, common words, no marketing language.
8. **Research stays outside the system.** `research/`, `requirements/` and `presentation/` are documents. `system/` is code only.
9. **Not related to LSEG.** Nothing from Florin's employer goes here.

## Layout

```
AGENTS.md       this file (CLAUDE.md imports it)
research/       domain knowledge, pain points, market, hosting and model costs, sources
requirements/   users, use cases, scope, non-functional needs (cost, language, privacy)
presentation/   the deck and its notes
decisions/      ADRs
system/         the application
  web/          website (frontend)
  api/          backend API
  agents/       agent logic and tools
  rag/          ingestion, chunking, retrieval
  data/mock/    mock businesses, documents and conversations
tests/          unit and integration tests for system/
evals/          retrieval and answer quality evals (test questions, expected answers, scoring)
```

## Commits

Work on `main` and push to `main`. Keep research, requirements and decisions up to date in the same change as the work.
