# Decisions (ADRs)

One file per decision: `NNNN-short-title.md` with context, decision, options considered and consequences.

Rules (ADR 0020): an accepted ADR is not rewritten. A change is a new ADR, and the old one gets one header line,
"Changed by: NNNN". Older ADRs also hold dated notes from before this rule; they stay as history. Status and live
figures belong in the designs, not here.

| ADR | Decision | Status | Changed by |
|---|---|---|---|
| [0001](0001-romanian-chat-over-english-sources.md) | Romanian chat over English sources | accepted | 0012, 0019 |
| [0002](0002-read-gmail-api-with-mock-council-sender.md) | Read Gmail through the API, mock council sender | accepted, mostly replaced | 0005, 0014 |
| [0003](0003-aws-bedrock-small-server-pilot.md) | AWS, one small server for the pilot | accepted, mostly replaced | 0007, 0009 |
| [0004](0004-structured-customer-data-shared-regulations-store-mcp.md) | Firm data as records, shared regulations store, MCP as the interface | accepted | 0015 |
| [0005](0005-demo-inbox-and-email-simulator.md) | Demo inbox: own Gmail, a label, an email simulator | accepted for the demo | – |
| [0006](0006-agents-in-claude-extraction-by-claude.md) | Agents live in Claude; no model on our server | accepted | 0011, 0017, 0019 |
| [0007](0007-mcp-server-security.md) | Server security: API keys now, OAuth next | accepted | 0015 |
| [0008](0008-regulations-corpus-harvesting-and-storage.md) | Corpus harvesting: versions, raw files in S3 | accepted | 0016 |
| [0009](0009-ec2-server-with-cloudformation-and-scripted-upgrades.md) | One EC2 server, CloudFormation, scripted upgrades | accepted | 0015 |
| [0010](0010-parsing-library-first-model-checks.md) | Parsing: library first, model checks, chunk by structure | accepted | 0013, 0018 (proposed) |
| [0011](0011-package-as-claude-plugin.md) | Package as a Claude plugin | accepted | 0015, 0019 |
| [0012](0012-language-and-voice.md) | Language and voice: user's language, English to the tools, speak first | accepted | – |
| [0013](0013-hybrid-search-vectors-keywords-rerank.md) | Hybrid search: vectors, BM25, re-rank | accepted | 0014, 0016 |
| [0014](0014-pilot-business-model.md) | Pilot business model | accepted | – |
| [0015](0015-two-mcp-servers-regulations-and-firm.md) | Two MCP servers: regulations and firm | accepted, built | – |
| [0016](0016-retrieval-strategy-lanes-measure-first.md) | Retrieval: measure first, four lanes, complete recall | accepted, partly built | – |
| [0017](0017-workflow-control-on-server-no-agent-runtime.md) | Workflow control on our server; no agent runtime | accepted, not built | – |
| [0018](0018-parse-profiles-per-document-family.md) | Parse profiles per document family | proposed | – |
| [0019](0019-main-model-does-the-work-skills-not-sub-agents.md) | The main model does the work; skills, not sub-agents | accepted, built | – |
| [0020](0020-docs-structure-one-source-of-truth.md) | Docs structure, one source of truth | accepted | – |
| [0021](0021-answer-judge-design.md) | Answer judge: search plus Sonnet, pass or fail per criterion, judge chosen by human labels | accepted | – |

Next free number: 0021.
