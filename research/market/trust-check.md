# Trust check of existing AI tools

Checked 19 Nov 2026, from vendor pages only. We did not test the tools. We did not check any certificate on a register, so a certificate here means "claimed". "Not stated" means we looked and did not find it. It does not mean the vendor does not do it. Full report with sources: `research/reports/Builder AI tools trust check.md`. Notes: `research/research_notes/Builder AI tools trust check/`.

## 1. Scorecard

Marks: **Yes**, **No**, **Partly**, **not stated**, **could not read**, **not checked**.

| Tool | Security evidence | Names AI provider | Trains on your data | Publishes accuracy | Compliance claim backed | DPA |
|---|---|---|---|---|---|---|
| **Small AI-first tools** | | | | | | |
| StructureGPT (Building Regs Q&A) | Partly: encryption, Azure UK, no certificate | Yes (OpenAI via Azure) | not stated (keeps queries 2 years "for service improvement") | No | Partly: cites clause, clear disclaimer | not stated |
| BuildingRegs.app | not stated | not stated | not stated | No | No: "trusted answers", terms say you must check | not stated |
| Struck (Dutch) | ISO 27001 claimed, no number | could not read | could not read | No ("0% hallucination", no test shown) | No | could not read |
| BuildwellAI (waitlist) | Partly: says pen testing, no certificate | not stated | not stated | No | No: "Assured Compliance", terms give no warranty | not stated |
| RAMSReady | Partly: detailed DPA, no certificate | Yes (Anthropic, Google) | No | No | Partly: honest FAQ, no guarantee | Yes |
| Ramsgen | Cyber Essentials Plus claimed, UK hosting | Yes (OpenAI, Google) | No | No (cites every source) | Partly: states the law correctly | Yes |
| RAMS AI | Partly: ICO registered, no certificate | Yes (OpenAI or Anthropic) | No | No | Partly: human-reviewed library, reviewer not named | not stated |
| DocGen | Partly: says pen testing, no certificate | not stated | No by default (opt-in) | No (terms ban publishing benchmarks) | No: "HSE-aligned", no backing | not stated |
| RAMS PRO | not stated | not stated | could not read | No | No: "full compliance", terms page 404 | not stated |
| QuickPrice (quotes) | Partly: encryption, no certificate | No (categories only) | not stated | No | n/a | not stated |
| TradeQuoteAI (quotes) | Self-awarded badges only | not stated | not stated | No | No: self-declared "GDPR Compliant" badge | not stated |
| QuoteSmith (quotes) | Partly: UK hosting, no certificate | Yes (Anthropic) | No | No | n/a | not stated |
| Sleepless Tradesman (quotes) | Partly: US hosting, encrypted HMRC tokens | Yes (Anthropic) | No | No | No: "not allowed to" make things up, no evidence | not stated |
| **Trades and accounting apps** | | | | | | |
| Xero (JAX) | Yes: ISO 27001, SOC 2 | Yes (OpenAI, AWS, Azure, Google Cloud) | No (JAX chat) | No | Yes: on HMRC MTD VAT list | not checked |
| QuickBooks UK (Intuit) | not checked | No | not stated | No (says "can make mistakes") | Yes: on HMRC MTD VAT list | not checked |
| Jobber (AI, Receptionist) | not stated | not stated | Partly: AI chats may be logged for improvement | No | Not on HMRC list; Canadian law | not checked |
| ServiceM8 (Office Agent) | Partly: AWS EU region, no certificate | Yes (OpenAI, Anthropic listed) | not stated | No | Not on HMRC list | Yes |
| Fergus | not stated | not stated | not stated | No | Not on HMRC list | Yes (not read) |
| Tradify (SmartTools) | No security page (404) | No | not stated | No | Not on HMRC list | not stated |
| Commusoft | Partly: yearly pen test, UK hosting | not stated | not stated | No | Not on HMRC list | Yes (processor contracts) |
| Joblogic | Cyber Essentials Plus claimed | not stated | not stated | No | Not on HMRC list | not checked |
| Powered Now (Receptionist) | not stated | not stated | not stated | No | Yes: on HMRC MTD VAT list | not checked |
| **Construction platforms** | | | | | | |
| Procore | Yes: ISO 27001, SOC 2, UK data zone | not stated publicly | No for outside models; own models not stated | Gated (on request) | Partly | not checked |
| Autodesk Construction Cloud | ISO 42001 claimed; others not checked | Yes, per feature (Transparency Cards) | Per feature | Partly: cards list limits | Partly | not checked |
| Buildertrend | Host's certificates only | not stated | No ("not on individual customer data") | No | n/a | not stated |
| Houzz Pro | Host's (AWS) certificates only | not stated | No for "public AI tools"; own not stated | No | n/a | not stated |
| **General AI assistants** | | | | | | |
| Free or personal plans (ChatGPT Free/Plus, Claude Free/Pro) | n/a | n/a | Yes, by default or if you agree | not checked | n/a | No |
| Business plans (ChatGPT Business, Claude Team, Copilot work, Gemini Workspace) | Yes: ISO 42001 for Anthropic, Google (others claimed) | n/a | No, by default | not checked | n/a | Yes |

Nobody, large or small, publishes how often its AI is wrong.

## 2. Five key messages for the talk

1. **Free AI is public AI.** Free ChatGPT and Claude can learn from your chats and give you no data agreement. For client or council data, use a business plan.
2. **No tool shows how often it is wrong.** Not one. Treat "0% hallucination" or "fully compliant" as a warning sign. Good tools show the clause so you can check it.
3. **The terms always hand the risk back to you.** Most cap what they owe you at about one year of fees. If AI writes your RAMS, quote or invoice, it is still yours. A competent person still signs.
4. **Big is not always better, small is not always worse.** Some small UK tools (Ramsgen, RAMSReady) are clearer about your data than some well-known apps. Read the privacy page, not the homepage.
5. **Ask four questions before you sign up.** Who is the company? Which AI company sees my data, and where is it kept? Do you train on it? Can I have your data agreement (DPA)?

## 3. Builder checklist

Before you put client or council data into any AI tool:

1. Use a business plan, not a free or personal account.
2. Get the data agreement (DPA) and a written "we do not train any model on your data".
3. Ask which AI company sees the data, and where it is stored (UK, EU or US).
4. Look the company up on Companies House. No company name is a warning.
5. Ask for a certificate number (Cyber Essentials, ISO 27001) and check it on the register.
6. Take out names, addresses, phone numbers, bank and health details, passwords and confidential tender papers first.
7. Check every answer against the real source. Prefer tools that show the clause.
8. Keep a competent person signing RAMS, quotes and compliance papers.
9. For AI phone answering: tell callers it is AI and that calls are recorded. Keep a human approving. Know how to switch it off.
10. Write a one-page AI rule for your team: which tools are allowed, and what never goes in.

On Microsoft 365: ask your IT person to check the Anthropic (Claude) setting in Copilot before 9 December (secondary sources, see below).

## 4. Not verified

- No certificate was checked on a register (Ramsgen Cyber Essentials Plus, Struck ISO 27001, Joblogic Cyber Essentials Plus, Xero, Procore).
- Could not read: Struck legal pages, StructureGPT terms, Sleepless Tradesman terms, RAMS PRO privacy page, Regulex site.
- Procore's "AI Legal Terms" and "AI Accuracy and Transparency" documents are behind an access request.
- Not checked: QuickBooks security certificates; Autodesk Construction Cloud certificates and UK data location; DPAs of Xero, Jobber, Procore, Autodesk.
- OpenAI and Microsoft 365 Copilot ISO 42001 come from secondary sources only.
- ChatGPT plan details come from secondary sources (openai.com blocked our fetch).
- Copilot turning on Claude by default for UK tenants on 9 Dec: secondary sources disagree.
- Commusoft ISO 27001: shown on third-party sites, not on Commusoft's own page.
- HMRC MTD for Income Tax list: could not reach it.
- Survey figures (FMB/CIOB, RICS 2026) come from press reports, not the original documents.
- ArchiChat and RiskGen: no product found. ToolBoxHQ is a safety records tool, not a quoting app.
