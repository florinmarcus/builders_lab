# 0006: Agents live in Claude; extraction done by Claude through our MCP server

Date: 20 Nov 2026. Status: accepted for the demo and the pilot.

## Context

Florin wants all agent work in Claude (the Claude app for builders, Claude Code for us), not on our server. Our AWS server should stay simple and cheap. Filing emails needs a model to read each email and record key facts (job, document type, dates, approvals with the client's own words, expiry dates).

## Decision

- **No chat or agent model on our server.** On AWS, the only models are for the shared regulations corpus: the embedder and the re-ranker.
- **Our server does the plain work:** fetch emails and attachments from Gmail, pull text out of PDFs, store them, search them, and do date sums.
- **Claude does the extraction.** `sync_inbox` returns the new, unfiled emails with their text. Claude reads them and calls a new tool, `save_facts`, to record the job and the facts, each with its source and exact quote. The server checks every fact (known job, real email or attachment, quote found in the source text) before saving it.
- **When it runs:** when the user asks ("check my emails"), and on a schedule using a Claude Code scheduled task (hourly at most often, as of 20 Nov 2026).
- **Our harness and evals run in Claude Code:** subagents and hooks, same MCP server. Run the same golden set in Claude Code and the Claude app, and compare the server's trace rows to spot drift.
- **Distribution:** a Claude Code plugin (subagents, hooks, skills, MCP server address) for us and testers. Builders add the connector in the Claude app by its URL.

## Options considered

- **Haiku on Bedrock in the ingestion worker:** automatic on arrival, a few pence per email, but adds a model, prompts and cost tracking on our side. Kept as a fallback if scheduled Claude runs are not reliable enough.
- **No saved facts; Claude reads all emails at question time:** nothing to build, but slow, different answers each time, and no "what's missing" or deadline checks without a chat.

## Consequences

- Extraction cost moves to the user's Claude plan. Our costs: server, storage, embeddings and re-ranking.
- Model calls made by Claude are not in our trace table with tokens and cost. We still trace every tool call (inputs, sources, latency, status, tool version).
- Fact quality depends on Claude following the `save_facts` description. The server's checks (quote must appear in the source) catch invented facts.
- Facts appear only after a sync runs (by request or on schedule), not the moment an email arrives.
- `facts.prompt_version` records the `save_facts` tool description version.
