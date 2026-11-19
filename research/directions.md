# Product directions

Updated 19 Nov 2026.

## Positioning (agreed with Florin, 19 Nov 2026)

- **Romanian is a secondary point, not the selling point.** Competitors already answer in Romanian because the models do (tested on RAMSReady, 19 Nov 2026).
- **Modules, not one feature.** Core: email and documents (read, file by job or property, search with sources). Next: RAMS, built from the job's own documents (works order, asbestos survey) instead of a typed description. Quotes: lowest priority (crowded, less painful).
- **What we sell:** a standard core plus a short setup per company (connecting their messy data), domain knowledge built into extraction and checks, and trust: tested answers with published accuracy, open security and data terms. Prompts and models are not the selling point: they are easy to copy and the same for everyone.
- **Risk:** custom setup per company turns into consultancy. Keep a standard core; make setup short and repeatable.
- **Input channels:** email first; WhatsApp next (builders get many messages and files there). See backlog.

## Business model to test (agreed with Florin, 19 Nov 2026)

- **Interface: the normal Claude app** (web, desktop, phone, with voice). Not Claude Code (developer tool, paid plan, permission prompts). The app gives compaction, memory, voice, file uploads and mobile for free; rebuilding that is hard.
- **Each builder buys their own Claude plan:** Team for firms handling client or tenant personal data (Team includes Anthropic's DPA); possibly Pro for a sole trader with no personal data.
- **They add our MCP connector:** email, documents, WhatsApp, Xero or QuickBooks, our UK storage behind it.
- **We charge for the connector and the setup.** Price to test on 21 Nov 2026 (suggestion, not a fact): about £30–60 a month per firm plus a setup fee of a few hundred pounds. Benchmarks: trades apps £25–45 per user a month, RAMSReady £49, Copilot about £16 on top of Microsoft 365.
- **Not:** reselling Team seats from one account (likely needs a reseller agreement; mixes customers' data under one admin).
- **Later option:** our own app on the Claude Agent SDK or Managed Agents (same engine, our screens). No voice out of the box.
- **To check:** whether Claude voice mode can use custom connectors; UK prices in GBP for Pro and Team.


## Chosen to explore first: council refurbishment contractors

From Builder 1 (`interviews/builder-1.md`). Small firms refurbishing council flats get many emails and documents per property from the council. They need to find things fast, e.g. where the asbestos is in a property. First use case: search over their own emails and attachments, organised by property, with the source document and page always shown.

## A. Companion

A Romanian layer over the English tools builders already use (QuickBooks, Tradify, RAMSReady): explain documents and rules in Romanian, write English text to paste in. See `market/walkthrough.md`.

## B. AI-first system

For builders with no system: email (read, draft replies), calendar, client and property database, "copy a similar job", full documentation. Romanian-first. The council use case is the first slice of B.

## Still unknown

- What most Romanian builders use today (one interview so far).
- Whether council contractors are a big enough group.
