# Prototype for the builders' meeting (Saturday 21 Nov 2026)

Status: agreed with Florin, 19 Nov 2026. Build on 20 Nov. Business prototype, not production. Mock data only.

## Goal

Show about 100 UK builders, live in the Claude app, an AI assistant that comes to where their work already is: their email, their documents, the rules, and their accounts. It must truly work and retrieve real (mock) data. Honest about what it does not do yet.

## Audience and story

Builders of every size, mostly private clients and main contractors, some council work. The demo follows one builder's day at a made-up firm.

## Priority 1: six demo moments

| # | The builder says | What happens | Needs |
|---|---|---|---|
| 1 | "What came in today?" | Lists new emails, filed by job | Email connector, filing by job |
| 2 | "Find the email where the client approved the extra work." | Finds it, quotes it, shows date and sender | Search over the firm's emails and attachments |
| 3 | "What's still missing before I can finish the Smith job?" | Lists missing items (e.g. electrical certificate, final photos) from the job's documents | Structured records per job |
| 4 | "Do I need building control to remove this wall?" | Answers from the regulations corpus, with document, section and date | Shared corpus (other session), hybrid search |
| 5 | "Draft the reply to the client." | Writes an email draft for the builder to check | Email draft (Gmail draft in the lab account) |
| 6 | "Make the invoice in Xero." | Creates a draft invoice in the Xero UK demo company | Xero official MCP connector |

## Priority 2: after priority 1 works

- **RAMS module:** draft a RAMS from the job's own documents (works order, asbestos survey), not a typed description. Never claim compliance; competent person signs.
- **WhatsApp:** check the WhatsApp Business Platform route (business number, forward messages and files). Meta approval will not be ready by Saturday: show as "coming next" unless a test number works.

## Priority 3

- Voice: check whether Claude voice mode on the phone can use custom connectors. Use it in the demo only if it works.
- Evening summary ("what came in, what's due tomorrow") sent by our server.

## How it is built

- **Interface:** the normal Claude app (Florin's account), with two connectors: ours and Xero's official MCP server (UK demo company). ADR 0004.
- **Our connector:** a small Python MCP server. Tools: `list_new_emails`, `search_documents`, `get_job`, `list_missing_items`, `search_regulations`, `create_email_draft`.
- **Email:** a separate lab Gmail account (ADR 0002). A mock sender script fills it with emails and attachments for the jobs. Read on a schedule (every 15 minutes) or on request.
- **Firm store:** structured records per job (job, client, address, document type, dates, key facts) in Postgres; documents read whole when needed. No per-firm vector store (ADR 0004).
- **Regulations:** from the corpus session (`corpus/`, `system/rag/`). Fallback if not ready: a few open documents loaded directly (e.g. Approved Document A, building control guidance on gov.uk).
- **Hosting:** public HTTPS address. Lightsail in London (ADR 0003) or a tunnel from a laptop for the demo.
- **Models:** Claude in the Claude app answers; Claude on Bedrock (Haiku) for extraction when filing emails.

## Mock data

A made-up firm, "Oakline Build Ltd", and three jobs that cover the audience:

1. **Smith bathroom, 14 Oak Street** (private client): quote, client approval of extra work by email, plumber invoice, missing electrical certificate.
2. **Patel rear extension, 3 Mill Lane** (private client, building control): drawings note, building control email, structural engineer letter.
3. **Flat 12, Riverside House** (council void): works order, asbestos survey (HSE HSG264 table), deadline.

About 15–20 emails with PDF attachments. All names, addresses and companies invented.

## Rules from the research (must show)

- AI notice on every answer path ("AI-generated, check before use").
- Every answer cites the source: email or document, page, date; regulations with document, section and edition date.
- Never say "no asbestos": say what the survey covered; "treat as present" for anything else.
- Drafts only: emails and invoices are created as drafts for a person to check and send.
- No decisions about workers or tenants.
- Mock data only. No real client data, no real council data.

## Security (show as concept)

- Each firm's data kept separate; UK storage; encryption at rest and in transit.
- Builder buys their own Claude plan: Team when handling client or tenant personal data (Anthropic DPA). Our connector stores only what it needs.
- Log every tool call (who, what, when, which sources).
- For the demo, the connector has no login (mock data only). Real use needs OAuth login.

## Out of scope for Saturday

Evals, production hosting, OAuth login, real customer data, QuickBooks (say "works the same way, next"), quotes.

## Demo script (5 minutes)

1. "What came in today?" 2. "Find the approval email." 3. "What's missing on the Smith job?" 4. "Do I need building control to remove this wall?" 5. "Draft the reply." 6. "Make the invoice in Xero." Then: what it never does, and what comes next (RAMS, WhatsApp, QuickBooks, voice).
