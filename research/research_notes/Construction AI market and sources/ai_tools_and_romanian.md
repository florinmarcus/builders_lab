# AI-first tools for UK construction businesses and tradespeople, and Romanian-language construction tools (checked 7 Nov 2026)

Scope note: all prices and features were taken from vendor pages or search results on 7 Nov 2026 unless stated. Most sources are vendor marketing, so treat feature claims as **unverified vendor claims**. Where a page was only seen as a search snippet (not fetched), that is marked "(snippet only)".

## 1. AI regulation and compliance assistants for UK construction (Building Regs, CDM, fire, BSA)

### Takeaway
This niche is already crowded with small UK startups doing cited Q&A over the Approved Documents (StructureGPT, BuildingRegs.app, ArchiChat, Struck, Regulex, Buildwell AI, plus a free open-source local tool). Prices start free and go up to about £19–£69 a month. None says it supports Romanian or any language other than English, and none is aimed at small Romanian-run trade firms.

### Cited Findings
- **StructureGPT** (Atlasync AI Ltd): plain-English chat over GOV.UK Approved Documents A–T, **England only** (no Scotland, Wales or NI). Uses "hybrid AI search" to find clauses, then answers with document, section and page citations (the RAG pattern, though it doesn't use that word). Pricing: Free £0 (50 queries/month); Basic £19/month (500 queries, 5 uploads, 10 AI images); Premium £69/month (2,000 queries, 25 uploads, team features). Disclaimer: "not professional architectural, structural engineering, or building control advice". Language support not stated. — [StructureGPT](https://www.structuregpt.co.uk/)
- **BuildingRegs.app** (Tidy Technology Ltd, London): chat assistant indexing the English and Welsh Approved Documents, Scottish Technical Handbooks, NI Technical Booklets, **CDM 2015 and HSE guidance (HSG168, GS6)**, BS 7671, BS 8300, NHBC Standards, BBA certificates, NPPF/London Plan, BREEAM and Passivhaus. Price not on the home page (separate pricing page, not checked). Languages not stated. — [BuildingRegs.app](https://www.buildingregs.app/)
- **Struck**: European regulation AI (navigation lists the Netherlands, Spain, Germany, Denmark, Poland, Norway, Belgium, UK). UK library of 81 documents (Approved Documents, Building Bulletins, HTMs), says "every answer names its clause". Claims ISO 27001 and 5,000+ users. Pricing not listed (demo/pricing page). The UK link pointed to a Dutch-language page, so UK coverage depth is unclear. It is multi-country but no Romanian or cross-language Q&A is mentioned. — [Struck UK](https://struck.eu/uk/home)
- **ArchiChat** "Building Regulations Assistant": cited answers over Approved Documents (snippet only). — [ArchiChat](https://www.archichat.co.uk/chatbot)
- **Regulex**: checks uploaded PDF drawings against selected Approved Documents with AI citations, aimed at design teams (snippet only). — [Regulex](https://regulex.co.uk/)
- **Buildwell AI**: a "UK Construction Regs Assistant" exists both as a custom GPT in the ChatGPT store and as its own web chat (snippet only; maker and price not checked). — [ChatGPT GPT](https://chatgpt.com/g/g-4zBHUMk2c-buildwell-ai-uk-construction-regs-assistant); [BuildwellAI chat](https://chat.buildwellai.com/chat/b7e953e9-5257-46f0-8697-3e8270ed8110)
- **para-building-regs** (GitHub, valtomas): free, open-source assistant for the building regulations in England that runs locally and links each cited paragraph (snippet only). — [GitHub](https://github.com/valtomas/para-building-regs)
- **Planner AI**: "compliance-first site management for UK contractors", uses a deterministic rules engine, not an LLM, to decide which Approved Documents apply (snippet only). — [Planner AI](https://plannerai.dev/)
- An ArchAdemia blog (which promotes its own tool) says general assistants (ChatGPT, Claude, Gemini) have given wrong or outdated Approved Document citations and advises checking primary sources. Not a systematic test. — [ArchAdemia](https://archademia.com/blog/how-architects-are-actually-using-ai-assistants-right-now-and-where-they-still-fall-short/)

### Inferences
- Plain "English Q&A over Approved Documents with citations" is commoditised: at least 6–8 products, with a free tier at the low end. A new product can't win on that alone.
- Coverage of the **Building Safety Act 2022 / Gateways / dutyholder duties** and **fire safety (Fire Safety Order, AD B)** was not explicitly listed by any vendor except via AD B in the Approved Documents set. BSA-specific coverage looks thin (not verified).
- Nearly all these tools are for designers (architects, design teams) not for site trades or small contractors. Their wording and pricing assume an English-speaking professional user.

### Gaps
- Pricing for BuildingRegs.app, Struck, ArchiChat, Regulex and Buildwell AI was not checked (pricing pages not fetched).
- No independent accuracy evaluations of any of these tools were found.
- Did not find any tool that states support for asking in Romanian (or any non-English language) over UK regulations. Absence of evidence, not proof; vendors' chat models might answer in Romanian if asked, but none markets it.

## 2. AI quote/estimate generators, takeoff tools, AI invoice/quote features for trades

### Takeaway
Two layers exist: (a) drawing-based AI takeoff/estimating aimed at estimators and QS (Togal.AI, Kreo, Handoff), mostly priced in USD and US-centric; (b) a crowded wave of UK AI quoting apps for tradespeople (QuickPrice, QuotePilot, Sleepless Tradesman, ToolBoxHQ, ToolsDownAI, TradeQuoteAI, QuoteSmith) where you speak, type or photograph the job and get a quote, often with free tiers. None mentions Romanian.

### Cited Findings
- **Togal.AI**: AI takeoff from drawings; about $299/user/month billed yearly per comparison sites; custom pricing for teams of 4+; described as "takeoff first", estimating done elsewhere. — [Togal llms.txt](https://www.togal.ai/llms.txt); [Capterra UK](https://www.capterra.co.uk/software/1038933/togal-ai); [Handoff comparison blog (vendor-written)](https://www.handoff.ai/blog/6-best-ai-construction-estimating-software-2026-picks-compared)
- **Kreo**: AI takeoff plus cost estimating with pricing libraries; from about $35/user/month; AI tiers reported as Plus $70, Pro $175/month; Capterra UK lists a starting price of £95. Sources disagree; check with vendor. — [Capterra UK Kreo](https://www.capterra.co.uk/software/1014073/kreo-2d-takeoff); [SourceForge UK AI takeoff list](https://sourceforge.net/software/ai-takeoff/uk/)
- **Handoff**: AI estimates for residential remodelers using localized supplier pricing (Home Depot, Lowe's: US only). Price reported as $149/month or $119/month annual; sources conflict. — [Handoff blog](https://www.handoff.ai/blog/6-best-ai-construction-estimating-software-2026-picks-compared); [TechnBrains](https://www.technbrains.com/blog/ai-construction-estimating/)
- A commentary notes Handoff's accuracy figures are for residential drawings and say nothing about commercial work. — [Bricks & Bytes](https://bricks-bytes.beehiiv.com/p/ai-reads-the-blueprint-what-it-reads-next)
- **QuickPrice** (UK): describe job by text, voice or photo; branded PDF quote; claims AI trained on current UK material prices and regional labour rates; claims 500+ tradespeople. — [QuickPrice](https://quickprice.co.uk/) (snippet only)
- **QuotePilot** (DemandPilot): spoken or typed description to line-item quote; iOS app "coming soon". — [DemandPilot](https://www.demandpilot.co.uk/) (snippet only)
- **Sleepless Tradesman**: UK AI quoting, VAT and CIS; free tier with 10 AI messages/month. — [Sleepless Tradesman](https://sleeplesstradesman.com/blog/best-quoting-apps-uk-tradespeople-2026) (snippet only)
- **ToolBoxHQ**: "AI-powered quotes in 20 seconds", free to start, 7-day Pro trial. — [ToolBoxHQ](https://toolboxhq.io/) (snippet only)
- **ToolsDownAI**: quoting over **WhatsApp**, no app download; waitlist ("coming soon"). — [ToolsDownAI](https://toolsdown.uk/) (snippet only)
- **TradeQuoteAI**: positioned as cheapest, with WhatsApp integration. — [TradeQuoteAI](https://tradequoteai.com/blog/best-quoting-apps-tradesmen-uk.php) (snippet only)
- **QuoteSmith**: AI writes scope of work, timeline and T&Cs. — [QuoteSmith comparison (vendor-written)](https://quotesmith.co.uk/blog/quoting-app-for-tradespeople-comparison.html)
- Established job-management apps: Wickes Trade's "AI tools for tradespeople, Summer 2026" page names **Tradify, Powered Now, VioTrade** as strongest UK options, with AI formatting and multi-rate VAT; a QuoteSmith comparison disputes that Tradify has AI content generation. **Fergus** from about £50/user/month. — [Wickes](https://www.wickes.co.uk/trade/ai-tools-for-tradespeople-summer-26); [QuoteSmith](https://quotesmith.co.uk/blog/quoting-app-for-tradespeople-comparison.html)

### Inferences
- A big UK merchant (Wickes) publishing an "AI tools for tradespeople" guide in 2026 suggests AI quoting is becoming mainstream for UK trades.
- Voice/photo-to-quote and WhatsApp delivery are already being copied by several small entrants, so they are table stakes, not a differentiator.
- Comparison articles are mostly written by competing vendors and contradict each other.

### Gaps
- No UK GBP price list found for Togal.AI or Handoff.
- No independent user numbers or accuracy data for the UK trade quoting apps.
- Bolt (mentioned in the brief) was not found as a construction takeoff tool in these searches; unverified whether it exists in this category.

## 3. AI RAMS / risk assessment / method statement / CPP generators (UK)

### Takeaway
Very crowded in the UK: at least 8 AI RAMS generators (RAMSReady, RAMS PRO, RAMSAI, DocGen, RAMSGen, RiskGen, RAMS Generator UK, Brightbit). Prices from free to about £15–£49/month for sole traders, up to £299/month for principal contractors. None advertises output in Romanian or other languages.

### Cited Findings
- **RAMSReady** (trading name of Bloor Engineering Ltd, Swadlincote): free RAMS quality checker vs "HSE standard"; £29 one-off document; Unlimited £49/month (7-day trial); Team £340/month for 10 seats; Vetting £149/month (for main contractors receiving subcontractor RAMS); Enterprise £299/month (PQQ/CHAS/SSIP answer tool). Also COSHH, fire assessments, induction packs, toolbox talks with attendance register. CPP not mentioned; languages not mentioned. — [RAMSReady](https://ramsready.co.uk/). (Search snippet also said "plans from £15/mo", which conflicts with the fetched page; the fetched page is preferred.) — [search snippet source](https://ramsready.co.uk/)
- **RAMS PRO**: AI RAMS for UK construction; claims outputs are "100% CDM 2015 & ISO 45001 compliant" (vendor claim, unverified). Its FAQ says HSWA 1974 requires assessments be "suitable and sufficient" without saying how they're authored (vendor's reading). — [RAMS PRO](https://www.ramspro.co.uk/) (snippet only)
- **DocGen**: walk the site on video or describe the job; drafts full RAMS, method statement **and Construction Phase Plan (CPP)**; free tier for UK contractors. — [DocGen](https://app.docgen.co.uk/) (snippet only)
- **RAMSGen**, **RAMSAI**, **RiskGen**, **RAMS Generator UK (free)**, **Brightbit Digital** also offer AI RAMS for UK trades. — [RAMSGen](https://www.ramsgen.com/); [RAMSAI](https://ramsai.co.uk/); [RiskGen](https://riskgen.ai/); [RAMS Generator UK](https://www.ramsgenerator.uk/); [Brightbit](https://www.brightbitdigital.com/services/ai-for-construction/rams-method-statements) (all snippet only)
- Language gap on site: a University of Reading / RICS piece estimates just over one in three workers may not fully understand site instructions, safety briefings or technical documents. — [RICS Built Environment Journal](https://ww3.rics.org/uk/en/journals/built-environment-journal/site-safety-risks-language-gap.html) (snippet only)
- Multilingual safety tools exist but are generic: **Navatech** (AI SafetyTech via WhatsApp/mobile), **nAI Hub** (multilingual AI safety assistant), Need2Say and toolbox-talk translation apps. No source found on RAMS translated into Romanian or Polish specifically. — [Navatech on AEC+Tech](https://www.aecplustech.com/companies/navatech-group); [nAI Hub](https://www.aecplustech.com/tools/compare/nai-hub); [Contractor Mag](https://contractormag.com/management/best-practices/article/55304492/how-translation-tech-is-revolutionizing-construction-communication-and-efficiency)
- Generic machine translation (Google Translate, Papago) mistranslated construction terms in a Korean case study, causing safety risk. — [EasyChair paper](https://easychair.org/publications/paper/6P1Q)

### Inferences
- English RAMS generation is commoditised; a Romanian product should not compete head-on but could add value as "explain/check/brief the English RAMS in Romanian" while producing the formal document in English (which is what UK principal contractors expect). This is an inference, not a vendor finding.
- Terminology accuracy is a real risk for any translation layer, so a curated EN–RO construction glossary would matter.

### Gaps
- No pricing checked for RAMS PRO, DocGen, RAMSGen, RiskGen, RAMSAI.
- No source on whether any RAMS tool outputs Romanian.

## 4. AI chat assistants for tradespeople (WhatsApp bots, voice quoting, AI receptionists)

### Takeaway
AI receptionists and missed-call/WhatsApp responders for UK trades are a crowded, low-barrier market (many small agency sites on pages.dev), priced roughly £39–£149/month. Established trade software (Powered Now) has added a Receptionist. No Romanian-language offer found.

### Cited Findings
- Many UK "AI receptionist for trades" products: call answering, missed-call text-back, SMS/WhatsApp enquiry handling. Example prices: £39/month (basic answering and booking), £59/month all-in with 14-day trial, £99/month, £149 setup plus monthly. — [Softsync AI](https://softsync-ai.pages.dev/blog-7-ai-answering-services); [Tradgo](https://tradgo-site.pages.dev/); [Alf Digital](https://alf-digital.pages.dev/); [TradesCall AI](https://tradescall-ai.pages.dev/) (all snippet only, vendor claims)
- **Powered Now Receptionist**: established UK trade job-management vendor offering a receptionist feature (snippet only). — [Powered Now](https://powerednow.com/receptionist/)
- IONOS UK publishes a guide to AI phone assistants for trades, showing mainstream interest. — [IONOS](https://www.ionos.co.uk/digitalguide/e-mail/technical-matters/ai-phone-assistant-for-trades/)
- Vendors claim tradespeople miss 40–60% of calls; one attributes it to the Federation of Master Builders. **Unverified**: original research not found. — [Softomate](https://www.softomatesolutions.com/blog/ai-voice-agent-uk-plumbers-tradesmen/)
- WhatsApp-native quoting: ToolsDownAI (waitlist), TradeQuoteAI (see section 2). Navatech uses WhatsApp for site safety capture. — [ToolsDownAI](https://toolsdown.uk/); [Navatech](https://www.aecplustech.com/companies/navatech-group)

### Inferences
- WhatsApp is the natural channel for Romanian builders (heavy WhatsApp use in the community is likely but **not sourced** here). A Romanian WhatsApp assistant would be unusual; a WhatsApp assistant per se would not.

### Gaps
- No market-size or adoption data for AI receptionists among UK trades.
- No evidence on which languages these receptionists support.

## 5. Big-vendor construction LLM/RAG products (brief)

### Takeaway
The big platforms (Procore, Autodesk, Trimble) are building agentic AI over a company's own project data (RFIs, submittals, daily logs, design). They target mid-to-large contractors on enterprise pricing, not small trade firms, and are not about UK regulation Q&A.

### Cited Findings
- **Procore Helix**: AI layer with **Procore Assist** (conversational assistant) and pre-built agents (e.g. RFI Creation Agent); **Agent Builder** went to open beta late 2025. — [Business Wire, Groundbreak 2025](https://www.businesswire.com/news/home/20251015796723/en/Procore-Advances-the-Future-of-Construction-with-New-AI-Innovations-at-Groundbreak-2025)
- Procore completed the acquisition of **Datagrid** on 20 Jan 2026; reported launch of Datagrid-based agents for submittals, RFIs and daily logs (private beta, May 2026), and embedding in its CDE aiming to cut RFI/submittal review time by 50% (June 2026). — [Verdantix](https://www.verdantix.com/insights/blog/construction-software-consolidation-heats-up-in-2026--procore-acquires-datagrid-as-hexagon-launches-multivista); [Pulse](https://www.pulse.bot/proptech/news/procore-deploys-agentic-ai-in-its-common-data-environment-to-cut-rfi-work-by-50-33e7d3ba-825c-4f8e-9575-73ede1bff844/) (aggregator; verify with Procore)
- **Autodesk Assistant**: agentic interface that detects intent and routes to multiple agents; focus mostly on design assistance. — [Gerard de Valence substack](https://gerarddevalence.substack.com/p/update-on-ai-in-construction) (secondary)
- **Trimble**: open agentic platform; Viewpoint Finance Assistant, Accubid Assistant and Trimble Connect Help Assistant expected in Trimble Labs in early 2026; one source calls it still proof-of-concept. — [Gerard de Valence substack](https://gerarddevalence.substack.com/p/update-on-ai-in-construction) (secondary)
- WSJ (Jan 2026), quoting Autodesk's Amy Bunszel: getting construction workers to use AI over pen-and-paper is still a challenge. — [WSJ via iTiger](https://www.itiger.com/hans/news/2606322733)
- Oracle Aconex: not researched (time).

### Inferences
- Big vendors are not serving sole traders or small Romanian-run firms, and do not offer Romanian UK-regulation Q&A.

### Gaps
- Oracle Aconex AI features not checked. Release status of big-vendor agents changes fast; check primary vendor pages.

## 6. Romanian-language or Romanian-community construction tools (UK and Romania)

### Takeaway
In Romania, the established "devize" (cost estimate) software market is adding AI: eDevize (Exenne Technologies) with eVision AI, and Softmagazin's Deviz 360 / WinDoc Deviz "asistate de AI". These are built around Romanian norms (HG 907/2016, SEAP tenders) and are useless for UK regs. In the UK, the Romanian builder community is organising (Romanian Builders Network UK, 2nd edition 21 Nov 2026), and one Romanian-built ERP (Abilo) sells in the UK, but no AI assistant in Romanian for UK construction rules was found.

### Cited Findings
- **eDevize / eVision AI** (Exenne Technologies, Romania): AI reads any Excel or BoQ (description, unit, quantity, no fixed format), matches each line to a norm recipe (materials, labour, equipment) from a database based on **HG 907/2016**, bulk repair/replace of recipes; demo shows 96% match; covers takeoffs to general estimate and F1–F6 forms; public tenders via SEAP Expert and private work. Price not on page; free registration and demo. Partners: Forumul Construcțiilor, SEAP Expert. — [eDevize eVision AI](https://edevize.ro/resurse/solutii-dedicate/evision-ai/); [YouTube demo](https://www.youtube.com/watch?v=lfhivGxHXRU); [Digital Romania (sponsored)](https://www.digitalromania.ro/articole/edevize_ro-cel-mai-eficient-software-pentru-crearea-devizelor-de-lucrari-constructii)
- **Deviz 360** (Softmagazin, Brașov): browser-based estimating, annual subscription, 10-day free trial; titled "program online devize asistate de AI" but no specific AI functions described beyond AI material price updates and an AI-estimates webinar. Desktop sibling WinDoc Deviz also marketed with AI suggestions. No prices on page. — [Deviz 360](https://www.deviz.ro/deviz-360.php); [deviz.ro home](https://www.deviz.ro/index.php?pag=home); [AI offer page](https://deviz.ro/oferta-soft-devize.php)
- **WindevRO**: older Romanian estimating system (devize and payment statements), dongle-protected licence; only an old euro price list found (historical). Not to be confused with PC SOFT's WINDEV development tool. No link to "Intersoft" found. — [Scribd doc](https://ro.scribd.com/doc/295889807/windev); [PC SOFT WINDEV](https://windev.com/en/offers)
- **Abilo** (Obi Systems, Romanian IT company; CEO Costin Șerban): cloud ERP for construction sold across the UK: project management, accounting, construction payroll, inspections, equipment, documents/contracts, cost tracking, BI; aimed at construction firms and self-employed trades; 2,000+ users; over £1.6M and 12 years invested; from £20/month + VAT; **no AI features mentioned**; Romanian version planned for Romania. Article dated 30 June 2025. — [Revista Biz](https://www.revistabiz.ro/un-antreprenor-roman-digitalizeaza-constructiile-din-marea-britanie-cu-un-software-in-care-a-investit-peste-16-milioane-de-lire/)
- **Romanian Builders Network UK**: started by Larisa Aramă; 1st edition June 2026 (13 June per search summary) at the Romanian Consulate General in London, with attendees from Nottingham and Doncaster; speakers on qualifications/certifications (HPL Centre), CIS and VAT tax, and financial protection. 2nd edition 21 Nov 2026, Crystals of London (NW10), 80 places, £35. Audience: Romanian contractors, subcontractors, architects, engineers, PMs, developers. The article does not mention regulations, compliance, tech or AI. — [Ziarul Românesc](https://ziarulromanesc.net/prim-plan-uk/constructorii-romani-din-uk-se-intalnesc-din-nou-la-londra-romanian-builders-network-uk-editia-a-ii-a/); [Diaspora RO](https://diasporaro.co.uk/prima-retea-a-constructorilor-romani-din-uk-s-a-lansat-la-londra/)
- A search summary said forming an association of Romanians working in UK construction was raised (from Diaspora RO coverage; not confirmed on the fetched Ziarul Românesc page). — [Diaspora RO](https://diasporaro.co.uk/constructori-romani-uk-intalnire-londra-noiembrie-2026/) (page returned empty when fetched; unverified)
- Context: a July 2026 ACORD UK / Bournemouth University report says over 1.3 million Romanians hold some form of UK residence status. — [Bursa.ro](https://www.bursa.ro/romanii-din-regatul-unit-construiesc-si-sustin-marea-britanie-63484953) (snippet only)
- **Romanian Talent Builders**: recruitment firm placing Romanian workers with UK construction companies (not software). — [Romanian Talent Builders](https://romaniantalentbuilders.com/about-us)
- **BuildersAI**: UK site-coordination app (plans, photos, compliance), UK-hosted data; not Romanian-specific; Play Store page could not be read. — [Google Play](https://play.google.com/store/apps/details?id=uk.co.buildersai.app&hl=en_US) (snippet only)

### Inferences
- Romanian devize software shows Romanian builders already accept AI in estimating, but it encodes Romanian norms, so Romanian builders in the UK have nothing native that maps to UK regs, CDM or BSA.
- The Romanian Builders Network's chosen topics (qualifications, CIS/VAT, insurance) hint that compliance-and-paperwork help is wanted, and the network is a direct channel to early users. This is an inference.

### Gaps
- No current prices for eDevize, Deviz 360 or WinDoc Deviz.
- "Intersoft" as a Romanian devize vendor could not be confirmed.
- No count of Romanian-run construction firms in the UK found.

## 7. Gaps in the market: language, small-firm pricing, UK compliance in other languages

### Takeaway
Across ~30 products found, none markets Romanian (or other non-English) Q&A over UK construction regulations, CDM or BSA. English regulation Q&A, AI RAMS, AI quoting and AI receptionists are each crowded and cheap (free to ~£50/month for small firms). The open gap is the combination: a Romanian-language assistant over English UK rules, with UK RAMS/CDM paperwork help, delivered where Romanian builders already are (likely WhatsApp).

### Cited Findings
- Regulation assistants list English-only (or unstated) language support: StructureGPT, BuildingRegs.app, Struck. — [StructureGPT](https://www.structuregpt.co.uk/); [BuildingRegs.app](https://www.buildingregs.app/); [Struck](https://struck.eu/uk/home)
- RAMS generators do not mention languages (RAMSReady checked). — [RAMSReady](https://ramsready.co.uk/)
- Small-firm price points already set: StructureGPT free/£19/£69; RAMSReady £29 one-off or £49/month; Abilo from £20/month; AI receptionists £39–£149/month; Fergus ~£50/user/month. — sources as cited above
- Site language comprehension gap: about one in three workers may not fully understand instructions or documents. — [RICS](https://ww3.rics.org/uk/en/journals/built-environment-journal/site-safety-risks-language-gap.html)
- Generic machine translation fails on construction terms. — [EasyChair](https://easychair.org/publications/paper/6P1Q)
- Multilingual safety tools exist (Navatech, nAI Hub) but are safety-briefing focused, not regulation Q&A, and Romanian support not confirmed. — [AEC+Tech Navatech](https://www.aecplustech.com/companies/navatech-group)

### Inferences
- Pricing must sit near £15–£50/month for sole traders to match the existing anchors.
- Competitors could add Romanian quickly (modern LLMs answer in Romanian if asked), so the moat would need to be community trust, curated EN–RO terminology, answers tuned to small-firm questions (CDM duties for domestic clients, Part P, BSA dutyholder roles), and distribution through the Romanian network, not language alone.
- Liability: every regulation assistant found carries a "not professional advice" disclaimer; a Romanian product would need the same, plus clear links to the English source clause.

### Gaps
- No evidence on willingness to pay among Romanian builders in the UK.
- No check on whether general chatbots (ChatGPT etc.) already serve this need informally among Romanian builders (likely, but unsourced).
- Polish-, Bulgarian- or other migrant-community UK construction AI tools not researched; they would be the closest analogues.
