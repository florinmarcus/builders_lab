# Trust check: construction platforms and general AI assistants for UK builders (as of 19 Nov 2026)

All sources accessed 19 Nov 2026 unless another date is given. "Primary" means the vendor's or regulator's own page; "secondary" means a blog, review or compliance site. Many vendor pages could only be read via search snippets (openai.com returned HTTP 403 to direct fetch), so points marked "secondary" should be checked on the vendor page before they go on a slide.

## 1. Construction platforms: security, data protection, AI transparency, compliance, liability

### Takeaway
Procore has the strongest public security evidence of the four construction platforms (ISO 27001, SOC 2 Type 2, UK data zone, and a clear "no third-party model training" claim). Autodesk is the only one with ISO/IEC 42001 and published per-feature AI Transparency Cards. Buildertrend and Houzz Pro publish much less: mostly marketing claims and hosting-provider (AWS) certifications, not their own.

### Cited Findings

**Procore (Procore Helix / Procore AI / agents)**
- Trust centre lists ISO/IEC 27001:2022, SOC 1 Type 2, SOC 2 Type 2, SOX, EU-US DPF, Swiss-US DPF, UK Extension to EU-US DPF, VPAT, FedRAMP Moderate; "Procore is SSAE 18, SOC 1 & 2 Type 2 compliant and ISO 27001 Certified"; reports available "under NDA or contract" — [Procore Trust Center](https://trust.procore.com/) (primary)
- Trust centre links to documents called "AI Overview", "AI Legal Terms" and "AI Accuracy and Transparency", but their content sits behind a "Get access" request; no ISO 42001, sub-processor list or hosting region shown on the public page ("Major Cloud Provider") — [Procore Trust Center](https://trust.procore.com/) (primary)
- UK/EU residency: "with the launch of the UK and EU application zones, Procore hosts application data in-region for users in UK, Europe and surrounding areas" — [Procore Global Infrastructure (en-gb)](https://www.procore.com/en-gb/trust-and-security/infrastructure) (primary). A June 2026 trade article reports a UK Data Zone live, an EU Data Zone due autumn 2026, and Cyber Essentials targeted for year end — [Highways Today, 7 Jun 2026](https://highways.today/2026/06/07/procore-cde-agentic-ai/) (secondary; not confirmed on Procore's page)
- Not stated publicly: whether Helix AI processing (calls to model providers) stays in the UK zone.
- Training: "your data is never used to train models like ChatGPT, Claude or Gemini" ("No third-party model training") — [Procore AI](https://www.procore.com/ai); [Procore Helix](https://procore.com/en-ae/helix-intelligence) (primary). Note this wording covers third-party models; it does not say whether Procore itself trains its own models on customer data.
- Permissions: Procore AI "honours your existing role-based Procore permissions"; users "only see data they're already allowed to see"; "Agents do the data gathering and drafting, your team makes the final call" — [Procore AI (en-gb)](https://www.procore.com/en-gb/assist); [Procore AI](https://www.procore.com/ai) (primary)
- Citations: "numbered citations and visual previews show you the exact source files so you can verify the facts" — [Procore AI](https://www.procore.com/en/ai) (primary)
- Data protection page: [Procore Data Privacy and Governance Standards](https://www.procore.com/trust-and-security/data-protection) (primary; content not extracted in this session)
- Agents and Helix announcements: [Procore Groundbreak 2025 press release, 15 Oct 2025](https://www.businesswire.com/news/home/20251015796723/en)
- Liability on AI output: not found publicly (the "AI Legal Terms" document is gated).

**Autodesk Construction Cloud (Autodesk AI / Autodesk Assistant)**
- Autodesk's Trusted AI programme rests on five Trust Principles for AI, "independently validated through ISO/IEC 42001 certification" — [Autodesk News: Trusted AI starts with transparency and governance](https://adsknews.autodesk.com/en/stories/how-autodesk-builds-trusted-ai/) (primary)
- AI Transparency Cards describe each AI feature: what it does, which models sit behind it, what data it uses and where it comes from, how it was trained, limitations, and safeguards. Originally on the Trust Center, now answerable inside Autodesk Assistant; updated at Autodesk University 2026 — [Autodesk News: AI Transparency Cards in Assistant](https://adsknews.autodesk.com/en/?post_type=news&p=59885) (primary); [AEC Magazine](https://aecmag.com/ai/autodesk-puts-updated-ai-transparency-cards-inside-assistant/) (secondary). AEC Magazine notes the cards will need dates and version histories as providers and models change.
- How to find AI components per product — [Autodesk support article](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-find-information-about-AI-components-integrated-in-Autodesk-products.html) (primary)
- Construction-specific trust blog — [Autodesk Digital Builder: Blueprint for Trusted AI in Construction](https://www.autodesk.com/blogs/construction/autodesks-blueprint-for-trusted-ai-in-construction/) (primary)
- On training: "when features do necessitate training data, Autodesk uses various sources ... while ensuring transparency" — no blanket "we never train on ACC customer data" statement found; answer is per feature in the Transparency Cards — [Autodesk Blueprint blog](https://www.autodesk.com/blogs/construction/autodesks-blueprint-for-trusted-ai-in-construction/)
- Security certifications, UK/EU residency for ACC, sub-processors, AI output disclaimers: not verified in this session (gap).

**Buildertrend (AI features)**
- AI features listed: Client Updates, Bill Capture, Page Naming, Selections, Submittals — [Buildertrend AI in construction](https://buildertrend.com/ai-in-construction/) (primary)
- Training claim: AI "built on the company's deep expertise in residential construction and not on individual customer data"; data protected with "encrypted data protocols, continuous monitoring and industry-leading infrastructure partners" — [Buildertrend AI in construction](https://buildertrend.com/ai-in-construction/) (primary)
- SOC 2: conflicting. One review says Buildertrend "does not currently hold" SOC 2 — [Connecteam review](https://connecteam.com/reviews/buildertrend/) (secondary); another says the hosting facilities hold ISO 27001/FedRAMP and supply an annual SOC 2 Type 2 report (i.e. the host's, not Buildertrend's) — [Buildertrend FAQ](https://buildertrend.com/frequently-asked-questions/) (primary, via snippet)
- Liability: Website Services Agreement (last updated 17 Feb 2026) says generative AI output may be incorrect or incomplete, gives no assurance on accuracy, legality or fitness for purpose, and puts the risk on the user — [Buildertrend Website Services Agreement](https://buildertrend.com/web-services-terms-and-conditions/) (primary; this agreement covers the website service; main T&Cs not checked)
- Trust centre, ISO 42001, UK residency, DPA, sub-processors: not stated / not found. Buildertrend is US-focused; no UK data residency found.

**Houzz Pro (Houzz AI)**
- Training: client details, projects and financials "are never used to train public AI tools" — [Houzz Pro Data, Security & Privacy FAQ](https://www.houzz.com/pro-help/r/houzz-pro-data-security--privacy-faq); [Houzz Pro privacy & trust](https://pro.houzz.com/for-pros/feature-privacy-trust) (primary). Wording is "public AI tools", which leaves open use for Houzz's own models.
- Security: data stored with AWS in multiple locations; certifications quoted are AWS's (SOC 2, SOC 3, ISO 9001/27001, FedRAMP), not Houzz's own — [Houzz Pro FAQ](https://www.houzz.com/pro-help/r/houzz-pro-data-security--privacy-faq) (primary)
- UK AI features marketed — [Houzz Pro UK blog](https://pro.houzz.co.uk/pro-learn/blog/houzz-pro-puts-the-power-of-artificial-intelligence-to-work-for-you) (primary)
- A risk-rating site says the Houzz (consumer) privacy policy allows AI training with no opt-out described — [Gen Digital Agent Trust Hub](https://ai.gendigital.com/app/houzz-com) (secondary; covers consumer houzz.com, not Pro terms)
- Own SOC 2/ISO certificates, ISO 42001, UK residency, DPA, AI disclaimers: not found.

### Inferences
- For a small UK builder, Procore and Autodesk are the only two of the four that publish enough to do a real check. Buildertrend and Houzz Pro rely on "our cloud host is certified", which is not the same as the vendor being audited.
- "Never used to train ChatGPT/Claude/Gemini" (Procore) and "never used to train public AI tools" (Houzz) are narrower than "never used to train any model". Builders should ask the exact question.
- None of the four construction platforms publicly states its EU AI Act (Art 50) position, or publishes model cards/evaluations beyond Autodesk's Transparency Cards.

### Gaps
- Procore's gated "AI Legal Terms" and "AI Accuracy and Transparency" content; whether Helix model calls stay in the UK zone; Procore ISO 42001 status (not listed).
- Autodesk ACC certifications list, UK/EU residency, sub-processors, and the exact ISO 42001 certificate scope and date.
- Buildertrend and Houzz Pro DPAs, sub-processor lists, and UK GDPR statements.
- No construction platform's EU AI Act statement found.

## 2. General AI assistants: plan differences on training, DPA, retention, residency, certifications

### Takeaway
The biggest risk line is free/personal plans versus business plans. ChatGPT Free/Plus and Claude Free/Pro can use chats for training (ChatGPT by default; Claude if the user allows it, with 5-year retention), and have no DPA. Business/Team/Enterprise tiers of all four assistants do not train on business data by default and come with a DPA. Microsoft (Copilot), Google (Gemini for Workspace) and Anthropic hold or claim ISO/IEC 42001; OpenAI's claim is only from secondary sources here.

### Cited Findings

**ChatGPT (OpenAI)**
- Free, Plus and Pro: chats used for training by default; each user can opt out in Data Controls — [Janus Compliance, plan-by-plan 2026](https://www.januscompliance.co.uk/blog/is-chatgpt-gdpr-compliant-plan-by-plan-2026) (secondary)
- Business and Enterprise: inputs and outputs excluded from training by default — [Janus Compliance](https://www.januscompliance.co.uk/blog/is-chatgpt-gdpr-compliant-plan-by-plan-2026); OpenAI's own page is [openai.com/enterprise-privacy](https://openai.com/enterprise-privacy/) (primary; returned HTTP 403 to fetch in this session)
- DPA: only Business, Enterprise and API; Free/Plus/Pro not covered — [Janus Compliance](https://www.januscompliance.co.uk/blog/is-chatgpt-gdpr-compliant-plan-by-plan-2026); [Teamazing DPO checklist](https://www.teamazing.com/blog/chatgpt-business-gdpr/) (secondary)
- Retention: consumer deleted chats removed within 30 days; Business/Enterprise admins control retention — [Humla, OpenAI retention 2026](https://humla.team/blog/openai-data-retention-policy) (secondary)
- Residency: Enterprise and Edu (and API) offer storage regions including "Europe (EEA + Switzerland)" and "United Kingdom"; inference residency in Europe but reportedly not UK; Business tier reportedly lacks residency (data in US under SCCs) — sources disagree, confirm in writing — [Janus Compliance](https://www.januscompliance.co.uk/blog/is-chatgpt-gdpr-compliant-plan-by-plan-2026); [Yardwork](https://yardwork.dev/en/blog/chatgpt-gdpr) (secondary)
- ISO 42001: a secondary report says OpenAI's security page claims ISO/IEC 42001:2023 coverage for consumer and business products — [Blocksize, ISO 42001 2026](https://ai.blocksize.hr/blog/en/iso-42001-ai-management-system-certification-2026); [AI Provider Trust Registry](https://aiprovidertrust.com/questions/iso-42001/) (secondary; not confirmed on openai.com this session)
- Copyright indemnity ("Copyright Shield") announced Nov 2023 for ChatGPT Enterprise and API — [Wilson Sonsini](https://www.wsgr.com/en/insights/will-indemnification-commitments-address-market-demands-in-ai.html) (secondary, 2023–24; check current terms)

**Microsoft 365 Copilot (Business / Enterprise)**
- Microsoft's Copilot privacy page: for EU customers Copilot is an EU Data Boundary service; customers outside the EU may have queries processed in the US, EU or other regions — [Microsoft Learn: Data, Privacy, and Security for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365/copilot/microsoft-365-copilot-privacy) (primary)
- UK is not in the EU Data Boundary; data at rest can be stored in the UK for UK tenants, but LLM processing is not limited to the UK; one UK guide says Microsoft (3 Apr 2026 update) expects UK local inferencing by end of 2026, another says no UK date was announced — [CompanyScope review](https://companyscope.io/vendors/microsoft-365-copilot); [The AI Consultancy](https://theaiconsultancy.ai/blog/anthropic-models-microsoft-365-copilot-uk); [MickAI](https://mickai.co.uk/articles/is-microsoft-copilot-sovereign-data-leaves) (secondary, conflicting)
- "Flex Routing" can send LLM processing outside the EU boundary at peak demand and can be disabled by admins — [Janus Compliance, Copilot 2026](https://www.januscompliance.co.uk/blog/is-microsoft-365-copilot-gdpr-compliant-2026) (secondary)
- Anthropic (Claude) models in Copilot: excluded from EU Data Boundary and in-country commitments, with a move into the boundary for EU/EFTA by end of 2026; reports that Claude is switched on by default for UK/EU/EFTA tenants that never set the Anthropic sub-processor control (from 9 Dec) — [Beri.net](https://www.beri.net/article/microsoft-365-copilot-claude-default-on-december-9-uk-eu-efta-eu-data-boundary-mc1546435-anthropic-subprocessor-opt-out); [TechsCurrent, Nov 2026](https://techscurrent.com/2026/11/claude-microsoft-copilot-eu-data-boundary-admin-checklist/) (secondary; sources disagree on UK default)
- ISO 42001: M365 Copilot "holds ISO/IEC 42001" plus SOC 1/2, ISO 27001/27018 — [CompanyScope](https://companyscope.io/vendors/microsoft-365-copilot) (secondary); Microsoft Learn ISO/IEC 42001 offering page lists in-scope services (updated 11 Sep 2026, per [aicompliancevendors.com](https://aicompliancevendors.com/blog/iso-42001-certified-companies-list)). Verify in Microsoft Service Trust Portal.
- Copilot Copyright Commitment (Sep 2023) covers Microsoft and OpenAI-model tools, not third-party models — [NZ Herald / FT](https://nzherald.co.nz/business/cloud-giants-offer-only-limited-protection-to-businesses-over-ai-copyright-claims/UJGD3KODAJBJNB73X6FOWJGXQU) (secondary, 2024; check whether Claude-in-Copilot is covered)
- Free consumer "Microsoft Copilot" (personal account) terms not checked in this session (gap).

**Google Gemini in Workspace**
- "Gemini has received security and privacy certifications, including ISO 42001, BSI C5 and FedRAMP High"; also SOC 1/2/3 — [Google Workspace: Generative AI Security, Compliance and Privacy](https://workspace.google.com/security/ai-privacy/); [Workspace AI tools for business](https://workspace.google.com/solutions/ai/) (primary)
- Google "does not use customers' Workspace data to train or improve the underlying generative AI and LLMs that power Gemini, Search, and other systems outside of Workspace without permission" — [Workspace AI privacy hub](https://workspace.google.com/security/ai-privacy/) (primary)
- Gemini applies existing Workspace controls such as data-regions policies and DLP — [Google Cloud generative AI privacy whitepaper](https://services.google.com/fh/files/misc/genai_privacy_google_cloud_202308.pdf) (primary, older doc)
- UK data region option for Gemini processing: not stated in sources found (gap). Consumer Gemini app (personal Google account) terms not checked (gap).

**Claude (Anthropic)**
- Consumer plans (Free, Pro, Max): since the Sept 2025 terms update, users choose whether chats are used for training; if they allow it, retention extends to five years; if not, 30 days — [Anthropic: Updates to our consumer terms](https://www.anthropic.com/news/updates-to-our-consumer-terms) (primary); [Claude Code docs: data usage](https://code.claude.com/docs/en/data-usage) (primary)
- Team, Enterprise, Education, API and third-party cloud deployments fall under Commercial Terms; the training choice and 5-year retention do not apply; no training by default — [Anthropic consumer terms update](https://www.anthropic.com/news/updates-to-our-consumer-terms) (primary); one secondary blog contradicts this for Team — [Humla](https://humla.team/blog/anthropic-data-retention-policy)
- ISO/IEC 42001:2023 accredited certification announced 13 Jan 2025, issued by Schellman (ANAB-accredited); certificate on Anthropic Trust Center — [Anthropic news](https://www.anthropic.com/news/anthropic-achieves-iso-42001-certification-for-responsible-ai) (primary). Scope reportedly first-party services only — [AI Provider Trust Registry](https://aiprovidertrust.com/questions/iso-42001/) (secondary)
- Copyright indemnity in Commercial Terms from 1 Jan 2024 (enterprise and API), with exclusions (misuse, customer modifications, combinations) — [Proskauer](https://www.proskauer.com/blog/anthropic-joins-the-party-offers-copyright-shield-to-enterprise-ai-customers) (secondary)

**AI transparency, cross-vendor**
- ISO 42001 certifies the organisation's AI management system, not any individual model; product coverage depends on certificate scope — [aicompliancevendors.com](https://aicompliancevendors.com/blog/iso-42001-certified-companies-list) (secondary); see also [AWS ISO 42001 FAQ](https://aws.amazon.com/compliance/iso-42001-faqs/)
- Vendor AI-output disclaimers are typical: e.g. "no responsibility for errors or inaccuracies; verify outputs" — [Upland AI disclaimer](https://help.uplandsoftware.com/disclaimers/BYOAI.htm) (example of the norm, not one of the eight tools)

### Inferences
- Simple slide message: "Free/personal AI = treat as public. Business plan + DPA + training off = minimum for client data."
- For UK firms, "UK data residency" for model processing is still patchy: ChatGPT Enterprise stores in UK but infers in EU; Copilot UK inference not confirmed; Gemini UK region not found. Builders should not assume prompts stay in the UK.
- Microsoft 365 tenants should check the Anthropic sub-processor toggle before December 2026.
- Copyright indemnities exist for business tiers only and are narrow; they don't cover wrong answers (e.g. a wrong Building Regs reading).

### Gaps
- OpenAI ISO 42001 and SOC 2 not confirmed on openai.com (403). Model/system cards and evaluations pages for each vendor were not collected in this session (OpenAI, Anthropic and Google publish system/model cards, but no URLs verified here).
- Google Workspace UK processing region; consumer Gemini and consumer Copilot training defaults.
- EU AI Act GPAI Code of Practice signatory list not found in this session.

## 3. Legal compliance: UK GDPR, EU AI Act, ISO/IEC 42001

### Takeaway
UK GDPR still applies in full when a builder uses AI; the vendor DPA is the key document. The EU AI Act Article 50 transparency duties have applied since 2 Aug 2026 (not delayed by the Digital Omnibus); this matters to UK firms mainly if they serve EU clients. ISO 42001: confirmed for Anthropic (primary), Autodesk (primary), Google Gemini for Workspace (primary); claimed by secondary sources for Microsoft 365 Copilot and OpenAI; not found for Procore, Buildertrend, Houzz Pro.

### Cited Findings
- Adopting AI does not change UK GDPR obligations (ICO 2023 Guidance on AI and data protection, as summarised) — [GDPR Local summary](https://gdprlocal.com/ico-artificial-intelligence-navigating-ai-compliance-and-governance/) (secondary)
- ICO consulted on generative AI in a five-part series (2024) and committed to update guidance; updated guidance expected after the Data (Use and Access) Act 2025 — [GDPR Local](https://gdprlocal.com/ico-artificial-intelligence-navigating-ai-compliance-and-governance/) (secondary); ICO AI plans for 2026/27 — [PrivacyLaws](https://www.privacylaws.com/reports-gateway/articles/uk146/uk146ico/) (secondary)
- ICO agentic AI Tech Futures report (Jan 2026) is explicitly not guidance — [Lewis Silkin](https://www.lewissilkin.com/en/insights/2026/01/22/ico-tech-futures-report-agentic-ai-102mdki); [Skadden, Mar 2026](https://www.skadden.com/insights/publications/2026/03/uk-regulator-to-agentic-ai-developers-and-deployers) (secondary)
- EU AI Act Art 50 applies from 2 Aug 2026, unchanged by the Omnibus; grace period to 2 Dec 2026 for machine-readable marking on systems already on the market — [Legalithm](https://www.legalithm.com/en/blog/eu-ai-act-what-applies-2-august-2026); [Elevate Consult](https://elevateconsult.com/insights/eu-ai-act-article-50-icp-impact/) (secondary)
- Digital Omnibus on AI = Regulation (EU) 2026/1744 (OJ 24 Jul 2026, in force 27 Jul 2026); Annex III high-risk delayed to 2 Dec 2027, Annex I to Aug 2028 — [Usercentrics](https://usercentrics.com/knowledge-hub/eu-ai-act-high-risk-delay-article-50-transparency-consent/); [AIActo](https://www.aiacto.eu/en/blog/digital-omnibus-ai-act-report-2027) (secondary; check against EUR-Lex)
- GPAI model provider duties (from 2 Aug 2025) not delayed — [AI Policy Desk](https://www.aipolicydesk.com/blog/eu-ai-act-august-2026-whats-delayed-vs-what-applies) (secondary)
- ISO 42001 holders: Anthropic ([primary](https://www.anthropic.com/news/anthropic-achieves-iso-42001-certification-for-responsible-ai)); Autodesk ([primary](https://adsknews.autodesk.com/en/stories/how-autodesk-builds-trusted-ai/)); Google Gemini for Workspace ([primary](https://workspace.google.com/security/ai-privacy/)); AWS ([primary](https://aws.amazon.com/blogs/machine-learning/aws-achieves-iso-iec-420012023-artificial-intelligence-management-system-accredited-certification/)); Microsoft 365 Copilot ([secondary](https://companyscope.io/vendors/microsoft-365-copilot)); OpenAI ([secondary](https://ai.blocksize.hr/blog/en/iso-42001-ai-management-system-certification-2026)). Procore trust centre does not list it ([primary](https://trust.procore.com/)).

### Inferences
- A builder is the data controller for client and council data they paste into AI; the vendor is a processor only under a business plan with a DPA.
- No vendor-specific EU AI Act Art 50 statements were found for any of the eight tools; this is a fair "not stated" across the board.

### Gaps
- ICO's current ico.org.uk AI guidance pages not fetched directly. Suggested page to verify: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/ (not verified this session).
- Vendor EU AI Act readiness statements.

## 4. "Before you use AI with client or council data" checklist (ICO / NCSC grounded)

### Takeaway
Grounded in NCSC's LLM risk post and AI guidance plus ICO principles: keep sensitive data out of public/free tools, use a business plan with a DPA and training off, limit access, check outputs, and keep a human responsible.

### Cited Findings
- NCSC (Mar 2023): do not include sensitive information in queries to public LLMs; queries are visible to the provider and may be stored; the operator could later change privacy approach; prompt injection risk — [NCSC: ChatGPT and large language models: what's the risk?](https://www.ncsc.gov.uk/blog-post/chatgpt-and-large-language-models-whats-the-risk) (primary)
- NCSC guidelines for secure AI system development (for builders of AI systems; supply chain, access controls) — [NCSC collection](https://www.ncsc.gov.uk/collection/guidelines-secure-ai-system-development) (primary)
- NCSC "Thinking about the security of AI systems" (Aug 2026 PDF) — [NCSC PDF](https://www.ncsc.gov.uk/sites/default/files/2026-08/Thinking-about-the-security-of-AI-systems_0.pdf) (primary; content not extracted)
- NCSC agentic AI guidance: start small, low-risk tasks, keep humans in oversight, name who approves AI access and who can shut it down — [Bratby Law summary](https://bratby.law/ncsc-agentic-ai-guidance/); [The Cyber Express](https://thecyberexpress.com/agentic-ai-expands-enterprise-attack-surface/) (secondary)
- Plain-English SME reading of NCSC: keep sensitive information out of public AI tools; distinguish public, private cloud and self-hosted — [Dr Dave Heath](https://drdaveheath.com/blog/ncsc-guidance-on-generative-ai-in-plain-english) (secondary)
- UK government AI Cyber Security Code of Practice implementation guide — [GOV.UK PDF](https://assets.publishing.service.gov.uk/media/679cae441d14e76535afb630/Implementation_Guide_for_the_AI_Cyber_Security_Code_of_Practice.pdf) (primary)
- Small-business AI checklist (useful model, but New Zealand/Australia, Jan 2026, not UK) — [NCSC NZ AI guide for small businesses](https://www.ncsc.govt.nz/protect-your-organisation/ai-guide-for-small-businesses/)
- UK GDPR applies unchanged to AI use (ICO) — [GDPR Local summary](https://gdprlocal.com/ico-artificial-intelligence-navigating-ai-compliance-and-governance/)

Draft checklist (built from the above; wording is ours):
1. Is it a business plan (ChatGPT Business/Enterprise, Copilot with work account, Gemini in Workspace, Claude Team/Enterprise) and not a free/personal account? (NCSC; vendor plan terms above)
2. Is there a signed/accepted DPA and is model training off by default? (UK GDPR processor rules; vendor pages)
3. Do you know where data is stored and processed (UK/EU/US) and how long it is kept? (vendor residency pages)
4. Does the vendor show a trust centre with ISO 27001 / SOC 2 of its own (not just "our host AWS is certified")? ISO 42001 is a plus.
5. Remove names, addresses, phone numbers, bank details and anything about health or children before pasting; never paste council portal passwords or confidential tenders into public tools. (NCSC)
6. Does the tool respect who can see what (permissions), and is MFA on? (Procore permissions claim; NCSC basics)
7. Check every AI answer against the source (drawings, Approved Documents, contract); prefer tools that show citations. Vendors put accuracy risk on you (Buildertrend agreement). (NCSC; vendor disclaimers)
8. Tell clients if AI helped produce something they rely on, and record which tool you use in your privacy notice. (ICO transparency principle; EU Art 50 if EU clients)
9. For AI agents that send emails or change records: start with low-risk tasks, keep a human approving, and know how to switch it off. (NCSC agentic guidance)
10. Write a one-page AI rule for staff: which tools are allowed, what data never goes in.

### Inferences
- Items 1–2 remove most of the data-protection risk for a sole trader at low cost (business tiers are a per-seat subscription).

### Gaps
- No UK NCSC small-business-specific AI checklist found (the NZ one is the closest); ICO small-organisation generative AI page not verified.

## 5. UK construction-sector surveys on AI adoption and trust (2025–2026)

### Takeaway
Adoption is rising fast but shallow: RICS 2026 says two-thirds of construction respondents use AI in some form but only 19% regularly in specific processes; privacy and security concern rose from 22% to 30%. FMB/CIOB (Nov 2026) says 57% of builders use AI more than a year ago, 22% don't use it at all, and 80% of users use it for admin.

### Cited Findings
- RICS AI in Commercial Property and Construction Report 2026 (3,100+ responses): two-thirds of construction respondents use AI in some form, up from just over half in 2025; regular use in specific processes up from 12% to 19%; organisations reporting no AI use fell by over a third; privacy and security concerns rose from 22% to 30%; 37% of construction respondents plan to increase AI investment in next 12 months (47% in commercial property); skills shortage remains a major barrier — [RICS 2026 report](https://www.rics.org/news-insights/ai-in-commercial-property-and-construction-report-2026); [Property Week](https://www.propertyweek.com/news/ai-use-jumps-across-commercial-property-and-construction-rics-reports) (figures via search summary; verify on RICS PDF)
- RICS 2025 report (2,200+ responses): 45% of organisations reported no AI use; 1% had scaled AI across projects — [RICS 2025](https://www.rics.org/news-insights/optimism-high-for-ai-in-construction-but-skills-shortages-and-integration-challenges-adoption) (primary)
- FMB and CIOB State of Trade Survey (Nov 2026): 57% of construction businesses use AI more than a year ago; 22% not using AI at all; among users, 80% use it for admin/office tasks, 42% for quotes, estimates and tenders — [Specification Online, 11 Nov 2026](https://specificationonline.co.uk/sections/sustainability/articles/2026-11-11/ciob/builders-embrace-ai-as-pressures-mount-across-construction); [Build News](https://www.buildnews.co.uk/more-than-half-of-construction-firms-increase-ai-use-survey-finds/) (secondary reports of FMB/CIOB release)

### Inferences
- The FMB/CIOB 80% admin figure suggests builders mostly use general assistants (ChatGPT, Copilot, Gemini) for emails, quotes and paperwork, which is exactly where client personal data leaks into free tools.
- The 42% quoting figure links to accuracy risk: AI-made quotes need checking.

### Gaps
- No NFB survey on AI found. No survey gives a direct "trust in AI" percentage; privacy/security concern (RICS) is the closest measure.
- No survey data specific to Romanian-run UK building firms.
