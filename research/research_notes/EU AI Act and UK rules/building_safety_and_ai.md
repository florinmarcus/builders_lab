# Building safety rules and AI tools: England, with Romania/EU comparison (as of 18 Nov 2026)

Scope: what UK building and construction safety law means for an AI assistant that answers small contractors' questions (e.g. "where is the asbestos in this flat?") from council documents, in Romanian. Who is liable if an answer is wrong, and what sector bodies say about AI. Not legal advice. Interpretations are marked as inferences.

Method note: about 18 searches and fetches. Primary sources fetched in full: HSE AI policy statement (12 Jun 2026), Control of Asbestos Regulations 2012 reg 5, UCTA 1977 s2, RICS AI standard news page. Many other points rest on search-result summaries of law firm or trade press pages; these are marked "(secondary)".

## 1. Duties that cannot be handed to software (asbestos, CDM 2015, HSWA) and HSE's position on AI

### Takeaway
UK health and safety law is goal-setting and technology-neutral: the contractor's duty to assess asbestos before work (CAR 2012 reg 5) and to plan work safely stays with the contractor whatever tool they use. HSE published a formal AI policy statement on 12 June 2026 saying existing law applies to AI, any AI use that affects safety needs a risk assessment, and it will publish new guidance in 2026/27. I found no HSE statement specific to AI-generated RAMS and no enforcement case involving an AI-generated document.

### Cited Findings
**Control of Asbestos Regulations 2012, reg 5 (primary text)**
- Reg 5 ("Identification of the presence of asbestos"): an employer must not undertake demolition, maintenance or any other work which exposes or is liable to expose employees to asbestos at any premises unless either (a) it has carried out "a suitable and sufficient assessment" of whether asbestos is or is liable to be present, its type, the material it is in and its condition; or (b) where there is doubt, it assumes asbestos is present and that it is not chrysotile alone, and "observes the applicable provisions of these Regulations". Latest revised version shows no outstanding effects. — [legislation.gov.uk, SI 2012/632 reg 5](https://www.legislation.gov.uk/uksi/2012/632/regulation/5)
- The reg 4 duty-to-manage risk assessment provision is expressly "subject to regulation 5". — [legislation.gov.uk, SI 2012/632 Part 2 (made)](https://www.legislation.gov.uk/uksi/2012/632/part/2/made)
- HSE's Approved Code of Practice L143 "Managing and working with asbestos" contains HSE's guidance on reg 5 (copy hosted by UKATA; not read in full). — [ACoP L143 (UKATA copy)](https://www.UKATA.org.uk/documents/115/ACoP_L143_-_Managing_and_working_with_asbestos.pdf)

**HSE's regulatory approach to AI (policy statement, 12 June 2026, primary)**
- HSE regulates AI where it affects health and safety in workplaces it enforces, and in the design, manufacture and supply of workplace machinery and products (as a Market Surveillance Authority). Approach is "risk-based and proportionate". — [HSE press, 12 Jun 2026](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/) (the old URL [hse.gov.uk/news/hse-ai.htm](https://hse.gov.uk/news/hse-ai.htm) redirects here)
- Quote on law: "The goal-setting nature of this legislation means it is applicable regardless of the technology being used." — [HSE press, 12 Jun 2026](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- Quote on responsibility: "those who create risks are best placed to manage and control that risk in a sensible, proportionate, and pragmatic way." — [same](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- A risk assessment is required for any use of AI that affects workplace health and safety; controls must reduce risk so far as is reasonably practicable; cyber security threats must be covered. Long-term aim: AI risk managed like any other risk. — [same](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- The statement does not mention generative AI specifically, nor the Building Safety Regulator. — [same](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- HSE next steps for 2026/27: publish new guidance on how health and safety law applies to AI; work with the Office for Product Safety and Standards on the Product Safety Review (including AI); explore an innovation hub/sandbox; continue research on "cognitive offloading" effects on human performance (ThinkSHARP project). — [same](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- HSE research and related reports linked from the statement: "Understand how AI is used in HSE Regulated Sectors" ([PDF](https://www.hse.gov.uk/news/assets/docs/understand-how-ai-is-used-in-hse-regulated-sectors.pdf)); Industrial Safetytech Regulatory Sandbox for UK construction ([report](https://www.discoveringsafety.com/reports/creating-first-industrial-safetytech-regulatory-sandbox-uk-construction-sector/)); Smarter Regulation Sandbox ([gov.uk case study](https://www.gov.uk/government/case-studies/new-smarter-regulatory-sandbox-developed-to-increase-compliance)). — [HSE press, 12 Jun 2026](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/)
- (Secondary) The May 2025 HSE report lists generative AI risk assessment tools among examples, and flags over-reliance on AI, deskilling, algorithmic bias and failures from poor data or weak oversight. — [Burges Salmon summary](https://www.burges-salmon.com/articles/102kdpj/how-is-ai-used-in-the-health-and-safety-executives-regulated-sectors-2025-ai-re)

**AI-generated RAMS: industry warnings (no HSE statement found)**
- (Secondary, trade body) The Building Safety Group (26 Feb 2026) says HSWA 1974 duties "cannot be delegated to automated systems"; CDM 2015 requires suitable and sufficient risk assessments and method statements; AI RAMS risk being generic (missing site-specific factors), ignoring human factors and emergencies; recommends competent-person review of all AI output, site visits, worker consultation, documented amendments and audits. Note: the page found sits on a staging-like domain (bsg.barques.dev), so the live BSG site should be checked. — [Building Safety Group article](https://bsg.barques.dev/news/dangers-of-using-ai-to-create-risk-assessments-and-method-statements/)
- (Secondary, research) A 2026 pilot comparing AI-generated and worker-written point-of-work risk assessments found no credible evidence that AI matches workers' own assessments; authors say human oversight is still needed. — [CIB Conferences (Purdue e-Pubs)](https://docs.lib.purdue.edu/cib-conferences/vol2/iss1/24)
- (Secondary) Industry adoption is real: Amey reportedly rolling out FYLD's AI-enabled risk assessment tool to 2,500+ field workers (Mar 2026). — [Pulse](https://www.pulse.bot/ai/news/amey-deploys-fylds-ai-enabled-risk-assessment-tool-a7f2d4df-a5a2-4bf5-abb9-853aaa2099f7/)
- Other professional bodies (NEBOSH, RoSPA) have published general pieces on AI in health and safety. — [NEBOSH](https://www.nebosh.org.uk/our-news-and-events/our-news/ai-the-great-enabler/); [RoSPA](https://rospa.com/News-and-Views/How-to-integrate-AI-into-health-and-safety)

**Enforcement**
- A search of HSE prosecution reporting found no case involving ChatGPT or another AI tool; recent cases are standard failures to make a "suitable and sufficient" risk assessment, e.g. a builder fined £10,000 plus £4,263 costs (Leeds, Aug 2026) over an extension that put a family at CO risk, with commentary noting the single contractor is responsible for the construction phase plan. — [Outsource Safety summary](https://www.outsource-safety.co.uk/?p=9993); [HSE press, prosecution tag](https://press.hse.gov.uk/tag/prosecution)

### Inferences
- (Interpretation) Reg 5 puts the assessment duty on the employer doing the work, i.e. the contractor. An AI answer can help the contractor find what the council's survey says, but it cannot be the "suitable and sufficient assessment". If the documents don't clearly cover the area, reg 5(b) means the safe default is "assume asbestos is present". The assistant should push that default, not a reassurance.
- (Interpretation) Because HSE says AI use that affects safety needs a risk assessment, a contractor using our assistant should, in principle, include it in their own risk assessment. We can make this easy (a one-page "how to use this tool safely" note).
- (Interpretation, from my background knowledge, not verified this session) Inside individual council flats (domestic premises) the reg 4 duty to manage does not apply in the same way as in common parts, so the council's asbestos register may cover common parts better than flat interiors. Pre-refurbishment surveys (HSG264) are what matter for refurbishment work. To verify.
- No AI-specific enforcement case is a gap, not a sign of safety: an HSE investigation would simply ask whether the assessment was suitable and sufficient.

### Gaps
- Did not read CDM 2015 text (SI 2015/51) this session; duties of client, principal contractor and contractor (regs 4, 8, 13, 15) not cited from primary source. Check [legislation.gov.uk SI 2015/51](https://www.legislation.gov.uk/uksi/2015/51/contents).
- Did not read HSWA 1974 ss2–3 text or ACoP L143 / HSG264 in full.
- No HSE statement specific to AI-generated RAMS or asbestos found. HSE's promised 2026/27 AI guidance had not been found as published by Nov 2026.
- No enforcement case involving AI found.

## 2. Building Safety Act 2022: golden thread, competence, BSR on AI, relevance to council low-rise flats

### Takeaway
The golden thread is a legal duty to keep accurate, digital safety information for higher-risk buildings (HRBs: at least 18 m or 7 storeys, with at least 2 residential units). Most council low-rise flats are not HRBs, so golden thread duties mostly won't apply, though the idea (accurate, current, traceable information) is a good design model. I found no official BSR statement on AI.

### Cited Findings
- An occupied building in England is an HRB if it is at least 18 m tall or has at least 7 storeys and contains at least 2 residential units (hotels, secure institutions and military premises excluded). — [GOV.UK: criteria for HRB in occupation](https://www.gov.uk/guidance/criteria-for-being-a-higher-risk-building-during-the-occupation-phase-of-the-new-higher-risk-regime.); [GOV.UK: criteria for new HRBs in design/construction](https://www.gov.uk/guidance/criteria-for-determining-whether-a-new-building-that-is-being-designed-and-constructed-is-a-higher-risk-building)
- During design and construction, hospitals and care homes meeting the height test are also in scope. — [GOV.UK consultation outcome](https://www.gov.uk/government/consultations/consultation-on-the-higher-risk-buildings-descriptions-and-supplementary-provisions-regulations/consultation-on-the-higher-risk-buildings-descriptions-and-supplementary-provisions-regulations)
- (Secondary) Duty-holders, and then the accountable person, must start and maintain a golden thread: a digital record of specified information, for new and existing HRBs. — [ICAEW legal alert](https://www.icaew.com/library/subject-gateways/law/legal-alert/2022-07/New-law-New-laws-on-building-and-maintenance-of-higher-risk-properties-aimed-at-reducing-prospects); [ICE](https://ice.org.uk/news-views-insights/inside-infrastructure/golden-thread-through-new-building-safety-regime)
- (Secondary) At a roundtable with the BSR, discussion of AI and how technology could support the regulator left "the room much less certain"; the piece argues structured, traceable information is what makes technology (including AI finding missing information) useful. — [Construction Management](https://constructionmanagement.co.uk/golden-thread-building-safety-act/)
- (Secondary) Commentary urges preparing submissions on the assumption they will be read by AI as well as by professionals. — [PBC Today](https://www.pbctoday.co.uk/news/digital-construction-news/signal-noise-why-machine-readable-buildings-closer-think/165324/)

### Inferences
- (Interpretation) Council low-rise flats (under 18 m / 7 storeys) are outside the HRB golden thread duties. Council tower blocks are in scope; if the product later covers them, the golden thread is a high-quality structured source to retrieve from, and the accountable person (the council) owns its accuracy.
- (Interpretation) Golden thread language ("accurate, up to date, accessible, digital") gives us a good standard for our own outputs: every answer tied to a dated source document.

### Gaps
- No official BSR (now under MHCLG/standalone regulator) statement on AI found. Did not verify exact regulation titles for golden thread information (search suggested "Higher-Risk Buildings (Key Building Information etc.) (England) Regulations 2023"); confirm on legislation.gov.uk.
- Dutyholder competence regime (Building Regulations etc. (Amendment) (England) Regulations 2023, Part 2A) not researched this session.

## 3. Professional and industry guidance on AI in construction

### Takeaway
RICS is the only body with a mandatory AI standard: in force from 9 March 2026, it keeps the surveyor accountable for all advice, whatever tool produced it. CIOB has a 2024 AI playbook and 2026 survey data; RIBA has survey reports (2024, 2025) and says guidance is in development. The common message: AI assists, humans stay accountable.

### Cited Findings
- RICS professional standard "Responsible use of artificial intelligence in surveying practice" (published Sept 2025) in effect since 9 March 2026, for all RICS members and regulated firms worldwide. — [RICS news](https://www.rics.org/news-insights/rics-first-ever-standard-on-responsible-ai-use-now-in-effect); [standard PDF](https://www.rics.org/content/dam/ricsglobal/documents/standards/Responsible-use-of-artificial-intelligence-in-surveying-practice_September-2025.pdf)
- RICS quotes: "AI assists professional practice; it does not replace it." and "The surveyor remains accountable for every piece of professional advice, regardless of the tools used to produce it." Requirement areas: risk registers, responsible use policies, procurement due diligence, professional scepticism (curating inputs, validating outputs), transparency with clients, responsible development. — [RICS news](https://www.rics.org/news-insights/rics-first-ever-standard-on-responsible-ai-use-now-in-effect)
- (Secondary) Law firm commentary flags the standard's relevance to insurers and their surveyor clients. — [CMS](https://cms.law/en/gbr/legal-updates/rics-introduces-mandatory-ai-standard-for-surveyors-what-insurers-and-their-clients-need-to-know)
- CIOB's Digital and Innovation Advisory Panel published an AI playbook (2024), free, aimed at organisations of all sizes; CIOB says AI could especially help smaller firms. — [CIOB](https://www.ciob.org/news/new-playbook-on-ai-in-construction-published-by-ciob); [Building](https://www.building.co.uk/news/ai-could-help-smes-compete-with-bigger-firms-says-ciob/5130151.article)
- (Secondary) CIOB/FMB State of Trade Survey, Jan–Jun 2026: 57% of construction businesses using AI more than a year earlier. — [PBC Today](https://pbctoday.co.uk/news/hr-skills-news/more-than-half-construction-businesses-using-ai-amid-skills-issues/167539/)
- CIOB President's blog (Jan 2026) stresses data quality, transparency and ethics; AI should complement human judgement. — [CIOB blog](https://www.ciob.org/blog/ai-and-construction-the-power-of-progress-not-perfection)
- RIBA AI Report 2025: practice-level AI use up from 41% (2024) to 59% (2025); RIBA developing guidance on responsible use. — [RIBA](https://www.riba.org/knowledge-and-resources/knowledge-landing-page/second-riba-ai-report-shows-surge-in-usage-among-uk-architects)
- (Secondary) Nearly half of RIBA respondents fear unqualified use of AI could lead to unsafe or inadequate buildings. Figures for the "imitation" concern differ between RIBA pages (67% vs 69%). — [Beale & Co](https://beale-law.com/?p=24669); [RIBA risks feature](https://www.riba.org/knowledge-and-resources/knowledge-landing-page/what-are-the-risks-to-architects-and-practices-who-use-ai)

### Inferences
- (Interpretation) RICS does not bind our contractors (they are mostly not RICS members), but its principles are a ready-made benchmark buyers and councils will recognise: register of AI tools, risk register, human validation, transparency.
- (Interpretation) If council asbestos or stock-condition surveys are prepared by RICS-regulated firms, those firms already work under this standard; our tool reads their outputs, it doesn't replace them.

### Gaps
- Not found this session: CITB, Construction Leadership Council, BSI (BS ISO/IEC 42001:2023 AI management system) or UKAS statements on AI in construction. ISO/IEC 42001 exists as an AI management system standard but I did not fetch a source; check [bsigroup.com](https://www.bsigroup.com) and UKAS for any accreditation scheme.
- Did not read the RICS PDF itself; exact clauses (e.g. register review frequency) unverified.

## 4. Liability when a contractor relies on an AI answer

### Takeaway
The contractor stays liable to workers, residents and HSE for its own safety duties. The software supplier can limit liability for ordinary loss in its terms, but under UCTA 1977 s2(1) cannot exclude liability for death or personal injury caused by its negligence. Product liability for software and AI is changing: the Law Commission (consulting until 14 Jan 2027) proposes treating software and AI as products; the EU's new Product Liability Directive covers software from 9 December 2026. Insurers are adding generative AI exclusions to general liability (mostly US evidence); UK PI wording is less settled.

### Cited Findings
- UCTA 1977 s2(1): a person cannot by reference to any contract term or notice exclude or restrict liability for death or personal injury resulting from negligence. s2(2): other loss or damage can be excluded only so far as the term meets the "requirement of reasonableness". — [legislation.gov.uk UCTA s2](https://www.legislation.gov.uk/ukpga/1977/50/section/2)
- Law Commission of England and Wales review of Part 1 of the Consumer Protection Act 1987: started Sept 2025 (DBT remit); consultation opened 8 Oct 2026, closes 14 Jan 2027. Terms of reference call the Act potentially "no longer fit for purpose" given AI. — (secondary) [Pinsent Masons](https://www.pinsentmasons.com/out-law/news/law-commission-bring-ai-within-uk-product-liability-regime); [Osborne Clarke](https://www.osborneclarke.com/insights/uk-product-liability-law-commission-reviews-consumer-protection-act-1987); [Wiggin](https://wiggin.co.uk/insight/product-liability-law-commission-publishes-terms-of-reference-for-wide-ranging-review/)
- (Secondary) Provisional proposals: cover software however supplied (including SaaS); treat AI as a product defined by core features rather than a fixed definition; a rebuttable presumption of defect and risk-sharing for complex software/AI; add "relevant circumstances" (warnings, learning and adaptation, interoperability) to the defect test. Sources differ on some details. — [CMS](https://cms.law/en/gbr/legal-updates/product-liability-reform-proposed-expansion-of-england-and-wales-regime); [Freshfields](https://riskandcompliance.freshfields.com/post/102kz0x/uk-product-liability-reform-new-redress-rules-for-ai-systems)
- EU Product Liability Directive (EU) 2024/2853: software (embedded and standalone) is a product; member states must transpose by 9 December 2026. — (secondary) [Faegre Drinker, Oct 2026 transposition update](https://www.faegredrinker.com/en/insights/publications/2026/10/transposing-the-eu-new-product-liability-directive-a-member-state-progress-report-october-2026-update); [Cleary Gottlieb](https://www.clearygottlieb.com/news-and-insights/publication-listing/the-new-eu-product-liability-reform-addressing-the-digital-age)
- (Secondary) Insurance: ISO introduced generative AI exclusion endorsements for US CGL forms effective Jan 2026; for PI, a CMS webinar summary (Sept 2026) says most insurers have not yet added dedicated AI exclusions, relying on existing technology exclusions; a Beale & Co roundtable (Apr 2026) says PI insurers are not yet routinely asking about AI use. Lockton advises checking PI and cyber cover for AI exclusions. — [Gallagher](https://www.ajg.com/us/news-and-insights/2026/jul/iso-introduces-generative-ai-exclusion-in-commercial-general-liability-policies/); [CMS](https://cms.law/en/media/international/files/events/webinars/ai-in-construction-projects-executive-summary); [Beale & Co](https://beale-law.com/?p=26284); [Lockton](https://global.lockton.com/apac/en/news-insights/how-architects-and-engineers-can-manage-risks-associated-with-ai-adoption); [Browne Jacobson](https://www.brownejacobson.com/insights/the-word-february-2026/pi-insurers-questions-about-clients-ai-usage)

### Inferences
- (Interpretation) Chain of liability for a wrong asbestos answer: (1) the contractor faces HSE enforcement and civil claims from workers/residents, because reg 5 and HSWA duties are theirs; (2) the contractor may then try to recover from us in contract or negligence. Our terms can cap ordinary losses (if reasonable), but not negligence liability for personal injury. Asbestos harm is personal injury, often decades later.
- (Interpretation) Strong disclaimers ("not a survey, check the source") help show the tool was not presented as a substitute, and help on reasonableness, but do not remove the injury exposure. Product design (citations, refusal to say "no asbestos" without coverage) is the real risk control.
- (Interpretation) Our customers are businesses, not consumers. CPA 1987 product liability protects people who suffer damage (e.g. an injured worker), so a future UK regime treating AI as a product could expose the supplier directly. Watch the Law Commission outcome.
- (Interpretation) Contractors' own insurance may not cover AI-related losses; worth asking pilot users and an insurer.

### Gaps
- No UK case law found on a contractor relying on an AI summary. No UK PI policy wording with an AI exclusion verified from primary source.
- Negligent misstatement (Hedley Byrne) and duty of care of an information tool supplier not researched; needs a lawyer.

## 5. Romania: construction safety, asbestos, digitalisation, AI Act

### Takeaway
Romania's asbestos worker protection rules are in HG 1875/2005 (not HG 1218/2006, which is about chemical agents), implementing EU Directive 2009/148/EC; a draft to transpose amending Directive (EU) 2023/2668 (deadline 21 Dec 2025) existed in July 2025, but I could not confirm adoption. The Labour Inspectorate (Inspecția Muncii) requires written risk assessment and a work plan per task. Romania had not published its PLD transposition by mid-2026 per secondary sources.

### Cited Findings
- HG 1875/2005 on protecting workers' health and safety from risks of asbestos exposure is listed in the Labour Inspectorate's applicable OSH legislation; HG 300/2006 sets minimum safety requirements for temporary or mobile construction sites. — [Inspecția Muncii, legislation list (PDF)](https://www.inspectiamuncii.ro/documents/66402/201782/legislati+aplicabila+in+domeniul+ssm.pdf/c0f4f7f8-bfe9-42a7-8bf3-769c5d38eeef); [avocatnet HG 300/2006 summary](https://avocatnet.ro/articles/download/393c5ae3be558c91cf11de9b66a5f171)
- Labour Inspectorate employer guide: a written risk assessment and a work plan for each task, specific to the site and special activities, including preparatory work such as enclosures. Worker guide: if unexpected asbestos is found, stop work immediately and report to the responsible person. — [Ghid azbest angajator](https://www.inspectiamuncii.ro/documents/825609/1209953/Ghid+azbest_angajator.pdf/572f16c5-2598-455d-b054-64751e0cd72f); [Ghid azbest lucrător](https://www.inspectiamuncii.ro/documents/825609/1209953/Ghid+azbest_lucrator.pdf/e52fa964-0c59-4777-a671-035d78cb5aef); [Ghid metodologic](https://inspectiamuncii.ro/documents/66402/264079/GHID+METODOLOGIC+PENTRU+PREVENIREA+RISCURILOR+LEGATE+DE+EXPUNEREA+LA+AZBEST/5d332116-1297-4a9e-b9fb-662d7ad7f835)
- Draft government decision (July 2025) to amend HG 1875/2005 transposing Directive (EU) 2023/2668 (lower exposure limits). — [CES draft note (PDF)](https://www.ces.ro/newlib/PDF/proiecte/2025/NF-proiect-transp-Dir-2023_2668-azbest_DPP_EP_16-iul-2025-curat.pdf)
- Directive (EU) 2023/2668 of 22 Nov 2023 amends Directive 2009/148/EC; (secondary) transposition deadline 21 Dec 2025. — [EU Publications Office](https://op.europa.eu/en/publication-detail/-/publication/bacbeacf-8f22-11ee-8aa6-01aa75ed71a1/language-ro); [Croatian Parliament bill](https://sabor.hr/sites/default/files/uploads/sabor/2026-04-09/164102/PZE_247.pdf)
- (Secondary) Romania PLD transposition: not published in Monitorul Oficial as of July 2026; EUR-Lex showed no Romanian measure as of 10 Aug 2026. — [Global Law Experts](https://globallawexperts.com/eu-product-liability-directive-2024-2853-what-romanian-tech-businesses-must-know-about-software-as-a-product/); [Reed Smith](https://www.reedsmith.com/articles/eu-product-liability-directive-where-things-stand-with-member-state-transposition/)

### Inferences
- (Interpretation) Romania and England share the same core idea through EU-origin law (UK's CAR 2012 also derives from the EU asbestos directive): the employer assesses before work and stops if unexpected asbestos appears. Our "assume present when unclear, stop and check" rule works in both.
- (Interpretation) If we only serve contractors working in England, Romanian law matters little apart from language. If we sell to businesses in Romania, the PLD (software as product, from 9 Dec 2026, once transposed) and the EU AI Act apply. Under the AI Act, an information assistant like this is likely not "high-risk" but has transparency duties; another researcher covers this.

### Gaps
- Law 10/1995 on quality in construction (republished/updated) not fetched; check [legislatie.just.ro](https://legislatie.just.ro).
- Could not confirm whether the HG 1875/2005 amendment was adopted, or its number.
- Romanian construction digitalisation or AI initiatives (e.g. national BIM strategy) not found this session.
- Whether Romania transposed the PLD between Aug and Nov 2026 is unconfirmed.

## 6. Practical design rules that follow

### Takeaway
The law leaves the duty with the contractor, so the assistant must behave like a careful document finder, not a surveyor: cite source and date, never give a "no asbestos" assurance unless the survey clearly covered that area, push "assume present" when unclear, keep a log, and make human sign-off visible.

### Cited Findings
- Basis: reg 5's "suitable and sufficient assessment" or "assume present" choice — [CAR 2012 reg 5](https://www.legislation.gov.uk/uksi/2012/632/regulation/5); HSE requires a risk assessment for AI use that affects safety — [HSE, 12 Jun 2026](https://press.hse.gov.uk/2026/06/12/hses-regulatory-approach-to-artificial-intelligence-ai/); RICS: professional stays accountable, validate outputs, transparency — [RICS](https://www.rics.org/news-insights/rics-first-ever-standard-on-responsible-ai-use-now-in-effect); competent-person review of AI RAMS — [BSG](https://bsg.barques.dev/news/dangers-of-using-ai-to-create-risk-assessments-and-method-statements/); pilot evidence AI risk assessments don't match workers' own — [CIB/Purdue](https://docs.lib.purdue.edu/cib-conferences/vol2/iss1/24); Romanian guidance to stop work on unexpected asbestos — [Inspecția Muncii worker guide](https://www.inspectiamuncii.ro/documents/825609/1209953/Ghid+azbest_lucrator.pdf/e52fa964-0c59-4777-a671-035d78cb5aef).

### Inferences (all are proposals, not legal requirements)
- Always cite the document, page/section, survey type and survey date in every safety answer. Show "survey dated X; older than Y years" warnings.
- Never say "there is no asbestos". Say what the survey found, and which rooms or materials it did not cover or could not access. If not covered or unclear: "Treat as containing asbestos until checked (reg 5)." Answer in Romanian, with the key legal phrase also in English for the site manager.
- Distinguish survey types (management vs refurbishment/demolition) and flag when only a management survey exists for refurbishment work.
- Stop-work prompt: if the user reports suspect material not in the survey, tell them to stop and get it checked.
- Human sign-off: the contractor confirms they read the source before using an answer in RAMS; the tool never produces a finished, signed RAMS.
- Logging: keep question, answer, sources and versions, timestamp and user, so the contractor (and we) can show what was relied on. Mind UK GDPR for logs (mock data only in this repo).
- Terms: clear "information tool, not a survey or risk assessment" wording; cap ordinary losses; do not try to exclude personal injury liability (UCTA s2(1) makes it void); check our own PI/product cover.
- Evals: include negative tests (rooms not covered, outdated surveys, conflicting documents) where the correct answer is "not covered: assume present".

### Gaps
- No regulator or court guidance tells AI suppliers how to design such tools in construction; these rules are reasoned from the duties above. A solicitor and an asbestos professional should review them before any real use.
