# Official UK government routes for AI/MCP access to legislation and building guidance (as of 21 Nov 2026)

Method note: pages fetched 21 Nov 2026 with a summarising fetch tool. Quotes are as returned by that tool. Where a page did not say something, that is listed under Gaps. 13 of 21 tool calls were primary government pages.

## 1. legislation.gov.uk API (The National Archives)

### Takeaway
legislation.gov.uk has a free, keyless REST-style API: add `/data.xml` (CLML), `/data.akn` (Akoma Ntoso), `/data.html` (HTML5), `/data.pdf`, or `/data.feed` (Atom) to any legislation URL. Content is under OGL v3.0. The fair use limit is 1,500 requests per 5 minutes, and a User-Agent is required. Revised text can lag: each item shows an "up to date with all changes known to be in force on or before" date and lists outstanding (unapplied) effects. legislation.gov.uk has no official MCP server.

### Cited Findings
- Formats and file names: CLML `data.xml`, Akoma Ntoso `data.akn`, XHTML snippet `data.htm`/`data.xht`, HTML5 `data.html`, PDF `data.pdf`, Atom (feeds only) `data.feed` — [legislation.github.io formats overview](https://legislation.github.io/data-documentation/formats/overview.html)
- The site's own formats page also lists RDF/XML (`data.rdf`) — [legislation.gov.uk/developer/formats](https://www.legislation.gov.uk/developer/formats). The GitHub docs do not list RDF but mention a SPARQL endpoint for linked data — [API overview](https://legislation.github.io/data-documentation/api/overview.html)
- HTML5 is a serialisation of the AKN XML. It carries the full AKN markup plus presentation information — [formats docs (via search)](https://legislation.github.io/data-documentation/formats/overview.html)
- Versions: latest is `/ukpga/2021/1/data.xml`. As enacted is `/ukpga/2021/1/enacted/data.xml`. A URL with no date gives the current version, the same as today's date. Dated versions use a date segment, e.g. `.../1999-09-27/data.xml` — [API overview](https://legislation.github.io/data-documentation/api/overview.html). Example of a dated live URL: `/ukpga/2020/29/schedule/4/crossheading/.../2023-12-31` — [legislation.gov.uk](https://legislation.gov.uk/ukpga/2020/29/schedule/4/crossheading/amendments-of-subordinate-legislation/2023-12-31)
- API responses: 403 means the rate limit was exceeded. 202 means a dynamically generated resource (e.g. PDF) is not ready; retry after 10 seconds or more — [API overview](https://legislation.github.io/data-documentation/api/overview.html)
- Rate limit (current official page): "You must not exceed the request rate limit of 1,500 requests in any 5-minute period." Suggested polite rate is "10 requests per 5-10 seconds". A legitimate User-Agent is required, ideally with contact details. For large crawls, use the New Legislation feed and the Publication Log feed. The policy may change without notice. No AI- or LLM-specific clauses — [legislation.gov.uk/fair-use-policy](https://www.legislation.gov.uk/fair-use-policy)
- Conflict: the older GitHub data docs say 3,000 requests per 5 minutes per IP — [API overview](https://legislation.github.io/data-documentation/api/overview.html). Treat the official fair use page (1,500) as current.
- Licence: "All content is available under the Open Government Licence v3.0 except where otherwise stated". Some content comes from EUR-Lex, reused under Commission Decision 2011/833/EU — [legislation.gov.uk/developer](https://www.legislation.gov.uk/developer)
- Currency: Acts show a line like "up to date with all changes known to be in force on or before 09 July 2026", and pages say "revised legislation carried on this site may not be fully up to date". Outstanding changes appear alongside the provisions, with a "View outstanding changes" link. Changes lists are normally updated within two weeks of new legislation being published. The Changes to Legislation search can filter applied and unapplied changes — [legislation.gov.uk search results and /changes](https://www.legislation.gov.uk/changes)
- In CLML, known unapplied effects are flagged in the metadata element `<ukm:UnappliedEffects>` — [legislation.gov.uk/developer/limitations](https://www.legislation.gov.uk/developer/limitations)
- The limitations page says secondary legislation "is not revised" (except NI Orders in Council). Primary legislation is included only if it was in force at the 1 Feb 1991 base date (NI: 1 Jan 2006). It also says the data "cannot be guaranteed" for completeness or accuracy — [legislation.gov.uk/developer/limitations](https://www.legislation.gov.uk/developer/limitations). CAUTION: this page refers to the Statute Law Database (SLD) and seems old. The live site does show revised SIs (e.g. uksi/2010/93 is labelled "Latest available (Revised)") — [legislation.gov.uk](https://legislation.gov.uk/uksi/2010/93/schedule/2/part/1). These conflict, so check before relying on it.

### Inferences
- For building regs (e.g. Building Regulations 2010, SI 2010/2214) the API can return dated, revised CLML or AKN with unapplied-effects metadata. A tool should read the "up to date to" date and the unapplied effects and show them to the user. (Inference from the format docs.)
- At 1,500 requests per 5 minutes with no key, the API is fine for a small corpus harvest or live lookups. It is not meant for large crawls.

### Gaps
- No official TNA document on the size of the current revision backlog (the number of outstanding effects) was found in this pass.
- No official JSON format was found.
- The `/developer/uris` page was not fetched, so the full point-in-time URL grammar is not confirmed here.

## 2. i.AI "Lex" (Incubator for AI, with TNA)

### Takeaway
Lex is an experimental, open-access UK legal API with a public MCP endpoint at `https://lex.lab.i.ai.gov.uk/mcp`. i.AI (DSIT) built it with support from TNA, MoJ and GLD. It covers legislation from 1267 (complete from 1963), explanatory notes and amendments. Case law is "temporarily disabled pending TNA licence". The code is MIT, the data is OGL v3.0. It is rate limited to 60 requests per minute and 1,000 per hour per IP. It is not for production use.

### Cited Findings
- "UK legal API for AI agents and researchers". Labelled "EXPERIMENT": "This is an experimental service for research and non-production use." — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- MCP endpoint `https://lex.lab.i.ai.gov.uk/mcp`, over HTTP or streamable transport. Setup docs cover Claude Code, VS Code, Cursor and Copilot Studio. "No API key required — the Lex API is open access." — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- Rate limits: 60 requests per minute and 1,000 per hour per IP — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- Coverage per the GitHub README: 8.4M+ documents. 220K Acts and SIs ("1267-present, complete from 1963"), 892K legislative changes, 89K explanatory notes. Case law: 70K judgments and 4.7M paragraphs, "temporarily disabled pending TNA licence". Pre-1963 PDFs are digitised with AI — [github.com/i-dot-ai/lex](https://github.com/i-dot-ai/lex)
- "LLM transcriptions are not independently verified"; verify at source where accuracy matters — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- Search is hybrid semantic plus exact, e.g. `POST /legislation/search`. Bulk Parquet downloads update "weekly every Sunday at 03:00 UTC", with archived files kept for 4 weeks — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- Licence: code MIT, legislation data OGL v3.0 — [github.com/i-dot-ai/lex](https://github.com/i-dot-ai/lex); [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk/)
- Backend is FastAPI plus MCP. Local runs need Azure OpenAI credentials (for embeddings) — [github.com/i-dot-ai/lex](https://github.com/i-dot-ai/lex)
- i.AI is working with MoJ, Government Legal Department and The National Archives on Lex — [UKAuthority](https://ukauthority.com/articles/iai-develops-lex-tool-for-legislative-drafting) (via search snippet only)
- A Claude plugin listing, "i-dot-ai lex uk law", exists — [claudepluginhub.com](https://claudepluginhub.com/plugins/i-dot-ai-lex-uk-law) (third party, not checked)

### Inferences
- Lex is the nearest thing to an official government MCP server for UK legislation. But it is an i.AI lab experiment with no SLA, and its text comes from legislation.gov.uk with a lag of up to a week (weekly refresh). Point-in-time and outstanding-effects handling is not documented on the landing page.
- Lex indexes legislation only. It does not cover Approved Documents or HSE guidance.

### Gaps
- Launch date and last-updated date are not on the page. The MCP tool names are not listed on the landing page (they are in the API docs, not fetched).
- No separate terms of service were found.

## 3. TNA / GDS work on "AI-ready" legal data and MCP (2026)

### Takeaway
In 2026, GDS and TNA ran a National Data Library "kickstarter" on making legislation and case law AI-ready. Discovery ended in April 2026 and found the data "close to being AI ready". It tested MCP at a hackathon and found that "MCP makes a significant positive difference to the quality of AI outputs". It moved into Alpha (June 2026). No official TNA MCP server or AI dataset has been announced.

### Cited Findings
- Discovery done April 2026. A hackathon with DBT and MoJ had about 40 participants. "Early evidence indicated that MCP makes a significant positive difference to the quality of AI outputs." Next is Alpha, exploring MCP further. No public prototype is mentioned — [GDS blog, 4 Jun 2026](https://gds.blog.gov.uk/2026/06/04/data-maturity-the-foundation-for-ai-ready-public-sector-data/)
- TNA legal data was named a "kickstarter" project in the January 2026 National Data Library update — [GOV.UK NDL progress update Jan 2026](https://www.gov.uk/government/publications/national-data-library-progress-update-january-2026/national-data-library-progress-update-january-2026) (via search snippet)
- A related GDS prototype, "NDL PubSec MCP", covers data.gov.uk, not legislation. It is not a live service and has not been through a service assessment — [github.com/cyberdudeuk/ndl-pubsec-mcp](https://github.com/cyberdudeuk/ndl-pubsec-mcp) (search snippet; the repo is under a personal account, so its official status is uncertain)

### Gaps
- No public URL for any TNA or GDS legal-data MCP alpha was found.

## 4. Find Case Law (TNA)

### Takeaway
Find Case Law has a public API. Judgments are under the Open Justice Licence, which allows reading, quoting and commercial reuse but NOT computational analysis. Bulk programmatic searching or extraction needs a separate, free computational analysis licence, assessed case by case. No official MCP server exists. Lex's case law is switched off pending this licence.

### Cited Findings
- "The Open Justice Licence does not permit computational analysis." You need a licence for programmatic bulk searches across records to identify, extract or enrich content. Ordinary reading, citing and commercial use need "No permission needed, no forms to fill in and no fees to pay." API docs: https://nationalarchives.github.io/ds-find-caselaw-docs/public — [caselaw.nationalarchives.gov.uk/re-use-find-case-law-records](https://caselaw.nationalarchives.gov.uk/re-use-find-case-law-records)
- Applying for the licence is free. There are 29 questions, assessed against the Five Safes and nine MoJ principles (2023). A board meets monthly. R&D licences typically run up to 5 years. Contact: caselawlicence@nationalarchives.gov.uk — [licence application process](https://caselaw.nationalarchives.gov.uk/licence-application-process); [what you need to apply](https://caselaw.nationalarchives.gov.uk/what-you-need-to-apply-for-a-licence) (via search snippets)

### Inferences
- An MCP tool that searches case law in bulk on the user's behalf probably counts as "computational analysis" and needs the licence. Linking to or quoting single judgments does not. (Inference; confirm with TNA.)

## 5. GOV.UK (GDS): Content API, Search API, GOV.UK Chat, Approved Documents

### Takeaway
GOV.UK has a public, keyless Content API (`https://www.gov.uk/api/content/<path>`) and an unsupported Search API (`/api/search.json`), both OGL. GDS has not published an official GOV.UK MCP server. GOV.UK Chat (an AI assistant) went live in the GOV.UK app on 14 May 2026, app only, with no API. Approved Documents are published by MHCLG under OGL v3.0 (Crown copyright). The Content API gives their metadata and PDF links. The full text is PDF only: no HTML or structured version.

### Cited Findings
- Content API: "Anyone can use this API for any purpose," with "no need for onboarding or signing any agreements". OGL v3.0. It "does not allow direct access to attachments or images"; the files are linked from the content — [content-api.publishing.service.gov.uk](https://content-api.publishing.service.gov.uk/)
- Search API is at https://www.gov.uk/api/search.json with count, fields, order, filter_* and reject_* parameters. It is described as an unsupported API that may change without notice — [docs.publishing.service.gov.uk using-the-search-api](https://docs.publishing.service.gov.uk/repos/search-api/using-the-search-api.html); [gov.uk/help/reuse-govuk-content](https://gov.uk/help/reuse-govuk-content) (via search snippets)
- No official GDS MCP server for GOV.UK was found. The GOV.UK MCP servers found are third party (e.g. `govuk-mcp` on PyPI, paulieb89 on PulseMCP) — [PyPI govuk-mcp](https://pypi.org/project/govuk-mcp/0.3.1/); [PulseMCP](https://www.pulsemcp.com/servers/paulieb89-govuk)
- GOV.UK Chat: soft launch 26 Mar 2026, public launch in the GOV.UK app on 14 May 2026. Web version "in the future" — [GDS blog 14 May 2026](https://gds.blog.gov.uk/2026/05/14/gov-uk-chat-launches/); [GOV.UK news](https://www.gov.uk/government/news/millions-to-get-faster-easier-access-to-government-support-with-new-ai-tool); algorithmic transparency record: [DSIT: GOV.UK Chat](https://www.gov.uk/algorithmic-transparency-records/dsit-gov-dot-uk-chat)
- Approved Documents collection: publisher MHCLG. "All content is available under the Open Government Licence v3.0, except where otherwise stated", © Crown copyright. Latest dates: A 2013, B 16 Sep 2026, C 2013, D 2010, E 2015, F 15 Jun 2022, G 1 Oct 2024, H 2010, J 30 Sep 2022, K 2013, L 2 Feb 2023, M 1 Oct 2024, O 15 Jun 2022, P 2013, Q 22 Nov 2024, R 4 Oct 2022, S 17 Apr 2023, T 3 Nov 2025, 7 29 Nov 2018. Merged Approved Documents: 1 Oct 2024 — [gov.uk collection](https://www.gov.uk/government/collections/approved-documents)
- The same collection as Content API JSON: `document_collection`, `links.documents` with each child's `base_path` and `public_updated_at`. Collection `updated_at` is 2026-10-20 — [gov.uk/api/content/.../approved-documents](https://www.gov.uk/api/content/government/collections/approved-documents)
- Approved Document B via the Content API: the full text is PDF only (AD_B1_2026.pdf, 200 pp, about 10.1 MB; AD_B2_2026.pdf, 224 pp, about 2.5 MB), plus amendment booklets labelled 2025, 2026 and "2029". The only HTML is an FAQ page. Latest change note, 16 Sep 2026: "guidance on second stairs and evacuation lifts in taller residential buildings" — [gov.uk/api/content/government/publications/fire-safety-approved-document-b](https://www.gov.uk/api/content/government/publications/fire-safety-approved-document-b)

### Inferences
- A tool can watch Approved Document changes by polling the Content API (`public_updated_at`, `change_history`) and then download the PDFs from assets.publishing.service.gov.uk. Turning those PDFs into searchable text is our job; no official structured version exists.
- OGL allows reuse, including commercial reuse, with attribution. Material marked "except where otherwise stated" (e.g. third-party figures) needs checking per document.
- The "2029 amendments" booklet label looks odd. It may be future-dated amendments with transition periods. Unverified.

### Gaps
- The Content API rate limit is not stated on the fetched page.
- The licence of third-party material cited inside Approved Documents (e.g. BS standards) was not checked. BSI standards are not OGL (general knowledge, not verified here).

## 6. HSE / Building Safety Regulator

### Takeaway
HSE web content is under OGL v3.0, with a few exceptions (Law poster, logo, some third-party images). No HSE or BSR API or MCP for guidance was found. Priced HSE Books titles (L-series such as L153 CDM and L143 asbestos, and HSG264) are not addressed on the copyright page, so their reuse status is unconfirmed.

### Cited Findings
- "All content is available under the Open Government Licence v3.0, except where otherwise stated." Crown material can be reused "free of charge in any format or medium". Credit line: "Contains public sector information published by the Health and Safety Executive and licensed under the Open Government Licence". Exclusions: the "Health and Safety Law: what you need to know" poster suite, the HSE logo, and third-party images. Page updated 2025-08-29 — [hse.gov.uk/help/copyright.htm](https://www.hse.gov.uk/help/copyright.htm)
- HSE Books says the Law Poster and Accident Book cannot be licensed for reuse by third parties. Photos and video are licensed for a fee (e.g. £50 + VAT for up to 2 photos; older source) — [books.hse.gov.uk copyright](https://books.hse.gov.uk/copyright) (via search snippet; may be dated)

### Gaps
- Whether the free PDFs of L153, L143 and HSG264 on hse.gov.uk fall under the OGL (likely, since they are on the site, which says "all content", but not confirmed per title).
- No search was made for a BSR-specific data or API offering. None turned up in passing. Treat as "not found", not as "does not exist".

## 7. UK Parliament APIs (brief)

### Takeaway
UK Parliament runs a Bills API with an OpenAPI spec at bills-api.parliament.uk. The fetched page gave no licence or auth details.

### Cited Findings
- The Bills API exists as part of the UK Parliament Developer hub and links to an OpenAPI specification — [bills-api.parliament.uk](https://bills-api.parliament.uk/index.html)

### Gaps
- Licence (likely the Open Parliament Licence, a guess) and auth were not confirmed. No official Parliament MCP server was searched for.
