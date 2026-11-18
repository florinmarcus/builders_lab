# Claude for a UK contractor pilot: terms, data handling and commercial use (checked 18 Nov 2026)

Not legal advice. "Inference" bullets are my reading, not what the source says. Pages were fetched on 18 Nov 2026; the date shown for each page is the date that page gives itself.

## 1. Consumer Terms vs Commercial Terms: which plans, business use, sharing, building products

### Takeaway
Free, Pro and Max fall under the Consumer Terms (individuals). Team, Enterprise and the API fall under the Commercial Terms. Consumer accounts cannot be shared or made available to others. Using a Pro account to serve a business client's personal data does not fit the consumer model.

### Cited Findings
- Consumer Terms (effective 8 Oct 2025) cover "Claude.ai, Claude Pro, and other products and services that we may offer for individuals". API keys and the Console are excluded and fall under the Commercial Terms. — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Anthropic's legal index: individual terms cover "Claude Free, Pro and Max plans, including usage of Claude Code and Claude Cowork through those plans". Commercial terms cover "commercial use of Claude API and Claude for Work (Teams and Enterprise plans)". This is a search-result snippet; the full page was not fetched. — [anthropic.com/legal](https://anthropic.com/legal)
- Consumer Terms: "You may not share your Account login information, Anthropic API key, or Account credentials with anyone else. You also may not make your Account available to anyone else." — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Consumer Terms forbid reselling the Services. They forbid access "through automated or non-human means, whether through a bot, script, or otherwise" unless you use an Anthropic API key or Anthropic explicitly allows it. They forbid developing "products or services that compete with our Services". — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Consumer Terms: "Use of our Services for evaluation purposes are for your personal, non-commercial use only. For clarity, this does not include Claude.ai or Claude Pro use for individuals or entities." The wording is ambiguous: it seems to say paid Claude.ai/Pro use is not limited to non-commercial use. — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Consumer Terms: if you sign up with an employer or organisation email, the account may be linked to that organisation and its admin "may be able to monitor and control the Account". — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- The Pro help article says it "is about paid Pro plans for individual consumers. If you're part of an organization looking to use Claude with your team, refer to Claude for Work (Team and Enterprise Plans)." Search-result snippet. — [What is the Pro plan](https://support.claude.com/en/articles/8325606-what-is-the-pro-plan)
- Commercial Terms (version dated 17 Jun 2025) cover "Anthropic API keys and any other Anthropic offerings that references these Terms". "Anthropic may not train models on Customer Content from Services." The DPA is incorporated by reference. — [Commercial Terms](https://www.anthropic.com/legal/commercial-terms)

### Inferences
- A sole trader using Pro for their own work emails seems allowed: the terms do not ban commercial use by a paying individual. But Pro gives no DPA and no processor terms (see section 3). So it cannot meet a council's processor and sub-processor requirements.
- A pilot where we (the developer) run one Pro/Max account for the contractor, or where the contractor's staff share one login, breaks the no-sharing rule. A product that scripts or automates claude.ai breaks the automated-access rule. A product built for a client should use the API (Anthropic or Bedrock).
- The contractor can safely build its own custom connector (MCP server) for its own Pro use. That is its own tooling, not resale. But the data problem stays (sections 2 and 3).

### Gaps
- I found no official Anthropic page that answers "may I use Pro for my business work" in plain words. Third-party pages say no DPA on Pro (e.g. [compound-website](https://compound-website.pages.dev/en-DE/tools/claude-pro-privacy/), [pro-manchester](https://www.pro-manchester.co.uk/?p=111760)). These are not official sources.
- I did not fetch the full current Usage Policy.

## 2. Training and retention

### Takeaway
Consumer plans: training is a user setting (since the Aug–Oct 2025 change). With training on, chats are kept 5 years; with it off, 30 days. Flagged chats and feedback can be trained on even if you opted out. Commercial (Team, Enterprise, API): no training by default, 30-day backend deletion, and zero data retention (ZDR) by agreement. Bedrock: AWS says no training and no sharing with Anthropic.

### Cited Findings
- Consumer change (announced 28 Aug 2025): users choose whether their data is used to improve Claude. The deadline to choose was 8 Oct 2025. If training is allowed, data is kept "five years instead of 30 days". If not, the 30-day retention still applies. It covers Free, Pro and Max (including Claude Code on those accounts). It excludes Claude for Work (Team, Enterprise), Gov, Education, and API use, "including through Amazon Bedrock and Google Cloud's Vertex AI". — [Updates to Consumer Terms](https://www.anthropic.com/news/updates-to-our-consumer-terms)
- The default position (on or off) is not stated in the announcement or the privacy article. — [Updates to Consumer Terms](https://www.anthropic.com/news/updates-to-our-consumer-terms), [Is my data used for model training (consumer, 16 Mar 2026)](https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training)
- Consumer Terms: "Even if you opt out, we will use Materials for model training when: (1) you provide Feedback to us ... (2) your Materials are flagged for safety review". — [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Consumer: Incognito chats are never used for training. Thumbs up/down feedback is kept for up to 5 years. — [Consumer training article (16 Mar 2026)](https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training)
- Commercial: "By default, we will not use your inputs or outputs from our commercial products" for training (Team, Enterprise, API). Exceptions: thumbs up/down feedback (whole conversation kept up to 5 years, IDs removed) or explicit opt-in. Team/Enterprise owners can turn off member feedback ("Rate chats" setting). — [Commercial training article (18 Aug 2026)](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training)
- Commercial retention: API inputs and outputs are deleted from the backend "within 30 days of receipt or generation". Team and Enterprise chats stay in the product until deleted, then are removed from the backend within 30 days. ZDR is an exception "when you and we have agreed otherwise". Chats flagged for Usage Policy violations are kept "up to 2 years", and trust and safety scores "up to 7 years". Feedback is kept 5 years. — [How long do you store my organization's data (1 Jul 2026)](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)
- The API data residency feature is "eligible for zero data retention", except for "Covered Models". — [Data residency docs](https://platform.claude.com/docs/en/manage-claude/data-residency)
- Bedrock: "your content is not used to improve the base models and is not shared with any model providers". AWS and third-party providers "will not use any inputs to or outputs from Amazon Bedrock to train ... third-party models". — [Bedrock FAQs](https://aws.amazon.com/bedrock/faqs/)
- Bedrock runs models in AWS-owned "Model Deployment Accounts" that model providers cannot access, "they don't have access to Amazon Bedrock logs or to customer prompts and completions". — [Bedrock data protection](https://docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html)

### Inferences
- On Pro/Max, the contractor must set training off, and must never use thumbs up/down on chats holding tenant data. Even then, flagged chats can be trained on and kept. That risk cannot be removed by settings.
- On Team, Enterprise and API, training is off by default. Turn off "Rate chats" so feedback does not pull tenant data into the 5-year store.
- Bedrock gives the cleanest story: AWS processes the data, and Anthropic never sees it.

### Gaps
- Which commercial products can get ZDR (Team? Enterprise only? API on approval?). The ZDR scope article was not fetched.
- Bedrock's own retention and abuse-detection details (pages `data-retention` and `abuse-detection` in the Bedrock guide) were not fetched. The FAQ says stored content is encrypted in the Region you use.
- The current consumer default for the training setting is not stated in the sources I read.

## 3. Data Processing Addendum (DPA), UK transfers, sub-processors

### Takeaway
Anthropic's DPA applies only to commercial products (API, Claude for Work). It is built into the Commercial Terms automatically. In it the customer is controller and Anthropic is processor. It uses the ICO's UK Addendum for UK transfers, and allows new sub-processors with a 15-day objection window. Consumer plans have no DPA. AWS's DPA, including a UK GDPR Addendum with the IDTA, applies automatically to Bedrock customers.

### Cited Findings
- DPA (effective 24 Feb 2025): part of "the Anthropic Commercial Terms of Service or other agreement between Customer and Anthropic that references this DPA". "Customer is the controller and Anthropic is Customer's processor." — [Anthropic DPA](https://www.anthropic.com/legal/data-processing-addendum)
- UK transfers: Schedule 3, Part B uses the "International Data Transfer Addendum" issued by the Information Commissioner (Approved Addendum B.1.0). — [Anthropic DPA](https://www.anthropic.com/legal/data-processing-addendum)
- Sub-processors: the customer gives "general authorization". Anthropic gives "reasonable notice" (no fixed days) before a new sub-processor gets access. The customer may object on reasonable privacy or security grounds within 15 days, or is deemed to consent. — [Anthropic DPA](https://www.anthropic.com/legal/data-processing-addendum)
- The DPA "is automatically incorporated into our Commercial Terms of Service". It covers commercial products, e.g. Claude for Work and the API. Users reaching Claude through a third-party platform are covered by that platform's terms. — [How do I view and sign your DPA (16 Mar 2026)](https://privacy.claude.com/en/articles/7996862-how-do-i-view-and-sign-your-data-processing-addendum-dpa)
- The sub-processor list is at anthropic.com/subprocessors, which redirects to trust.anthropic.com/subprocessors. The page needs JavaScript and I could not read it. — [Subprocessors](https://trust.anthropic.com/subprocessors)
- A third-party tracker lists AWS (worldwide cloud), Nutun (South Africa, user support for EU and UK users) and Yoti (UK identity verification, consumer plans) as Anthropic sub-processors. Not verified against the official list. — [conductatlas (AWS)](https://conductatlas.com/platform/anthropic/anthropic-sub-processors/provision/CA-P-066884/amazon-web-services-cloud-infrastructure-worldwide/), [conductatlas (Nutun)](https://conductatlas.com/platform/anthropic/anthropic-sub-processors/provision/CA-P-016516/international-subprocessor-nutun-south-africa-for-user-support/)
- AWS: the UK GDPR Addendum is part of the AWS Service Terms and "applies automatically for all customers who require a data processing agreement". It includes the EC SCCs plus the ICO's IDTA. AWS "acts as both a data processor and a data controller under the GDPR". Under the UK Addendum it takes on processor obligations. — [AWS GDPR Center](https://aws.amazon.com/compliance/gdpr-center/)
- Bedrock customers "can use Amazon Bedrock in compliance with the General Data Protection Regulation (GDPR)". — [Bedrock FAQs](https://aws.amazon.com/bedrock/faqs/)

### Inferences
- The chain for the council would be: council (controller) → contractor (processor) → us or the contractor's provider (sub-processor). With Bedrock, that provider is AWS (one well-known sub-processor; Anthropic is not in the data path). With the Anthropic API or Team/Enterprise, it is Anthropic plus Anthropic's own sub-processors (including AWS and others on its list).
- Pro/Max cannot be presented as a processor arrangement. There is no DPA, and Anthropic sets the purposes (e.g. training if opted in, safety review).
- The DPA's general authorisation and 15-day objection window must flow down. The contractor needs a matching right to tell the council about sub-processor changes. This needs checking against the council's contract terms.

### Gaps
- Official current Anthropic sub-processor list (needs a browser).
- Whether Team (not only Enterprise) gets the full DPA with no extra signature. The help article says "Claude for Work", which suggests yes.

## 4. Data location

### Takeaway
On the Anthropic API, inference can be "global" (any region) or "us" only. There is no EU or UK option, and stored data is US only. On Bedrock, the Region and inference profile set where processing happens. London (eu-west-2) supports in-Region inference for some Claude models, and the EU geographic profile from London stays within the EU Regions plus London.

### Cited Findings
- `inference_geo` values: "global" (default, "may run in any available geography") and "us". "Only 'us' and 'global' are available." Workspace geo (data at rest and endpoint processing): "Currently, 'us' is the only available workspace geo." — [Data residency docs](https://platform.claude.com/docs/en/manage-claude/data-residency)
- US-only inference costs 1.1x standard on Claude 4.6 and later. It is supported on 4.6 and later models; older models return a 400 error. — [Data residency docs](https://platform.claude.com/docs/en/manage-claude/data-residency)
- "On ... Amazon Bedrock, the inference region is determined by the endpoint URL or inference profile, so inference_geo is not applicable." — [Data residency docs](https://platform.claude.com/docs/en/manage-claude/data-residency)
- Bedrock stores customer content "encrypted and stored at rest in the AWS Region where you are using Amazon Bedrock". — [Bedrock FAQs](https://aws.amazon.com/bedrock/faqs/)
- EU cross-region inference: requests from the London Region "can only be routed between available EU Regions and London Region". When a destination Region is added, AWS publishes a new profile ID. From secondary sources quoting an AWS blog. — [AWS ML blog: cross-region inference for EU](https://aws.amazon.com/blogs/machine-learning/unlocking-ai-flexibility-in-europe-a-guide-to-cross-region-inference-for-eu-data-processing-and-model-access/), [mirror](https://aihub.hkuspace.hku.hk/2026/06/09/unlocking-ai-flexibility-in-europe-a-guide-to-cross-region-inference-for-eu-data-processing-and-model-access/)
- In-Region (London only) Claude: an AWS blog (Aug 2026, read via a mirror) reportedly says eu-west-2 offers in-Region inference for Claude Opus 4.6 and Sonnet 4.6, while Opus 4.7 and 4.8 are geo-only. A third-party page says Sonnet 5 has in-Region support in eu-west-2. The AWS URL returned 404 when fetched, so both claims are unverified. — [mirror of AWS blog](https://aihub.hkuspace.hku.hk/2026/08/07/enforcing-data-residency-with-single-region-claude-code-on-amazon-bedrock/), [AWS inference profile support table](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- A GitHub issue asks for EU data residency in Cowork and Claude.ai Enterprise (e.g. via Bedrock, Vertex or Foundry backends). That suggests claude.ai has no EU residency option. — [claude-code issue 40526](https://github.com/anthropics/claude-code/issues/40526)

### Inferences
- claude.ai (consumer or Team/Enterprise) and the Anthropic API mean US processing and storage, with transfers covered by the DPA's UK Addendum (commercial only). A council may accept that with a DPA, but UK or EU processing is easier to approve.
- Bedrock in eu-west-2 (in-Region where the model allows, else the EU geo profile) is the only option here that keeps processing in the UK/EU.

### Gaps
- An official statement on where claude.ai processes and stores data for Team/Enterprise. Inferred as US from the API workspace geo; not confirmed.
- The current official per-model London in-Region table (AWS page not read in full).

## 5. MCP connectors in claude.ai

### Takeaway
Data a connector returns into a chat becomes part of that conversation, so the plan's retention rules apply. Anthropic says training and feedback data exclude "raw content from connectors", including MCP servers, unless the content is copied into the conversation.

### Cited Findings
- Consumer: training data "does not include raw content from connectors" (e.g. Google Drive), including remote and local MCP servers, "unless the content is copied directly into your conversation". — [Consumer training article (16 Mar 2026)](https://privacy.claude.com/en/articles/10023580-is-my-data-used-for-model-training)
- Commercial: feedback data excludes raw connector content, including remote and local MCP servers, unless copied directly into the conversation. — [Commercial training article (18 Aug 2026)](https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training)

### Inferences
- "Raw content" seems to mean the source files in the connected system, not the text the tool returns into the chat. Tool results sit in the conversation transcript and are probably kept and handled like other chat content. On a consumer plan with training on, they could be trained on. This is my reading; Anthropic does not address tool results directly.
- On claude.ai, the connector call is made from Anthropic's cloud to the MCP server. So the council data passes through Anthropic either way.

### Gaps
- No explicit Anthropic statement on how tool results returned by a custom connector are retained or used for training.

## 6. Which option a council is most likely to approve; ICO view

### Takeaway
Bedrock in London/EU under the AWS DPA is likely the easiest to approve. Next is the Anthropic API or Team/Enterprise under the Anthropic DPA, with US processing. Consumer Pro/Max with a connector should not be used for tenant personal data. The ICO says roles follow what actually happens, not the contract. A provider that trains on customer data is unlikely to be a mere processor.

### Cited Findings
- ICO (fifth and final generative AI call for evidence; the page gives no date; the series ran in 2024): in AI-as-a-Service, when a customer sends its own data to a provider, the provider is "most likely a processor" if it acts on the customer's behalf. If the provider is a processor it cannot use the data for training: "Later training is a different purpose and outside the original instructions". "Whether an organisation is a controller, joint controller or processor is not necessarily determined by a contract." — [ICO generative AI fifth call for evidence](https://ico.org.uk/about-the-ico/what-we-do/our-work-on-artificial-intelligence/generative-ai-fifth-call-for-evidence)
- ICO also warns that developer and deployer may be joint controllers where they share objectives and influence. — [ICO fifth call](https://ico.org.uk/about-the-ico/what-we-do/our-work-on-artificial-intelligence/generative-ai-fifth-call-for-evidence)
- ICO Tech Futures report on agentic AI (early 2026) flags difficulty in setting controller and processor roles along agentic AI supply chains. It is not formal guidance. — [ICO tech futures: agentic AI](https://ico.org.uk/about-the-ico/research-reports-impact-and-evaluation/research-and-reports/technology-and-innovation/tech-horizons-and-ico-tech-futures/ico-tech-futures-agentic-ai), [Lewis Silkin summary, 22 Jan 2026](https://www.lewissilkin.com/insights/2026/01/22/ico-tech-futures-report-agentic-ai-102mdki)
- A law firm note (Aug 2026) says the ICO now has a statutory duty to produce an AI code of practice (after the Data (Use and Access) Act 2025). Not read in full. — [Arnold & Porter](https://www.arnoldporter.com/en/perspectives/advisories/2026/08/the-icos-new-statutory-duty-to-produce-an-ai-code-of-practice)

### Inferences
- Ranked for council approval (my judgement):
  1. **Bedrock, eu-west-2 (London), in-Region or EU profile.** AWS DPA with UK Addendum/IDTA applies automatically. No training, and Anthropic never sees the data. AWS is a sub-processor councils already know, with UK/EU processing. A custom app (our website plus agent) calls Bedrock.
  2. **Anthropic API or Claude Team/Enterprise.** The DPA applies automatically, Anthropic is processor, no training by default, 30-day deletion (ZDR possible by agreement on the API). But processing is US (or "global"), and the council must approve Anthropic and its sub-processor list. Team gives the chat UI and connectors with a DPA.
  3. **Pro/Max with a custom connector.** No DPA. Training depends on a user setting, flagged chats can be trained on and kept for years, and accounts cannot be shared. It fails the processor test the ICO describes. Use it only for demos with mock or public data.
- Whatever option is chosen, the council will likely also want: a DPIA, a data flow diagram, a sub-processor list with locations, retention settings, and a way to delete data.

### Gaps
- No final ICO guidance specific to generative AI processors was found as of Nov 2026. A claim that a consultation closes on 20 Nov 2026 (from a Freshfields search snippet) could not be checked.
- Typical council (UK local authority) policies on AI sub-processors were not researched.
