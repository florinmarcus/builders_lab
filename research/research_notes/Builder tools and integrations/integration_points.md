# Integration points of software UK builders use (APIs, webhooks, MCP servers, Zapier/Make)

All sources checked on 19 Nov 2026 unless a different date is given. "Unofficial" means not published by the vendor. "Unverified" means only a third-party page says it, or the page could not be opened. Many API facts come from third-party "API report" sites (Supergood, apis.io, API Evangelist): treat them as unverified until the vendor confirms.

## 1. Email, files and calendar: Google Workspace, Microsoft 365, Dropbox

### Takeaway
These are the easiest wins: Gmail, Google Drive, Google Calendar, Microsoft 365 and Dropbox all already have connectors in Claude's directory, marked "Anthropic verified". We should not build these; we should use them. The Microsoft 365 connector looks read-only, so writing to Outlook/OneDrive would need our own Microsoft Graph MCP server.

### Cited Findings
- Claude's connector directory showed 1,167 connectors on 19 Nov 2026. Gmail, Google Drive, Google Calendar, Microsoft 365 and Box were visible with an "Anthropic verified" badge. — [Claude connectors](https://claude.com/connectors)
- Gmail connector: "Made by Google", added March 2026, "Anthropic verified". 29 tools, including read/search (get_message, search_threads), create_draft, send_message, reply, forward, labels, filters, trash. The page does not say which Claude plans include it. — [Claude: Gmail connector](https://claude.com/connectors/gmail)
- Microsoft 365 connector: made by Anthropic, added November 2025. Covers SharePoint, OneDrive, Outlook (email and calendar) and Teams chat search. All listed tools are search/lookup, so it appears read-only (page does not say so outright). Free, Pro, Max and Ultra support work/school and personal Microsoft accounts; Team and Enterprise support work/school accounts only. Respects existing Microsoft permissions. — [Claude: Microsoft 365 connector](https://claude.com/connectors/microsoft-365)
- Third-party guides say the Microsoft 365 connector is read-only and that admins can limit who can authenticate in Microsoft Entra; one guide said it was limited to Team and Enterprise plans, which the official page now contradicts. — [fast.io guide](https://fast.io/resources/claude-integrations-guide/); contradicted by [Claude: Microsoft 365](https://claude.com/connectors/microsoft-365)
- Dropbox connector: "Made by Dropbox", "Anthropic verified", added June 2026. Read tools (search, fetch, preview, metadata, folder listing, shared links) and write tools (create files and folders, copy, move, delete, create shared links, create file requests). Plans not stated; an enterprise auto-connect setup is in beta. — [Claude: Dropbox connector](https://claude.com/connectors/dropbox)
- Google Drive connector: third-party guides say Claude can search and read Docs, Sheets, Slides, PDFs and Office files in Drive. Maker and write support not confirmed from the official page. — [fast.io guide](https://fast.io/resources/claude-integrations-guide/) (unverified)

### Inferences
- For a pilot, the email/file/calendar layer costs us nothing to build. A builder on Google Workspace gets read and write (Gmail send/draft) today. A builder on Microsoft 365 gets search only.
- Writing to Outlook, OneDrive or Teams (e.g. "file this photo in the job folder", "send this quote") would need our own Graph-based MCP server. That is a candidate build, but only if pilot users are on Microsoft 365.

### Gaps
- Microsoft Graph throttling limits, Gmail API quotas and Google app verification steps for our own app were not checked in this pass.
- Who made the Google Drive and Google Calendar connectors and their exact tools were not confirmed (pages not opened).
- Whether a community Microsoft Graph MCP server with write support is well maintained was not checked.

## 2. WhatsApp: WhatsApp Business Platform (Cloud API)

### Takeaway
WhatsApp is how many trades talk to clients and crews, but the official API only works with a business number the firm registers. It cannot read personal chats or existing groups. Groups support exists in 2026 but is narrow (8 people, invite-only, gated). Messages now cost per message; replies within 24 hours of a customer message are mostly free. There is no official Meta MCP server; community ones exist with mixed upkeep.

### Cited Findings
**What it can and cannot do**
- The Groups API is on the Cloud API in 2026: max 8 participants per group, invite-only, up to 10,000 groups per number, no endpoint adds a participant directly. — [Unipile: WhatsApp Group API 2026](https://www.unipile.com/whatsapp-group-api/) (third party)
- Groups created by the API only work with API-created groups; existing community groups cannot be adopted; developer forum complains of the 8-person cap. — [Meta developer community thread](https://developers.facebook.com/community/threads/1084199161066371/)
- Eligibility: one source says Official Business Account (OBA) is required; another says 100,000 daily business messages or OBA. Both say Groups API is not available for WhatsApp Business app numbers. — [Kapso: state of Groups API 2026](https://kapso.ai/blog/whatsapp-groups-api-state-2026); [WATI (Chinese)](https://www.wati.io/zh-hant/blog/gcr-seo-whatsapp-groups-api-%E5%95%86%E6%A5%AD%E6%87%89%E7%94%A8%E5%85%A8%E6%94%BB%E7%95%A5%E4%BC%81%E6%A5%AD%E6%87%89%E5%A6%82%E4%BD%95%E9%83%A8%E7%BD%B2%E8%88%87%E9%81%B8%E6%93%87/)
- Meta's Groups FAQ (updated 21 May 2026): Groups available in all Cloud API countries. — [Meta: Groups API FAQ](https://developers.facebook.com/documentation/business-messaging/whatsapp/groups/faq/)
- Calls, disappearing messages, view-once, interactive buttons/lists and catalogue messages are not supported in groups. — [Omnichat](https://blog.omnichat.ai/whatsapp-groups-api/amp/) (third party)
- lharries/whatsapp-mcp connects to a personal WhatsApp via WhatsApp Web, not the Business API (an unofficial route with ban risk; not suitable for a product). — [WATI blog on WhatsApp MCP](https://www.wati.io/en/blog/whatsapp-mcp-server/)

**Pricing (Meta)**
- Per-message billing since 1 July 2025, by category (marketing, utility, authentication templates) and recipient country. Only delivered messages are charged. — [Meta: WhatsApp pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- A customer message opens a 24-hour service window; free entry point window up to 7 days from Click-to-WhatsApp ads. — [Meta: WhatsApp pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- Each business number gets 1,000 free service messages per month. From 1 Oct 2026, service messages beyond the free tier are charged, and utility messages inside an open service window are also charged. — [Meta: WhatsApp pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- New "Meta Business Agent" AI message category (July 2026), billed at $2.00 per 1M tokens. — [Meta: WhatsApp pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- UK is a standalone market; its marketing rate rose on 1 July 2026. Meta's page does not show the figures inline (GBP CSV/PDF rate cards linked from the page). — [Meta: WhatsApp pricing](https://developers.facebook.com/docs/whatsapp/pricing)
- UK rate figures from third parties disagree: marketing £0.0382, £0.0458, £0.0529, or $0.0635 / $0.07303 (the last "effective 1 Oct 2026"); utility about £0.0128–£0.0159 ($0.022–$0.0253); authentication ~£0.0286. — [WebSearch summary of aggregators incl. Hyperleap](https://hyperleap.ai/whatsapp-pricing-calculator-uk), [Whautomate UK](https://whautomate.com/whatsapp-business-api-pricing-uk), [Blueticks 2026](https://blueticks.co/blog/whatsapp-business-api-pricing-2026) (unverified; check Meta GBP rate card)
- Meta rates exclude VAT; UK BSPs add 20% VAT plus their own platform fee. — [Hyperleap UK calculator](https://hyperleap.ai/whatsapp-pricing-calculator-uk)

**Approval and timing**
- New business portfolios start with a messaging limit of 250; business verification is needed to raise limits and get templates approved. — [WATI: API access](https://www.wati.io/en/blog/whatsapp-api-access/) (quoting Meta)
- Display name is verified automatically when the number reaches a higher messaging limit; after approval the number must be re-registered. — [Meta: display names](https://developers.facebook.com/documentation/business-messaging/whatsapp/display-names)
- Timelines conflict: display name review 6–12 hours per review ([360dialog FAQ](https://docs.360dialog.com/docs/useful/common-issues)); business verification 1–2 business days ([ChatDaddy guide](https://help.chatdaddy.tech/getting-started/922MY2B1hVzdtQHBsTicEx/meta-business-verification-guide/6e2ixJTwLudgCpkV4MohXS)). You can start messaging after sender registration, before verification ([Infobip](https://www.infobip.com/docs/whatsapp/get-started/sender-registration)).

**MCP servers (all unofficial; no Meta MCP server found)**
- Wati (a Meta Business Solution Provider) says it ships an MCP server. — [WATI blog](https://www.wati.io/en/blog/whatsapp-mcp-server/)
- YCloud WhatsApp MCP server: 11 GitHub stars, one directory shows 585 days since last commit (likely unmaintained). — [Enterprise DNA listing](https://enterprisedna.co/directories/mcp/ycloud-developers-ycloud-whatsapp-mcp-server)
- Jem-HR pywa-mcp-server (18 tools, PyWA library); Gonzalez8 whatsapp-business-mcp (templates, send, status); nakulben whatsapp-mcp (templates and send via Cloud API). Maintenance not checked. — [LobeHub: pywa](https://lobehub.com/it/mcp/jem-hr-pywa-mcp-server), [claudemarket: Gonzalez8](https://www.claudemarket.ai/mcp/Gonzalez8/whatsapp-business-mcp), [claudemarketplaces: nakulben](https://claudemarketplaces.com/mcp/nakulben/whatsapp-mcp)

### Inferences
- An MCP connector cannot "read the builder's WhatsApp". Realistic design: the firm gets a dedicated WhatsApp Business number, clients and subs message it, a webhook stores messages, and our MCP server exposes them to Claude. That is a bigger build (webhook receiver, storage, templates) than a pure API wrapper.
- Cost for a pilot is small (pennies per template message), but the 1 Oct 2026 change means even service replies past 1,000/month cost money.
- Groups at 8 people is too small for most site crews and cannot adopt existing groups.

### Gaps
- Exact Meta UK GBP rates for marketing/utility/authentication/service as of Nov 2026 (rate card CSV not opened).
- Whether the WhatsApp Business app "coexistence" mode (same number on app and API) is available in the UK in 2026 was not checked.

## 3. Construction platforms: Procore, Buildertrend, Houzz Pro, Fieldwire, Autodesk Construction Cloud, Bluebeam

### Takeaway
Only Autodesk has a vendor-published MCP server (local, needs APS app and service account). Procore has a good public API but no MCP server for outside AI (only a partner-specific MCP link, unverified). Buildertrend and Houzz Pro have no public API. Fieldwire's API is a paid add-on. Bluebeam has a Studio API with an approval step. These platforms are mostly used by bigger contractors, less by small UK firms (inference).

### Cited Findings
**Procore**
- REST API, OAuth 2.0 (authorization code and client credentials). — [Procore developer docs](https://procore.github.io/documentation/introduction) (via search summary)
- Rate limits: an hourly window plus a 10-second spike limit; read limits from response headers. Third parties say 3,600 requests/hour per app per company, spike 100 per 10 seconds, raisable to 7,200 or 14,400 via Procore support. — [Procore: rate limiting](https://procore.github.io/documentation/rate-limiting); [Hingepoint](https://proconnector.hingepoint.com/support/throttle-limits/)
- Public Marketplace apps need the Technology Partner Program and Marketplace QA; no self-serve publishing. — [Procore API usage guidelines](https://procore.github.io/documentation/api-usage-guidelines); [Supergood report card](https://supergood.ai/api-report-card/procore-technologies) (third party)
- No official Procore MCP server for outside AI found. A competitor page says Procore's first MCP connection (Oct 2026) was for partner app COMPASS; Procore's Datagrid AI uses MCP as a client; Procore agents were in private beta (May 2026). — [Ingenious vs Procore MCP](https://www.ingenious.build/ingenious-vs-procore-mcp) (competitor, unverified); [Carly blog](https://www.usecarly.com/blog/claude-procore-integration/)
- Unofficial MCP servers: TylerIlunga/procore-mcp-server (MIT, TypeScript, ~8 stars); mohllal server (stdio, local OAuth token); Pipedream and Zapier hosted Procore MCP. — [GitHub: TylerIlunga](https://github.com/TylerIlunga/procore-mcp-server), [mcp.so](https://mcp.so/servers/procore-mcp-server), [Pipedream](https://mcp.pipedream.com/app/procore), [Zapier MCP Procore](https://zapier.com/mcp/procore)

**Buildertrend**
- No self-serve public API: REST API at api.buildertrend.com is gated by partner agreement, no open portal or public spec; integration mainly via a curated marketplace (QuickBooks, Xero, etc.). Supergood grades it F. — [apis.io: Buildertrend](https://apis.io/providers/buildertrend/); [Supergood report card](https://supergood.ai/api-report-card/buildertrend) (third party)
- developer.buildertrend.com does not resolve (per Carly), though another page cites an "Open API portal". Status unclear. — [Carly blog](https://www.usecarly.com/blog/buildertrend-api/) (unverified)
- An "MCP server" listing exists (cotlet-dev) but would depend on the gated API. — [mcpservers.org](https://mcpservers.org/servers/cotlet-dev-integrations-buildertrend-api-mcp-server) (unofficial, unverified)

**Houzz Pro**
- Official integrations: one-way QuickBooks Online sync (estimates, invoices, payments out of Houzz Pro), and a one-way Zapier integration that only imports leads and projects into Houzz Pro, only on Custom packages. — [Houzz Pro UK help: integrations](https://pro.houzz.co.uk/pro-help/r/what-integrations-does-houzz-pro-support); [Houzz Pro UK: Zapier](https://pro.houzz.co.uk/pro-help/r/how-to-integrate-zapier-with-houzz-pro)
- No back-office public API, no webhooks (third-party assessment). — [Supergood: Houzz Pro](https://supergood.ai/api-report-card/houzz-pro)

**Fieldwire (Hilti)**
- API access for Enterprise customers, or as a sales add-on for Pro, Business, Business Plus. Developer access must be approved before generating tokens. Docs at developers.fieldwire.com. — [Fieldwire help](https://help.fieldwire.com/hc/en-us/articles/360034986232); [Fieldwire Business Plus](https://help.fieldwire.com/hc/en-us/articles/15723076024603)
- A pricing tracker claims on 15 Nov 2026 Fieldwire gated Enterprise API access behind $5,000+ contracts. — [PricingSaaS diff 2026W47](https://pricingsaas.com/companies/fieldwire/diffs/2026W47) (unverified)

**Autodesk Construction Cloud (APS)**
- Official repo autodesk-platform-services/aps-mcp-server-nodejs (moved from petrbroz). Local Node.js server, uses Secure Service Accounts; the service account must be invited as a member of each ACC project. Works with Claude Desktop, VS Code, Cursor. — [GitHub: aps-mcp-server-nodejs](https://github.com/autodesk-platform-services/aps-mcp-server-nodejs)
- Community/hosted ACC MCP servers exist (issues, RFIs, submittals, cost, forms), labelled "Not an Autodesk product". — [Glama ACC MCP](https://glama.ai/mcp/servers/n38ot4vlm6), [Vinkius](https://vinkius.com/es/apps/autodesk-construction-cloud-mcp)

**Bluebeam**
- Studio API covers Sessions, Projects and Project File Jobs, plus webhooks. Developer Portal access reviewed in 5–7 business days; apps start in sandbox; production needs approval via integrations@bluebeam.com; regions include UK. — [Bluebeam: develop integrations](https://support.bluebeam.com/integrations/develop-integrations.html); [Bluebeam Integrations Hub](https://support.bluebeam.com/integrations/integrations-hub.html)
- 2026 changes: integration entitlements retired 20 Feb 2026 (creating Sessions/Projects via integration needs Core or Complete plan); RevisionID change 2 Mar 2026; integration rate limits from 1 Jul 2026. — [Bluebeam Integrations Hub](https://support.bluebeam.com/integrations/integrations-hub.html) (via search summary)
- No Bluebeam MCP server found.

### Inferences
- Procore is the only construction platform with a solid, public, documented API we could wrap ourselves; but its users are larger contractors. For a small Romanian-run UK firm, these platforms are probably rare (guess, needs research in `research/`).
- Buildertrend and Houzz Pro are blocked for us without partner deals.

### Gaps
- Procore developer sandbox cost and any API fee: not found. Official Procore MCP announcement not verified.
- Autodesk APS pricing (token/credit model) not checked in this pass.
- Bluebeam exact rate limits not found.

## 4. Trades apps: Tradify, Powered Now, Fergus, ServiceM8, Jobber

### Takeaway
Jobber and ServiceM8 lead: both have vendor MCP servers and public APIs. Fergus has an open API (OAuth or personal token) and Zapier. Tradify and Powered Now have no public API we could find; Powered Now is on Zapier only.

### Cited Findings
- **Jobber:** a third-party review (2 Nov 2026) says Jobber publishes an official remote MCP connector with OAuth sign-in (search clients, quotes, jobs, visits, invoices; create clients, properties, requests, quotes) and that it is listed in Claude's directory. Endpoint reported as https://mcp.getjobber.com/mcp. — [eSEOspace: Jobber MCP](https://eseospace.com/blog/jobber-mcp-server/) (unverified; endpoint not confirmed by Jobber page)
- Jobber has a GraphQL API that requires registering an app. Unofficial MCP servers: friendlygeorge/jobber-mcp-server (stdio, mock-data mode), Composio, Truto, Pipedream. — [claudemarket: friendlygeorge](https://claudemarket.ai/mcp/friendlygeorge/jobber-mcp-server), [Composio](https://composio.dev/toolkits/jobber), [Truto](https://truto.one/blog/connect-jobber-to-claude-track-work-requests-and-service-bookings/)
- **ServiceM8:** official developer page "MCP Server: connect to your ServiceM8 account as an MCP server"; search snippet gives endpoint https://developer.servicem8.com/mcp (API access, docs search, live account data). Auth, scope and plan not stated on the page. — [ServiceM8 developer: MCP server](https://developer.servicem8.com/docs/mcp-server)
- Unofficial ServiceM8 MCP: BackCrew, Composio, Vinkius. — [Glama BackCrew](https://glama.ai/mcp/servers/qp2lyrjkch), [Composio](https://composio.dev/toolkits/servicem8)
- **Fergus:** "Fergus Developer Platform" supports OAuth and personal access tokens; docs at https://api.fergus.com/docs; developers submit a form describing what they build. Data scope, webhooks, rate limits, plans and cost not stated. Zapier integration uses the open API (trigger and action). — [Fergus developers](https://info.fergus.com/developers); [Fergus help: Zapier](https://help.fergus.com/en/articles/11644092-zapier-integration)
- Unofficial Fergus MCP: Jayco-Design/fergus-mcp (uses personal access token, base URL api.fergus.com). — [Glama: fergus-mcp](https://glama.ai/mcp/servers/@Jayco-Design/fergus-mcp/blob/cbfb69471710f17996ee613632ef7a3baf32f834/.env.example)
- **Tradify:** no open, self-serve public API, portal or webhooks; integrations limited to accounting and payment partners. apis.io OpenAPI files are not confirmed by Tradify. — [API Evangelist: Tradify](https://providers.apievangelist.com/providers/tradify/); [Supergood: Tradify](https://supergood.ai/api-report-card/tradify); [apis.io: Tradify](https://apis.io/providers/tradify/) (all third party)
- **Powered Now:** Zapier app exists (e.g. "Job Closed" trigger). No public API documentation found. — [Zapier: Powered Now](https://zapier.com/apps/powered-now-1/integrations)

### Inferences
- If pilot firms use Jobber or ServiceM8, we can connect today with vendor MCP servers (zero build). Fergus is a small, cheap build. Tradify and Powered Now would need Zapier (Powered Now) or nothing (Tradify).
- Which of these UK small builders actually use (Tradify and Powered Now are UK-popular; Jobber is North America-led) needs the market research note.

### Gaps
- Jobber and ServiceM8 MCP auth, plan requirements and write scope not confirmed from vendor docs.
- Powered Now API: none found; asked nothing of vendor.
- Rate limits and costs for all five not found.

## 5. Accounting: Xero, QuickBooks (summary), Sage

### Takeaway
Xero and QuickBooks have official MCP servers (QuickBooks also a hosted Claude connector, per a third party). Sage Accounting (cloud) has a self-serve REST API and only community MCP servers. Sage 50 UK has no REST API (Windows COM SDK, paid developer programme), which blocks us.

### Cited Findings
- Xero: official XeroAPI/xero-mcp-server (MIT, TypeScript, run via npx @xeroapi/xero-mcp-server; contacts, invoices, accounts, payroll, reports). — [Glama: XeroAPI README](https://glama.ai/mcp/servers/@XeroAPI/xero-mcp-server/blob/main/README.md)
- QuickBooks: intuit/quickbooks-online-mcp-server (local, stdio; tool counts and licence disputed across sources); a hosted Claude connector "Made by Intuit QuickBooks" reported by one source. — [Glama: intuit QBO MCP](https://glama.ai/mcp/servers/intuit/quickbooks-online-mcp-server); [Carly: QuickBooks MCP](https://www.usecarly.com/blog/quickbooks-mcp/) (hosted listing unverified)
- Sage Accounting (Business Cloud): REST API v3.1, OAuth 2.0, self-serve signup on developer.sage.com. Community MCP server larrygmaguire/hash-sage-accounting-mcp (local, your own OAuth credentials); Unified.to hosted option. No official Sage MCP. — [LobeHub: Sage Accounting MCP](https://lobehub.com/mcp/larrygmaguire-hash-sage-accounting-mcp); [Apideck Sage field guide](https://radar.apideck.com/blog/sage-integration-field-guide); [Unified.to](https://unified.to/integrations/sageaccounting)
- Sage 200: REST/OData API, OAuth 2.0 via Sage ID, credentials by form (no Developer Programme needed). — [Sage 200 developer portal](https://developer.columbus.sage.com/docs/services/api/uk); [Apideck](https://radar.apideck.com/blog/sage-integration-field-guide)
- Sage 50 UK: no RESTful API; integration via Sage Data Objects (Windows COM), gated by the paid Developer Programme and tied to each release. — [Apideck Sage field guide](https://radar.apideck.com/blog/sage-integration-field-guide); [Supergood: Sage 50](https://supergood.ai/api-report-card/sage-50) (third party)

### Inferences
- Accounting is covered by the other note; for ranking, Xero/QuickBooks are near-zero build. Sage Accounting is a small build. Sage 50 desktop is out of scope.

### Gaps
- Sage API rate limits and any fees not found.

## 6. Safety and compliance: SafetyCulture, CHAS, Constructionline

### Takeaway
SafetyCulture has a documented API (Premium or Enterprise plans, per a third party) and only unofficial MCP servers. CHAS and Constructionline have no public developer API; their data flows through partner integrations (COINS, Causeway) and Build UK data sharing.

### Cited Findings
- SafetyCulture API needs a Premium or Enterprise plan; rate limit 800 requests per 60 seconds on some endpoints. — [Rollout: SafetyCulture API essentials](https://rollout.com/integration-guides/safety-culture/api-essentials) (third party; official page [developer.safetyculture.com/reference/rate-limits](https://developer.safetyculture.com/reference/rate-limits) exists but numbers not confirmed)
- No official SafetyCulture MCP. Unofficial: zerubroberts/safetyculture-mcp-server (Python, API key in .env, Feed API); Truto and Composio hosted. — [LobeHub](https://lobehub.com/mcp/zerubroberts-safetyculture-mcp-server); [Truto](https://truto.one/blog/connect-safetyculture-to-claude-track-assets-and-custom-fields/); [Composio](https://composio.dev/toolkits/safetyculture/framework/claude-code)
- Build UK: supplier data is shared in real time between Recognised Assessment Bodies (including Constructionline and CHAS), with supplier consent; not for products outside the Common Assessment Standard. — [Build UK: data sharing](https://builduk.org/DataSharing)
- Constructionline data reaches Access Coins through a pre-built connector, enabled by the Access account manager. — [Access Group: Coins + Constructionline](https://www.theaccessgroup.com/en-gb/construction/integrations-and-partners/constructionline/)
- CHAS data is integrated into Causeway Tradex. — [Causeway news](https://causeway.com/news/chas-partners-with-causeway-technologies-to-ensure-contractor-health-safety-compliance-across-the-supply-chain)
- No public CHAS or Constructionline API docs found.

### Inferences
- CHAS/Constructionline would need a commercial partnership: not a pilot candidate. SafetyCulture is feasible but needs the customer on a paid plan.

### Gaps
- SafetyCulture plan prices for UK and official rate limits.

## 7. Signatures: DocuSign and Adobe Acrobat Sign

### Takeaway
DocuSign has an official remote MCP connector in Claude's directory (open beta), so contracts and variations can be sent for signature from Claude with no build. Adobe Acrobat Sign has a free developer account but no MCP server and custom enterprise pricing for production.

### Cited Findings
- DocuSign MCP connector: open beta for developer and production accounts, no intake form; available via Claude's connector directory or as a custom connector at https://mcp-d.docusign.com/mcp with Client ID and Secret; needs a DocuSign account and Claude Pro or higher (or Claude Desktop). — [DocuSign developer blog: Claude MCP connector guide](https://www.docusign.com/blog/developers/claude-docusign-mcp-connector-guide)
- Adobe: free Acrobat Sign Developer Edition with API access for testing. — [Adobe Acrobat Sign API overview](https://developer.adobe.com/acrobat-sign/docs/overview/developer_guide/)
- Production API use needs an Enterprise account; no published production API price. — [Adobe community forum](https://community.adobe.com/questions-35/what-adobe-plan-is-needed-to-use-adobe-acrobat-sign-api-21164); [SignEasy guide](https://signeasy.com/esign-api-guide/adobe-esign-api) (competitor)
- No Adobe Sign MCP server found.

### Inferences
- DocuSign is a zero-build integration; if the firm uses Adobe, it is a build and an enterprise cost.

### Gaps
- Whether DocuSign's connector has left beta; DocuSign plan needed for API envelopes (cost) not checked.

## 8. Glue layer: Zapier and Make as MCP connectors

### Takeaway
Zapier MCP and the Make MCP server let Claude reach apps without APIs of their own on our side (e.g. Powered Now, Houzz Pro leads). Make is a built-in Claude connector. Zapier charges two tasks per successful tool call.

### Cited Findings
- Zapier MCP: each successful tool call uses two tasks; failed calls none; no separate MCP billing. Free plan has 100 tasks/month (~50 calls). — [Zapier docs: MCP usage](https://docs.zapier.com/mcp/usage); [Zapier blog: what is a task](https://zapier.com/blog/what-is-a-task-in-zapier/)
- From 1 Dec 2026, AI by Zapier steps run via MCP use their own price. — [Zapier help: AI model tier pricing](https://help.zapier.com/hc/en-us/articles/46425475442829)
- Zapier has MCP pages for Procore and Houzz Pro. — [Zapier MCP: Procore](https://zapier.com/mcp/procore), [Zapier MCP: Houzz Pro](https://zapier.com/mcp/houzz-pro)
- Make MCP server is a built-in Claude connector (OAuth; also https://mcp.make.com); runs active and on-demand scenarios. — [Make help: built-in Claude connector](https://help.make.com/make-now-a-built-in-connector-on-anthropic-claude.md); [Make developers: MCP server](https://developers.make.com/mcp-server/)

### Inferences
- For apps with only Zapier support, Zapier MCP is the fastest route, but costs scale with every tool call and the firm must hold a Zapier plan.

### Gaps
- Zapier and Make plan prices in GBP for a small firm not checked.

## 9. Inputs for ranking which integrations to build first

### Takeaway
Use what already exists first (Gmail/Drive/Calendar, Microsoft 365 read, Dropbox, DocuSign, Xero, QuickBooks, Jobber, ServiceM8, Make/Zapier). Our own builds with best value: WhatsApp Business (high value, real build), Microsoft 365 write via Graph, Fergus, Sage Accounting, SafetyCulture. Blocked: Buildertrend, Houzz Pro, Tradify, Sage 50, CHAS, Constructionline.

### Cited Findings
- Existing vendor or Anthropic connectors: Gmail, Microsoft 365, Dropbox ([Claude connectors](https://claude.com/connectors)); DocuSign ([DocuSign blog](https://www.docusign.com/blog/developers/claude-docusign-mcp-connector-guide)); Xero ([XeroAPI](https://glama.ai/mcp/servers/@XeroAPI/xero-mcp-server/blob/main/README.md)); Autodesk ([APS GitHub](https://github.com/autodesk-platform-services/aps-mcp-server-nodejs)); ServiceM8 ([ServiceM8](https://developer.servicem8.com/docs/mcp-server)); Make ([Make help](https://help.make.com/make-now-a-built-in-connector-on-anthropic-claude.md)).
- Public API but no official MCP: Procore, Fergus, Sage Accounting, SafetyCulture, Bluebeam (approval), Fieldwire (paid add-on). Sources in sections 3–6.
- No public API: Buildertrend, Houzz Pro, Tradify, Powered Now (Zapier only), Sage 50 (COM only), CHAS, Constructionline. Sources in sections 3–6.

### Inferences
Suggested tiers (our judgement, not a source):
1. **Use now, no build:** Google Workspace, Microsoft 365 (read), Dropbox, DocuSign, Xero, QuickBooks, Jobber/ServiceM8 if used.
2. **Build first:** WhatsApp Business number + webhook + MCP (highest value for trades; costs pennies per message; needs Meta verification, days not weeks). Then Microsoft Graph write tools if pilots use M365.
3. **Build if a pilot uses it:** Fergus, Sage Accounting, SafetyCulture, Procore.
4. **Skip for now:** Buildertrend, Houzz Pro, Tradify, Sage 50, CHAS, Constructionline, Adobe Sign, Fieldwire, Bluebeam.

### Gaps
- Which tools small Romanian-run UK building firms actually use. This ranking needs that market data to be final.
