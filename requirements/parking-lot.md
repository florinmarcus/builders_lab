# Parking lot: shortcuts, gaps and things not built

Every corner we cut goes here, so nothing is forgotten after the demo. Use it for code, architecture and security reviews.
Update it in the same commit as the shortcut. Remove an item only when it is done, and say where.

Started 20 Nov 2026. Status of the demo build: steps 1 (mock data plan), 2 (schema), 5 (MCP server), security layer and deploy code done; 3, 4 and the first AWS run not yet.

## Not built yet

| # | What | Why parked | Risk if forgotten |
|---|---|---|---|
| N1 | ~~Mock email and PDF generator~~ Done 20 Nov 2026: `system/data/mock/generate.py` | – | – |
| N2 | Gmail loader, reset and live simulator: code done 20 Nov 2026 (`system/data/mock/gmail_demo.py`, tested against a fake Gmail). Not yet run on the real inbox | Needs Florin's Google Cloud client and login | No live "email arrives" moment |
| N3 | `sync_inbox` reads the demo mail folder and, once a Gmail login is stored on the server, the Gmail label too (`MAIL_SOURCE=eml:/data/mail,gmail`). Gmail path written and unit-tested, not yet run against the real inbox | Needs Florin's Google login | Live emails would not reach our tools |
| N4 | ~~`save_facts` with server checks~~ Done 20 Nov 2026 (`service/facts.py`) | – | – |
| N5 | ~~First AWS run~~ Done 20 Nov 2026: stack `builders-lab-prod` up, server installed itself, Let's Encrypt certificate, demo data and Florin's key loaded. Still open: turn on the GitHub deploy step (repository variables) and watch its first run | Repo variables need Florin | Pushes test but do not deploy |
| N6 | OAuth login (Cognito) as the second auth layer (ADR 0007) | API keys first for the demo | One shared secret per firm |
| N7 | ~~App alerts (lockdown, IP blocks) to the email topic.~~ Done 20 Nov 2026: CloudWatch logs (90 days) and alarms for rejected keys, IP blocks, lockdown/alerts, scans and server errors (deploy/README.md). Old text: Budget alarm and server-down alarm are in the CloudFormation template | `security.alert()` only logs | Attacks go unseen |
| N8 | Backups copied off the server's account and region (now: daily dumps on the disk + daily disk snapshots in the same region) | Pilot | Region or account loss loses data |
| N9 | Evals and the Claude Code mini harness (subagents, hooks, LLM judge) | Out of scope for Saturday | No measure of answer quality |
| N10 | Claude Code plugin for testers | After the demo | Manual setup per tester |
| N11 | Data deletion per property and at contract end (design rule 10) | Not needed for mock data | Fails UK GDPR expectations with real data |
| N12 | Machine-readable "AI-generated" marker (design rule 2) | Text notice only for now | Needed if we serve EU users (Art 50) |
| N13 | Romanian answers and AI notice in Romanian (ADR 0001, design rules 1 and 11) | English-first demo | Main audience is Romanian |
| N14 | Evening summary, RAMS module, WhatsApp channel (prototype priorities 2 and 3) | After priority 1 | – |
| N15 | Corpus parser, chunker, `get_section` and `rag.search` (design: `architecture/design/regulations-corpus.md`, ADRs 0010 and 0013) | **Live on the server 20 Nov 2026:** 12 documents in pgvector on RDS, vector search + Amazon Rerank + relevance floor (`backend: corpus`). Not yet: keyword (BM25) on the server (S76), `get_section`, more documents | Fallback set kept for `rag_enabled=off` |
| N16 | Text fingerprint for PDFs, so byte-only changes are not new versions (ADR 0008 update) | Comes with the parser, which extracts PDF text anyway | A re-saved PDF would look like a new edition |

## Shortcuts taken (works, but not production)

| # | Shortcut | Where | What to do later |
|---|---|---|---|
| S1 | Tools use a small seed loaded straight into Postgres, not ingested email | `system/data/mock/db_seed.sql` | Replace with ingestion (N3, N4) |
| S2 | Regulations fallback is 7 passages; no Approved Document A, so the wall question is weak | `regulations_fallback/passages.json` | Connect the corpus session's `rag.search` |
| S3 | `rag.search` contract written by us, not yet confirmed by the corpus session | `system/rag/README.md` | Confirm with the other session |
| S4 | Payment dates count calendar days. To check: the Construction Act may exclude bank holidays, Christmas Day and Good Friday from periods of days (s116, not yet read) | `service/payments.py` | Read s116; add UK bank holidays if needed |
| S5 | Contract payment terms are invented mock values | seed data | Real terms come from the contract document |
| S6 | Required-items checklists are our own mock lists, not legal rules | `required_items` table | Agree real lists with builders |
| S7 | Rate limiter is in memory, per process; resets on restart | `mcp_server/ratelimit.py` | Fine for one server; use Redis or the database if we scale out |
| S8 | Default daily quotas picked by us (500 tool calls, 200 documents, $2 model spend) | `quotas.py`, seed | Set per plan |
| S9 | Each tool call gets its own trace id; calls in one conversation are not linked | `mcp_server/server.py` | Link by session id or harness trace id |
| S10 | Trace rows written in the request path; no OpenTelemetry | `tracing.py` | Move to OpenTelemetry later |
| S11 | Full-text search is English only | `0001_initial.sql` | Add Romanian or `simple` config |
| S12 | Demo inbox is Florin's personal Gmail; Claude's Gmail connector sees the whole inbox | ADR 0005 | Separate inbox or label-only access for real users |
| S13 | Google OAuth app in testing mode; logins may expire after 7 days | ADR 0002 | Recheck before the demo; verification for real users |
| S14 | AI notice is in the tool output; it shows only if Claude repeats it | `mcp_server/server.py` | Check in evals that answers carry it |
| S15 | Claude's own model calls (in the app or Claude Code) have no token or cost rows in our traces | ADR 0006 | Accept, or estimate from the harness |
| S16 | API keys are long-lived; rotation only on leak, staff leaving, or once a year | ADR 0007 | OAuth (N6) gives short-lived tokens |
| S17 | Lockdown and IP blocking are in memory, per process | ADR 0007 | Fine for one server |
| S18 | CI written (`.github/workflows/ci-deploy.yml`) but not yet run on GitHub | `.github/` | Check the first run |
| S20 | Lockdown can be triggered on purpose: many bad keys in a minute pause the service for everyone (a cheap denial of service). Scanner 404s don't count | `security.py` | Put AWS WAF or CloudFront in front; lockdown only as last resort |
| S21 | Prompt injection defence is a notice in tool results plus a server instruction; no filtering of email text | `mcp_server/server.py`, instructions v2 | Add tests with poisoned emails in evals (N9) |
| S22 | ~~App database user had full rights~~ Done 20 Nov 2026: `builders_app` has row rights only (`deploy/db-init/`). Local dev and tests still use one superuser | `deploy/db-init/01-app-role.sh` | – |
| S23 | Demo host name is `<ip>.sslip.io` unless a domain is given; depends on a free outside service | `server.yaml` | Use our own domain |
| S24 | One server, one availability zone; auto-recover only | `server.yaml` | Second server or managed services when customers pay |
| S25 | Images built on the server, not in a registry; the pipeline runs the server's current copy of `upgrade.sh` before it checks out the new version | `upgrade.sh`, `ci-deploy.yml` | Build in GitHub, push to ECR |
| S26 | ~~Server role has no Bedrock rights~~ Template updated 20 Nov 2026 (`server.yaml`: Titan V2 London, Amazon Rerank Frankfurt, hop limit 2); applied with the next stack update | `server.yaml` | – |
| S27 | Upgrade rollback restores the whole database from the pre-upgrade dump; writes made during the failed minute are lost | `upgrade.sh` | Acceptable for the pilot |
| S45 | Server-down alarm only emails; auto-recover was dropped (needs a service-linked role the deploy user may not create) | `server.yaml` | Allow `iam:CreateServiceLinkedRole` for CloudWatch Events, then add the recover action back |
| S46 | Server disk survives stack deletion (`DeleteOnTermination: false`); a failed first create leaves an orphan disk to delete by hand | `server.yaml` | Keep for data safety; check for orphan volumes after failed creates |
| S47 | Deploy user `builders-claude` holds a long-lived access key with the deploy policy | IAM | Remove the key after setup, or move to SSO / short-lived credentials |
| S31 | Connector path secret was shown in a screenshot in chat (20 Nov 2026); the key was not | Parameter Store | Rotate the path secret (new value, restart, update the connector URL) |
| S32 | Every push to main deploys (we work straight on main for now) | `ci-deploy.yml` | After the demo: work on branches with pull requests (tests on the PR), deploy only on version tags |
| S33 | Reset moves demo emails to Gmail Trash (kept 30 days), not permanent delete: permanent delete needs the full mail scope | `gmail_demo.py` | Fine for the demo |
| S34 | Simulator polls Gmail every 10 seconds from the laptop | `gmail_demo.py` | Gmail push notifications (Pub/Sub) if it becomes a product feature |
| S35 | ~~Some HSG227 figure crops shifted (figures 3, 5, 6, 9)~~ Done 20 Nov 2026: `photo_box` finds the photo's own pixels above its caption, inside the image box; HSG264 crops also got tighter. Figures with nothing drawn above the caption keep the image box | `system/rag/parse_pdf.py` | – |
| S36 | ~~HSG227 worked-example tables in two layouts~~ Done 20 Nov 2026: tables 9-14 converted by a script to the tables 4-8 layout (Sub-factor column, overall score once per factor, as printed), sentences rebuilt the same way | `corpus/fixes/hse-hsg227.json` | – |
| S37 | Job filing is plain word matching plus sender history; Claude can override with save_facts | `service/ingest.py` | Fine for small firms; review with real email |
| S38 | Contract payment terms come only from the seed, not from ingested contract documents | `db_seed.sql` | Add a contract_terms step to save_facts |
| S39 | Model checks: the session starts the subagents and collects their replies into answers.jsonl by hand, following the runbook; no script does it | `.claude/skills/corpus-document/SKILL.md` | Script the loop with the Agent SDK if hand runs drift or it gets slow |
| S40 | AD B diagram images are `images: check-only` because the source note says "third-party images; ingest text only" (a guess from the inventory). Not checked against the document's own copyright page | `corpus/sources.yaml` | Read AD B's copyright notice; switch to `show` if Crown copyright under OGL |
| S41 | AD B letter repair only works when the whole word appears at least 3 times in the same document; a few words stay broken (e.g. "Roofng", "infll") | `system/rag/parse_adoc.py` `_ligatures` | Add a shared word list from all parsed documents |
| S42 | AD B Appendices F and G (standards and documents referred to) are kept as text blocks under their headings, not one record per standard | `system/rag/parse_adoc.py` | Split per entry if evals ask "which standard covers X" |
| S43 | Only AD B volume 1 is parsed; volume 2 and the amendment booklets are not | `corpus/sources.yaml` `parser.parts` | Parse volume 2 with the same parser when needed |
| S44 | 6 AD B volume 1 model-check fixes are medium confidence: requirement boxes B2, B4 (boxes 2 and 3), B5, and the 2029 copies of Tables B1 and C1 (long tables with templates) | `corpus/fixes/adb.json` | A person checks these six against the PDF before the demo; redo with `checks` if wrong |
| S48 | Plugin skeleton built 20 Nov 2026 (`plugin/`, validates). Not yet tried: installing it, `${BUILDERS_API_KEY}` expansion in the plugin's connector headers, and whether plugins work in the Claude phone app | `plugin/` | Install in Claude Code and Cowork, run the six phrases |
| S49 | Plugin has no icon, privacy policy URL or licence file (needed only to list it in Anthropic's directory) | `plugin/` | Add before any public listing |
| S50 | Skill files are not under the version lock yet (tool descriptions are) | `plugin/skills/` | Extend `builders_api.versions` or version the plugin on every skill change |
| S51 | Specialist tool limits are written in each agent's instructions, not enforced with a `tools:` list (plugin tool names not yet confirmed) | `plugin/agents/` | Confirm plugin MCP tool names, then add `tools:` to each agent |
| S52 | `model: haiku` for sub-agents is a Claude Code setting; not checked in Cowork | `plugin/agents/` | Check in Cowork |
| S53 | verify_answer checks numbers and quotes, not meaning: a true quote can still be used for a wrong claim | `service/verify.py` | Evals with an LLM judge (N9) |
| S54 | ~~Agent contract JSON only in prose~~ Done 20 Nov 2026: `contracts.py` is the source, schema generated, examples tested | – | – |
| S55 | Rules text exists three times (MCP server instructions, plugin rules, Claude app project instructions) | `versions/server/`, `plugin/shared/rules.md`, `plugin/claude-app/` | One source file; build or check the others from it |
| S56 | 45 of 193 Building Regulations definitions are cut at "means—" in the parsed tree (their list is lost); the chunker takes the full text from regulation 2 instead | `system/rag/parse_legislation.py` | Fix the definition reader so the tree has the full text |
| S57 | Cross-references are found by a fixed list of patterns (paragraph, Diagram, Table, Figure, Section, Appendix, regulation, requirement); other forms are missed. References to another document (AD B to the Building Regulations) are kept but not checked | `system/rag/chunk.py` | Check them once both documents are loaded together; add patterns when evals show misses |
| S58 | Whole-table chunks can be long (up to about 6,500 characters for AD B Table B1); split rule is 2,500 characters for regulations and paragraphs only | `system/rag/chunk.py` | Revisit when the embedding model is chosen |
| S59 | Only regulation 2's definitions get their own chunks; terms defined in other regulations are found inside those regulations' chunks | `system/rag/chunk.py` | Add if evals ask for them |
| S60 | Glossary rows mostly "unverified", incl. 12 added for the demo; Romanian word-ending match is simple | `research/domain/glossary.md`, `terminology/` | Native-speaker tradesperson review; collect real phrasing at the event |
| S61 | Speak-first chunking is instructions only; nothing checks chunk length | rules, workflow, server instructions v3 | Eval for spoken style (N9) |
| S62 | Gmail token on the server is a long-lived refresh token in Parameter Store and a file readable by the app user; testing-mode logins can expire after 7 days | `env-from-ssm.sh`, compose | Move to a verified Google app or forwarding (ADR 0002 fallback) for real users |
| S63 | HSE L143 (asbestos ACoP) and the EM1 task sheet are not parsed: L143's 600+ numbered paragraphs stop at 20, its ACoP text in shaded boxes is read as notes, and small text is taken for tables. Margin labels (Regulation / ACOP / Guidance) are already read and give each passage its own legal weight | `system/rag/parse_pdf.py` | Fix the L143 layout with tests, then run its model checks |
| S64 | Act sections (Construction Act) are found by the chunker's "regulation" pattern only; references written as "section 110A" are not linked | `system/rag/chunk.py` | Add a "section N" pattern for Acts |
| S65 | ~~Hybrid search local only~~ Done 20 Nov 2026: the server searches the RDS corpus (pgvector + re-rank); the local SQLite index stays for building and testing | `system/rag/pgsearch.py` | – |
| S66 | HTML parser: GOV.UK "example" and "call-to-action" boxes are plain text, not notes; `<dl>` definitions are not read; numbered headings whose text sits under h4 headings (CIS 340 para 1.12) get no chunk of their own | `system/rag/parse_html.py` | Fix if evals need them |
| S67 | Internal firm id (slug) is still `oakline`; only the shown name is Marcus Limited | `db_seed.sql`, tests | Rename the slug with a data migration when convenient |
| S68 | The owner persona uses Florin's real name at his request; everything else is invented | `system/data/mock/` | Keep in mind before sharing the repo or recordings |
| S69 | Calendar actions run through Claude's Google Calendar connector; not yet tried end to end, nor the `calendar` reset against a real account | `plugin/`, `gmail_demo.py` | Try after the Google login |
| S70 | Delays advice rests on the mock council call-off terms; real contracts vary and this is not legal advice | `scenario.py` a21, `plugin/agents/delays.md` | Review with a builder and a construction adviser |
| S71 | No AI notice on answers (removed 20 Nov 2026 at Florin's request). UK: no legal duty. EU AI Act Art 50 needs a notice at first use if we serve users in the EU (Romania) | rules, server instructions v4, `verify.py` | Add a first-use notice before any EU launch (`research/domain/ai-regulation.md`) |
| S72 | The app container carries the database owner's URL (`MIGRATE_DATABASE_URL`) because migrations run from it; the running app needs only `builders_app`. Not least privilege (raised by Florin 20 Nov 2026) | `deploy/compose.yaml`, `builders_api/db/migrate.py` | Run migrations as a one-off step and keep the owner URL out of the app's environment |
| S73 | The regulations corpus database shares the lab's RDS instance (`rag-lab-db`, Frankfurt): the lab's `pause`/`down` stop or delete it too; no backups (rebuild from Git) | `deploy/rds/README.md` | Own instance or RDS backups when customers depend on it |
| S74 | The loader's database test needs Postgres with pgvector; CI's Postgres has none, so it skips there | `tests/test_load.py` | Use a pgvector image in CI |
| S75 | The GitHub repository is public (Florin's choice, 20 Nov 2026). Scan that day: no keys or tokens, MCP path secret not in any file or commit, no raw or restricted documents (4 restricted sources are catalogue entries only). Anyone can read how the server is built and protected | GitHub repository settings | Keep secrets in Parameter Store only; make private before restricted documents or real customer data come near the repo |
| S76 | Server search is vector + re-rank only; keyword (BM25) is postponed (Florin, 20 Nov 2026). The corpus tables already hold the BM25 data | `system/rag/pgsearch.py` | Add BM25 candidates and RRF when evals show code-style questions missing |
| S77 | Relevance floor is a guess: re-rank score 0.05. "Does the survey cover this room" keeps only 1 passage (the right one) | `RAG_MIN_SCORE` | Calibrate with the builder test questions |
| S78 | The server drops `legal_weight` and `printed_page` from passages, so answers cannot say law vs guidance from the search result | `system/api/builders_api/service/regulations.py` | Pass them through (server session) |
| S79 | Awaab's Law phase 2: the amending regulations are loaded but their title never says "Awaab", so "what does phase 2 add" finds only phase 1 guidance. The phase 2 guidance pages (`awaab-guidance-phase2`, `awaab-triage-phase2`) are harvested but not parsed | `corpus/sources.yaml` | Add `parser: {module: parse_html}` to both and rebuild |
| S80 | Amending instruments are findable from the day they were made; their in-force date is kept in the chunk (`in_force`) but the server does not show it yet (only regulation 1's own text says it) | `system/rag/chunk.py`, `pgsearch.py` | Show "in force from" as the passage's edition note |
| S81 | Plugin slash commands use the legacy `commands/` format (installed fine in the Claude app on 20 Nov 2026, with a warning) | `plugin/commands/` | Migrate each command to `skills/<name>/SKILL.md` |
| S19 | Cost figures are first-pass, partly guesses, mostly US prices | `research/hosting-costs/connector-auth-options.md` | Review in detail; check London prices |
| S28 | Postgres runs in Docker on the one server; no managed database, no read replica (raised by Florin 20 Nov 2026) | ADR 0009 | RDS, or a writer plus at least one reader, when traffic or customers need it |
| S29 | 17 raw corpus files missing: the source now gives different bytes, so they were not restored (16 same size, legislation metadata order) | `corpus/harvest-report.md` | Decide: keep today's bytes with a note in the record, or fetch when evals need them |
| S30 | Old Approved Document B editions all carry valid_from 2025-01-14 (GOV.UK page date), so their dates are unusable | `corpus/versions/adb-historical/` | Set real edition dates before any "rules on date X" answer uses them |

## Open questions

| # | Question | Where it came from |
|---|---|---|
| Q1 | Can a Claude app connector send a header API key and use OAuth at the same time? | ADR 0007 |
| Q2 | Does the Claude app have hooks? None found (20 Nov 2026) | `research/hosting-costs/connector-auth-options.md` |
| Q3 | Can a connector reach files on an iPhone? | `research/backlog.md` item 12 |
| Q5 | ~~Which header does the Claude app accept?~~ Answered 20 Nov 2026: `Authorization` works with Authentication set to "No sign-in". The server also accepts the key without "Bearer" or without the space | ADR 0007 |
| Q4 | Is a Claude Code scheduled task reliable enough for regular inbox syncs, or do we need Haiku on the server? | ADR 0006 |
