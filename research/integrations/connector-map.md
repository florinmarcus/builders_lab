# Connector map: builder tools and the Claude app

Short version of `research/reports/Builder tools and integrations.md`. Checked 19 Nov 2026. Sources are in that report and in `research/sources/links.md` (heading "Builder tools and integrations").

Main point: small builders use email, a shared drive with Excel and PDFs, accounts software and WhatsApp. Most of this connects to Claude today. What is missing is a tool that knows the jobs. That is our MCP server.

We know nothing about the real tools of Robert's 21st Century Design or FDT Construction Services. Their websites name no software. "Robert-type" and "FDT-type" below mean the kind of firm, not the firm.

## 1. Tools and how they connect

"Built-in" = in Claude's connector directory. "Official MCP" = the vendor publishes an MCP server. "API we wrap" = public API, we would write the MCP server. "Not possible" = no open API for us.

| Tool | Category | Typical user | Connect how | Cost note | Priority |
|---|---|---|---|---|---|
| Gmail | Email | Both, small firms | Built-in (made by Google). Read, search, draft, send | Free with the Claude plan | Use now |
| Google Drive, Google Calendar | Files, calendar | Both | Built-in. Maker and write scope not confirmed | Free with the Claude plan | Use now |
| Microsoft 365 (Outlook, OneDrive, SharePoint, Teams) | Email, files | Both | Built-in, made by Anthropic. Looks read-only. Writing needs our own Microsoft Graph server | Free with the Claude plan. Graph build is our time | Use now (read). Build write if pilots use it |
| Dropbox | Files | Both | Built-in, made by Dropbox. Read and write | Free with the Claude plan | Use now |
| Xero | Accounts | Both, SME default | Official MCP (local; hosted at api.xero.com/mcp/v1) | Starter tier free. Hosted needs Core, about AUD 35 a month | Use now |
| QuickBooks Online | Accounts | Both | Official MCP (local). Hosted connector reported, not confirmed | Builder tier free | Use when asked |
| Sage Accounting (cloud) | Accounts | FDT-type | API we wrap (self-serve REST). Community MCP only | Fees not found | Build if a pilot uses it |
| Sage 50 (desktop) | Accounts | FDT-type | Not possible (Windows COM, paid developer programme) | Paid programme | Skip |
| WhatsApp | Chat with clients, crews | Both, very common | API we wrap: new business number + webhook + our MCP. Cannot read existing chats or groups. API groups max 8 people | 1,000 free service messages a month; more is charged since 1 Oct 2026. Pennies per template. Needs Meta verification | Build next |
| DocuSign | Signatures | Both | Built-in / official remote MCP, open beta | Needs a DocuSign account and Claude Pro or higher | Use now (variations) |
| Adobe Acrobat Sign | Signatures | Some | API we wrap. No MCP | Production needs Enterprise, price not published | Skip |
| Procore | Project management | Larger contractors (£18M+ in case studies) | API we wrap. No official MCP for outside AI | Annual fee by turnover, not published | Build if a pilot has it |
| Fieldwire | Field app (snags, drawings) | FDT-type | API is a paid add-on, needs approval | Add-on price not public | Skip for now |
| Autodesk Construction Cloud | Documents, BIM | Larger firms | Official MCP (local, service account) | APS pricing not checked | Skip for now |
| Bluebeam | Drawings, markup | Larger firms | API with 5–7 day approval. No MCP | Needs Core or Complete plan | Skip |
| Houzz Pro | Leads, estimates, takeoffs | Robert-type (plausible, not confirmed) | Not possible (no API; Zapier imports leads into Houzz Pro only) | Zapier on Custom packages only | Skip |
| Buildertrend | Project management | Rare in UK | Not possible (partner-gated API) | n/a | Skip |
| Jobber, ServiceM8 | Trades job apps | Small trades | Official MCP (ServiceM8 confirmed; Jobber not confirmed) | Firm's own plan | Use if a firm has it |
| Fergus | Trades job app | Small trades | API we wrap (open API, token) | Not stated | Build if a pilot uses it |
| Tradify, Powered Now | Trades job apps | Small trades, UK-popular | Not possible (Tradify). Zapier only (Powered Now) | Zapier: 2 tasks per tool call; free plan 100 tasks a month | Skip |
| SafetyCulture | Inspections, H&S | FDT-type | API we wrap. Community MCP only | Needs Premium or Enterprise plan | Build if a pilot uses it |
| CHAS, Constructionline | Accreditation | Both | Not possible (no public API; partner data sharing only) | n/a | Skip. Keep the evidence files in Drive instead |
| Excel trackers, PDFs | Valuations, change logs, drawings | Both | Through the file connectors above, or upload | Free | Use now |
| Make, Zapier | Glue | Any | Make is built-in. Zapier MCP | Zapier charges per call | Use only to reach an app with no other route |

## 2. Ranked build list

1. **Gmail** (built-in). Use. Email is the main record for both firm types.
2. **Our job MCP server.** Build (the prototype). Files emails by job, lists missing items, tracks deadlines, searches the regulations. No product does this.
3. **Xero official MCP.** Use. Draft invoices in the UK demo company.
4. **Google Drive, Microsoft 365, Dropbox** (built-in). Use. RAMS, certificates, insurance and Excel trackers live here.
5. **WhatsApp Business number + webhook + our MCP.** Build next. Not ready by 21 Nov: show as "coming next", with a pasted chat export for now.
6. **DocuSign** (built-in, beta). Use. Turns a variation record into a signed one.
7. **QuickBooks official MCP.** Use when a firm asks. Same pattern as Xero.
8. **Microsoft Graph write tools.** Build only if pilot firms use Microsoft 365.
9. **Sage Accounting, Procore, Fergus, SafetyCulture.** Build only if a pilot firm uses one.
10. **Jobber, ServiceM8, Make, Zapier.** Use if a firm already has them.

Skip: Buildertrend, Houzz Pro, Tradify, Sage 50, CHAS, Constructionline, Adobe Sign, Bluebeam, Fieldwire.

## 3. Demo scenarios for 21 Nov 2026 (our proposals)

These are our ideas, not things the firms asked for. Each one is tied to a sourced pain in the report. Every answer ends in a draft a person checks.

| # | The builder says | Firm type | What happens | Connectors | Why it matters (sourced) |
|---|---|---|---|---|---|
| 1 | "The client said yes on WhatsApp. Write it up." | Robert-type | Reads a pasted chat or forwarded email. Writes a variation record (what, price, date, who). Drafts a confirmation email | Gmail, our server (DocuSign optional) | A UK court held WhatsApp messages to be a binding building contract (2025) |
| 2 | "When is my next payment notice due?" | FDT-type | Lists valuation, payment notice and pay less dates from the contract. Drafts the application from the Excel valuation | Our server, Drive or M365, Gmail draft | JCT deadlines are 5 and 14 days. A missed notice can cost the full sum |
| 3 | "Is this subcontractor ready to start?" | FDT-type, CHAS Elite firms | Checks RAMS, insurance and training records. Flags gaps and expiry dates | Our server, Drive or Dropbox | CDM: the principal contractor must check competence. CHAS: out-of-date evidence is a common failure |
| 4 | "What's missing before handover?" | Both | Lists missing items: electrical certificate, O&M manual, completion documents | Our server | O&M and H&S file are often conditions for practical completion. Warranty final inspection needs completion documents |
| 5 | "Write today's site diary." | FDT-type | Turns a chat export, photos and notes into a dated diary and a short note for the client's facilities team | Our server, Gmail draft | Site manager adverts list diaries and resident liaison. WhatsApp is often the real record |
| 6 | "Make the invoice and chase what's overdue." | Both | Creates a draft invoice in Xero. Lists overdue invoices and drafts a polite chase | Xero MCP, Gmail | Money admin is the best-measured pain (vendor surveys) |

Scenarios 1, 4 and 6 use the prototype's moments 2, 3 and 6. Scenarios 2, 3 and 5 need extra mock records for a commercial job. Keep the regulations question (prototype moment 4) for both groups.

## 4. Not verified

- What software Robert's or FDT use. Their sites name none. Ask them.
  - Update 27 Nov 2026: one design-and-build owner answered in writing (`research/interviews/builder-2.md`): Microsoft 365 Outlook, Dropbox, Excel and Monday.com, WhatsApp, no accounts software. Monday.com is not in the table above yet.
- Which tools Romanian-run UK firms use: Gmail or Outlook, Xero or Sage, Houzz Pro or nothing. Ask the room on 21 Nov.
- Microsoft 365 connector is read-only: all listed tools are search, but the page does not say so outright.
- Google Drive and Calendar connectors: maker and write support not confirmed.
- Jobber official MCP and its endpoint (third-party page only).
- QuickBooks hosted Claude connector and whether it works for UK companies.
- Procore official MCP for outside AI (competitor page only).
- DocuSign connector still in beta, and which DocuSign plan is needed.
- Exact UK WhatsApp rates in GBP (third-party figures disagree). WhatsApp coexistence mode in the UK.
- Fieldwire Enterprise API behind $5,000+ contracts (pricing tracker only).
- JCT Minor Works 2024 payment timings (the 5 and 14 days are from JCT SBC/Q).
- Software shares among small UK builders: no survey found. Most software numbers come from vendors.
