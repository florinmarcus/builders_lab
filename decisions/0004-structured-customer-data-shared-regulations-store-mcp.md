# 0004: Customer data as structured records, shared regulations in a vector store, MCP as the interface

Date: 19 Nov 2026. Status: accepted.

## Context

We don't replace the builder's tools; we make them work together (`research/directions.md`). Builders want one place to talk to, not new screens. In the first year, customers are small and medium firms with a few hundred documents each. Shared guidance (building regulations, HSE asbestos and CDM guidance, HMRC CIS) is the same for everyone and mostly under the Open Government Licence.

## Decision

- **Interface:** an AI client (Claude or ChatGPT) talking to our backend through an **MCP server**. Our own small web page stays possible as a fallback and for the demo.
- **Customer data:** no per-customer vector store at first. Extract key facts once (property or job, date, document type, asbestos items) into **structured records**. To answer, select the right documents by metadata and let the model read them whole.
- **Shared knowledge:** one **vector store for regulations and methods**, built once and shared. **Hybrid search** (meaning + keywords), because users ask for clause and document names.
- **Connectors behind the MCP server:** email first, then WhatsApp, Xero or QuickBooks, documents. Stored in our own UK storage, not in GitHub.
- **GitHub + Claude Code:** fine for the prototype and for Florin; not for real client data (developer tool, extra US sub-processor, binary files).

## Options considered

- Per-customer vector store from day one: more moving parts for small data sets.
- GitHub repo per client as storage, used through Claude Code: cheap, but not usable by most builders and hard to approve for council data.
- Own chat web app only: more UI to build; see `research/hosting-costs/claude-app-vs-bedrock.md`.

## Consequences

- Real council data through Claude or ChatGPT needs a business plan with a DPA (Team, Enterprise or equivalent), or our own page on Bedrock (`research/reports/Claude app vs Bedrock costs.md`).
- Add a per-customer vector store if a customer reaches thousands of documents. Keep the storage layer able to take it.
