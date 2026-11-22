# Commercial legal information providers with MCP servers, connectors or AI APIs (UK focus, as of 21 Nov 2026)

Research note. 15 tool calls. Many sources are vendor pages (good) but several are third-party blogs or directories (marked). Prices are mostly US and mostly reported, not official.

## Which providers actually ship an MCP server, and is it usable by a small third party building an assistant for UK builders?

### Takeaway
Thomson Reuters (CoCounsel Legal), Harvey and Legora ship official remote MCP servers. All three need an existing paid seat. Each user signs in with their own account. Thomson Reuters' terms expressly ban using its content as a retrieval or knowledge source for other AI systems, or passing it to other tools. LexisNexis has no official MCP connector. It went the other way and put Claude plugins inside Lexis+ with Protégé. vLex/Clio has no official Claude MCP for Vincent research content. None of these is a realistic, licensable data source for a third-party SaaS assistant aimed at builders.

### Cited Findings

**Anthropic "Claude for Legal" (12 May 2026)**
- On 12 May 2026 Anthropic announced 12 legal practice-area plugins plus MCP connectors to legal tools. Named partners include Thomson Reuters, Harvey, Box, Everlaw and DocuSign — [Law.com Legaltech News](https://www.law.com/legaltechnews/2026/05/12/anthropic-announces-legal-practice-plug-ins-for-claude-legal-tech-integrations/); [Artificial Lawyer](https://www.artificiallawyer.com/2026/05/12/claude-for-legal-launches-may-reshape-the-legal-tech-world/); [Quartz](https://qz.com/anthropic-claude-legal-ai-tools-law-firms-051226)
- A third-party list of launch connectors includes: CoCounsel Legal (TR), Harvey, Midpage, Trellis, Legal Data Hunter, Solve Intelligence, Relativity, Everlaw, Consilio, Ironclad, DocuSign, Definely, iManage, NetDocuments, Box, Datasite, Lawve AI, The L Suite, CourtListener (free, US), Courtroom5, Descrybe and BoardWise. Almost all are US-focused. LexisNexis is not in the list — [Claude for Lawyers blog (third-party)](https://claudeforlawyers.com/blog/mcp-connectors-for-legal)
- Connectors and plugins are available to all paid Claude customers — [Legal Practice Intelligence (secondary)](https://www.legalpracticeintelligence.com/en-us/blogs/technology-intelligence/anthropic-adds-12-legal-plug-ins-claude-connectors)
- The CoCounsel Legal listing is live in Claude's connector marketplace — [claude.com marketplace](https://claude.com/marketplace/connectors/cocounsel-legal)
- Free Law Project's CourtListener MCP (US case law) is free. Its API is free with any account since 7 May 2026 — [LawNext, May 2026](https://www.lawnext.com/2026/05/two-legal-research-providers-launch-mcp-integrations-with-claude-thomson-reuters-and-free-law-project-connect-their-data-to-ai.html)

**Thomson Reuters: CoCounsel Legal MCP connector (Westlaw, Practical Law)**
- Announced 12 May 2026 with Anthropic. It draws on about 1.9 billion Westlaw and Practical Law documents and 1.4 billion KeyCite signals. The article does not mention the UK or price — [LawNext](https://www.lawnext.com/2026/05/two-legal-research-providers-launch-mcp-integrations-with-claude-thomson-reuters-and-free-law-project-connect-their-data-to-ai.html)
- Requirements: an active Thomson Reuters account with a CoCounsel Legal package subscription. A Claude admin adds the connector once, then each user signs in with their own TR account. It also works in ChatGPT and in Microsoft 365 Copilot (web, desktop and Teams) — [TR help page](https://www.thomsonreuters.com/en-us/help/cocounsel/legal/integrations/mcp-connector/cocounsel-legal-mcp-connector)
- Tools: Ask CoCounsel (main tool), Get Run Status, Upload File, List Files, Get Deliverable, Start Chat. Research can take 10 minutes or more — [TR help page](https://www.thomsonreuters.com/en-us/help/cocounsel/legal/integrations/mcp-connector/cocounsel-legal-mcp-connector)
- Endpoint listed in Anthropic docs: `https://cocoagent-service.cocounsel.thomsonreuters.com/mcp` — [Claude Platform docs, remote MCP servers](https://platform.claude.com/docs/en/agents-and-tools/remote-mcp-servers) (reported via search summary)
- **Terms (key for us):** "Thomson Reuters offers this connector as a pilot and may modify, suspend, or withdraw it at any time." TR content may be used only for the organisation's internal business purposes. It may not be made available to other professional AI tools, or used to train models, or used as a retrieval or knowledge source for AI systems. Users must not use "always allow" or auto-approve settings that could route TR content to other tools — [TR help page](https://www.thomsonreuters.com/en-us/help/cocounsel/legal/integrations/mcp-connector/cocounsel-legal-mcp-connector)
- The marketplace listing requires a CoCounsel Legal licence, the next-generation CoCounsel, and a TR account. The June 2026 next-gen rollout started in the US, then Canada, UK and Australia. The August 2026 release extended the Claude MCP link to research, analysis and drafting — [search summary of claude.com marketplace and TR posts](https://www.thomsonreuters.com/en-us/posts/innovation/the-next-generation-of-cocounsel-legal-is-here-and-early-access-starts-now/); [TR Aug 2026 press release](https://www.thomsonreuters.com/en/press-releases/2026/august/thomson-reuters-launches-next-generation-of-cocounsel-legal-the-ai-ecosystem-built-for-legal-professionals)
- A third-party guide says the connector targets up to three US jurisdictions and sends non-US law questions elsewhere — [Claude for Lawyers blog (third-party, unverified)](https://claudeforlawyers.com/blog/mcp-connectors-for-legal)
- CoCounsel Legal (inside TR's own product) launched in the UK on 26 Jan 2026, with deep research on UK Practical Law and Westlaw — [TR post, 26 Jan 2026](https://www.thomsonreuters.com/en-us/posts/innovation/cocounsel-legal-is-redefining-professional-ai-in-the-uk-legal-market/); [Legal IT Insider](https://legaltechnology.com/thomson-reuters-expands-cocounsel-legal-to-uk-including-deep-research-on-practical-law-and-westlaw/)
- August 2026 "Deep Research Verify" checks AI claims against passages from Westlaw UK and Practical Law — [TR Aug 2026 release notes](https://www.thomsonreuters.com/en-us/posts/innovation/cocounsel-legal-august-2026-releases/)

**LexisNexis: Lexis+ with Protégé, Lexis+ UK, Lexis APIs**
- Lexis+ AI was renamed Lexis+ with Protégé in February 2026. The product page lists a Protégé API — [LexisNexis product page](https://www.lexisnexis.com/en-us/products/lexis-plus-protege.page)
- 13 May 2026: LexisNexis built Anthropic's Claude legal plugin suite into Lexis+ with Protégé. Claude runs inside Lexis, not Lexis content inside Claude — [LexisNexis on X](https://x.com/LexisNexis/status/2054556191418613939); [The Legal Wire](https://thelegalwire.ai/lexisnexis-expands-lexis-with-protege-by-integrating-anthropics-claude-legal-plugin-suite/); earlier Cowork plugin link 24/25 Feb 2026 — [Artificial Lawyer](https://www.artificiallawyer.com/2026/02/25/lexisnexis-embraces-anthropic-claude-cowork-legal-plugin/)
- No official LexisNexis connector for Claude as of 26 Sept 2026. "LexisNexis MCP" servers in directories are community-built, unverified, and would need a separate LexisNexis API licence. The API licence is "by quote" and sold separately from a Lexis+ seat — [cases.ai (third-party, a competitor)](https://cases.ai/lexisnexis-claude-connector); also [Oktopeak blog (third-party)](https://oktopeak.com/blog/lexisnexis-api-law-firm-claude/)
- LexisNexis publishes REST APIs (search and retrieve legal and news content, alerts), mainly US — [Lexis APIs page](https://www.lexisnexis.com/en-us/products/lexis-api.page)
- LexisNexis UK has construction practice notes, e.g. on section 38 of the Building Act 1984 — [LexisNexis UK construction](https://www.lexisnexis.com/en-gb/legal/construction-law/other-documents)

**Harvey**
- Hosted remote MCP server (Streamable HTTP plus OAuth). Tools: `ask_harvey`, `ask_with_knowledge_source`, `list_knowledge_sources`, `list_vault_projects`, `ask_about_vault`. Works with Claude, Gemini and Microsoft 365 Copilot. Needs a Harvey account with MCP enabled for the user. UK tax law (HMRC guidance) is given as an example knowledge source. No date on the page — [Harvey developer docs](https://developers.harvey.ai/guides/harvey_mcp)
- Harvey says it is "not responsible for how third-party services handle data once it leaves Harvey's systems" — [Harvey developer docs](https://developers.harvey.ai/guides/harvey_mcp)
- The Harvey and LexisNexis alliance (June 2025) is grounded in US primary law, US only at first — [Harvey blog](https://www.harvey.ai/blog/introducing-ask-lexisnexis); [nonbillable.co.uk](https://www.nonbillable.co.uk/news/harvey-lexisnexis-partnership)

**Legora**
- Remote MCP server with one tool, "Ask Legora", which takes a question and optional jurisdictions. Legora's own US primary-law corpus went live on 5 Aug 2026 — [search summary of Vaquill and ServiceNow community pages (third-party)](https://www.vaquill.ai/blog/do-harvey-and-legora-have-apis). Everlaw added Harvey and Legora connections on 4 Nov 2026 — [Everlaw release notes](https://support.everlaw.com/hc/en-us/articles/57880265668891-November-4-2026-Build-reusable-review-processes-with-Workflows-connect-to-Harvey-and-Legora-the-ability-to-use-Deep-Dive-to-clarify-unfamiliar-terms-without-leaving-a-document-and-more)

**vLex / Vincent (Clio) and Justis**
- No official vLex or Vincent MCP server for Claude found. A community MIT-licensed `vlex-mcp` on GitHub wraps the vLex API, which still needs a vLex licence — [GitHub RosenAdvertising/vlex-mcp](https://github.com/RosenAdvertising/vlex-mcp)
- Clio and Perplexity: Vincent connector for "Computer for Counsel", announced 24 June 2026, launching "in the coming months" — [Clio press](https://www.clio.com/about/press/clio-perplexity-partnership/)
- Vincent plugin for OpenAI Codex over MCP, 17 Sept 2026 — [Clio press](https://www.clio.com/about/press/clio-vincent-codex-plugin/)
- Sources conflict on whether Clio (practice management, not Vincent research) has a Claude directory connector (Oct 2026) — [eseospace (third-party)](https://eseospace.com/blog/clio-mcp-server/) vs [Oktopeak (third-party)](https://oktopeak.com/blog/clio-work-vs-claude-law-firms/)
- vLex Justis claims the largest online collection of UK judgments — [vLex UK coverage page](https://ca.vlex.com/coverage/united-kingdom)

**CaseMine**
- CaseMine sells a developer API, but its API page describes US data (case law, statutes, regulations). Its consumer platform covers UK Supreme Court, Court of Appeal, High Court and tribunals — [CaseMine API page](https://www.casemine.com/home/casemine-api); [CaseMine FAQ](https://www.casemine.com/home/faq)

**Free government alternative (for context, not commercial)**
- The UK government's i.AI team runs a free Lex API with an MCP endpoint for UK legislation and case law, described as fully free and open source — [lex.lab.i.ai.gov.uk](https://lex.lab.i.ai.gov.uk) (via search summary)

### Inferences
- For a small third party, the only MCP servers that "work" are per-user wrappers around the user's own paid seat. Our builders would each need a CoCounsel, Harvey or Legora licence. That is not realistic for a small building firm.
- The TR terms ban exactly what we would do: use TR content as a knowledge source alongside our own MCP tools in one Claude session. Auto-approve settings are also forbidden. Even a builder with a seat could break the terms by using it next to our connector.
- Embedding or redistributing any of these vendors' content inside our SaaS would need a separate enterprise content licence (Lexis API "by quote"; vLex API terms not published). Guess: such licences cost far more than our whole budget.

### Gaps
- Whether the TR Claude connector is open to UK CoCounsel customers today. No explicit statement found.
- Official Harvey and Legora UK content lists and their redistribution or AI-use terms. Not published on the pages read.
- vLex API terms and price. Not public.
- Luminance, Jade (an Australian free case law service), Westlaw API, Wordsmith, Garfield.law, Lawhive, LawLink and Legislate were not checked, or the search found nothing (Garfield.law and Lawhive: no API found). These need a follow-up if relevant.

## Realistic cost for a small firm or startup

### Takeaway
No UK prices are published for Westlaw UK, Practical Law, Lexis+ UK or CoCounsel. All are by quote. US list prices and reported prices suggest about $80 to $800 per user per month. API or content licences for embedding are "by quote" only. UK public-sector contracts show tens of thousands of pounds a year for organisation-wide Westlaw plus Practical Law.

### Cited Findings
- CoCounsel Legal: $784 per attorney per month (1-year plan, up to 10 attorneys), published US price as cited by a third party — [cases.ai](https://cases.ai/lexisnexis-claude-connector)
- Westlaw Advantage (US): $256.75 to $399.75 per user per month for firms of up to 10 attorneys, published US price as cited by a third party — [cases.ai](https://cases.ai/lexisnexis-claude-connector)
- Lexis+ with Protégé: no published price. Reported at about $128 to $494 per user per month. Base Lexis+ for small firms reported at about $80 to $175 — [cases.ai (reported)](https://cases.ai/lexisnexis-claude-connector)
- Westlaw (US) flat-rate plans reported at $78 to $381 per month. Practical Law (US) reported from about $115 to $119 per month, and law-firm editions at about $199 to $427 per seat per month — [TrustRadius Westlaw (reported)](https://www.trustradius.com/products/thomson-reuters-westlaw/pricing); [TrustRadius Practical Law (reported)](https://www.trustradius.com/products/thomson-reuters-practical-law/pricing); [TrustRadius comparison](https://www.trustradius.com/compare-products/thomson-reuters-practical-law-vs-thomson-reuters-westlaw)
- UK public-sector data points: the Intellectual Property Office's award for Practical Law plus Westlaw Edge was about £284,450 ex VAT over about three years. A Met Office subscription for Practical Law plus Westlaw was about £40,870 ex VAT for one year — [Find a Tender 053264-2025](https://www.find-tender.service.gov.uk/Notice/053264-2025); [Find a Tender 018722-2025](https://www.find-tender.service.gov.uk/Notice/018722-2025)
- Smaller US legal AI with Claude connectors: Midpage $100 a month (or $80 billed annually), Descrybe $25 a month, Paxton $499 a month — [cases.ai (third-party)](https://cases.ai/lexisnexis-claude-connector). All US law, not UK.
- LexisNexis API licence: by quote, separate from the seat — [cases.ai](https://cases.ai/lexisnexis-claude-connector)

### Inferences
- Guess: a UK sole trader or small builder would pay hundreds of pounds per month per seat for Practical Law Construction alone. Adding CoCounsel to get the MCP connector moves it towards the US $784 level. That is far above our pilot price range.
- These products are sold to law firms and in-house legal teams. Nothing found shows they target building SMEs. Practical Law is sold to in-house teams too, so a building firm could probably buy it (guess, not confirmed).

### Gaps
- No official UK price for any of these products. All UK figures above are either public-sector totals or US prices.
- No published price for an embedding or redistribution licence from any provider.

## Do any include Approved Documents or Building Regulations commentary?

### Takeaway
Yes, as commentary. Practical Law Construction (TR) and Lexis PSL Construction (LexisNexis UK) both have practice notes on building regulations, the Building Safety Act 2022 and construction products. Through the CoCounsel connector, Practical Law content is reachable only for CoCounsel subscribers, under internal-use terms. None of the MCP products found carries the Approved Documents text itself as a licensable dataset. The Approved Documents are free government publications anyway.

### Cited Findings
- Practical Law Construction has the note "Building regulations: an overview" (0-381-0634). It covers the Building Act 1984, the Building Safety Act 2022, higher-risk buildings, the role of Approved Documents and the 1 October 2023 building control regime (England and Wales) — [Practical Law UK](https://uk.practicallaw.thomsonreuters.com/0-381-0634?transitionType=Default&contextData=%28sc.Default%29)
- Practical Law: "Building Safety Act 2022" overview note (Construction and Property). "Construction products" note covers the new liabilities for manufacturers and suppliers. "BSA 2022: drafting issues for construction contracts" is marked as no longer maintained — [PL BSA note](https://uk.practicallaw.thomsonreuters.com/Document/Ifc1e34c21d0d11ebbea4f0dc9fb69570/View/FullText.html?ppcid=d8ce4fa3c63e49d58ff965ab90285f59&originationContext=assetPage&transitionType=KnowHowItem); [PL Construction products](https://uk.practicallaw.thomsonreuters.com/4-504-5992?transitionType=Default&contextData=%28sc.Default%29&firstPage=true); [PL BSA drafting](https://uk.practicallaw.thomsonreuters.com/w-035-9213?transitionType=Default&contextData=(sc.Default)); [About Practical Law Construction](https://uk.practicallaw.thomsonreuters.com/3-383-1079?transitionType=Default&contextData=%28sc.Default%29)
- LexisNexis UK construction content includes a practice note on section 38 of the Building Act 1984 (not yet commenced) — [LexisNexis UK construction](https://www.lexisnexis.com/en-gb/legal/construction-law/other-documents)
- The government publishes the Approved Documents and their amendment circulars for free, e.g. the circular on amendments to Approved Document B — [gov.uk circular PDF](https://assets.publishing.service.gov.uk/media/6605f132f9ab416792eea370/Circular_-_Amendments_to_Approved_Document_B_Fire_safety.pdf)

### Inferences
- The legal providers offer commentary written for lawyers (contracts, liability, the BSA regime). They do not offer practical "how do I comply with Part L on site" guidance. A builders' assistant gets more from the free primary sources (legislation.gov.uk, gov.uk Approved Documents) plus its own corpus.
- Under the TR terms, even a subscribing builder could not let our assistant use Practical Law Construction as a knowledge source.

### Gaps
- Lexis PSL Construction pages on building regulations were not returned directly. Only one LexisNexis UK construction page was found.
- Specialist building-control content providers (e.g. NBS, LABC, i-law/Informa construction law) were not covered here. They are outside the "legal information provider" scope, but they may be a better fit and are worth a separate check.
