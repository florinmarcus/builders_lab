# WhatsApp: what Claude can reach (checked 26 Nov 2026)

Why: builders send each other messages and documents on WhatsApp. Robert's firm uses Claude Team. Parked as N23.
Sources are vendor guides unless marked Meta or OpenAI; figures change often, so check again before building.

## Short answer

- **No official route reads existing chats**, for Claude or ChatGPT.
- ChatGPT on WhatsApp ended on 15 Jan 2026 after Meta banned general-purpose AI assistants from the WhatsApp
  Business API (OpenAI, TechRadar). Firms using AI for their own customer service are still allowed.
- No official WhatsApp connector for Claude (eesel). Third-party MCP connectors exist (Wati, Wassenger, Composio,
  2Chat). On Team plans an owner must enable a custom connector first (Composio).
- Unofficial bridges (QR code, WhatsApp Web) can read chats, but WhatsApp says linking unofficial apps can get the
  number banned (EnrichLabs). Not for a firm's main number.
- Safe today: WhatsApp's own "Export chat" (text, optionally photos and documents), dropped into Claude by hand.
  The variation skill already reads chat exports.

## The official WhatsApp Business API (Cloud API)

Only sees new messages sent to a business number set up for it. Cannot read existing chats or crew groups.

Test setup (Meta get-started page):
1. Meta developer account, a business portfolio and a Meta app with the WhatsApp use case. All free.
2. Meta creates a test business number automatically.
3. Add your phone as a recipient, send a test message, reply to open the 24-hour window.
4. Permanent token from a system user; webhook on our server for incoming messages.

Not stated by Meta, from guides: up to 5 recipient numbers on the test number (Expertflow, respond.io); one guide
says the test number lasts 30 days (Wati, not confirmed).

Real number (Meta phone numbers page): owned by you, not already on WhatsApp (delete it first), verified by SMS or
voice, display name and PIN. New portfolios are capped at 2 numbers; 20 after business verification.

Business verification (guides): 10 minutes to 14 working days; needs an official document with the legal name and
address that match the profile; scans and screenshots are refused. One provider says it has not been needed to
message customers since Nov 2023. Not needed for a test.

Cost, UK, from 1 Oct 2026 (guides disagree slightly): first 1,000 service messages per number a month free, then
about £0.016; utility about £0.016; marketing about £0.046 per message. A test costs nothing.

## Questions for the firms

- Personal phones or the WhatsApp Business app?
- Which groups matter: client, crew, subcontractors?
- Which documents arrive by WhatsApp, and are they saved anywhere after?
- Would they forward the important ones to email or a shared folder, if that made the AI work?

## Sources

- Meta, Cloud API get started: https://developers.facebook.com/documentation/business-messaging/whatsapp/get-started
- Meta, business phone numbers: https://developers.facebook.com/documentation/business-messaging/whatsapp/business-phone-numbers/phone-numbers
- OpenAI, ChatGPT on WhatsApp ending: https://openai.com/index/chatgpt-whatsapp-transition/
- TechRadar, Meta bans rival AI chatbots: https://techradar.com/ai-platforms-assistants/meta-will-ban-rival-ai-chatbots-from-whatsapp
- respond.io, 2026 AI policy: https://respond.io/blog/whatsapp-general-purpose-chatbots-ban
- respond.io, Cloud API: https://respond.io/help/whatsapp/whatsapp-cloud-api
- eesel, WhatsApp Claude connector: https://www.eesel.ai/blog/whatsapp-claude-connector
- Composio, WhatsApp MCP: https://composio.dev/content/whatsapp-mcp-connect-your-ai-to-whatsapp-without-the-risky-bridge
- EnrichLabs, WhatsApp MCP 2026: https://www.enrichlabs.ai/blog/whatsapp-mcp
- Expertflow, Cloud API setup: https://docs.expertflow.com/cx/4.5/meta-whatsapp-cloud-api-configuration-deployment-g
- Wati, test sends: https://www.wati.io/en/blog/test-whatsapp-message-sends-safely/
- Wati, business verification: https://support.wati.io/en/articles/11462440-meta-business-verification-step-by-step-guide
- 360dialog, business verification: https://docs.360dialog.com/docs/waba-management/meta-business-verification
- menuthere, UK pricing: https://menuthere.com/en-gb/whatsapp-business-api-pricing-uk
- Blueticks, pricing 2026: https://blueticks.co/blog/whatsapp-business-api-pricing-2026
