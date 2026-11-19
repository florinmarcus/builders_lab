# Trust check: small AI-first tools for UK builders (as of 19 November 2026)

All pages were checked on 19 Nov 2026 unless stated otherwise. The pages were read as raw HTML text with curl, plus web search. Some sites only render with JavaScript, so their legal pages could not be read. Where that happened it is marked "could not read" rather than "not stated". "Not stated" means the page loaded and did not say it. I did not create accounts or test the products, and I checked no certificate against a certifier's register.

Tools not found: **ArchiChat** (no product found by search; archichat.co.uk and archichat.ai did not load) and **RiskGen** (no product found; riskgen.co.uk and riskgen.ai did not load). **Regulex** (regulex.co.uk) is a JavaScript-only page: only its title loaded. **ToolBoxHQ** (toolboxhq.co.uk) turned out to be a health and safety records tool, not a quoting app, so it may not be the product meant.

## 1. Regulation assistants: what they claim and what backs it

### Takeaway
All three working regulation tools (StructureGPT, BuildingRegs.app, Struck) show citations to clauses, which is the main good practice. None publishes accuracy figures, test sets or error rates. The strongest claim, Struck's "0% hallucination on legal facts", has no evidence behind it on the page. Policy quality ranges from good (StructureGPT names Azure UK and OpenAI) to a one-paragraph privacy notice (BuildingRegs.app).

### Cited Findings

**StructureGPT (structuregpt.co.uk), by Atlasync AI Ltd**
- Says it gives "cited answers from official GOV.UK Approved Documents in under 3 seconds", using "hybrid AI search". Every answer has "source document, section, and page", described as "Auditable and defensible". Covers England only (Approved Documents A–T), and says so plainly on the homepage. — [structuregpt.co.uk](https://structuregpt.co.uk)
- Disclaimer on the homepage: "does not constitute professional architectural, structural engineering, or building control advice. Always verify with a qualified professional." — [structuregpt.co.uk](https://structuregpt.co.uk)
- Security claims: "Enterprise security: Microsoft sign-in, multi-tenant isolation, and role-based access". The privacy policy says encryption in transit (TLS) and at rest, "Regular security assessments", and "Microsoft Azure UK regions". No ISO 27001, SOC 2, Cyber Essentials or pen test stated. — [structuregpt.co.uk](https://structuregpt.co.uk); [Atlasync privacy](https://www.atlasync.co.uk/privacy)
- Names its AI and hosting providers: "Microsoft Azure (AI processing and cloud hosting)" and "OpenAI/GPT-4 (AI model provider)". Data is "primarily stored in the UK and EU", with SCCs for transfers. Mentions UK GDPR rights and the ICO. — [Atlasync privacy](https://www.atlasync.co.uk/privacy) (last updated 1 Jan 2026)
- Training and retention: queries are collected "for service improvement" and kept "Up to 2 years". Uploaded documents are kept 30 days. Account data is kept for the life of the account plus 6 years. It does not say whether queries are used to train models. No DPA and no named sub-processor list beyond the categories above. — [Atlasync privacy](https://www.atlasync.co.uk/privacy)
- Terms page returned "Forbidden" to my fetch, so I could not read it. — [atlasync.co.uk/terms](https://www.atlasync.co.uk/terms)
- Company: Atlasync AI Ltd, no. 16935402, incorporated 30 Dec 2025 (under a year old), London EC2A, no accounts filed yet. — [Companies House](https://find-and-update.company-information.service.gov.uk/company/16935402)

**BuildingRegs.app, by Tidy Technology Ltd**
- Claims: "Trusted answers. Confident decisions." and "the only AI assistant that covers the full spectrum of UK building and construction compliance". Covers Scotland, Wales and Northern Ireland, plus CDM 2015, HSE guidance, BS 7671, BS 8300, NHBC Standards, BBA certificates, NPPF and the London Plan. — [buildingregs.app](https://buildingregs.app)
- The privacy policy is one paragraph: "Data is stored using our managed infrastructure providers." It does not state the AI provider, hosting location, sub-processors, retention, UK GDPR, training or encryption. — [buildingregs.app/privacy](https://buildingregs.app/privacy) (last updated 1 Mar 2026)
- The terms are also one paragraph: "You are responsible for reviewing citations and validating outputs against official documents before making project or legal decisions." There is no liability clause. — [buildingregs.app/terms](https://buildingregs.app/terms)
- Company: Tidy Technology Ltd, no. 16716492, incorporated 15 Sep 2025, 71-75 Shelton Street, London WC2H 9JQ. — [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=Tidy%20Technology)
- Licensing question: the site says it covers BS 7671, BS 8300 and NHBC Standards, which are paid, copyrighted documents. It does not say how it is licensed to use them. — [buildingregs.app](https://buildingregs.app)

**Struck (struck.eu/uk), by struck.build BV (Netherlands)**
- Claims "ISO-27001 ISO-certified for secure, reliable, and fully compliant data handling processes". No certificate number, certifier or scope is given on the UK page. — [struck.eu/uk](https://struck.eu/uk)
- Claims "Struck only uses verified, up-to-date regulatory databases to ensure 0% hallucination on legal facts, and the sources so you can double-check." It also says "every answer names its clause", "5000+ users", and "30 sec vs 30 min". — [struck.eu/uk](https://struck.eu/uk)
- Testimonials are almost all from Dutch municipalities and architects. The UK library shows 81 England documents, some old editions (e.g. Approved Document A, 2012 or 2013 versions listed). — [struck.eu/uk](https://struck.eu/uk)
- The company is Dutch: "struck.build BV", KVK 92270271, "Made with 🧡 in Amsterdam". It is not a UK company. — [struck.eu](https://struck.eu/uk)
- The privacy, terms and data security pages are JavaScript-only, so I could not read them. AI provider, hosting and training policy: could not confirm. — [struck.eu/uk](https://struck.eu/uk)
- The AEC Magazine AI directory lists Struck as adding the UK building code to its library. — [AEC Magazine directory](https://aidirectory.aecmag.com/entry/struck-ai/)

**Buildwell AI**
- Two different things use this name. (1) BuildwellAI Ltd (buildwellai.com) is a "compliance intelligence platform" with a "Join the waitlist" button. It is not a question-and-answer regulation tool, and the site does not show it as live. — [buildwellai.com](https://buildwellai.com). (2) "Buildwell AI – UK Building Assistant" is a custom ChatGPT (a GPT inside ChatGPT), listed since Dec 2023. — [There's An AI For That](https://theresanaiforthat.com/ai/buildwell-ai-uk-building-assistant/)
- BuildwellAI launch coverage (July 2026) describes AI site monitoring, digital inspections and "golden thread" records, with founder and CEO Ben Smallwood. — [IT Brief UK](https://itbrief.co.uk/story/buildwellai-launches-compliance-platform-for-uk-construction); [Construction Management](https://constructionmanagement.co.uk/start-up-lowdown-buildwellais-compliance-safety-net/)
- The privacy policy claims TLS 1.2+, AES-256 at rest, "Regular security testing, vulnerability assessments, and penetration testing", MFA, and data "primarily stored and processed within the United Kingdom". It names no AI provider and no sub-processors. Dated "January 2024". — [buildwellai.com/privacy](https://buildwellai.com/privacy)
- The terms are a generic template: "BuildwellAI does not warrant that any of the materials on its website are accurate, complete or current". They exclude all damages, with no cap figure, and use "the laws of the United Kingdom" (UK law is in fact split into separate legal systems; this is my inference about drafting quality). — [buildwellai.com/terms](https://buildwellai.com/terms)
- The About page promises "Assured Compliance" and "fully compliant designs". — [buildwellai.com/about](https://buildwellai.com/about)
- Company: BUILDWELLAI LIMITED, no. 15278991, incorporated 13 Nov 2023, registered in Maidenhead. The privacy policy says "Registered Office: London". These don't match. — [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=BuildwellAI)
- A Hugging Face page holds a "BuildwellTHREAD" specification for Gateway 2/3 compliance checking. Its link to the company is unverified. — [Hugging Face](https://huggingface.co/Choukrijer/buildwellai-model-v2/blob/main/BuildwellTHREAD_Complete_Specification.md)

**Regulex (regulex.co.uk)**: only the page title loaded: "AI-Cited Building Regulations Compliance for UK Design Teams". No other content could be read. — [regulex.co.uk](https://regulex.co.uk)

**Background on accuracy**
- A Designing Buildings article reports that the platforms it tested were not trained on UK Building Regulations, with occasional inaccuracies and fabricated references. — [Designing Buildings](https://www.designingbuildings.co.uk/wiki/AI-Driven_automation_in_architectural_design:_Reducing_time,_enhancing_compliance) (via search result summary; the full article was not read)

### Inferences
- Citations are now a basic feature, but a citation alone does not prove the answer is right. No tool shows how often its citations are correct.
- "0% hallucination" (Struck) and "Assured Compliance" (BuildwellAI) are absolute claims, and nothing published backs them. They are red flags in a field where vendors' own terms say users must check everything.
- Four of the five companies here are under three years old. Two (Atlasync, Tidy Technology) were incorporated in the last 15 months.

### Gaps
- No tool published an evaluation, test set or error rate. I found no independent review (Trustpilot, Reddit) that names wrong answers from these specific tools.
- Struck's ISO 27001 certificate was not checked against a certification body's register.
- I could not read the terms for Struck or StructureGPT. Regulex could not be read at all.

## 2. RAMS and safety document generators

### Takeaway
This group shows the widest spread. RAMSReady and Ramsgen publish detailed privacy notices, a DPA, named sub-processors, AI providers and "no training" terms. Ramsgen also claims Cyber Essentials Plus and UK hosting. RAMS PRO publishes no readable legal pages and names no company, yet claims "full compliance with CDM 2015 regulations and ISO 45001 standards". Every tool whose terms could be read puts the legal duty back on the user, and most cap liability at about 12 months of fees.

### Cited Findings

**RAMSReady (ramsready.co.uk), by Bloor Engineering Ltd**
- Marketing claims: "written to the letter of UK safety law", "Scored against the HSE standard", "Built to MHSWR 1999 · CDM 2015 · 15+ UK regulations", "Every legal claim traced to the actual regulation", "Three steps. No safety qualification needed." — [ramsready.co.uk](https://ramsready.co.uk)
- Its own FAQ answers "Is it actually compliant?" honestly: "no document is 'compliant' until the responsible person has reviewed it… that duty stays with you as the employer under MHSWR 1999 reg 3." The footer says: "RAMSReady does not provide a guarantee of compliance." — [ramsready.co.uk](https://ramsready.co.uk)
- No named competent person, accreditation or third-party audit is given for the "HSE standard" scoring. — [ramsready.co.uk](https://ramsready.co.uk)
- Privacy: names every processor with location and transfer basis. Anthropic (Claude, US) and Google (Gemini, US/EEA) are the AI providers, "under paid API terms that do not permit them to train their models on the content you send". Data is held by Hetzner in Helsinki, Finland. Vercel (US), Stripe, Resend and Microsoft are also listed. — [ramsready.co.uk/privacy](https://ramsready.co.uk/privacy) (updated 9 Oct 2026)
- Retention: generated documents are kept while the account is active plus 30 days. Account records are kept 6 years after closure. Diagnostics are kept 30–90 days. Content is used to "deliver the service and improve quality". — [ramsready.co.uk/privacy](https://ramsready.co.uk/privacy)
- DPA published (Article 28 UK GDPR terms): TLS 1.3 to the database with certificate check, least-privilege database account, nightly off-site backups kept 14 days, breach notice to customers within 24 hours, and a yearly audit right. It says frankly: "We are a small company… they are not solicitor drafted." No ISO, SOC 2 or Cyber Essentials stated. — [ramsready.co.uk/dpa](https://ramsready.co.uk/dpa)
- Terms: "not legal… or other professional advice". Liability is capped at the greater of 12 months' fees or £100. The terms contain an odd stray line from another product ("that a quiz will be entertaining"), which suggests a reused template. — [ramsready.co.uk/terms](https://ramsready.co.uk/terms) (updated 9 May 2026)
- Company: Bloor Engineering Ltd, no. 14230472, incorporated 12 July 2022, Swadlincote. SIC code 71129 "Other engineering activities". — [Companies House](https://find-and-update.company-information.service.gov.uk/company/14230472)

**Ramsgen (ramsgen.com; ramsgen.co.uk redirects there), by RAMSGen Ltd**
- Security claims on the homepage: "Stored and processed in the UK", "Cyber Essentials Plus certified", "No customer data is used to train the AI", "No data is given to 3rd parties for their own use", SAML single sign-on. — [ramsgen.com](https://www.ramsgen.com)
- AI quality approach: "If it isn't cited, it's not used. Any recommendation our AI makes is cited to a source. If it can't find a source, it doesn't make the recommendation." The library is "grounded in 52 HSE publications and approved codes of practice". RAMS review uses 165 review questions, and each finding is "cited to the page". — [ramsgen.com](https://www.ramsgen.com)
- Gets the law right in its FAQ: a risk assessment must be "suitable and sufficient (MHSWR 1999, regulation 3), and the competent person who signs it stays responsible." — [ramsgen.com](https://www.ramsgen.com)
- Privacy: Google Cloud in London (europe-west2) "is where all Customer Data is held at rest". AI is "OpenAI, called directly, and Google Vertex AI on the EU endpoint". The OpenAI account is "configured for zero data retention… not used to train". — [ramsgen.com/privacy](https://www.ramsgen.com/privacy) (updated 3 Nov 2026)
- DPA published (14 Sep 2026), with a sub-processor list in Annex 3, a right to object to new sub-processors, and UK transfer mechanisms. — [ramsgen.com/dpa](https://www.ramsgen.com/dpa)
- Terms: business customers only. RAMS Review findings are "for review by a competent person". No plan is sold as unlimited. — [ramsgen.com/terms](https://www.ramsgen.com/terms)
- Founder background: "Built by Royal Engineers". The founder (Dylan) writes that as an army officer he wrote and reviewed safe systems of work. — [ramsgen.com/about](https://www.ramsgen.com/about)
- Company: RAMSGen Ltd, no. 16458298, incorporated 19 May 2025, Cardiff. — [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=Ramsgen)
- Directory listings (Capterra, Serchen) showed zero reviews. — [Capterra NZ](https://www.capterra.co.nz/software/1079650/RAMSGen); [Serchen](https://serchen.com/company/ramsgen)

**RAMS AI (ramsai.co.uk), by United Applications Ltd**
- Main design claim: "Every hazard and every control comes out of a UK safety library we write and maintain, reviewed by a qualified health and safety consultant. The AI only tidies the wording; it is never allowed near the safety content." The consultant is not named. — [ramsai.co.uk](https://ramsai.co.uk)
- Disclaimer: its assistant "Simon… does not replace professional health and safety judgement… For complex or high-risk work, you should consult a qualified H&S professional." — [ramsai.co.uk](https://ramsai.co.uk)
- Privacy: ICO registration ZC237001. AI is "OpenAI or Anthropic", and "Your data is not used to train AI models". Documents are stored at rest in London, and the app runs in Amsterdam (EU). Inactive accounts are closed after 36 months. No DPA link and no named hosting company. — [ramsai.co.uk/privacy](https://ramsai.co.uk/privacy)
- Terms (v2.0, 2 Sep 2026): business customers only. "All content must be reviewed, adapted and approved by a competent person… AI output can be inaccurate and must be independently verified." Liability is capped at 12 months' fees. — [ramsai.co.uk/terms](https://ramsai.co.uk/terms)
- Company: United Applications Ltd, no. 16955835, incorporated 12 Jan 2026, at 20 Wenlock Road, London N1 7GU. — [Companies House](https://find-and-update.company-information.service.gov.uk/company/16955835)

**DocGen (docgen.co.uk; legal pages at app.docgen.co.uk)**
- Claims: "A real RAMS, in 90 seconds", "UK-built, HSE-aligned, CDM 2015 ready", "Two-pass AI system… More accurate detection", "Learns Over Time". It analyses site videos for hazards and equipment. No accuracy figures are given. — [docgen.co.uk](https://docgen.co.uk)
- Privacy: "By default, we do not use your uploaded content to train our AI models". There is an opt-in improvement programme. Videos are kept 30 days. It claims "security assessments and penetration testing". The AI provider and hosting location are not stated (searched the text for OpenAI, Anthropic, Google, AWS, Azure: only Google Analytics and Google Ads appear). — [app.docgen.co.uk/privacy](https://app.docgen.co.uk/privacy)
- Terms: documents "must be reviewed, validated and approved by a competent person (a qualified health and safety professional) before use… DocGen does not guarantee the accuracy". Liability is capped at the greater of 12 months' fees or £1,000. The terms forbid users to "Publish or share performance benchmarks or comparisons". — [app.docgen.co.uk/terms](https://app.docgen.co.uk/terms)
- Company: no company name or number found on the homepage or legal pages. A Companies House search for "DocGen" returned nothing relevant. — [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=DocGen)

**RAMS PRO (ramspro.co.uk)**
- Claims: "the UK's leading AI-powered software", "ensuring full compliance with CDM 2015 regulations and ISO 45001 standards", "legally-binding electronic signatures", "templates are regularly updated to reflect the latest guidance from the HSE". — [ramspro.co.uk](https://ramspro.co.uk)
- The privacy page is JavaScript-only and could not be read. The terms page returned "404 - Not found". No company name or number appears on the homepage ("© 2024 - 2026 RAMS PRO"). A Companies House search found no match. — [ramspro.co.uk/terms](https://ramspro.co.uk/terms); [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=RAMS%20PRO)

**ToolBoxHQ (toolboxhq.co.uk)**: "Health & safety records that prove someone did it". It has a login page only, plus very short policies ("stored securely using industry-standard encryption"). No company, AI provider or hosting is stated. — [toolboxhq.co.uk/privacy](https://toolboxhq.co.uk/privacy); [toolboxhq.co.uk/terms](https://toolboxhq.co.uk/terms)

### Inferences
- "HSE standard" (RAMSReady) and "HSE-aligned" (DocGen) suggest an official benchmark. HSE publishes guidance, but I know of no official HSE scoring standard for RAMS. This is my inference: the claim should be read as "built from HSE guidance", not as an HSE endorsement.
- "No safety qualification needed" (RAMSReady) sits uneasily with every vendor's own terms, which need a competent person to approve the document. That includes RAMSReady's own FAQ, which says it is fine because you "sign off as the competent person".
- The best design pattern is a human-written hazard library, with AI used only for wording (RAMS AI) or only with citations (Ramsgen). It limits what the AI can invent. Neither vendor publishes test results, though.
- DocGen's ban on publishing benchmarks blocks the independent testing that would build trust.

### Gaps
- Ramsgen's Cyber Essentials Plus claim was not checked on the IASME certificate register.
- No RAMS tool names its "qualified consultant" or shows a third-party audit, accreditation (e.g. CHAS, SSIP, NEBOSH-qualified author) or acceptance by a principal contractor.
- RAMSGen terms liability clause not extracted. No company was found for DocGen or RAMS PRO.

## 3. AI quoting apps

### Takeaway
The quoting apps hold customer names, addresses and prices, so data protection matters most here. QuoteSmith and RAMS-style good practice (named AI provider, UK hosting, no training) contrast with Sleepless Tradesman (US hosting, company less than a month old) and TradeQuoteAI (no company named, badge-style claims). All say AI prices are estimates the user must check, and cap liability at about 12 months of fees.

### Cited Findings

**QuickPrice (getquickprice.com)**
- Terms: "We do not guarantee the accuracy of AI-generated pricing… We are not liable for any financial loss resulting from reliance on AI-generated pricing." Liability is capped at the greater of 12 months' fees or £100. — [getquickprice.com/terms](https://getquickprice.com/terms) (updated 23 Mar 2026)
- Privacy: AES-256 at rest and TLS in transit. The AI and hosting providers are named only as categories ("AI service providers", "Cloud hosting providers"), with no location. It sends hashed emails, IP addresses and events to OpenAI "to measure advertising conversions". Retention: "as long as your account is active", plus a 30-day deletion grace period. — [getquickprice.com/privacy](https://getquickprice.com/privacy) (updated 24 Jul 2026)
- Prices are based on "UK material costs and regional labour rates", and "Quote DNA" learns from past quotes. No figures on price accuracy. — [getquickprice.com](https://getquickprice.com); [terms](https://getquickprice.com/terms)
- Company: "QuickPrice is a company registered in England and Wales" with a Bristol address, but no company number is given. A Companies House search for "QuickPrice" found no match. — [privacy](https://getquickprice.com/privacy); [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=QuickPrice)

**TradeQuoteAI (tradequoteai.com)**
- Claims: "The #1 Quoting App for Tradesmen" and footer badges "256-bit SSL Encrypted · GDPR Compliant · 99.9% Uptime · 24/7 Support". Prices are in US dollars. "Built by Gulraiz Athar." — [tradequoteai.com](https://tradequoteai.com)
- Privacy: HTTPS/TLS, hashed passwords, LemonSqueezy for payments, UK GDPR rights and the ICO. Retention is spelled out (account deletion within 30 days, logs 12 months, billing 7 years). AI provider and hosting location: not stated. — [tradequoteai.com/privacy.php](https://tradequoteai.com/privacy.php)
- Terms: "as is". Liability is capped at 12 months' fees, and users are "solely responsible for any decisions made based on information generated". — [tradequoteai.com/terms.php](https://tradequoteai.com/terms.php)
- Company: no company name or number found. Companies House search found no match. Product Hunt shows a small following. — [Companies House search](https://find-and-update.company-information.service.gov.uk/search/companies?q=TradeQuoteAI); [Product Hunt](https://www.producthunt.com/products/tradequoteai/reviews)

**QuoteSmith (quotesmith.co.uk)**
- Privacy: "stored on secure servers hosted in the United Kingdom", TLS 1.2+, bcrypt, HSTS. AI is "Anthropic (Claude AI)… Anthropic does not use this data for training purposes." Google Analytics 4 is used. Deletion within 30 days on request. — [quotesmith.co.uk/privacy.html](https://quotesmith.co.uk/privacy.html)
- Terms: "QuoteSmith does not guarantee the accuracy, completeness, or suitability of AI-generated text". "As is", with liability capped at 12 months' fees. UK residents only. — [quotesmith.co.uk/terms.html](https://quotesmith.co.uk/terms.html)
- The homepage sample quote shows "Wilson Builders Ltd Reg. England 09214477". This is a sample, not the vendor. No company name or number for QuoteSmith itself was found. — [quotesmith.co.uk](https://quotesmith.co.uk)

**Sleepless Tradesman (sleeplesstradesman.com)**
- Claims: "The AI is trained on UK-specific trade rates, regulations, and certifications". To "Does the AI ever make prices or rules up?" it answers: "It is not allowed to. When the app is not sure of a price or a regulation it says so, and every looked-up price is labelled an estimate". Social proof: "410+ contractors" and "5.0 · 5 reviews". It offers HMRC Making Tax Digital features. — [sleeplesstradesman.com](https://sleeplesstradesman.com)
- Privacy: uses "Anthropic's Claude AI", and "We do not use your personal job data to train AI models". Hosting is on Vercel, and "Our infrastructure and some of our service providers (including hosting and our database) are located in the United States." HMRC tokens are encrypted with AES-256-GCM. — [sleeplesstradesman.com/privacy](https://sleeplesstradesman.com/privacy)
- The terms page returned almost no text to my fetch, so I could not read it. — [sleeplesstradesman.com/terms](https://sleeplesstradesman.com/terms)
- Company: Sleepless Tradesman Ltd, no. 17538029, incorporated 23 Oct 2026, less than a month before this check, with a Cornwall address. — [Companies House](https://find-and-update.company-information.service.gov.uk/company/17538029)
- The Capterra listing says the software checks plans and quotes against building regulations. — [Capterra UK](https://www.capterra.co.uk/software/1091836/Sleepless-Tradesman)

### Inferences
- "GDPR Compliant" badges (TradeQuoteAI) are self-declared. No certificate for GDPR compliance exists in the sense a badge suggests, so this is marketing, not evidence.
- Sleepless Tradesman says the AI is "trained on UK… regulations", but its privacy notice says it uses Anthropic's Claude. "Trained" most likely means a prompt or data lookup, not training a model. This is my inference.
- For UK clients' personal data, US hosting (Sleepless Tradesman) is lawful with safeguards but is weaker than the UK or EEA hosting offered by QuoteSmith, Ramsgen, RAMS AI and RAMSReady.

### Gaps
- No quoting app publishes how accurate its prices are against real quotes. I found no independent review naming wrong prices.
- The terms for Sleepless Tradesman could not be read. No Trustpilot rating could be extracted for TradeQuoteAI (the site links to a Trustpilot page).

## 4. Patterns, red flags and good practice across all tools

### Takeaway
The market is young and small: most companies were set up in 2025–2026. Not one tool publishes AI accuracy figures or a test method. Security certificates are rare: only Ramsgen (Cyber Essentials Plus) and Struck (ISO 27001) claim one, and neither gives a certificate reference. The legal pattern is the same everywhere: bold "compliant" marketing on the homepage, then "no guarantee, you are responsible, liability capped at about 12 months' fees" in the terms.

### Cited Findings
- **Age of companies (Companies House):** Sleepless Tradesman Ltd, Oct 2026; United Applications Ltd (RAMS AI), Jan 2026; Atlasync AI Ltd (StructureGPT), Dec 2025; Tidy Technology Ltd (BuildingRegs.app), Sep 2025; RAMSGen Ltd, May 2025; BuildwellAI Ltd, Nov 2023; Bloor Engineering Ltd (RAMSReady), Jul 2022. — [CH 17538029](https://find-and-update.company-information.service.gov.uk/company/17538029); [CH 16955835](https://find-and-update.company-information.service.gov.uk/company/16955835); [CH 16935402](https://find-and-update.company-information.service.gov.uk/company/16935402); [CH search Tidy](https://find-and-update.company-information.service.gov.uk/search/companies?q=Tidy%20Technology); [CH search Ramsgen](https://find-and-update.company-information.service.gov.uk/search/companies?q=Ramsgen); [CH search BuildwellAI](https://find-and-update.company-information.service.gov.uk/search/companies?q=BuildwellAI); [CH 14230472](https://find-and-update.company-information.service.gov.uk/company/14230472)
- **No company identifiable:** DocGen, RAMS PRO, QuickPrice (no number), TradeQuoteAI, QuoteSmith, ToolBoxHQ. — see the per-tool sources above
- **Liability caps:** RAMSReady (greater of 12 months or £100) — [terms](https://ramsready.co.uk/terms); QuickPrice (greater of 12 months or £100) — [terms](https://getquickprice.com/terms); DocGen (greater of 12 months or £1,000) — [terms](https://app.docgen.co.uk/terms); RAMS AI, TradeQuoteAI and QuoteSmith (12 months' fees) — [RAMS AI](https://ramsai.co.uk/terms), [TradeQuoteAI](https://tradequoteai.com/terms.php), [QuoteSmith](https://quotesmith.co.uk/terms.html)
- **AI providers named:** OpenAI (StructureGPT via Azure, Ramsgen, RAMS AI); Anthropic (RAMSReady, RAMS AI, QuoteSmith, Sleepless Tradesman); Google Gemini or Vertex (RAMSReady, Ramsgen). Not stated: BuildingRegs.app, BuildwellAI, DocGen, QuickPrice, TradeQuoteAI, RAMS PRO. — see the per-tool privacy pages above
- **"No training on your data" stated:** RAMSReady, Ramsgen (zero data retention), RAMS AI, QuoteSmith, Sleepless Tradesman, DocGen (by default, with opt-in). Not stated: StructureGPT (keeps queries 2 years "for service improvement"), BuildingRegs.app, QuickPrice, TradeQuoteAI. — see the per-tool privacy pages above
- **Published DPA:** RAMSReady and Ramsgen only. — [RAMSReady DPA](https://ramsready.co.uk/dpa); [Ramsgen DPA](https://www.ramsgen.com/dpa)

### Red flags (each with its source above)
- Absolute accuracy claims with no evidence: Struck "0% hallucination on legal facts"; BuildwellAI "Assured Compliance".
- Compliance claims with no legal pages behind them: RAMS PRO ("full compliance with CDM 2015… and ISO 45001"; terms 404; no company named).
- Very thin privacy notices: BuildingRegs.app and ToolBoxHQ (one paragraph, no AI provider or hosting stated).
- Self-awarded badges: TradeQuoteAI ("#1", "GDPR Compliant", "24/7 Support").
- A benchmark ban in the terms: DocGen.
- Templated or mismatched legal text: RAMSReady's stray "quiz" line; BuildwellAI's London office in the policy against a Maidenhead office at Companies House, and policy dated Jan 2024.
- A very new company holding financial and HMRC data on US hosting: Sleepless Tradesman.

### Good practice examples
- Full, named sub-processor list with location and transfer basis, a DPA, a 24-hour breach notice to customers, and an honest "not solicitor drafted" note: RAMSReady. — [privacy](https://ramsready.co.uk/privacy); [DPA](https://ramsready.co.uk/dpa)
- UK-only data at rest, zero data retention with OpenAI, Cyber Essentials Plus claimed, "if it isn't cited, it's not used", and the correct MHSWR reg 3 position: Ramsgen. — [ramsgen.com](https://www.ramsgen.com); [privacy](https://www.ramsgen.com/privacy)
- AI kept away from the safety content, with a human-reviewed hazard library: RAMS AI. — [ramsai.co.uk](https://ramsai.co.uk)
- Clear scope limits shown up front ("England only") and a visible disclaimer: StructureGPT. — [structuregpt.co.uk](https://structuregpt.co.uk)
- Honest FAQ that says no document is compliant until the responsible person reviews it: RAMSReady. — [ramsready.co.uk](https://ramsready.co.uk)

### Inferences
- For Florin's audience, the honest message is this. These tools can save drafting time, but none has shown, with published evidence, that its answers are accurate. Every vendor's own terms make the builder legally responsible. A good tool shows its sources, names where data goes, and does not train on it.
- Questions a builder can ask any vendor: Which AI company sees my data, and where is it stored? Do you train on it? Can I see your DPA? What certificate do you hold (with its number)? How do you test answers, and how often are they wrong? Who is the named competent person behind your safety content?

### Gaps
- No tool published accuracy figures, evaluations or test sets, so AI quality could only be judged from design claims.
- I found no Reddit or UK trade forum threads naming errors from these specific tools within this check (search budget was limited).
- No certificate claims were checked against registers (IASME for Cyber Essentials, certification bodies for ISO 27001).
