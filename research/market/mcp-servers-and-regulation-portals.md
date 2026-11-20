# MCP servers and regulation portals for builders (other than ours)

Checked 20 Nov 2026. Sources are listed at the end and in `research/sources/links.md`. Listings in MCP registries are written by their authors, so treat them as self-description. Star counts and dates come from the GitHub and PyPI APIs on 20 Nov 2026. Earlier regulation chatbots (StructureGPT, BuildingRegs.app, Struck, ArchiChat, Regulex, Buildwell AI, para-building-regs, Planner AI) are in `existing-solutions.md` and not repeated here.

## Short version

- **No MCP server for UK building regulations is in a usable state, and none is in Claude's connector directory.** The one we found is a hobby project (0 stars, local only, "not recommended for production", last change Nov 2025). It searches one PDF of the Approved Documents (Oct 2024): no legislation, no HSE guidance, no versions or dates, no England/Wales split.
- **UK legislation already has MCP servers, including one from government:** the Incubator for AI (i.AI) runs **Lex**, an experimental, free, open-access MCP endpoint over Acts and Statutory Instruments (data from legislation.gov.uk, OGL; code MIT). It has no Approved Documents and no HSE guidance. Open-source alternatives: uk-legal-mcp (active, hosted endpoint), Openlaw MCP, GovUK MCP.
- **Building-code MCP servers exist in other countries:** Canada (16 codes, a structural index; full text needs your own PDFs), Spain (Normatia, hosted), Turkey (mimari.ai), US municipal codes (Muni, paid).
- **Regulation chatbots for builders keep appearing as websites, not as MCP servers:** My Research.ai (cited answers over Approved Documents A–S and the Welsh, Scottish and Northern Irish rules) is new to our list; BuildwellAI turned its chatbot into a "compliance intelligence platform" (July 2026). Neither says it offers an MCP server or API.

**What this means for us (our reading, not a source):** what we combine is still not offered in one place: Approved Documents, legislation with dated versions and Wales/England marks, HSE asbestos guidance with model-checked tables, all in Claude through one connector, together with the builder's own job data. Lex could be a free fallback or cross-check for legislation text; it does not cover the guidance builders ask about most.

## UK: building regulations

| Name | What it is | State | Source |
|---|---|---|---|
| uk-building-code-mcp (LeoRickayzen) | MCP server: semantic search and page lookup over the Merged Approved Documents PDF (Oct 2024), which you supply locally. ChromaDB vectors. | Local only (stdio or localhost). "Under heavy development", "not recommended for production use". GitHub: 0 stars, created 24 Oct 2025, last push 9 Nov 2025, no licence. LobeHub: 13 installs. | [LobeHub](https://lobehub.com/mcp/leorickayzen-uk-building-code-mcp), [GitHub](https://github.com/LeoRickayzen/uk-building-code-mcp) |
| para-building-regs (valtomas) | Open-source local tool for England's rules (already in `existing-solutions.md`). | GitHub: 0 stars, created 3 Nov 2026, last push 20 Nov 2026, AGPL-3.0. Not an MCP server as far as its listing shows. | [GitHub](https://github.com/valtomas/para-building-regs) |

## UK: legislation (Acts and SIs, not Approved Documents)

| Name | What it is | State | Source |
|---|---|---|---|
| Lex (i.AI) | Legal API and MCP endpoint over Acts, SIs, sections, explanatory notes and amendments; data from legislation.gov.uk, complete from 1963. MCP at `https://lex.lab.i.ai.gov.uk/mcp`; also a REST search API and a "Lex UK Law" skill. | Labelled an experiment, "for research and non-production use". Free, no key; 60 requests a minute and 1,000 an hour per IP. Data OGL v3.0, code MIT (`github.com/i-dot-ai/lex`). Some PDF-sourced texts are LLM transcriptions, "not independently verified". | [Lex](https://lex.lab.i.ai.gov.uk) |
| uk-legal-mcp (paulieb89) | Case law, legislation, Parliament, bills, votes, committees, citations, HMRC. | Version 0.11.2, last upload 19 Nov 2026 (active). Hosted endpoint `uk-legal-mcp.fly.dev/mcp` or local. Its docs say legislation.gov.uk's firewall sometimes blocks the hosted server (search snippet). | [PyPI](https://pypi.org/project/uk-legal-mcp/), [GitHub](https://github.com/paulieb89/uk-legal-mcp) |
| Openlaw MCP (damankaur-dev) | UK and EU open law, with a point-in-time lookup of UK statute sections (search snippet). | 6 stars, Apache-2.0, last push 28 May 2026. | [GitHub](https://github.com/damankaur-dev/openlaw-mcp), [listing](https://mcpservers.org/servers/damankaur-dev/openlaw-mcp) |
| GovUK MCP (Stealth Labs) | 27 GOV.UK data sources, one of them legislation. | 3 stars, no licence, last push 14 Nov 2026. | [GitHub](https://github.com/Stealth-Labs-LTD/GovUK-MCP) |

## UK: other construction MCP servers (not regulations)

- **construction-iso-19650-mcp:** checks BIM information-management documents (EIR, BEP, MIDP, TIDP, CDE) against ISO 19650. [PyPI](https://pypi.org/project/construction_iso_19650_mcp/)
- **Procore MCP server (community):** Procore's compliance-document tools are contractor paperwork (bonds, licences, insurance), not building regulations. [Glama](https://glama.ai/mcp/servers/TylerIlunga/procore-mcp-server/tools/show_compliance_documents_for_a_contract_project)
- Nothing found for HSE guidance or asbestos (search, 20 Nov 2026).

## Other countries: building-code MCP servers

| Name | Country | Notes | Source |
|---|---|---|---|
| building-code-mcp / Canada-AEC-Code-MCP | Canada | 16 codes and guides, 22,500+ indexed sections (listing). A structural index: no copyrighted text is distributed; full text needs your own PDFs. Hosted demo is "map-only". | [PyPI](https://pypi.org/project/building-code-mcp/), [Glama](https://glama.ai/mcp/servers/@DavidCho1999/Canada-AEC-Code-MCP) |
| Normatia | Spain | Hosted MCP for architecture, engineering and construction rules (`mcp.normatia.com/mcp`). | [mcpservers.org](https://mcpservers.org/servers/normatia/normatia) |
| mimari.ai MCP | Turkey | Turkish building regulations and standards; remote endpoint or pip install. | [PyPI](https://pypi.org/project/mimari-ai-mcp/) |
| Muni | United States | Municipal codes through the Municode API; premium (listing). | [MCP Market](https://mcpmarket.com/server/muni) |

## UK regulation portals (websites) new since 7 Nov 2026

| Name | What it claims | Pricing | Source |
|---|---|---|---|
| My Research.ai (MY-RESEARCH.AI LTD) | "Cited responses from official government documents": Approved Documents A–S, Welsh guidance, Scottish Technical Handbooks, Northern Ireland. Mentions an API in its menu (not read). Page says © 2025; hosted on pages.dev. | Not on the page read ("Get started for free" link) | [site](https://my-research-marketing.pages.dev/uk/building-regulations) |
| BuildwellAI (update) | Launched a "compliance intelligence platform" on 8 Jul 2026: five apps (defect video, photo inspection, golden-thread records, technical chat, regulatory news). Which regulations it covers is not stated. | Not stated | [IT Brief](https://itbrief.co.uk/story/buildwellai-launches-compliance-platform-for-uk-construction) |
| Government | i.AI's "Extract" helps planning officers (planning, not building regulations). No government chatbot for building regulations found. | – | [GOV.UK](https://gov.uk/government/news/faster-planning-decisions-as-new-rules-and-ai-tackle-delays) |

## Not checked

- My Research.ai pricing and API pages; uk-legal-mcp's README (PyPI page blocked automated reading; facts above come from the PyPI JSON API and search snippets).
- Whether Lex is reliable enough to use as a fallback in a demo (experimental service, rate-limited per IP).
- Smaller registries (Smithery, PulseMCP, mcp.so) were not searched one by one; Claude's connector directory search found no building-regulation connector.
