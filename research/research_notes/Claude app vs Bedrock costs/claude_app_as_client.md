# The Claude app as the client for our own backend (remote MCP custom connector), as of Nov 2026

Research date: 18 Nov 2026. "Checked" means the page was fetched on that date. Pages on support.claude.com and claude.com/docs carry no exact dates unless stated ("Updated this week" on the custom connector article). Items from search snippets only are marked **(unverified, snippet)**.

## 1. Custom connectors: plans, who can add, setup, auth, transport, clients

### Takeaway
Any Claude plan can add a custom connector (a remote MCP server URL), including Free (one connector only). On Team and Enterprise only Owners add them, then each member clicks Connect. Connectors are added on web or desktop and then work on iOS/Android too. Auth can be none, OAuth (DCR or CIMD), or (beta, limited orgs) a fixed API key header. Transport is Streamable HTTP on port 443, reachable from Anthropic's cloud.

### Cited Findings
- Custom connectors using remote MCP are available on "Free, Pro, Max, Ultra, Team, and Enterprise plans"; "Free users are limited to one custom connector." — [Claude Help: Get started with custom connectors (checked 18 Nov 2026)](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- Team: "only Owners and Primary Owners can add them to Team plans." Enterprise: Owners, Primary Owners and "people with a custom role that includes Manage access to Libraries." After an org adds a connector, each user connects and enables it individually. — [same](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- Setup (Team/Enterprise Owner): Organization settings > Connectors > Add > Custom > Web; name + remote MCP server URL; choose auth mode ("Sign in now", "Sign in when needed", "No sign in"); OAuth client option ("Use Claude's published identity (Recommended)", "Register automatically", "Use your own OAuth client"); optional fixed credentials under Request headers. Pro/Max: Customize > Connectors > "+ Add" > "Add custom connector". Members: Customize > Connectors > "Connect". Enabled per chat via "+" > Connectors. To edit a connector you remove and re-add it. — [same](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- Connections come from Anthropic's cloud, not the user's device; the server "must also be reachable on the standard HTTPS port (443)"; servers on private networks need Anthropic IP ranges allowlisted. — [same](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- Anthropic's outbound traffic comes from `160.79.104.0/21`. — [Claude docs: Authentication for connectors (checked 18 Nov 2026)](https://claude.com/docs/connectors/building/authentication.md)
- Clients: "Claude connects to your server from claude.ai, Claude Desktop, Claude mobile, Cowork, and Claude Code, and the same connector infrastructure backs all of them." — [Claude docs: Build an MCP server for Claude (checked 18 Nov 2026)](https://claude.com/docs/connectors/building.md)
- Mobile: older Anthropic support text says users can use remote servers on iOS/Android that they "already added via claude.ai" and "cannot add new servers directly from Claude Mobile"; rollout dated July 2025 (developer write-up gives 26 Jul 2025). **Older info (2025), unverified for Nov 2026, snippet.** — [Claude Help: pre-built connectors](https://support.claude.com/en/articles/11176164-pre-built-connectors-using-remote-mcp); [DEV Community guide](https://dev.to/zhizhiarv/how-to-set-up-remote-mcp-on-claude-iosandroid-mobile-apps-3ce3). The current custom-connector article does not say whether mobile can add connectors, but says connection behaviour applies to "every Claude client, including claude.ai, Claude Desktop, Cowork, and the mobile apps." — [Claude Help](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp). A search snippet also says "Installing connectors on mobile is currently in beta" **(unverified, snippet)**.
- Transport: use Streamable HTTP; Claude also supports legacy HTTP+SSE, "which is being deprecated." — [Build an MCP server for Claude](https://claude.com/docs/connectors/building.md)
- Auth types: `oauth_dcr` and `oauth_cimd` supported by default; `none` (authless) supported by default; `static_headers` (API key/bearer token entered once by an org Owner) is "Beta, for a limited set of organizations"; `oauth_anthropic_creds` and `custom_connection` are for directory listings / by contacting Anthropic. — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)
- OAuth specifics: Claude follows the 2025-03-26, 2025-06-18 and 2025-11-25 MCP authorization specs; redirect URI `https://claude.ai/api/mcp/auth_callback` for web, desktop, mobile and Cowork; PKCE S256 required; server must answer unauthenticated calls with `401` + `WWW-Authenticate: Bearer resource_metadata=...` (Claude ignores it on a 200); Claude uses only the first `authorization_servers` entry; CIMD used only if AS metadata advertises `client_id_metadata_document_supported: true` and `none` in `token_endpoint_auth_methods_supported`, else falls back to DCR; 10 s limit on discovery/registration/token endpoints, 30 s on refresh; `client_credentials` (machine-to-machine) grant not supported; token endpoint must accept form-urlencoded. — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)
- Static header credential on Team/Enterprise: "every member's requests carry the same key, so don't use it to identify which user is calling. If your tools need to act as the individual user, use OAuth instead." Tokens must never go in the URL query string. — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)
- Third-party report says claude.ai does not fall back to DCR when CIMD is missing, which conflicts with the official doc. — [Skycloak blog](https://skycloak.io/blog/keycloak-cimd-claude-ai-public-client-jwt-grant/) (contradicted by [official docs](https://claude.com/docs/connectors/building/authentication.md))

### Inferences
- For one builder on Pro or Max, the builder (or we) adds our URL once on claude.ai; it then shows on his phone. For a small firm on Team, the Owner adds it and each worker connects.
- An authless server is technically allowed but anyone with the URL could call it. For real council emails and property data we need per-user OAuth (DCR or CIMD), unless the beta header option is enabled for the org. Header option shares one key across the org.
- A Free account with one connector could even work for a trial, but usage limits on Free are low.

### Gaps
- No current (Nov 2026) official statement on whether a connector can be *added* from the mobile app, only that it works there.
- No official per-plan cap on number of custom connectors found, except Free = 1.

## 2. Limits: size, timeouts, files, images, links

### Takeaway
On claude.ai/desktop a tool result can be about 150,000 characters and a tool call can run 240 seconds. Tools can return text and images; resources can be text or binary. Sampling and resource subscriptions are not supported.

### Cited Findings
- "Maximum tool result size: ~150,000 characters" (claude.ai and Desktop) vs 25,000 tokens in Claude Code; "Tool call timeout: 240 seconds per tool call" (claude.ai and Desktop). — [Build an MCP server for Claude](https://claude.com/docs/connectors/building.md)
- Server can expose tools, prompts and resources; "Text and image-based tool results"; "Text and binary resources." Not supported: "Resource subscriptions", "Sampling", "Advanced or draft capabilities." — [same](https://claude.com/docs/connectors/building.md)
- Advanced research "is not currently able to invoke tools from local MCP servers" (local only; remote not mentioned). — [Claude Help custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)
- MCP Apps can offer "Downloads: save a file from your app to the user's device." — [Get started with MCP Apps](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md)

### Inferences
- PDF pages can be returned as images (rendered page PNGs) or extracted text; a full PDF probably needs to be text-extracted or chunked to stay under ~150K characters.
- Links to source documents: a tool can return a URL in its text and Claude can show it, but that is normal model behaviour, not a documented feature. Links would need to point to our own hosted, access-controlled document viewer.
- A RAG search tool should return the top few chunks, not whole documents, to stay within size limits and save usage.

### Gaps
- No official doc found on whether a user's chat file uploads (photo, PDF) are passed to an MCP tool. Likely not directly (Claude would have to describe/transcribe them). Unverified.
- No official tool-calls-per-turn limit found.
- No official doc on citation/link rendering from connector results.

## 3. Interactive UI inside Claude (MCP Apps)

### Takeaway
MCP Apps (official MCP extension) let our server render interactive UI (tables, lists, buttons, maps) in the chat. Launched 26 Jan 2026 on web, desktop and mobile for all plans. Richer features (side panel, app tools, embedded sites, entry points) came 10 Nov 2026 in public preview, web and desktop only, not mobile yet. Custom connectors can render MCP Apps (Anthropic's own docs tell developers to test them as custom connectors).

### Cited Findings
- Interactive connectors launched 26 Jan 2026; "available in Claude on mobile, web and desktop" on "Free, Pro, Max, Ultra, Team, and Enterprise plans"; MCP Apps is "a new extension to MCP that lets any MCP server deliver interactive connectors with a rich user interface." — [Claude blog, 26 Jan 2026](https://claude.com/blog/interactive-tools-in-claude)
- MCP Apps became the first official MCP extension at production-ready status on 26 Jan 2026 (secondary). — [Alpic blog](https://alpic.ai/blog/mcp-apps-goes-official-claude-chatgpt-support)
- 10 Nov 2026: "Claude now supports more of the extension, such as app tools, along with embedded sites, so a developer's full app can run inside Claude"; public preview for developers; "rolling out on the web and in the Claude desktop app on all plans." Mobile not mentioned. — [Claude article, 10 Nov 2026](https://claude.com/de/resources/articles/interactive-connectors-full-tool)
- "Interactive connectors are available for all users on Claude, Cowork, Claude Desktop, and Claude for iOS/Android." Side panel, full-site views and pinning "aren't available on Claude Mobile yet." "Purchases through a connector's in-chat views aren't supported." Team/Enterprise owners can disable the tool calls that render interactive UI without disabling the connector. — [Claude Help: Use interactive connectors (checked 18 Nov 2026)](https://support.claude.com/en/articles/13454812-use-interactive-connectors-in-claude)
- MCP App capabilities: side panel and full screen; entry points from the Artifacts page with sidebar pinning; app tools (Claude can change what the app shows, e.g. selected rows); messages (a button in the app can send Claude a message); embedded websites in an iframe; downloads. App tools, entry points and embedded sites need a remote server. For directory connectors, entry points and embedded sites need a Verified listing, "even if both worked while you tested with a custom connector." Developers are told to "Add your server to Claude as a custom connector" to test. Claude asks permission to display the app ("Allow once"/"Always allow"). — [Get started with MCP Apps](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md)
- The MCP Apps SDK is JavaScript (vanilla JS, React, Vue, Svelte examples); one codebase can run in Claude and other MCP Apps hosts; there is a migration path from the OpenAI Apps SDK. — [same](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md)
- A newsletter claims mobile interactive connectors launched 25 Mar 2026; not confirmed by Anthropic. — [Buttondown](https://buttondown.com/verified/archive/anthropics-interactive-connectors-hit-claude); contradicted by [Claude blog](https://claude.com/blog/interactive-tools-in-claude) (mobile at launch)

### Inferences
- A property list as a table with "show details" / "draft reply" buttons is within what MCP Apps can do (inline card plus message-sending buttons). This works on phone as an inline view; the side-panel style needs desktop/web for now.
- The UI part is HTML/JS even if the server is Python; small amount of frontend work, but far less than a full chat web app.

### Gaps
- Not confirmed whether app tools / embedded sites work for a custom connector on every plan (the 10 Nov rollout depends on "organization access" checks).
- No size or CSP limits for MCP App bundles captured (see the troubleshooting/design-guidelines pages, not fetched).

## 4. Usage limits and the cost of heavy tool results

### Takeaway
Paid plans have a 5-hour session limit and a weekly limit, shared across claude.ai, desktop and Claude Code. Anthropic says "tools and connectors are token-intensive." Exact message counts are not published.

### Cited Findings
- Prices (USD, no GBP shown): Free $0; Pro $17/month annual or $20 monthly; Max $100/month ("5x Pro usage"); Ultra $200/month ("10x Pro usage", "No 5-hour limit" for verified accounts); Team Standard $20/seat annual or $25 monthly, Premium $100/$125, "For teams of 2 to 150"; Enterprise "US$20/seat/month, billed annually", "20 seat minimum", usage billed at API rates. Connectors marked "Yes" on all plans; Team/Enterprise add admin controls for remote and local connectors. — [claude.com/pricing (checked 18 Nov 2026)](https://claude.com/pricing)
- Session limit "resets every five hours"; "Weekly limits apply across all models"; usage on claude.ai, Claude Code and Desktop "counts towards the same usage limit"; "Tools and connectors are token-intensive"; long chats triggering context management "consume more of your usage limit"; "We don't guarantee uninterrupted service." No per-plan numbers. — [Claude Help: Understanding usage and length limits (checked 18 Nov 2026)](https://support.claude.com/en/articles/11647753-understanding-usage-and-length-limits)
- Third-party guides: every MCP tool response enters context and each tool step resends context, so tool use adds up; figures conflict between sources. **(secondary, numbers unverified)** — [chudi.dev](https://chudi.dev/blog/claude-usage-limits); [sandlabs](https://sandlabs.com.au/blog/claude-usage-limits-explained)

### Inferences
- A builder asking a few questions a day on Pro is probably fine; heavy daily use with big search results could hit the 5-hour limit. Keeping tool results small matters for usage as well as quality.
- With the Claude app, the model cost sits on the builder's Claude subscription (about $20/month Pro, or $25/seat Team), not on our Bedrock bill. We still pay for hosting the MCP server, database and search.

### Gaps
- No official numbers for messages per 5 hours or per week on any plan.
- No GBP prices on the pricing page.

## 5. ChatGPT as an alternative client

### Takeaway
ChatGPT also supports custom MCP servers ("developer mode", recently renamed "Add custom MCP server" per one source) and apps with UI built on the Apps SDK, which is compatible with MCP Apps. Plan rules are unclear: full read/write on Business/Enterprise/Edu; Plus/Pro reported as read/fetch only. Mobile is unconfirmed by OpenAI.

### Cited Findings
- OpenAI help (snippet): developer mode "available in beta on the web to Pro, Plus, Business, Enterprise, and Education accounts"; full MCP including write actions in beta for Business, Enterprise and Edu; Pro users can connect MCPs "with read and fetch permissions." **(snippet; page returned 403 on fetch)** — [OpenAI Help 12584461](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt)
- On Business, "Only admins/owners can enable developer mode and deploy an app" (snippet). — [OpenAI Help](https://help.openai.com/en/articles/12584461)
- A guide dated 2 Nov 2026 says the old developer mode page now 404s and the new flow is Plugins > Add custom MCP server. **(single third-party source)** — [eseospace](https://eseospace.com/blog/chatgpt-developer-mode-mcp/)
- OpenAI developer docs now frame this as "plugins with skills, MCP servers, and optional UI", with an MCP server "for ChatGPT and Codex, with optional UI in ChatGPT", and directory guidelines for public listing. — [OpenAI developers: apps-sdk / plugins index (checked 18 Nov 2026)](https://developers.openai.com/apps-sdk)
- Mobile: one third-party guide says connectors created on web sync to ChatGPT mobile; another says MCP apps are web only. Conflicting, unverified. — [Boomi help](https://help.boomi.com/docs/Atomsphere/Platform/Connect_chatgpt_setup); [coworker.ai](https://coworker.ai/blog/chatgpt-mcp)
- Claude docs offer a migration path from the OpenAI Apps SDK to MCP Apps; one MCP App codebase can run in multiple hosts. — [Get started with MCP Apps](https://claude.com/docs/connectors/building/mcp-apps/getting-started.md)

### Inferences
- The same remote MCP server could serve both Claude and ChatGPT, so the client choice is not locked in. Claude's plan rules for custom connectors are clearer and include Free and Pro with write tools.

### Gaps
- Could not fetch OpenAI's current help page (403). ChatGPT mobile support for custom MCP and plan rules as of Nov 2026 are unverified.

## 6. Developer side: building and hosting a remote MCP server in Python

### Takeaway
A Python remote MCP server is a small job with the official Python SDK (which includes FastMCP). It needs a public HTTPS URL on port 443, and for real data an OAuth 2.x authorization server that supports PKCE and DCR or CIMD. No Anthropic review is needed for private use as a custom connector.

### Cited Findings
- Official SDKs: TypeScript and Python, with server examples. — [Build an MCP server for Claude](https://claude.com/docs/connectors/building.md) linking [python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- "As a custom connector: a user or an organization Owner adds it by entering its URL, with no review by Anthropic." Directory listing requires review; anyone on a paid plan can submit, on Team/Enterprise an Owner submits. — [same](https://claude.com/docs/connectors/building.md)
- Testing is done against the real Claude client by adding the server as a custom connector; a local server can be exposed through a tunnel; MCP Inspector validates auth. — [same](https://claude.com/docs/connectors/building.md)
- Auth server must serve RFC 8414 or OIDC discovery metadata reachable from Anthropic's egress range; a WAF in front of the identity provider can break the flow. Microsoft Entra ID needs the MCP URL registered as an Application ID URI. — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)
- "Lazy authentication" lets some tools work without sign-in and ask for sign-in only when a protected tool is called. — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)

### Inferences
- Hosting: any small container or serverless host with HTTPS (e.g. a cheap VM, Cloud Run, App Runner) works; the auth server can be a managed identity provider (Auth0, WorkOS, Keycloak, Cognito) if it supports DCR or CIMD and PKCE S256. Check Cognito DCR support before choosing it (not verified here).
- The MCP server is the backend we would build anyway (tools for emails, property DB, document search); the Claude app replaces the chat UI, chat history, mobile app and the LLM bill.

### Gaps
- No time estimate from an authoritative source; FastMCP-specific auth helpers not checked.
- Which managed identity providers support CIMD/DCR in Nov 2026 not checked.

## 7. Known problems reported by developers

### Takeaway
GitHub issues on `anthropics/claude-ai-mcp` show OAuth connection failures on web and mobile, including on a Team plan, and a connector that worked on web and iOS then broke around April 2026. Most failures trace to auth discovery or redirect handling.

### Cited Findings
- Issue #410: custom connector fails at Connect, no login screen, on "claude.ai web connector AND Claude mobile app", while Claude Code connects to the same URL. **(snippet; plan not stated)** — [GitHub #410](https://github.com/anthropics/claude-ai-mcp/issues/410)
- Issue #215: connector "worked reliably via claude.ai web and iOS until approximately April 15, 2026." **(snippet)** — [GitHub #215](https://github.com/anthropics/claude-ai-mcp/issues/215)
- Issue #280: connector on a Team plan fails when auth finishes and redirects back to claude.ai (tested in Chrome on macOS). **(snippet)** — [GitHub #280](https://github.com/anthropics/claude-ai-mcp/issues/280)
- Common discovery failure: MCP server gets the first request but auth server sees no traffic, ending in "Couldn't reach the MCP server." — [Authentication for connectors](https://claude.com/docs/connectors/building/authentication.md)
- Slow token endpoints cause "intermittent connection failures for users." — [same](https://claude.com/docs/connectors/building/authentication.md)
- Community report of custom connector failing after successful authorisation. — [Activepieces community](https://community.activepieces.com/t/claude-ai-custom-mcp-connector-fails-after-successful-activepieces-authorization/11856)
- On Team plans, members see "Request" instead of "Connect" until an Owner adds the connector. **(snippet from search summary, unverified)**

### Inferences
- Main risk is the OAuth setup and Anthropic-side changes we cannot control. Plan for testing on web and phone, and a fallback (a minimal web page) if a Claude change breaks connections.
- Dependency risk: the builder's experience depends on Anthropic's product and pricing, which change often (the help pages changed plan lists between 2025 and 2026).

### Gaps
- Issue details read from search snippets only; status (open/closed) not checked.
- No Reddit threads reviewed.
