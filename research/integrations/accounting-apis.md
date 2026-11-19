# Accounting APIs: QuickBooks Online (UK) and Xero (UK)

How a small third-party app can connect to QuickBooks Online and Xero for a pilot. All facts checked on **19 Nov 2026** unless a line says otherwise. Each fact has a source number [n]; the list is at the end. "Unverified" means I could not confirm it from a primary source.

## Short answer

- Both have a free developer tier that is enough for a pilot with 1 or 2 customers.
- Both have a free test company with sample data. Xero's Demo Company can be switched to UK. QuickBooks lets you create a UK sandbox.
- **Xero is easier for a 1-day prototype.** A Custom Connection to the Demo Company is free, needs no redirect URL, and works with the official Xero MCP server in minutes.
- **Xero now has an official hosted MCP server** (`https://api.xero.com/mcp/v1`). It needs the paid Core plan, but Starter apps can try it with a demo organisation.
- Intuit has an official **local** MCP server on GitHub. A hosted Intuit MCP is reported but not documented for developers (unverified).
- **CIS:** Xero exposes CIS settings and CIS amounts as read-only. QuickBooks has CIS fields in its schema (UK only), but whether you can write them is unclear.
- Neither API files VAT or CIS returns to HMRC. That is done inside the products, or through HMRC's own APIs.
- **Watch out:** Xero's terms ban using API data to train or fine-tune AI models, and ban passing data to a third party without the user's consent. Sending data to an LLM provider needs to be covered by user consent and our privacy policy.

## Comparison table

| Topic | QuickBooks Online (UK) | Xero (UK) |
|---|---|---|
| Auth | OAuth 2.0 authorisation code. One broad scope `com.intuit.quickbooks.accounting` (no read-only variant) [3] | OAuth 2.0: code flow, PKCE, or Custom Connection (client credentials, one org) [10][12]. Granular scopes since Mar 2026 [11][13] |
| Test company | Sandbox, up to 10, UK region available, valid 2 years, sample data (UK = "Party Planning Services", 164 transactions) [4] | Demo Company: free, sample data, can switch country to UK, auto-resets every 28 days [14] |
| Contacts | Customer, Vendor: read and write [8] | Contacts: read and write [9] |
| Invoices / bills | Invoice, Bill: read and write [8] | Invoices (sales = ACCREC, bills = ACCPAY): read and write [9] |
| Payments | Payment, BillPayment: read and write [8] | Payments, BatchPayments: read and write [9] |
| Attachments | Attachable entity: read and write [8][7] | Attachments on invoices, contacts, bank transactions and more: GET, PUT, POST [15] |
| VAT domestic reverse charge | Tax codes are read-only. A "20.0% RC CIS" code appears when VAT and CIS are on (forum report, unverified) [20] | UK tax types `DRCHARGESUPPLY20`, `DRCHARGE20`, `DRCHARGESUPPLY5`, `DRCHARGE5` [9] |
| CIS | Schema has `LessCIS` on Invoice, Bill, Purchase, SalesReceipt; `CISRate`, verification status on Vendor; `IsCISContractor` on Customer. UK only [19]. Write support unclear (forum says not supported, unverified) [20] | Read-only: `GET /Contacts/{id}/CISSettings`, `GET /Organisation/{id}/CISSettings`; `CISDeduction` read-only on credit notes; CIS account types [9] |
| Rate limits | 500 requests/min per company, 10/sec per company and app, 40 batch/min [5] | 5 concurrent, 60/min, 1,000/day (Starter) or 5,000/day (Core+), per org; 10,000/min per app [12] |
| Free tier | Builder: no fee, unlimited "Core" (data-in) calls, 500,000 "CorePlus" (data-out) calls/month, then blocked [1] | Starter: no fee, 5 connections, 1,000 calls/day per org [16][17] |
| First paid tier | Silver: US$300/month, 1M CorePlus calls, then US$3.50 per 1,000 [1] | Core: AUD 35/month, 50 connections, 10 GB egress, AUD 2.40/GB over [16] |
| Before a real customer | Self-attested assessment questionnaire, then production keys. Marketplace listing adds security, technical and marketing reviews [1][6] | Starter and Core: no certification. Plus and above: certification [16][17]. Custom Connection: customer buys a subscription [10] |
| Official MCP | Local only: `intuit/quickbooks-online-mcp-server`, 145 tools, v0.0.1 [7] | Local: `XeroAPI/xero-mcp-server`, MIT, v0.0.18 [18]. Hosted: `api.xero.com/mcp/v1`, GA tools listed [21] |

## 1. Official APIs

### QuickBooks Online

- **Data.** The REST Accounting API covers Customer, Vendor, Invoice, Bill, Payment, Purchase, JournalEntry, Item, Account, TaxCode, TaxRate, Attachable and reports [8][7]. Tax codes and rates are read-only in the official MCP server [7].
- **Auth.** OAuth 2.0. The accounting scope is `com.intuit.quickbooks.accounting`. There are no read-only or granular variants for accounting [3]. Refresh tokens last about 100 days (MCP README) [7].
- **Sandbox.** Up to 10 sandbox companies. You start with one US sandbox. QuickBooks Online Plus sandboxes can be created for AU, CA, FR, IN, UK and US. The region can't be changed later. Valid 2 years. Sample data cannot be reset, only deleted [4]. For "non-commercial use and testing" [4b].
- **Sandbox redirect.** Sandbox allows `http://localhost` redirect URIs. Production needs a public HTTPS callback [7].
- **Rate limits.** 500 requests per minute per company (realm), 10 per second per realm and app. Batch: 30 payloads per request, 40 batch requests per minute. Throttled calls return HTTP 429 [5]. Sandbox: 40 emails per day [4].

### Xero

- **Data.** Contacts, Invoices (sales and bills), Payments, Credit Notes, Bank Transactions, Manual Journals, Items, Tax Rates, Attachments and more. Source: Xero's official OpenAPI spec, version 20.1.0 [9].
- **Auth.** OAuth 2.0. Three options:
  - Code flow or PKCE for many organisations [11].
  - **Custom Connection** (client credentials) for one organisation. Available in AU, NZ, UK, US. Needs a paid subscription by the customer, **but is free with the Demo Company** for development, and does not count towards the five uncertified app limit [10].
- **Scopes.** Since March 2026, new apps get granular scopes [11][13]. `accounting.transactions` is replaced by `accounting.invoices`, `accounting.payments`, `accounting.banktransactions`, `accounting.manualjournals` (each with a `.read` version). `accounting.reports.read` is split into per-report scopes. `accounting.contacts`, `accounting.settings`, `accounting.attachments` are unchanged. Broad scopes stay until September 2027 [11]. New custom connections (from 29 Apr 2026) lose `accounting.journals.read` [10].
- **Test company.** Demo Company: free, pre-filled, can switch to UK, resets 28 days after creation. You must reconnect after a reset [14].
- **Rate limits.** Per organisation: 5 calls at once, 60 per minute, 1,000 per day (Starter) or 5,000 per day (Core and above). Per app: 10,000 per minute. HTTP 429 with a `Retry-After` header [12].

## 2. Developer pricing

### Intuit App Partner Program (launched May 2025)

From the official Program Guide, version 1.2, March 2026 [1]:

| | Builder | Silver | Gold | Platinum |
|---|---|---|---|---|
| Monthly fee | none | US$300 | US$1,700 | US$4,500 |
| Core calls (data in: create/update) | unlimited | unlimited | unlimited | unlimited |
| CorePlus calls included (data out: reads, queries, reports) | 500,000, then **blocked** | 1M | 10M | 75M |
| Overage per 1,000 CorePlus calls | n/a | US$3.50 (1M–10M) | US$1.40 (10M–75M) | US$0.25 (75M+) |
| Payment method | no | yes | yes | yes |
| Minimum active connections | none | none | 500 | 3,000 |

- Only successful (2xx) calls are metered. Calls are counted across all production apps in a workspace [1].
- Prices are shown in USD; there is a country rate card. **UK prices: unverified** [1].
- The limits page says calls above 500,000 return HTTP 429 [5]. The guide says "blocked" [1].
- **Is sandbox traffic metered?** Not stated. Unverified.
- **Before a real customer:** every tier needs an approved "self-attested assessment questionnaire" and acceptance of the terms. Then the app moves to production. A marketplace listing needs three more reviews (security, technical, marketing) [1][6].

### Xero developer pricing (new tiers from 2 March 2026)

From developer.xero.com/pricing [16] and the pricing FAQ [17]. Prices are shown in **AUD**, tax excluded. I found no official GBP price (unverified).

| | Starter | Core | Plus | Advanced | Enterprise |
|---|---|---|---|---|---|
| Monthly fee (AUD) | none | 35 | 245 | 1,445 | on application |
| Connections | 5 | 50 | 1,000 | 10,000 | no limit |
| Egress included | none listed | 10 GB | 50 GB | 250 GB | on application |
| Overage | n/a | AUD 2.40/GB | AUD 2.40/GB | AUD 2.40/GB | on application |
| Daily calls per org | 1,000 | 5,000 | 5,000 | 5,000 | 5,000 |
| Certification | no | no | yes | yes + security assessment | yes + security assessment + App Store |

- New apps start on Starter. Adding payment details moves you to Core [17].
- Ingress (writing data) is unlimited on all tiers [16].
- Custom Connections "remain on the same commercial terms", outside these tiers [17]. The customer pays for them [10]. UK price: unverified.
- Each organisation can connect at most five uncertified apps [12].
- **For a pilot with 1–2 organisations:** Starter is enough, with no fee and no certification. The limits are 1,000 calls per day per org and 5 connections.

## 3. Official MCP servers

### Xero

- **Local server:** `github.com/XeroAPI/xero-mcp-server`. npm `@xeroapi/xero-mcp-server` v0.0.18. MIT licence, copyright Xero Limited [18]. Not labelled beta. Repo shows about 395 stars and 102 commits; last commit date not visible (checked via the GitHub page; the GitHub API was blocked in this session).
  - **Auth:** (1) Custom Connection with client ID and secret, recommended for testing and for Claude Desktop; or (2) a bearer token from a PKCE flow, for many organisations [18].
  - **Tools (51):** contacts (list, create, update, contact groups), invoices (list, create, update), credit notes, quotes, items, payments (list, create), bank transactions, manual journals, accounts, tax rates, tracking categories, organisation details, reports (P&L, balance sheet, trial balance, aged receivables and payables), UK and NZ payroll timesheets and leave. **No attachment tools. No CIS tools.** Bills are invoices of type ACCPAY [18][9].
- **Hosted server (new):** `https://api.xero.com/mcp/v1`, run by Xero [21].
  - Uses the normal Xero OAuth 2.0 flow; PKCE is recommended.
  - Included at no extra charge for Commercial apps on **Core or above**. Starter apps can try it **with a demo organisation**.
  - Data returned counts towards egress. Normal rate limits apply.
  - Tools listed "at GA": invoices, credit notes, items, quotes (including `authorise_invoice`, `void_invoice`), contacts, bank transactions, payments, manual journals, P&L, balance sheet, trial balance, aged reports, accounts, tax rates, organisation details, `get_connected_tenants`. Each tool needs a matching granular scope. No attachments or CIS tools listed [21].

### Intuit

- **Local server:** `github.com/intuit/quickbooks-online-mcp-server`. npm `@qboapi/qbo-mcp-server` v0.0.1 [7].
  - **Licence: unclear.** The README badge and package.json say MIT. The LICENSE file is Apache 2.0 [7].
  - **Status:** the README does not say beta. Intuit's developer blog called it an "early preview" in October 2025 (seen as a search result only; the blog now redirects to Medium, unverified).
  - **Auth:** you register an app on the Intuit Developer Portal, run a one-time browser OAuth handshake (`npm run auth`), and put client ID, secret, refresh token, realm ID and environment (sandbox or production) in `.env`. It rotates refresh tokens and writes them back. Runs locally over stdio [7].
  - **Tools (145):** create, get, update, delete, search on 29 entities, including Customer, Vendor, Invoice, Bill, BillPayment, Payment, Purchase, JournalEntry, Item, Account, Attachable (attachments). Tax code, tax rate and tax agency are read-only. 11 reports. Write, update and delete tools can be switched off with env flags [7].
- **Hosted server:** third-party sites report an Intuit-run endpoint used by the QuickBooks connector in Claude (US only). Intuit support answers say there is no public roadmap for a hosted MCP for developers. **Unverified**; not in Intuit's developer docs I could read [22].

## 4. UK specifics

### CIS (Construction Industry Scheme)

- **Xero:** CIS data is **read-only** in the API.
  - `GET /Contacts/{ContactID}/CISSettings`: whether a contact is a CIS subcontractor, and its deduction rate [9].
  - `GET /Organisation/{OrganisationID}/CISSettings`: whether the organisation is a CIS contractor or subcontractor, and its rate [9].
  - Both need `accounting.settings` or `accounting.settings.read` [9].
  - Credit notes carry read-only `CISDeduction` and `CISRate` [9].
  - CIS account types exist: `CISLABOUR`, `CISMATERIALS`, `CISLIABILITY` and others [9].
  - I found no endpoint to file a CIS return.
- **QuickBooks Online:** CIS is a built-in UK feature in the product (Settings > Advanced > CIS) [23].
  - The official Java SDK schema has UK-only CIS fields: `LessCIS` on Invoice, SalesReceipt, Purchase and Bill; `CISRate` (gross 0%, standard 20%, higher 30%), HMRC verification status and company registration number on Vendor; `IsCISContractor` on Customer [19].
  - Whether these can be written through the API is **unverified**. Intuit developer forum threads say CIS "is not currently supported in the API" [20] (forum pages would not load; seen as search snippets only).
  - Not exposed by the official MCP server [7].

### VAT domestic reverse charge (construction)

- **Xero:** UK tax types `DRCHARGESUPPLY20`, `DRCHARGE20`, `DRCHARGESUPPLY5`, `DRCHARGE5` are in the API enum. `REVERSECHARGES` is a separate EU type [9].
- **QuickBooks:** tax codes are read through the API, not created. Forum reports say a "20.0% RC CIS" code appears when both VAT and CIS are on, and can then be used on transactions. Unverified [20].
- The QuickBooks schema has a `REVERSE_CHARGE` tax type and `ReverseChargeRate` on Item [19].

### Making Tax Digital (MTD)

- I found **no endpoint in either accounting API to submit VAT returns or CIS returns to HMRC.** The products do this themselves.
- HMRC has its own APIs (for example the CIS Deductions API for MTD Income Tax), with its own sandbox and its own software registration. Separate from these integrations. Snippet only [24].

## 5. Data protection and security

### Xero

- **Developer terms** (last updated 4 Dec 2025; apply to older developers from 2 Mar 2026) [25]:
  - You may use API data only to develop, test and support your app's approved use case.
  - **"API Data cannot be used to train, fine tune, adapt, or enhance any AI Models."**
  - **"API Data shall not be passed to another third party without consent from the associated user."** This matters if we send Xero data to a hosted LLM.
  - Must not sell user data, or aggregate and supply it to another app or third party.
  - Your app needs its own terms and privacy policy, and users must agree to them.
  - Report security incidents to Xero within 24 hours.
  - Your app's use case must be approved by Xero, including material changes.
- **Security standard for API consumers** [26]:
  - OAuth 2.0. Encrypt refresh tokens (AES-128 or better preferred), key in a separate config file.
  - TLS 1.2 with AES-256 and SHA-256.
  - Strong user login (two-step or single sign-on; "Sign in with Xero" recommended).
  - Server hardening, OWASP Top 10, Secure and HTTPOnly cookies.
  - Encryption at rest for sensitive data.
  - Annual self-assessment is required for apps with more than 1,000 connections.
- **Caching:** Xero recommends caching data locally with `If-Modified-Since`. It is not required for certification [27].

### Intuit

- **Developer terms** (static copy dated 14 Oct 2025) [28]:
  - Store, process and use user data only to provide your app's functions.
  - Get user consent and give clear disclosures.
  - Follow Intuit's Data Stewardship Principles and **Responsible AI Principles**.
  - Stop processing when a user revokes consent or stops using the app. Securely delete data when the user asks.
  - Third parties you share data with must sign terms at least as strict.
  - GDPR rules for EU/UK personal data transfers.
  - Intuit's developer homepage reportedly says the terms were updated effective 12 Nov 2026. I could not read that version. **Unverified.** I did not find an explicit AI-training ban in the October 2025 text.
- **Security requirements** (checked during marketplace security review; listed apps and apps with over 500 connections are reviewed yearly) [29]:
  - Encrypt refresh token and realm ID (AES preferred), key in a separate config file.
  - "Your app cannot export, save, or store QuickBooks data for any purpose other than the functional use of your app."
  - No third-party access to customer QuickBooks data.
  - Never log credentials or QuickBooks data.
  - TLS 1.1+ (1.2 recommended), HTTPS everywhere, no-cache on sensitive pages, Secure and HTTPOnly cookies.
  - Allow Intuit vulnerability scans, or give scan results from the last year; fix critical, high and medium issues.
- **Sandbox use:** "non-commercial use and testing" only [4b].

## 6. Recommendation for a 1-day prototype

**Use Xero first, with the UK Demo Company and a Custom Connection.**

Why:

1. **No OAuth redirect work.** A Custom Connection uses client credentials. You get a token with one POST. It is free with the Demo Company [10].
2. **Realistic UK data.** The Demo Company can be switched to UK and comes pre-filled. Reset it whenever you want [14].
3. **MCP in minutes.** The official local Xero MCP server takes the client ID and secret as env vars [18]. A Claude client can then list contacts, invoices, bills and payments.
4. **Costs nothing.** Starter tier, no certification [16][17].
5. **Hosted MCP later.** For a multi-customer pilot, the hosted server at `api.xero.com/mcp/v1` with PKCE avoids running our own MCP server. It needs Core (about AUD 35/month) [21].

Limits to plan for:

- Demo Company resets after 28 days; reconnect then [14].
- 1,000 calls per day per org on Starter [12].
- CIS data is read-only. No attachments in the MCP servers; use the REST Attachments endpoint directly [15].
- Our own mock data must stay in the Demo Company or in `system/data/mock/`; no real customer data (AGENTS.md rule 2).
- Before a real customer: user consent for sending data to an LLM, our own terms and privacy policy, and no AI training on their data [25].

**QuickBooks second.** It works, but needs more set-up: create an app, create a UK sandbox (the default one is US), and do a browser OAuth handshake with a localhost redirect [4][7]. Its UK sample company is a party planning business, not construction [4]. Its MCP server must be cloned and built locally [7]. The free Builder tier is generous for a pilot [1].

## Open questions

- Official GBP prices for Xero tiers and Custom Connections.
- Whether QuickBooks UK API can write CIS fields (`LessCIS`, `CISRate`). Test in a UK sandbox.
- Whether Intuit meters sandbox calls against the 500,000 CorePlus cap.
- Text of Intuit's developer terms updated 12 Nov 2026, especially on AI.
- Whether the Intuit-hosted MCP (Claude connector) works for UK companies or third-party apps.

## Sources

All checked 19 Nov 2026.

1. Intuit App Partner Program Guide, v1.2_03.2026 (PDF): https://static.developer.intuit.com/resources/Intuit_App_Partner_Program_Guide.pdf
2. Intuit App Partner Program FAQ (page loads by JavaScript; not readable in this session): https://developer.intuit.com/app/developer/qbo/docs/get-started/partner-faq
3. Intuit OAuth scopes: https://static.developer.intuit.com/output_html/qbo/docs/learn/scopes.html
4. Intuit Sandbox FAQ (regions, limits, sample data): https://static.developer.intuit.com/output_html/qbo/docs/develop/sandboxes/sandbox-faqs.html
   4b. Intuit Manage your sandboxes: https://static.developer.intuit.com/output_html/qbo/docs/develop/sandboxes/manage-your-sandboxes.html
5. Intuit API call limits and throttles: https://static.developer.intuit.com/output_html/qbo/docs/learn/limits-and-throttles.html
6. Intuit Go live: https://static.developer.intuit.com/output_html/qbo/docs/go-live.html
7. Intuit QuickBooks Online MCP server (README, package.json, LICENSE): https://github.com/intuit/quickbooks-online-mcp-server
8. QuickBooks entity list as exposed by the official MCP server README [7]; full API reference at https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/account (JavaScript page, not read)
9. Xero Accounting OpenAPI spec v20.1.0: https://raw.githubusercontent.com/XeroAPI/Xero-OpenAPI/master/xero_accounting.yaml
10. Xero Custom Connections: https://developer.xero.com/documentation/guides/oauth2/custom-connections/
11. Xero OAuth 2.0 scopes: https://developer.xero.com/documentation/guides/oauth2/scopes/
12. Xero OAuth 2.0 API limits: https://developer.xero.com/documentation/guides/oauth2/limits/
13. Xero Granular Scopes FAQ: https://developer.xero.com/faq/granular-scopes
14. Xero Development accounts (Demo Company): https://developer.xero.com/documentation/development-accounts/
15. Xero Attachments API: https://developer.xero.com/documentation/api/accounting/attachments
16. Xero Developer Pricing: https://developer.xero.com/pricing
17. Xero Pricing and Policy Updates FAQ: https://developer.xero.com/faq/pricing-and-policy-updates
18. Xero MCP server (README, package.json, LICENSE): https://github.com/XeroAPI/xero-mcp-server
19. Intuit QuickBooks V3 Java SDK schema (Finance.xsd, IntuitNamesTypes.xsd, branch develop): https://github.com/intuit/QuickBooks-V3-Java-SDK/tree/develop/ipp-v3-java-data/src/main/xsd
20. Intuit developer forum threads on CIS and reverse charge (search snippets only; pages did not load): https://help.developer.intuit.com/s/question/0D54R00008KD6BwSAL/cis-tax-support-for-api and https://help.developer.intuit.com/s/question/0D54R00007mMa8eSAC/quickbooks-online-domestic-reverse-charge-vat
21. Xero Developer Remote MCP Server: https://developer.xero.com/documentation/guides/remote-mcp/overview
22. Intuit forum, hosted MCP roadmap question (search snippet only): https://help.developer.intuit.com/s/question/0D5TR00001LtKZk0AN/is-there-a-plan-or-timeline-for-when-intuit-will-provide-a-hosted-quickbooks-mcp-server-we-are-exploring-the-possibility-of-a-multitenant-integration-with-quickbooks-and-selfhosted-is-not-a-viable-option-for-us
23. QuickBooks UK help, CIS in QuickBooks (search snippet only): https://quickbooks.intuit.com/learn-support/en-uk/help-articles/cis-in-quickbooks/00/239830
24. HMRC CIS Deductions API (search snippet only): https://www.tax.service.gov.uk/api-documentation/docs/api/service/cis-deductions-api/2.0
25. Xero Developer Platform Terms and Conditions: https://developer.xero.com/xero-developer-platform-terms-conditions
26. Xero Security standard for API consumers: https://developer.xero.com/partner/security-standard-for-xero-api-consumers
27. Xero best practice, caching data: https://developer.xero.com/documentation/best-practices/api-call-efficiencies/caching-data
28. Intuit Developer Terms of Service (static copy "As of October 14, 2025"): https://static.developer.intuit.com/output_html/qbo/docs/legal-agreements/intuit-terms-of-service-for-intuit-developer-services.html
29. Intuit security requirements: https://static.developer.intuit.com/output_html/qbo/docs/go-live/publish-app/security-requirements.html

Note on method: Xero and Intuit doc sites load by JavaScript. Xero pages were read from their page-data JSON, Intuit pages from `static.developer.intuit.com`. GitHub repos were read as raw files; the GitHub API was blocked in this session, so last-commit dates are not shown.
