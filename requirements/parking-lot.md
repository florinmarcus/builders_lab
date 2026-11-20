# Parking lot: shortcuts, gaps and things not built

Every corner we cut goes here, so nothing is forgotten after the demo. Use it for code, architecture and security reviews.
Update it in the same commit as the shortcut. Remove an item only when it is done, and say where.

Started 20 Nov 2026. Status of the demo build: steps 1 (mock data plan), 2 (schema) and 5 (MCP server) done; 3, 4 and 6 not yet.

## Not built yet

| # | What | Why parked | Risk if forgotten |
|---|---|---|---|
| N1 | Mock email and PDF generator (20 emails, PDFs, WhatsApp export) | MCP server first | Demo has only the small seed |
| N2 | Gmail loader, reset and live simulator (ADR 0005) | Needs Google login on Florin's laptop | No live "email arrives" moment |
| N3 | Real `sync_inbox` (Gmail fetch, PDF text) | After the simulator | Tool returns "not connected yet" |
| N4 | `save_facts` with server checks (job exists, source exists, quote appears in source) (ADR 0006) | After `sync_inbox` | Facts only from seed data |
| N5 | Deployment: AWS server, HTTPS, GitHub Actions pipeline with OIDC | Needs Florin's AWS setup | Server only runs locally |
| N6 | OAuth login (Cognito) as the second auth layer (ADR 0007) | API keys first for the demo | One shared secret per firm |
| N7 | Email alerts (lockdown, failed logins, spikes) and AWS budget alarm | Come with deployment | Attacks or cost spikes go unseen |
| N8 | Backups of Postgres | Come with deployment | Data loss |
| N9 | Evals and the Claude Code mini harness (subagents, hooks, LLM judge) | Out of scope for Saturday | No measure of answer quality |
| N10 | Claude Code plugin for testers | After the demo | Manual setup per tester |
| N11 | Data deletion per property and at contract end (design rule 10) | Not needed for mock data | Fails UK GDPR expectations with real data |
| N12 | Machine-readable "AI-generated" marker (design rule 2) | Text notice only for now | Needed if we serve EU users (Art 50) |
| N13 | Romanian answers and AI notice in Romanian (ADR 0001, design rules 1 and 11) | English-first demo | Main audience is Romanian |
| N14 | Evening summary, RAMS module, WhatsApp channel (prototype priorities 2 and 3) | After priority 1 | – |

## Shortcuts taken (works, but not production)

| # | Shortcut | Where | What to do later |
|---|---|---|---|
| S1 | Tools use a small seed loaded straight into Postgres, not ingested email | `system/data/mock/db_seed.sql` | Replace with ingestion (N3, N4) |
| S2 | Regulations fallback is 7 passages; no Approved Document A, so the wall question is weak | `regulations_fallback/passages.json` | Connect the corpus session's `rag.search` |
| S3 | `rag.search` contract written by us, not yet confirmed by the corpus session | `system/rag/README.md` | Confirm with the other session |
| S4 | Payment dates count calendar days. To check: the Construction Act may exclude bank holidays, Christmas Day and Good Friday from periods of days (s116, not yet read) | `service/payments.py` | Read s116; add UK bank holidays if needed |
| S5 | Contract payment terms are invented mock values | seed data | Real terms come from the contract document |
| S6 | Required-items checklists are our own mock lists, not legal rules | `required_items` table | Agree real lists with builders |
| S7 | Rate limiter is in memory, per process; resets on restart | `mcp_server/ratelimit.py` | Fine for one server; use Redis or the database if we scale out |
| S8 | Default daily quotas picked by us (500 tool calls, 200 documents, $2 model spend) | `quotas.py`, seed | Set per plan |
| S9 | Each tool call gets its own trace id; calls in one conversation are not linked | `mcp_server/server.py` | Link by session id or harness trace id |
| S10 | Trace rows written in the request path; no OpenTelemetry | `tracing.py` | Move to OpenTelemetry later |
| S11 | Full-text search is English only | `0001_initial.sql` | Add Romanian or `simple` config |
| S12 | Demo inbox is Florin's personal Gmail; Claude's Gmail connector sees the whole inbox | ADR 0005 | Separate inbox or label-only access for real users |
| S13 | Google OAuth app in testing mode; logins may expire after 7 days | ADR 0002 | Recheck before the demo; verification for real users |
| S14 | AI notice is in the tool output; it shows only if Claude repeats it | `mcp_server/server.py` | Check in evals that answers carry it |
| S15 | Claude's own model calls (in the app or Claude Code) have no token or cost rows in our traces | ADR 0006 | Accept, or estimate from the harness |
| S16 | API keys are long-lived; rotation only on leak, staff leaving, or once a year | ADR 0007 | OAuth (N6) gives short-lived tokens |
| S17 | Lockdown and IP blocking are in memory, per process | ADR 0007 | Fine for one server |
| S18 | No CI yet: tests run by hand against a local Postgres | `tests/` | Run in the pipeline (N5) |
| S20 | Lockdown can be triggered on purpose: many bad keys in a minute pause the service for everyone (a cheap denial of service). Scanner 404s don't count | `security.py` | Put AWS WAF or CloudFront in front; lockdown only as last resort |
| S21 | Prompt injection defence is a notice in tool results plus a server instruction; no filtering of email text | `mcp_server/server.py`, instructions v2 | Add tests with poisoned emails in evals (N9) |
| S22 | Database user for the app still has full rights (no least-privilege role yet) | deployment | Create a role without DROP or DDL when deploying (N5) |
| S19 | Cost figures are first-pass, partly guesses, mostly US prices | `research/hosting-costs/connector-auth-options.md` | Review in detail; check London prices |

## Open questions

| # | Question | Where it came from |
|---|---|---|
| Q1 | Can a Claude app connector send a header API key and use OAuth at the same time? | ADR 0007 |
| Q2 | Does the Claude app have hooks? None found (20 Nov 2026) | `research/hosting-costs/connector-auth-options.md` |
| Q3 | Can a connector reach files on an iPhone? | `research/backlog.md` item 12 |
| Q5 | Which request header names does the Claude app accept for a custom connector? We accept `Authorization: Bearer` and `X-API-Key` | ADR 0007 |
| Q4 | Is a Claude Code scheduled task reliable enough for regular inbox syncs, or do we need Haiku on the server? | ADR 0006 |
