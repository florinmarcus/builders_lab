# Claude app vs our own app on Bedrock

Checked 18 Nov 2026. Prices in USD (no source gave GBP). Full report with sources: `research/reports/Claude app vs Bedrock costs.md`.

## The question

The pilot: a small UK contractor refurbishing council flats. Our backend reads council emails and PDFs, sorts them per property and answers in Romanian. Two users at first.

Which client should they use?

- **Option A: the Claude app.** Our backend becomes a remote MCP server. Users add it as a custom connector in Claude (web, desktop, phone).
- **Option B: our own small web app.** A mobile-friendly chat page on our server. The backend calls Claude on Amazon Bedrock.

Both options need the same backend: email reading, PDF extraction, Postgres with pgvector, one small server.

## Cost per month

Our assumptions: 500 questions a month, 10,000 tokens in and 600 out per question. 7,500 pages ingested once. These are estimates, not quotes.

| Item (USD, checked 18 Nov 2026) | A: Claude app | B: own app on Bedrock |
|---|---|---|
| Server, Lightsail 4 GB | $24.00 | $24.00 |
| Questions | on the users' seats | $0.72 (Haiku 5.5) to $14.30 (Sonnet 5.5) |
| Claude seats, 2 users | $40–50 (Team, $20 yearly or $25 monthly per seat) | none |
| OAuth identity provider | needed, not priced | not needed |
| **Total per month** | **about $64–74, plus OAuth** | **about $25–38** |
| One-off ingestion (Haiku 5.5 + Titan V2) | about $2–4 | about $2–4 |

Prices used:

- Bedrock EU geo, London = Frankfurt: Haiku 5.5 $0.11 in / $0.55 out per 1M tokens. Sonnet 5.5 $2.20 / $11.00. That is the Anthropic list price plus 10%. The global endpoint is the list price.
- Titan Text Embeddings V2: London $0.0001 per 1K tokens, Frankfurt $0.0002.
- Rerank: Frankfurt only. Amazon Rerank $1, Cohere Rerank 3.5 $2 per 1,000 search units.
- Lightsail 4 GB: $24 a month flat. EC2 t4g.medium in London with disk and IPv4: about $34.
- Claude plans: Pro $20 a month ($17 yearly). Team Standard $25 a seat ($20 yearly), for 2 to 150 people.

## What we must build

- **Both:** the backend tools (email, PDFs, properties, search).
- **A only:** an MCP server on the public internet (port 443), and per-user OAuth (PKCE, dynamic client registration or CIMD). A shared API key header is beta and limited. Tool results are capped at about 150,000 characters.
- **B only:** a chat page, chat history, and a simple login (already planned in ADR 0003).

## Data protection and council approval

The council sees the contractor as its processor. Any AI service is a sub-processor the council must approve in writing.

- **B, Bedrock in London:** AWS DPA with UK Addendum applies automatically. No training. Anthropic never sees the data. Inference stays in the UK/EU (EU profile), but may leave the UK. Easiest to approve.
- **A on Team:** Anthropic DPA applies. No training by default. But processing is in the US, and the council must approve Anthropic and its sub-processors.
- **A on Pro or Max:** consumer terms, no DPA, no account sharing. Training depends on a user setting. Not for tenant data. Fine for demos with mock data.

## Risks

- **A:** reported connector sign-in failures on web, phone and Team. Usage limits with no published numbers. Anthropic can change the product. The contractor's account owner controls connectors.
- **B:** we run, patch and back up the server. No batch discount for 5.5 models on Bedrock. No rerank in London.

## Recommendation

Build **option B**: our own small web app, server in London, Claude on Bedrock (EU profile). Haiku 5.5 by default, Sonnet 5.5 where answers need it.

Use **option A only for demos** with mock data, to show Builder 1 the backend early. Keep the tools cleanly separated, so an MCP server can be added later if a council ever accepts Anthropic.

## Not verified

- Whether AWS credits ($100–200 for new accounts) pay for Claude on Bedrock.
- Whether London has in-region-only routing for any current Claude model. Anthropic's page says no; one secondary source says yes for older models.
- Which regions sit inside the Bedrock "EU" profile.
- Real tokens per PDF page and thinking-token overhead. Test on 5–10 mock PDFs.
- Rerank "search unit" and Guardrails "text unit" definitions.
- Cost of a managed OAuth provider, and which ones support DCR or CIMD.
- Claude usage limits per plan (not published).
- Whether chat uploads reach MCP tools, and how links render in Claude.
- GBP prices: no verified exchange rate.
- Whether councils accept US processing for this data. Needs a real council's view.
