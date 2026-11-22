# 0015: Two MCP servers: public regulations and private firm data

Date: 22 Nov 2026. Status: proposed (Florin to confirm). Changes ADR 0004 (one MCP server in front of both stores),
and touches ADR 0007 (security), ADR 0009 (deploy) and ADR 0011 (plugin).

## Context

Today one MCP server, BuildersMCP, holds 12 tools: 10 for one firm's data, and 2 general ones (`search_regulations`
and `lookup_terms`). Florin finds the mix awkward. The facts behind that:

- **The data differs.** The regulations are public text, mostly OGL, and the same for every firm. Firm data
  (jobs, emails, documents, facts) is private to one firm. Today both sit behind the same key and in the same
  process. So a bug in regulation search runs next to private data.
- **They change at different speeds.** The corpus is rebuilt and re-measured often (`evals/PLAN.md`). Firm tools
  change with product features. Today every corpus change ships with the firm server, and the reverse.
- **More general tools are coming.** The library tool (`about_regulations_library`, parking lot S100) belongs with
  the regulations, not with one firm's jobs.
- **Reuse.** A regulations-only server could serve every firm, other apps, or a free taster, without exposing
  anything private. Government and community servers already offer this for legislation alone
  (`evals/experiments/X-external-mcp.md`).
- **The links between the two are few.**
  - `verify_answer` checks regulation quotes against the corpus (`service/verify.py`, `_regulation_passage`).
  - `get_payment_dates` tells the agent to use `search_regulations` for what the law says.
  - Both are calls inside the service layer, not calls between MCP tools.

## Decision

Split into two MCP servers. Both come from the same codebase and run on the same machine, with one deploy.

| Server | Tools | Data | Access |
|---|---|---|---|
| **Regulations** (public knowledge) | `search_regulations`, `lookup_terms`, later `about_regulations_library` | corpus (read-only database user), glossary | firm keys only; no open access (Florin, 22 Nov: we demo to firms, so nothing needs to be open) |
| **Firm** (private) | `get_firm_profile`, `lookup_terms` (also here, Florin 22 Nov), `list_jobs`, `get_job`, `get_job_timeline`, `search_job_documents`, `list_missing_items`, `get_payment_dates`, `sync_inbox`, `save_facts`, `verify_answer` | firm database | per-firm key, every query filtered by firm (ADR 0007, unchanged) |

Rules:
- **No firm data on the regulations server.** It has no firm database connection at all, not only no tool for it.
  Its questions may still mention a job, so its logs follow the same rules as now.
- **The firm server checks quotes through the shared code**, as now. It does not call the regulations server over
  MCP. One process per server keeps the two failure areas apart; the shared Python package keeps one source of
  truth.
- **Two endpoints, two paths, two key sets**, behind the same hardening: rate limits, lockdown, kill switch,
  unknown paths 404 (ADR 0007).
- **Server instructions split too.** Rules about firm data (approvals, drafts only, no worker decisions) go to the
  firm server. Rules about citing regulations, asbestos wording and "the library does not cover that" go to the
  regulations server. Rules for both (language, speak first) go to both. New `.vN.md` files, locked.
- **The plugin knows both.** Claude Code installs get both connectors from `plugin/.mcp.json`. In the Claude app,
  connectors are added by hand, so the set-up guide adds a second line.

**When:** after the parse and retrieval work in `evals/PLAN.md`, and before the library tool, so that tool lands on
the regulations server from the start.

## Options considered

- **Keep one server (today).** Simplest for builders: one connector. But it keeps public and private data in one
  process, and couples corpus releases to firm releases.
- **Two separate codebases and machines.** The cleanest isolation. But it doubles the deploys, the costs and the
  shared code (terminology, versions, security) for no gain at pilot size.
- **One server with two scopes on one key** (a key that may use only the regulations tools). Less set-up, but the
  same process still holds both, and it does not give a public regulations server later.
- **Use Lex or another public server for law, and keep only firm data.** Rejected on the numbers: no server covers
  HSE guidance or Approved Document passages (`evals/experiments/X-external-mcp.md`).

## Consequences

- **Builders in the Claude app add two connectors instead of one.** This is the real cost, because they are not
  technical. To soften it: one set-up sheet with both lines, the same key format, and later OAuth (ADR 0007) to
  remove the keys.
- **Tool and test changes:**
  - Tool registrations move to two server modules, and `tests/test_mcp_http.py` gets two tool-name sets.
  - The specialists in `plugin/agents/` name tools from both servers; tool names stay the same.
  - `verify_answer` is unchanged.
- **Deploy:** one Docker image, two server processes (or one process with two apps on two paths). It costs almost
  nothing extra on the same EC2 machine (ADR 0009). The health check covers both.
- **Docs to update with the build:** `architecture/ARCHITECTURE.md` and `architecture/design/server.md` (diagrams
  and tool tables), `system/api/README.md`, `deploy/README.md`, `plugin/README.md`, the Claude app instructions.
- **Later options this opens:**
  - per-server quotas
  - a separate release cycle for the corpus
- **Answered by Florin (22 Nov):**
  - No open access: the regulations server takes firm keys only. Firms see it in demos. This also keeps the
    copyrighted clause titles (BS 5250, JCT) to firms with a key.
  - `lookup_terms` is on both servers.
- **Still open, to settle before the build:**
  1. *(Settled: no open access, so no keyless cost or licence question.)*
  2. **Query logs.** Questions can name a job or a person. Decide what the regulations server logs and how long it
     keeps the logs.
  3. **Which key works where.** Simplest: a firm's one key works on both servers. Then the expiry warnings and
     "access ended" message (ADR 0007) apply to both.
  4. **Dates across servers.** The right edition depends on the job's dates (for example, AD B before or after
     2029). The agent gets the dates from the firm server and passes them to search. Today search does not take a
     date, so the specialist and the search tool need a clear date argument.
  5. **One source for shared rules.** The language and "speak first" rules go to both servers. Keep them in one
     versioned text, used by both, so they cannot drift.
  6. **One trace across two servers.** One answer will call both servers. The trace id (plan step 5, S9) must pass
     through both.
  7. **Connector names and the switch.** Rename BuildersMCP to two clear names. Existing users reconnect once.
     Plugin evals and judges must connect both.
