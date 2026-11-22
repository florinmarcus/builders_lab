# Construction-specific providers of UK building regulations content: APIs, MCP and AI (as of 21 Nov 2026)

Scope note: about 19 searches and page fetches on 21 Nov 2026. Several providers named in the brief (RICS isurv, CIOB, Planning Portal, FMB, Checkatrade, Premier Guarantee, Archistar, Plannerly, Kreo, Barbour/Glenigan, Specifiedby) returned nothing useful in the time available. They are listed under Gaps, not filled from memory. Items marked "unverified" come from training knowledge, not sources found today.

## Does any construction body offer an MCP server or API for building regs today?

### Takeaway
I found no MCP server, public API or announced AI connector from any established UK construction content body (NBS/Hubexo, BSI, NHBC, LABC). The only building-regs MCP server found is a hobby open-source project built on the free gov.uk merged Approved Documents PDF (October 2024 edition). Small startups (My Research.ai, Buildwell AI, Innex) offer AI Q&A. None of them was confirmed to expose MCP.

### Cited Findings
**NBS (part of Hubexo, formerly Byggfakta Group)**
- NBS has been part of Hubexo, formerly Byggfakta Group, since 2020 — [NBS joins Byggfakta](https://www.thenbs.com/about-nbs/press-releases/nbs-joins-byggfakta-to-bolster-growth); [yespress: NBS powered by Hubexo](https://yespress.io/nbs-powered-by-hubexo)
- NBS sells regulations content through the Construction Information Service (CIS). The "Core" package covers the Building Regulations Approved Documents for England, guidance for Scotland, Wales and Northern Ireland, and the standards the Approved Documents cite — [NBS CIS product page](https://www.thenbs.com/products/construction-information-service)
- CIS document pages now carry Accuris/IHS branding (cis.ihs.com) and already list the "Building Regulations etc. (Amendment) (England) Regulations 2026". Sources do not say whether this is a change of owner or only a site move — [cis.ihs.com doc 354211](https://cis.ihs.com//CIS/document/354211); [NBS publishers in CIS](https://cis.ihs.com/cis/browse/publishers/nbs)
- NBS Source is a product information platform (over 30,000 products from over 1,200 manufacturers). It links to NBS Chorus and Revit. In Aug 2025 NBS announced a GS1 UK partnership to add GTINs. I found no public API or AI feature for building regs — [NBS Source press release](https://www.thenbs.com/about-nbs/press-releases/nbs-source-the-future-of-construction-product-information); [Enhanced data with NBS Source](https://www.thenbs.com/resources/knowledge/enhanced-data-nbs-source)
- NBS's own "automated checking of Building Regulations" work dates from Feb 2014. It was rule-based checking of Approved Document B in BIM models, with Solibri, Butler & Young and Northumbria University. There was no AI and no API, and "a product to market during 2014" was promised — [NBS press release, 18 Feb 2014](https://www.thenbs.com/news-and-press/nbs-pioneering-automated-checking-of-building-regulations)
- NBS's Digital Construction Report 2025 covers AI adoption in the sector. It does not describe an NBS AI regs product — [NBS Digital Construction Report 2025](https://www.thenbs.com/digital-construction-report-2025)

**BSI (British Standards Online / BSI Knowledge)**
- BSI's licensing page lists the licence types "workflow integration", "training providers", "online subscription products" and "translations". It names "incorporating standards information into online and software products" as one use. It has no AI, text and data mining (TDM) or API category and lists no prices. Price depends on the number of users and the amount of content. Contact: copyright@bsigroup.com — [BSI Knowledge licensing](https://knowledge.bsigroup.com/pages/licensing)
- BSI Knowledge Terms and Conditions of Supply (page © 2026) do not mention AI, machine learning or TDM. They do ban things an AI tool would need: cl. 7.1.1(a) bans copying, scanning or creating "derivative works"; cl. 7.1.2 bans access "to build a product or service which competes with the Products"; cl. 5.6 bans storing any part "in a retrieval system" without written permission; cl. 5.7 requires permission to put a standard on an internal network; cl. 7.1.4 bans making Products available to anyone other than Authorised Users — [BSI Terms and Conditions of Supply](https://knowledge.bsigroup.com/pages/terms-and-conditions-of-supply)
- BSI says copyright in its material is owned by BSI and contributing bodies, including ISO, IEC, CEN and CENELEC — [BSI terms hosted by FIS](https://www.thefis.org/?p=241353); [BSOL T&Cs](https://bsol.bsigroup.com/TermsAndConditions)

**NHBC**
- NHBC Standards 2026 were published in Jan 2026 and apply to homes whose foundations start on or after 1 Jan 2026. There is also a 2027 edition page — [NHBC news](https://nhbc.co.uk/insights-and-media/news/nhbc-to-publish-latest-edition-of-technical-standards-updated-for-2026); [LexisNexis news 06/01/2026](https://www.lexisnexis.co.uk/legal/news/nhbc-publishes-updated-technical-standards-for-new-home-construction-in-2026)
- NHBC Standards Plus is an online platform for the Technical Standards plus extra technical information, launched in March 2016. I found no AI search, API or MCP announcement — [specificationonline, 2016](https://mail.specificationonline.co.uk/articles/2016-03-22/new-online-nhbc-standards-plus-launched-for-homebuilders)
- Unverified: NHBC Standards are free to read online (training knowledge).

**LABC / LABC Warranty**
- A search for an LABC or LABC Warranty AI assistant found nothing — no source.

**MCP servers and AI startups**
- "uk-building-code-mcp" (buildingcode-mcp) by GitHub user LeoRickayzen. It describes itself as experimental and "under heavy development". It loads the gov.uk "Merged Approved Documents" PDF (October 2024 edition) and offers semantic search and page retrieval (`/api/v1/search_excerpts`, `/api/v1/get_pages`). It had 0 stars, and no licence or date was shown — [LobeHub listing](https://market.lobehub.com/s/plugins/leorickayzen-uk-building-code-mcp); [GitHub](https://github.com/LeoRickayzen/uk-building-code-mcp)
- My Research.ai "UK Building Regulations": cited AI answers. It claims "All Approved Documents... Part A through to Part S" plus Scotland, Wales and Northern Ireland, with no editions listed. It has a free sign-up, "API" and "Documentation" links with no details, and no mention of MCP. These are vendor claims and I have not verified them — [My Research.ai UK page](https://my-research-marketing.pages.dev/uk/building-regulations)
- Buildwell AI: a ChatGPT custom GPT covering planning, building regulations, the Party Wall Act and fire safety — [There's An AI For That listing](https://theresanaiforthat.com/ai/buildwell-ai-uk-building-assistant/); [Hugging Face spec](https://huggingface.co/Choukrijer/buildwellai-model-v2/blob/main/BuildwellTHREAD_Complete_Specification.md)
- Innex (INNEX): an AI platform for compliance, built first for NHS estates, with an "AI Review Assistant" that checks documents against "verified UK legislation and guidance". The article is by its co-founder (July 2025). No licensing details — [CIBSE Journal, July 2025](https://www.cibsejournal.com/technical/making-compliance-work-smarter-ai-tools-for-building-regulations/)
- UpCodes Copilot is US-focused: 80+ federal, state and city jurisdictions and 11M+ code sections. A Dec 2025 announcement called it "project-aware" AI for AEC. I found no evidence of UK Approved Documents content — [UpCodes Copilot page](https://cms-v2.up.codes/features/ai); [Building Enclosure](https://www.buildingenclosureonline.com/articles/94432-upcodes-unveils-copilot-intelligence); [YC launch](https://www.ycombinator.com/launches/Iu3-upcodes-copilot-for-building-codes)
- Accuracy warning: a test of AI platforms found that none had been trained on UK Building Regulations. They gave occasional wrong answers and made-up references — [Designing Buildings](https://www.designingbuildings.co.uk/wiki/AI-Driven_automation_in_architectural_design:_Reducing_time,_enhancing_compliance)
- Research context: in 2020, the 16 Approved Documents for England referenced nearly 500 standards, 85 other government guidance documents and 176 industry guidance documents — [Strathclyde, Kruiper et al. 2024](https://strathprints.strath.ac.uk/89810/1/Kruiper-etal-AEI-2024-A-platform-based-Natural-Language-processing-driven-strategy-for-digitalising-regulatory-compliance-processes.pdf)

### Inferences
- The established content holders (NBS/Hubexo, BSI, NHBC) sell to human readers in a browser. Their terms are written for people, not machines. No licensed machine channel (API or MCP) for UK regs content was visible as of Nov 2026.
- The startups and the MCP project all build on free government text, mostly the gov.uk merged PDF. None shows a licence for BSI or NBS content.

### Gaps
- Not checked: whether NBS/Hubexo or Accuris have a private or partner API for CIS. Not publicly documented; would need a sales enquiry.
- Not checked: whether UpCodes has any UK plans.
- Not checked: whether My Research.ai's "API" link is a working public API.
- No sources found today for RICS isurv, CIOB, Planning Portal (beyond its Approved Documents page appearing in results: [Planning Portal approved documents](https://www.planningportal.co.uk/applications/building-control-applications/building-control/approved-documents)), Premier Guarantee, FMB, Checkatrade, Barbour ABI, Glenigan, Specifiedby, Archistar, Plannerly or Kreo. The searches returned unrelated results. Unverified (training knowledge): Archistar does automated planning and code checks mainly in Australia and the US; Kreo is takeoff and estimating software; Plannerly is BIM management. None of these is known to cover UK building regs Q&A.

## What does it cost and can a small startup license it for use inside an assistant?

### Takeaway
Government text (the Approved Documents, legislation, HSE web guidance) is Crown copyright under the Open Government Licence v3.0. A startup may ingest and serve it free, with attribution and with care over third-party material. BSI standards are the hard case: no published price, no AI licence category, and standard terms that ban retrieval systems and derivative works. Any use needs a bespoke BSI licence. NBS/CIS pricing was not published.

### Cited Findings
- The gov.uk Building Regulations and Approved Documents index says: "All content is available under the Open Government Licence v3.0, except where otherwise stated" (Crown copyright). The merged Approved Documents PDF (35.8 MB) is the October 2024 edition, page updated 1 Oct 2024. That edition includes 2024 G, M vol 2 and T; 2022/2023 B, J, L, R; and 2021 F, L, O, S — [gov.uk index](https://www.gov.uk/guidance/building-regulations-and-approved-documents-index)
- The OGL is the default licence for most Crown copyright material. Re-users must credit it as Crown copyright and give the source title. Third-party content inside government publications is not covered — [National Archives OGL](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/open-government-licence/); [Crown copyright](https://nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
- Legislation on legislation.gov.uk is also open for re-use — [legislation.gov.uk re-use licence docs](https://legislation.github.io/data-documentation/reuse-licence.html)
- HSE: Crown material on its website may be re-used free under the OGL. Suggested credit: "Contains public sector information published by the Health and Safety Executive and licensed under the Open Government Licence". Exclusions: logos, the "Health and Safety Law" posters, the Accident Book, some multimedia. HSE does not license re-use of its research reports — [HSE copyright](https://www.hse.gov.uk/help/copyright.htm); [HSE Books copyright](https://books.hse.gov.uk/copyright)
- 2026 editions: SI 2026/335, the Building Regulations etc. (Amendment) (England) Regulations 2026, brought in a new Approved Document L (vols 1 and 2) and a new Approved Document F vol 1. They were issued 24 Mar 2026 with Building Circular 01/2026 (the Future Homes and Buildings Standards). HBF says it applies from 24 Mar 2027 — [gov.uk Circular 01/2026](https://www.gov.uk/government/publications/the-future-homes-and-buildings-standards-building-circular-012026/the-future-homes-and-buildings-standards-building-circular-012026-letter); [HBF, Apr 2026](https://www.hbf.co.uk/news/future-homes-standard-april-2026/); [Building regulations circulars](https://www.gov.uk/government/collections/building-regulations-circulars)
- Approved Document B: gov.uk lists "Amendments to Approved Document B: Circular 01/2025" and a later Part B circular. Gowling WLG says Approved Document B amendments affect new building control applications for residential buildings of 18 m and above from 30 Sep 2026. The BSR's review of building regulations guidance was due to report in summer 2026 — [gov.uk circulars](https://www.gov.uk/government/collections/building-regulations-circulars); [Gowling WLG 2026](https://gowlingwlg.com/en/insights-resources/articles/2026/uk-construction-2026-what-are-the-policy-shifts-and-developments-you-need-to-know)
- BSI: no published price. The quote is based on the number of users and the amount of content. The terms ban storing standards "in a retrieval system", "derivative works" and competing products without permission — [BSI licensing](https://knowledge.bsigroup.com/pages/licensing); [BSI T&Cs of Supply](https://knowledge.bsigroup.com/pages/terms-and-conditions-of-supply)
- NBS CIS: subscription via thenbs.com. No public prices found — [NBS CIS](https://www.thenbs.com/products/construction-information-service)

### Inferences
- A builders assistant can legally build its own corpus from gov.uk Approved Documents, legislation.gov.uk text (Building Regulations 2010, Building Safety Act 2022 and its secondary legislation) and HSE web guidance, under OGL with attribution. This is what the repo's `corpus/` already does.
- The October 2024 merged PDF is out of date for Part L and Part F (2026 editions) and probably for Part B (2025 and later amendments). Any corpus must track separate Approved Document PDFs and circulars, not just the merged PDF. The MCP server found uses the out-of-date merged PDF.
- Putting BS 8414, BS 9991 or BS 7671 text into a RAG index would very likely breach BSI's standard terms (cl. 5.6, 7.1.1). A startup should only cite them by number and title, or get a bespoke licence. BS 7671 is co-published with the IET (unverified, training knowledge), so that licence may involve the IET too.
- Images and diagrams in Approved Documents may include third-party material outside the OGL. Check before serving figures (guess, based on the OGL "except where otherwise stated" wording).

### Gaps
- No public price for BSI workflow-integration licences, or for NBS CIS or BSOL subscriptions. Both need a quote.
- I did not confirm whether Approved Documents carry any extra non-OGL notice inside the PDFs themselves (only the gov.uk page licence was checked).
- Not confirmed: the exact date and title of the latest Approved Document B edition in force at 21 Nov 2026, and whether a new merged PDF was published after Oct 2024.
- Building Safety Act secondary legislation coverage by commercial providers was not checked.

## What is the gap a builders assistant must fill itself?

### Takeaway
No one offers a licensed, current, machine-readable UK regs feed for AI tools. A builders assistant must collect, version and cite government text itself (OGL). It must point to, but not reproduce, BSI standards. It also has to fill the practical-guidance layer (warranty standards such as NHBC/LABC), which is locked in paywalled or web-only portals.

### Cited Findings
- AI tools not grounded in UK regs make up references — [Designing Buildings](https://www.designingbuildings.co.uk/wiki/AI-Driven_automation_in_architectural_design:_Reducing_time,_enhancing_compliance)
- The Approved Documents depend on hundreds of standards and other guidance documents (about 500 standards in 2020) — [Strathclyde, Kruiper et al.](https://strathprints.strath.ac.uk/89810/1/Kruiper-etal-AEI-2024-A-platform-based-Natural-Language-processing-driven-strategy-for-digitalising-regulatory-compliance-processes.pdf)
- Approved Document editions change often (2024 G/M/T, 2025 B amendments, 2026 L/F) — [gov.uk index](https://www.gov.uk/guidance/building-regulations-and-approved-documents-index); [Circular 01/2026](https://www.gov.uk/government/publications/the-future-homes-and-buildings-standards-building-circular-012026/the-future-homes-and-buildings-standards-building-circular-012026-letter)
- Innex names three needs for useful AI in building services: trusted guidance, sector-specific language and fit with real workflows (vendor opinion) — [CIBSE Journal](https://www.cibsejournal.com/technical/making-compliance-work-smarter-ai-tools-for-building-regulations/)

### Inferences
- What the assistant must build itself:
  1. Edition tracking and transition rules: which edition applies to which job, based on application and start dates.
  2. Section-level citations with edition dates.
  3. A list of the standards each Approved Document cites (number and title only).
  4. Plain-English, small-builder framing, in Romanian too. No provider targets small trades, and the incumbents target specifiers and architects.
  5. An MCP interface. None exists from incumbents, and the one open-source server is experimental and out of date.
- Commercial angle (guess): a later partnership with NBS/Hubexo or BSI for licensed standards text is possible, but would need a bespoke deal at an unknown price. It is not needed for an MVP built on OGL content.

### Gaps
- No evidence on whether FMB or Checkatrade give members regs guidance that could be partnered with. Not researched successfully.
- No user evidence that small builders would pay for standards text beyond the Approved Documents.
