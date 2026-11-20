# Prototype for the builders' meeting (Saturday 21 Nov 2026)

Status: agreed with Florin, 19 Nov 2026. Build on 20 Nov. Business prototype, not production. Mock data only.

## Goal

Show about 100 UK builders, live in the Claude app, an AI assistant that comes to where their work already is: their email, their documents, the rules, and their accounts. It must truly work and retrieve real (mock) data. Honest about what it does not do yet.

## Audience and story

Builders of every size, mostly private clients and main contractors, some council work. The demo follows one builder's day at a made-up firm.

## Priority 1: seven demo moments

| # | The builder says | What happens | Needs |
|---|---|---|---|
| 1 | "What came in today?" | Lists new emails, filed by job | Claude's Gmail connector + our job filing |
| 2 | "Show me every change the client approved." | Finds approvals in emails and in a pasted WhatsApp chat export, quotes each with date and sender, builds a variation list | Search over emails, attachments and chat exports |
| 3 | "What's still missing before I can finish the Elm Avenue job?" | Lists missing items (e.g. electrical certificate, final photos) from the job's documents | Structured records per job |
| 4 | "Do I need building control to remove this wall?" | Answers from the regulations corpus, with document, section and date | Shared corpus (other session), hybrid search |
| 5 | "Draft the reply to the client." | Writes an email draft for the builder to check | Claude's Gmail connector (draft in the lab account) |
| 6 | "Make the invoice in Xero." | Creates a draft invoice in the Xero UK demo company | Xero official MCP connector |
| 7 | "When is the next payment notice due on the office job, and what happens if I miss it?" | Gives the date from the job's contract dates and explains the pay less notice rule, with the source | Job contract dates + regulations corpus (Construction Act) |

## Priority 2: after priority 1 works

- **RAMS module:** draft a RAMS from the job's own documents (works order, asbestos survey), not a typed description. Never claim compliance; competent person signs.
- **WhatsApp:** check the WhatsApp Business Platform route (business number, forward messages and files). Meta approval will not be ready by Saturday: show as "coming next" unless a test number works.

## Priority 2b: the Builders plugin (ADR 0005)

Package what works as a Claude plugin in `plugin/`:

```
plugin/
  .claude-plugin/plugin.json   name "builders", version, description
  .mcp.json                    our builders MCP server + Gmail, Xero, DocuSign
  shared/                      rules: sources and dates, drafts only, asbestos wording, untrusted content, personal data
  skills/
    variation-log/SKILL.md
    payment-notice-check/SKILL.md
    subcontractor-pack-check/SKILL.md
    handover-missing-items/SKILL.md
    regs-question/SKILL.md
  README.md                    install and "what you can say"
```

For Saturday, the connector alone is enough; show the plugin as the way builders will install it. Check whether plugins work in the Claude phone app.

## Priority 3

- Voice: dictation already works with connectors. Check only whether spoken voice mode (Claude talks back) can use custom connectors.
- Evening summary ("what came in, what's due tomorrow") sent by our server.

## How it is built

- **Interface:** the normal Claude app (Florin's account). Voice by dictation works today with any connector. ADR 0004.
- **Three connectors:**
  1. **Claude's own Gmail connector** reads emails and creates drafts (moments 1, 2, 5). We don't build this.
  2. **Xero's official MCP connector** with the UK demo company creates the draft invoice (moment 6). We don't build this.
  3. **Our MCP server** (small, Python) does what nobody else does: files emails and attachments by job, keeps job facts and "what's missing", and searches the regulations corpus with history (moments 2, 3, 4). Tools: `list_jobs`, `get_job`, `list_missing_items`, `search_job_documents`, `search_regulations`, `get_payment_dates` (moment 7: our code does the date sums), `sync_inbox`, `save_facts` (Claude records job and facts for new emails, ADR 0006).
- **Email:** Florin's own Gmail, with all demo mail under the label `oakline-demo` (ADR 0005). A loader imports past mock emails; a live simulator turns emails sent from his second address to `+hartley`, `+fm`, `+council`, `+mike` etc. into emails from those personas. One reset command restores the start state. Our server reads the label through the Gmail API to file by job (on request via `sync_inbox`, or every 15 minutes). Details: `system/data/mock/README.md`.
- **Firm store:** structured records per job (job, client, address, document type, dates, key facts) in Postgres; documents read whole when needed. No per-firm vector store (ADR 0004).
- **Regulations:** from the corpus session (`corpus/`, `system/rag/`). Fallback if not ready: a few open documents loaded directly (e.g. Approved Document A, building control guidance on gov.uk).
- **Hosting:** public HTTPS address. Lightsail in London (ADR 0003) or a tunnel from a laptop for the demo.
- **Models:** Claude in the Claude app answers and also extracts facts when filing emails, through our `save_facts` tool, on request or on a Claude Code schedule (ADR 0006). No chat model on our server.

## Mock data

A made-up firm, "Oakline Build Ltd", and three jobs that match the audience (all invented; no resemblance to real firms):

1. **Hartley house refurbishment, 22 Elm Avenue** (private client, high-end, design and build): client and architect emails, a pasted WhatsApp chat export where the client approves two changes, supplier quotes, missing electrical certificate and final photos.
2. **Unit 4 office refit, Kingsway Business Park** (commercial, occupied building, JCT contract, subcontractors): contract dates (valuation dates, payment terms), subcontractor documents (RAMS, insurance with expiry dates), an application for payment, facilities manager emails about working hours.
3. **Flat 12, Riverside House** (council void): works order, asbestos survey (HSE HSG264 table), deadline.

About 15–20 emails with PDF attachments. All names, addresses and companies invented.

## Rules from the research (must show)

- AI notice on every answer path ("AI-generated, check before use").
- Every answer cites the source: email or document, page, date; regulations with document, section and edition date.
- Never say "no asbestos": say what the survey covered; "treat as present" for anything else.
- Drafts only: emails and invoices are created as drafts for a person to check and send.
- No decisions about workers or tenants.
- Mock data only. No real client data, no real council data.

## Tracing, versions, quotas and errors (build in from the start)

- **Tracing:** one row per model call and per tool call: trace id, firm, tool or model, model id, prompt version, input and output tokens, cost (USD), latency, status, sources returned. Postgres tables now; OpenTelemetry later.
- **Versions:** every extraction prompt, MCP server instruction and tool description has a version id, stored in the repo and written into each trace row. Changing a prompt means a new version, never an in-place edit.
- **Quotas per firm:** daily limits on documents ingested, tool calls and Bedrock spend; rate limiting on the public MCP endpoint. Answers and extraction run on the builder's own Claude plan; our costs are embeddings, re-ranking and the server (ADR 0006).
- **Retries and errors:** retries with exponential backoff and jitter only for retryable errors (throttling, timeouts, 5xx). Typed exceptions for the rest (validation, auth, not found). MCP tools return clear structured errors, never a stack trace. Failed ingestion is logged and can be re-run.

## Security (show as concept)

- Each firm's data kept separate; UK storage; encryption at rest and in transit.
- Builder buys their own Claude plan: Team when handling client or tenant personal data (Anthropic DPA). Our connector stores only what it needs.
- Log every tool call (who, what, when, which sources).
- Connector login: API key per firm now, OAuth per person next; server hardened against bots (ADR 0007).

## Out of scope for Saturday

Evals, production hosting, OAuth login, real customer data, QuickBooks (say "works the same way, next"), quotes.

## Demo script (5 minutes)

1. "What came in today?" 2. "Show me every change the client approved" (email and WhatsApp export; mention the 2025 court case). 3. "What's missing on the Elm Avenue job?" 4. "Do I need building control to remove this wall?" 5. "Draft the reply." 6. "Make the invoice in Xero." 7. "When is the next payment notice due on the office job?" Then: what it never does, and what comes next (RAMS, WhatsApp, QuickBooks, voice).
