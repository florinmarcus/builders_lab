# Research summary: construction AI market and sources

Checked 7 Nov 2026. One page. Details and citations are in the linked files. Full report: `reports/Construction AI market and sources.md`.

## Key findings

1. **No Romanian offer exists.** Of about 30 AI tools and a dozen established apps, none offers Romanian Q&A over UK building rules, CDM or tax paperwork. Procore supports Polish, not Romanian. See `market/existing-solutions.md`.
2. **Each single feature is crowded and cheap in English.** Approved Document Q&A with citations (StructureGPT: free, £19, £69 a month). AI RAMS (RAMSReady: £29 one-off, £49 a month). AI quoting apps. AI receptionists (about £39 to £149 a month, unverified). Trades apps cost £25 to £45 per user per month.
3. **The legal core can be ingested.** Legislation, Approved Documents, HSE guidance and HMRC CIS/VAT guidance are under the Open Government Licence v3.0. Commercial use is allowed with attribution and no implied endorsement. See `domain/methodology-sources.md`.
4. **The sources builders quote most cannot be ingested.** British Standards, NHBC Standards, warranty manuals, RIBA Plan of Work, JCT and NEC are commercial copyright. Link and cite them, do not store them. UK law gives no commercial text-mining exception (confirmed March 2026).
5. **Paperwork grows with firm size.** Sole traders: quotes, invoices, CIS statements, scheme certificates, MTD from April 2026 if over £50,000. Small crews: monthly CIS returns and CDM client duties on homeowner jobs, which many may not know they hold. Design-and-build: CDM roles, building control, CHAS Elite, payment notices, handover packs. See `domain/user-levels.md`.
6. **Admin is done at night.** Surveys put it at about 5 to 8 hours a week, mostly evenings. Figures are soft and sponsored by software firms.
7. **The community is large but shrinking.** Romanians are about 5% of UK construction workers and about 19% in London. Our rough estimate: 100,000 to 110,000 people. Old data says two thirds are self-employed. Departures outpace arrivals. See `market/romanian-community.md`.
8. **The best channel is the Romanian Builders Network UK.** Its June 2026 event covered qualifications, CIS and VAT. Next event: 21 Nov 2026, London, 80 places.
9. **A starter glossary has 102 rows.** Only a few are sourced. Key traps: one Romanian building permit equals two UK regimes; "deviz" is not a UK quote; no UK "diriginte de șantier". See `domain/glossary.md`.

## The gap we could fill

A Romanian chat assistant over English UK sources, for small crews and CIS sole traders, not for architects. It would answer the duties small builders miss: CDM client duties on homeowner jobs, CIS returns and statements, reverse-charge invoices, written variations and quotes. Every answer would show the English clause and link. A checked glossary would keep terms right. Delivery where the community already talks, likely WhatsApp (not yet sourced).

Language alone is not a moat. Competitors can add Romanian fast, and builders may already use ChatGPT. The moat would be accuracy on terms and clauses, small-firm focus, and trust through the community.

## Open questions for Florin

1. Which user level first? The research points to small crews (2 to 10) and CIS sole traders, not design-and-build firms. Do you agree?
2. Is Robert's 21st Century Design a contact, a target customer, or only an example?
3. England only at first, or Scotland and Wales too? Scotland and Wales have their own rules.
4. Should we pay for any licence (BSI, NHBC)? Or stay on OGL sources plus links?
5. WhatsApp, web chat, or both for the first version?
6. Do we want legal advice on RAG and copyright before or after a prototype?
7. Can you attend the Romanian Builders Network event on 21 Nov 2026 (£35) to talk to builders?
8. Who can review the glossary? We need a native speaker who works in UK construction.
9. Do we touch quotes and invoices, or stay with rules and paperwork Q&A? Quoting is very crowded.

## Suggested next steps

1. Build a small OGL corpus: Building Regulations 2010, Approved Documents A to T, Manual to the Building Regulations, HSE CDM domestic-client pages and L153, HMRC CIS and reverse charge guidance. Keep edition dates as metadata.
2. Write 30 to 50 test questions in Romanian, as small builders would ask them, with expected English clauses. Use them as the first eval set.
3. Test general models (ChatGPT, Claude) on those questions in Romanian. This shows how big the gap really is.
4. Get the glossary reviewed by a native-speaker tradesperson. Turn it into a structured file for query rewriting.
5. Talk to 5 to 10 Romanian builders (network event, Facebook groups) about pain points and willingness to pay.
6. Check the unverified items: CDM construction phase plan rule, CIS 340, Scottish licence, warranty terms, Facebook group sizes.
7. Get a short legal opinion on the OGL attribution text and on linking to copyrighted standards.

## Council use case

Checked 7 Nov 2026. Full report: `reports/Council refurbishment and asbestos.md`. Details: `domain/asbestos.md`, `domain/council-contracting.md`, `market/council-contractor-tools.md`.

1. The asbestos check is the contractor's legal duty. Reg 5 of the Control of Asbestos Regulations 2012: no work that may disturb asbestos until it is ruled out or presumed.
2. For a kitchen or bathroom refit, the key document is a refurbishment and demolition (R&D) survey for that room. A management survey is not enough. "No asbestos found" is valid only for rooms the survey covered.
3. Surveys follow HSE's HSG264 (Open Government Licence). The results table has 12 fixed columns and a score from 2 to 12, so it suits extraction and mock data.
4. Councils order work per property (works order, schedule of rates). Payment within 30 days by law. Roughly 10 to 20 documents per void flat (our estimate), by portal and email. Average void costs £2,400 to £2,850.
5. Councils treat contractors as data processors. An AI tool on council email probably needs the council's written consent and UK hosting (needs legal review).
6. The gap: no tool searches a small contractor's own emails and attachments by property and cites the survey page and date. Landlords own the asbestos software. Copilot (Romanian, about £16 per user per month) is the real rival.

Open questions for Florin:
- Did Builder 1 mean asbestos (not "arson")? Can he share 2 or 3 anonymised property email threads?
- How many emails and attachments per property? Scanned or typed PDFs? Does his council use a portal?
- What does his council contract say about data sharing and outside software?
- Is the £10,000 budget per batch of properties, and how many properties per batch?
- Does he use Gmail or Outlook / Microsoft 365?

## Client and hosting costs

Checked 18 Nov 2026, USD. Details: `reports/Claude app vs Bedrock costs.md` and `hosting-costs/claude-app-vs-bedrock.md`.

1. **Own web app on Bedrock is cheaper.** About $25 a month on Haiku 5.5, $38 on Sonnet 5.5, for 2 users and about 500 questions. Most of it is the $24 Lightsail 4 GB server.
2. **The Claude app costs more.** About $64–74 a month: the same server and ingestion, plus 2 Team seats ($40–50), plus an OAuth provider (not priced).
3. **The Claude app only replaces the chat screen.** We would still build the backend, plus an MCP server on the public internet with per-user OAuth.
4. **Bedrock is easier for a council to approve.** AWS DPA with UK Addendum applies automatically, no training, Anthropic never sees the data. Processing stays in the UK/EU (EU profile), not UK-only.
5. **Claude Team means US processing** and Anthropic's sub-processors. **Pro/Max has no DPA:** mock data only.
6. **Bedrock gaps:** no batch discount for 5.5 models, rerank only in Frankfurt.
7. **Decision proposed:** London server, Claude on Bedrock, Haiku by default. Claude app for demos with mock data only.
8. **To check:** AWS credits for Claude, real tokens per PDF page, council view on US processing.

## AI regulation

Checked 18 Nov 2026. Not legal advice. Full report: `reports/EU AI Act and UK rules.md`. Short version: `domain/ai-regulation.md`.

1. EU AI Act: the Digital Omnibus (Reg. 2026/1744, in force 27 Jul 2026) delayed high-risk rules to 2 Dec 2027 (Annex III) and 2 Aug 2028 (Annex I). The duty to tell users it is AI and to mark AI text started on time, 2 Aug 2026.
2. For the England pilot, the EU Act very likely does not apply (interpretation). The UK has no AI law (Nov 2026).
3. What binds us now is UK GDPR: council = controller, contractor = processor, us = sub-processor. The council may need to approve us in writing. A DPIA is expected. This is the biggest risk.
4. About 30% of councils ask suppliers to declare AI use (LGA). Prepare a one-page AI-use statement.
5. Asbestos (CAR 2012 reg 5) and CDM duties stay with the contractor. HSE, 12 Jun 2026: existing law applies to AI. The tool finds what the survey says; it is never the assessment.
6. If we serve Romania: we are a limited-risk provider (interpretation). We need an AI notice, machine marking of AI text and AI literacy. No EU representative needed. Regulator: ANCOM (law pending, unverified).
7. Design rules: AI notice and AI-generated label from day one; cite source and date; never say "no asbestos"; no decisions about tenants or workers; AWS London.
8. Open: read the EU transparency guidelines in full, get real council data clauses, check Romanian laws, get a solicitor and an insurer view.

## Trust check of existing tools (19 Nov 2026)

1. No AI tool sold to UK builders publishes how often it is wrong: not the small tools, trades apps, big platforms or general assistants. "0% hallucination" (Struck) and "Assured Compliance" (BuildwellAI) have no evidence behind them.
2. Every tool's terms put the risk on the builder. Most small tools cap what they owe at about 12 months of fees. A competent person still signs RAMS and quotes.
3. Security evidence follows company size. Xero, Procore, Google and Anthropic publish certificates. Most small tools publish none, and five name no company number.
4. Small is not always worse: Ramsgen and RAMSReady name their AI providers, publish a DPA and say they don't train on your data. Some well-known trades apps (Tradify, Jobber) say less.
5. The biggest everyday risk is free ChatGPT or Claude: chats can train models and there is no DPA. Business plans fix most of this.
6. Only QuickBooks, Xero and Powered Now are on HMRC's MTD for VAT list.
7. Builder checklist (10 points) and scorecard: market/trust-check.md. Full report: reports/Builder AI tools trust check.md. No certificates were checked on a register.

## Builder tools and integrations

Checked 19 Nov 2026. Full report: `reports/Builder tools and integrations.md`. Short version: `integrations/connector-map.md`.

1. Small design-and-build firms and commercial contractors run on email, a shared drive with Excel and PDFs, Xero or Sage, and WhatsApp. Procore and similar platforms are mostly for bigger firms. Robert's and FDT name no software on their sites: ask them.
2. Most of this connects to the Claude app today with no build: Gmail, Google Drive, Microsoft 365 (search only), Dropbox, Xero, QuickBooks, DocuSign.
3. What nobody sells is knowing the job: which email is the variation, what is missing before handover, when the next payment notice is due. That is our MCP server.
4. WhatsApp is where variations get agreed (a 2025 court case held WhatsApp messages to be a binding contract). It needs a new business number and Meta approval, and cannot read existing chats. Show it as "coming next" on 21 Nov.
5. Build order: Gmail, our job server, Xero, file connectors, WhatsApp, DocuSign, QuickBooks. Skip Buildertrend, Houzz Pro, Tradify, Sage 50, CHAS, Constructionline.
6. Six demo scenarios (our proposals): variation from a chat, payment notice deadlines, subcontractor pack check, missing items before handover, site diary, Xero invoice and chase.
7. Open: ask the room which email, accounts and job apps they use. That decides ranks 5 to 9.
