# Trust check: trades/job-management apps, accounting apps and AI receptionists used by UK builders (checked 19 Nov 2026)

All pages below were checked on 19 Nov 2026 unless another date is given. "Not stated" means I looked at the page named and it did not say. Many vendor pages were only partly readable (long legal pages were truncated by the fetch tool), so "not stated" sometimes means "not found in what I could read". Where a third-party site makes a claim the vendor's own page does not back, I say so.

## 1. Security (certifications, hosting, encryption, trust centre)

### Takeaway
Only the two accounting giants publish hard security evidence. Xero states ISO/IEC 27001:2022 certification and SOC 2 reports. Among trades apps, Joblogic (Cyber Essentials Plus) and Commusoft (yearly external pen test, GCP hosting in the UK, encryption at rest) say the most. Tradify, Fergus, ServiceM8, Jobber, YourTradebase, Powered Now and the small AI receptionists publish no certification I could find.

### Cited Findings
**Xero**
- States it is certified to ISO/IEC 27001:2022. The certificate needs a Xero login, or you can request it with a form. — [Xero UK security](https://www.xero.com/uk/security/)
- Produces SOC 2 reports from independent audits. Download needs a login. — [Xero UK security](https://www.xero.com/uk/security/); [SOC report request](https://www.xero.com/about/security/soc-report/)
- PCI DSS v4.0 SAQ A. Encryption "when it's transferred and stored". Firewalls, intrusion protection, network segregation. Has a vulnerability disclosure programme and a security noticeboard. Hosting region not stated on the security page. — [Xero UK security](https://www.xero.com/uk/security/)

**QuickBooks UK (Intuit)**
- I did not fetch an Intuit security/certification page in this pass. Gap (see below).

**Commusoft**
- Hosted on Google Cloud Platform, with data centres in the USA, UK and India. Client data kept in the client's home country where possible. — [Commusoft security](https://www.commusoft.com/security)
- Encryption at rest on network drives; HTTPS with TLS 1.1 to 1.3, TLS 1.0 restricted; salted password hashes; daily encrypted backups with audited access. — [Commusoft security](https://www.commusoft.com/security)
- "External yearly penetration testing is performed by an industry-leading security company", plus quarterly vulnerability scans. "Commusoft operate a PCI compliant network." — [Commusoft security](https://www.commusoft.com/security)
- The official page does NOT mention ISO 27001 or Cyber Essentials. A search snippet of the same page and a review site said "ISO 9001 and ISO 27001 compliance", but I could not confirm this on the live page. Note also "compliance" is not the same as "certified". — [Commusoft security](https://www.commusoft.com/security); contradicted by [Zoftware analysis](https://zoftwarehub.com/products/commusoft/zoftware-analysis) (third party)

**Joblogic**
- Announces Cyber Essentials Plus (after first holding Cyber Essentials), reviewed annually per IASME guidance. Page last updated 4 June 2024; the accreditation date itself is not stated. No ISO 27001 or hosting mentioned. — [Joblogic blog](https://www.joblogic.com/blog/joblogic-achieves-cyber-essentials-plus-accreditation/)

**ServiceM8**
- Runs on AWS with data centres around the world; EU users' data moved to a European region; some transfers outside the EEA "with measures" but countries not named. No certifications mentioned. — [ServiceM8 GDPR page](https://servicem8.com/gdpr)
- A search summary of ServiceM8 pages says data is stored in the US, Australia, Ireland, Singapore and Tokyo. I could not see this sentence myself. — search summary of [ServiceM8 privacy policy](https://origin.servicem8.com/privacy-policy)
- SSL certificates issued by Amazon; account activity log kept 90 days (from a search summary of ServiceM8 security page). — [ServiceM8 features-security](https://servicem8.com/features-security)

**Tradify**
- No security page found: `tradifyhq.com/security` returns 404. — [tradifyhq.com/security](https://www.tradifyhq.com/security)
- A third-party review says no SOC 2 or ISO 27001 is publicly listed. — [The Techy Side, Tradify review](https://www.thetechyside.com.au/software/tradify) (third party, about 8 months old)

**Fergus**
- Fergus's own "official information" page does not mention certifications or hosting region. It links a Privacy Policy and a Data Processing Addendum. — [Fergus llm-info](https://fergus.com/llm-info/)
- A third-party review says no SOC 2 or ISO 27001 is publicly listed and no known breaches. — [The Techy Side, Fergus review](https://www.thetechyside.com.au/software/fergus) (third party)

**Jobber**
- I found no Jobber trust centre or SOC 2 statement by search. Jobber's community thread "AI and security" exists but returned 403 to my fetch. — [Jobber community thread](https://community.getjobber.com/discussions/operations-forum/ai-and-security/7048)

**YourTradebase**
- Homepage mentions only a "world's most secure payment processing service" partner for card payments, no certifications, no hosting, no security page; links to /about/privacy and /about/gdpr. — [YourTradebase](https://www.yourtradebase.com/)

**Powered Now (incl. PN Receptionist)**
- Receptionist page: data storage location not stated; only "UK-based support". No security claims. — [PN Receptionist](https://powerednow.com/receptionist/)

**TradGo (small UK AI receptionist)**
- Site hosted on a free `pages.dev` subdomain. Operated by "Michael Stevenson trading as Autaimate", St Austell address; no company number; no security claims, no data location, no GDPR mention on the homepage. — [TradGo](https://tradgo-site.pages.dev/)

**TradesCall AI**
- Two landing pages, both on `pages.dev` subdomains; no company registration, pricing, reviews or security information found. — [TradesCall AI](https://tradescall-ai.pages.dev/); [tradescall.pages.dev](https://tradescall.pages.dev/)

### Inferences
- For a council or public-sector buyer, Cyber Essentials (or Plus) is often the baseline. Of the trades apps checked, only Joblogic shows it publicly. One source notes that if a tender asks for Cyber Essentials, ISO 27001 alone may not satisfy it. — [CloudSwitched](https://www.cloudswitched.com/blog/cyber-essentials-plus-vs-iso-27001) (general background, third party)
- "Not published" is not the same as "not held". Vendors may share evidence on request. But a small builder cannot easily check what is not published.
- The two tiny AI receptionists look like very early, one-person products. That is not proof of bad practice, but there is nothing to check.

### Gaps
- Intuit/QuickBooks security certifications: not fetched this pass.
- Jobber SOC 2 / hosting: not found; community thread blocked (403).
- Whether Fergus, Tradify, ServiceM8, YourTradebase hold Cyber Essentials: not found anywhere public.
- Tradify ownership: one aggregator says The Access Group acquired Tradify in Oct 2024. Not verified with a primary source. — [Tradify AI search result summary, aggregator](https://dupple.com/tools/tradify)

## 2. Data protection (UK GDPR, DPA, sub-processors, AI provider, training, retention, call recording consent)

### Takeaway
Xero is the clearest: it names its LLM providers and says JAX chat data is not used to train or retained by them. ServiceM8 is the only trades app found that names OpenAI and Anthropic as sub-processors. Jobber's terms say AI chats "may be logged for analysis, improvement and security" and that it may use de-identified content to improve the service. Most trades apps do not name their AI provider or say anything about training. AI receptionists put call-recording consent on the business, or say nothing.

### Cited Findings
**Xero / JAX**
- "No, JAX chat doesn't use your data to train the LLMs it uses." Uses "third-party providers like AWS, Microsoft Azure, GCP, OpenAI". Data processed by providers "is not retained and isn't used to train the LLMs". — [Xero JAX page](https://www.xero.com/uk/jax/)
- No off switch as such: JAX only runs when opened; admins can limit access through roles. Users on Xero's ideas forum asked for an off switch. — [Xero JAX page](https://www.xero.com/uk/jax/); [Xero product ideas forum](https://productideas.xero.com/forums/939198-for-small-businesses/suggestions/49450391-just-ask-xero-jax-ability-to-turn-off-after-i)
- Data commitments: shares data with partners only with express consent; benchmarks privacy against GDPR. Does not say whether customer data trains Xero's own models. — [Xero responsible data use](https://www.xero.com/uk/data/)

**QuickBooks UK / Intuit**
- Intuit Intelligence "draws on data from 10 million customers", about 625,000 attributes per business; says it adheres to responsible AI principles. No AI vendor named; does not say if customer data trains models. — [Intuit UK press release, 14 Oct 2026](https://quickbooks.intuit.com/uk/press/intuit-intelligence-now-available-internationally/)
- Responsible AI page: principle of "privacy and security"; no statement on training, no AI opt-out described; no model provider named. — [Intuit responsible AI](https://www.intuit.com/privacy/responsible-ai/)
- A US QuickBooks help article says GenAI is not used to calculate the numbers in QuickBooks. — [How's Intuit using Generative AI? (US help)](https://quickbooks.intuit.com/learn-support/en-us/help-article/intuit-assist/hows-intuit-using-generative-ai/L1Z16bIPW_US_en_US) (US page; from search summary)

**Jobber**
- Terms (last updated 22 Sep 2026): "any information shared with an AI Tool may be logged for analysis, improvement, and security purposes" (s.12.2); may use "de-identified User Content for the purpose of improving the Service" (s.6.1(c)); for third-party AI tools you connect, training is governed by your agreement with that provider (s.12.6(b)). Governed by Canadian law. — [Jobber Terms of Service](https://getjobber.com/terms-of-service/)
- AI Receptionist: no AI provider named, no retention period. Stores call recording, transcript, summary, client name, phone and address. — [Jobber Receptionist help](https://help.getjobber.com/hc/en-us/articles/25315927533847-Receptionist-powered-by-Jobber-AI)
- Call recording consent: Jobber "recommends" telling callers that the phone is answered by AI or calls may be recorded, but says this is not required; tells users to "check any local or state regulations". Dedicated numbers available in US, Canada and UK. — [Jobber Receptionist help](https://help.getjobber.com/hc/en-us/articles/25315927533847-Receptionist-powered-by-Jobber-AI)

**ServiceM8 / Office Agent**
- DPA: customer is controller, ServiceM8 processor. — [ServiceM8 DPA](https://www.servicem8.com/dpa)
- Sub-processors for customers' customer data: AWS and Nexmo. Processors for account-holder data include Anthropic and OpenAI (plus Google, Twilio, Stripe, Mixpanel, FullStory and others). No statement on AI training. No UK GDPR wording; page footer © 2024. — [ServiceM8 GDPR page](https://servicem8.com/gdpr)
- Office Agent help: chats "private to you"; AI provider, training and retention not stated. — [ServiceM8 Office Agent](https://support.servicem8.com/help-center/servicem8-add-ons/office-agent/introducing-office-agent)
- Inference: the sub-processor split is confusing. Office Agent reads customer job data, but the AI providers are listed only under account-holder data. Worth asking ServiceM8.

**Tradify**
- Privacy policy: legal entity not named, UK GDPR not mentioned, sub-processors not named, hosting/transfers "wherever Tradify operates", no AI or ML mention (the only "OpenAI" is an ad-referral cookie). No visible date (cookie list "Version 1 / 2026-09-03"). — [Tradify privacy policy](https://www.tradifyhq.com/privacy-policy)
- Tradify has AI "SmartTools" (receipt reading, writing line items), but no AI data statement found. — [Tradify SmartTools](https://tradifyhq.com/features/smarttools)

**Fergus**
- Has a DPA and privacy policy linked; AI respects user permissions; AI provider not named. — [Fergus llm-info](https://fergus.com/llm-info/)
- Third-party review says Fergus claims compliance with NZ, Australian, EU and UK GDPR. — [The Techy Side](https://www.thetechyside.com.au/software/fergus) (third party)

**Commusoft**
- Provides GDPR data processor contracts to all clients. AI feature "AI:den" listed with no data-handling details. — [Commusoft security](https://www.commusoft.com/security)

**Powered Now Receptionist**
- Creates call summary and recording. Whether callers are told it is AI: not stated ("No robot voice" is not a disclosure). Consent: not stated. Data location and AI provider: not stated. — [PN Receptionist](https://powerednow.com/receptionist/)

**TradGo**
- Agent introduces itself as "[your name]'s agent". AI provider, recording, consent, data location: not stated on homepage. — [TradGo](https://tradgo-site.pages.dev/)

### Inferences
- UK law on call recording differs from US state law. Jobber's wording ("local or state regulations") is US-framed. Under UK GDPR, the business is controller and must tell callers about recording and AI use; none of the receptionist vendors spell this out for UK users. (Legal background to be checked by the legal-research note, not here.)
- The common pattern: "we are processor, you are controller" in the DPA, so the builder carries the duty to inform callers and customers.

### Gaps
- Retention periods for call recordings and AI chats: not stated by any vendor checked.
- Whether Powered Now, Tradify, Fergus, Commusoft, Joblogic, YourTradebase use customer data to train AI: not stated.
- Fergus and Tradify DPA texts not read.

## 3. AI transparency and quality (what the AI does, limits, accuracy, testing, human review, AI policy)

### Takeaway
Human approval before actions is the common design: ServiceM8, Fergus, Intuit and TradGo all say the AI prepares and the user approves. Only Xero and Intuit publish responsible-AI commitments. Nobody publishes accuracy figures or test results. Intuit says plainly "Intuit Intelligence can make mistakes".

### Cited Findings
- **Xero:** "we are transparent about where we use AI systems"; will "always assess the capabilities of a technology, including their accuracy and trustworthiness" before release; "actively monitor[s] newly released capabilities". — [Xero responsible data use](https://www.xero.com/uk/data/)
- **Xero:** CPTO said JAX combines an LLM with ML and deep learning models to bolster accuracy (press claim). — [Accounting Today](https://www.accountingtoday.com/news/xeros-jax-said-to-tame-gen-ai-hallucinations-for-acconting-tasks)
- **Intuit:** six responsible AI principles (incl. transparency, accountability); AI Governance Committee; concerns via Integrity Line. Testing not described. — [Intuit responsible AI](https://www.intuit.com/privacy/responsible-ai/); [Intuit AI governance](https://www.intuit.com/privacy/responsible-ai/governance/)
- **Intuit Intelligence (UK, Oct 2026):** features in beta; accountants have "every recommendation left for them to review and approve"; uses LLMs for reasoning, ML for prediction, "deterministic code where precision matters"; only customer-reported figures (13 hours a month saved, 70% "confident their books are done right"); "Intuit Intelligence can make mistakes." — [Intuit UK press release](https://quickbooks.intuit.com/uk/press/intuit-intelligence-now-available-internationally/)
- **ServiceM8:** "Office Agent prepares supported actions for your approval. Approving carries out the action." Features depend on permissions and plan. — [ServiceM8 Office Agent](https://support.servicem8.com/help-center/servicem8-add-ons/office-agent/introducing-office-agent)
- **Fergus:** AI "respects each user's existing Fergus permissions" and shows a confirmation step before anything is created, changed or sent. Assistant released to all users Sept 2026. — [Fergus llm-info](https://fergus.com/llm-info/); [Fergus release notes 2026](https://help.fergus.com/en/articles/13627195-release-notes-2026)
- **Jobber Receptionist:** no accuracy claim; you "test" to verify it handles calls accurately; admins review transcripts after the fact; escalation on keywords; greeting edits "may be reviewed". — [Jobber Receptionist help](https://help.getjobber.com/hc/en-us/articles/25315927533847-Receptionist-powered-by-Jobber-AI)
- **Tradify:** SmartTools page claims "faster and more accurate quoting"; no limits or testing stated. A reviewer called it mostly what you'd get pasting line items into ChatGPT. — [Tradify SmartTools](https://tradifyhq.com/features/smarttools); [usecarly review](https://www.usecarly.com/blog/tradify-ai/) (third party, competitor-adjacent blog)
- **Joblogic:** AI Dynamic Scheduler and free "AI Summariser" add-on; vendor marketing only, no limits or testing stated. — [Joblogic AI Summariser](https://www.joblogic.com/marketplace/ai-summariser); [Joblogic AI job management](https://www.joblogic.com/ai-embedded-job-management-software)
- **Powered Now:** urgency detection described only in general terms. — [PN Receptionist](https://powerednow.com/receptionist/)
- **TradGo:** "Estimates and pricing always go through your approval." — [TradGo](https://tradgo-site.pages.dev/)

### Inferences
- "Human in the loop" is real good practice here and worth showing to builders as the standard to expect.
- No vendor publishes evals, error rates or red-team results. For a council contractor that must explain how a quote or invoice was produced, there is no vendor evidence to point to.

### Gaps
- No vendor-published accuracy or testing data found for any tool.
- No AI policy page found for any trades app (Tradify, Fergus, ServiceM8, Jobber, Powered Now, Commusoft, Joblogic, YourTradebase).

## 4. Legal/tax compliance claims (MTD, CIS, VAT reverse charge)

### Takeaway
On HMRC's own MTD for VAT software list (fetched 19 Nov 2026), QuickBooks, Xero and Powered Now are listed. None of the other trades apps are; they rely on syncing to accounting software. CIS and reverse charge in trades apps is handled through the accounting link (e.g. Tradify via Sage/Xero).

### Cited Findings
- HMRC MTD for VAT software finder lists: "QuickBooks (Intuit)" (record-keeping and bridging; submit, view returns, check VAT owed), "QuickBooks Bridging Software (Intuit)", "Xero" (record-keeping and bridging; submit, view, check owed, payment history), and "Powered Now" (record-keeping; submit returns, check VAT owed, payment history). Tradify, Fergus, ServiceM8, Jobber, YourTradebase, Joblogic and Commusoft do not appear. — [HMRC: Find software for MTD for VAT](https://www.tax.service.gov.uk/making-tax-digital-software) (downloaded and searched 19 Nov 2026)
- HMRC: "All software listed has been through HMRC's recognition process" and "HMRC does not recommend any product or software provider." MTD Income Tax guidance last updated 13 July 2026. — [GOV.UK MTD Income Tax software guidance](https://www.gov.uk/guidance/find-software-thats-compatible-with-making-tax-digital-for-income-tax)
- Tradify reverse VAT works only via Sage and only when CIS is enabled for that contact in Sage; reverse VAT then shows on its own invoice row. — [Tradify help: Reverse VAT & Sage](https://help.tradifyhq.com/hc/en-us/articles/900005245206)
- Tradify publishes a CIS guide blog. — [Tradify CIS guide](https://www.tradifyhq.com/blog/simple-construction-industry-scheme-cis)
- Fergus claims "full localised support including market-specific tax, compliance, and invoicing" for UK/Ireland, without detail on HMRC or CIS. — [Fergus llm-info](https://fergus.com/llm-info/)
- YourTradebase homepage makes no MTD, CIS or reverse charge claims; it published a reverse charge blog in 2021. — [YourTradebase](https://www.yourtradebase.com/); [YourTradebase reverse charge blog](https://yourtradebase.com/blog/the-vat-reverse-charge-kicks-in-on-1-march-2021)
- HMRC rule summary (secondary): reverse charge applies when both parties are UK VAT-registered, customer CIS-registered, supply standard/reduced-rated and within CIS construction operations; invoice must say reverse charge applies. — [Ross Martin](https://www.rossmartin.co.uk/vat/vat/4137-construction-industry-vat-reverse-charge-at-a-glance) (secondary)
- Intuit's Nov 2025 UK AI agents were reported to cover tasks including VAT. — [Intuit UK press release](https://quickbooks.intuit.com/uk/press/intuits-all-in-one-platform-introduces-a-virtual-team-of-ai-agents-to-help) (from search summary)

### Inferences
- Builders should check the HMRC finder themselves; a "works with MTD" claim on a trades app usually means "syncs to Xero/QuickBooks/Sage", which is the product HMRC recognised.
- No vendor I checked claims that its AI features are responsible for VAT/CIS correctness; outputs still need a human or an accountant (see section 5).

### Gaps
- HMRC MTD for Income Tax software list: I could not reach the product list URL (404 on guessed URLs), so Income Tax recognition is unchecked for all tools.
- CIS handling in Jobber, ServiceM8, Fergus, Commusoft, Joblogic, Powered Now: not checked in detail.

## 5. Disclaimers and liability in terms around AI outputs

### Takeaway
Where terms exist, they put all AI risk on the user. Jobber's terms are the most explicit: you are "solely responsible" for AI outputs and agent actions, and liability is capped at the greater of US$100 or fees paid. Xero's JAX beta terms disclaim accuracy and say not to rely on outputs for accounting advice.

### Cited Findings
- **Jobber (terms last updated 22 Sep 2026):** outputs "may not always be accurate or contextually relevant", no warranty they are "free from error or bias"; "you are solely responsible for reviewing, editing, approving, and ensuring the accuracy" of outputs; AI "cannot provide legal, medical, or professional advice"; "any Agentic Action is treated as your action"; service "AS IS"; liability capped at "THE GREATER OF (I) ONE HUNDRED US DOLLARS ($100) OR (II) THE AMOUNTS YOU'VE PAID JOBBER"; Canadian law. — [Jobber Terms of Service](https://getjobber.com/terms-of-service/)
- **Jobber Bookkeeping terms:** users must review AI outputs before relying on them, especially for tax or accounting; warranties on AI disclaimed. — [Jobber bookkeeping program terms](https://www.getjobber.com/bookkeeping-program-terms/) (from search summary)
- **Xero JAX beta terms:** "no representations or warranties with respect to the accuracy of any content, including any Outputs. You should not rely on Outputs for accounting, financial or professional advice." (Beta terms; may be superseded now JAX is generally available.) — [Xero JAX beta terms (MY)](https://www.xero.com/my/legal/terms/just-ask-xero-beta-terms-of-use/); [US version](https://www.xero.com/us/legal/terms/just-ask-xero-beta-terms-of-use)
- **Intuit:** "Intuit Intelligence can make mistakes"; product direction "is not a commitment"; features "vary by plan and region and may change without notice". — [Intuit UK press release](https://quickbooks.intuit.com/uk/press/intuit-intelligence-now-available-internationally/)
- **Powered Now:** missed-call value calculator is "A rough guide from your own numbers, not a promise". — [PN Receptionist](https://powerednow.com/receptionist/)

### Inferences
- The burden sits with the builder. For a council-facing contractor, an AI-written quote, invoice or customer message is legally theirs.
- Jobber's governing law (Canada) and USD liability cap are worth flagging to UK builders.

### Gaps
- AI clauses in the terms of Tradify, Fergus, ServiceM8, Powered Now, Commusoft, Joblogic, YourTradebase, TradGo and TradesCall: not read (no time / not found).
- Current (post-beta) JAX terms in the UK: not found.
- Trustpilot ratings: not checked this pass.

---

## Per-tool scorecard (summary of the evidence above; "NS" = not stated / not found)

| Tool | Security evidence | Data protection / AI provider / training | AI transparency & human review | MTD (HMRC VAT list) / CIS | AI liability terms |
|---|---|---|---|---|---|
| Xero (JAX) | ISO 27001:2022 cert, SOC 2 reports, PCI | Names AWS, Azure, GCP, OpenAI; JAX data not retained or used for training; no true off switch | Responsible data commitments: assess accuracy before release, monitor after | Listed (VAT) | Beta terms: no accuracy warranty, don't rely for advice |
| QuickBooks UK (Intuit Intelligence) | NS in this pass | No AI vendor named; training NS; no AI opt-out described | Responsible AI principles + governance; features in beta; "can make mistakes"; accountant approval | Listed (VAT, plus bridging) | "Can make mistakes", not a commitment |
| Jobber (AI, Receptionist) | NS (no trust page found) | AI chats may be logged for improvement; de-identified data used to improve service; AI provider NS; consent "recommended, not required" | No accuracy claim; post-hoc transcript review; escalation | Not listed | Strongest disclaimers: user solely responsible, cap US$100 or fees, Canadian law |
| ServiceM8 (Office Agent) | AWS, EU region; no certs | DPA; OpenAI and Anthropic listed as processors (account-holder data); training NS | User approves every action | Not listed | NS |
| Fergus (Assistant/AI) | NS on own page | DPA exists; AI provider NS | Confirmation before create/change/send; respects permissions | Not listed; "localised tax" claim, no detail | NS |
| Tradify (SmartTools) | No security page (404) | Privacy policy has no UK GDPR, no entity, no sub-processors, no AI | Marketing only | Not listed; reverse VAT via Sage + CIS | NS |
| Powered Now (PN Receptionist) | NS | Recording yes; AI disclosure, consent, location, provider NS | Urgency detection vague | Listed (VAT) | Calculator "not a promise" |
| Commusoft (AI:den) | GCP incl. UK; encryption; yearly external pen test; PCI network; ISO 27001 not on live page | GDPR processor contracts; AI NS | NS | Not listed | NS |
| Joblogic | Cyber Essentials Plus | NS | Marketing only | Not listed | NS |
| YourTradebase | NS | GDPR page linked; AI none | No AI features found | Not listed | NS |
| TradGo | NS; sole trader on pages.dev | NS | "Estimates always go through your approval" | n/a | NS |
| TradesCall AI | NS; pages.dev; no company found | NS | NS | n/a | NS |

## Patterns, good practice, and gaps for a council-facing contractor (notes for the writer)
- Good practice examples: Xero naming its LLM providers and a no-training statement ([Xero JAX](https://www.xero.com/uk/jax/)); Fergus and ServiceM8 confirm-before-action design ([Fergus](https://fergus.com/llm-info/), [ServiceM8](https://support.servicem8.com/help-center/servicem8-add-ons/office-agent/introducing-office-agent)); Intuit's plain "can make mistakes" and LLM/ML/deterministic split ([Intuit](https://quickbooks.intuit.com/uk/press/intuit-intelligence-now-available-internationally/)); Commusoft's specific security detail ([Commusoft](https://www.commusoft.com/security)); ServiceM8 publishing a named processor list ([ServiceM8](https://servicem8.com/gdpr)).
- Patterns: big accounting vendors publish more than trades apps; trades apps added AI in 2026 without updating privacy policies to mention it (Tradify example); receptionist vendors leave caller consent to the business; terms push all AI risk to the user; nobody publishes accuracy or test results.
- Gaps vs what a council-facing contractor typically needs (inference, to be checked against procurement research): Cyber Essentials evidence (only Joblogic); UK data residency statement (only Commusoft says UK hosting; ServiceM8 says EU region); named sub-processors incl. AI provider (only Xero, ServiceM8); retention periods for recordings/AI logs (none); AI-specific policy (only Xero, Intuit); audit trail of AI actions (ServiceM8 activity log 90 days is general, not AI-specific).
