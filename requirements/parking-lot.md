# Parking lot: shortcuts, gaps and things not built

Every corner we cut goes here, so nothing is forgotten after the demo. Use it for code, architecture and security reviews.
Update it in the same commit as the shortcut. Remove an item only when it is done, and say where.

Started 20 Nov 2026. Status of the demo build: steps 1 (mock data plan), 2 (schema), 5 (MCP server), security layer and deploy code done; 3, 4 and the first AWS run not yet.

## Not built yet

| # | What | Why parked | Risk if forgotten |
|---|---|---|---|
| N1 | ~~Mock email and PDF generator~~ Done 20 Nov 2026: `system/data/mock/generate.py` | – | – |
| N2 | Gmail loader, reset and live simulator: code done 20 Nov 2026 (`system/data/mock/gmail_demo.py`, tested against a fake Gmail). Not yet run on the real inbox | Needs Florin's Google Cloud client and login | No live "email arrives" moment |
| N3 | `sync_inbox` built 20 Nov 2026 with the demo mail folder (`MAIL_SOURCE=eml:`). Gmail source written but not yet run: needs a Gmail login stored on the server | Needs Florin's Google login | Demo uses the folder feed, not the real inbox |
| N4 | ~~`save_facts` with server checks~~ Done 20 Nov 2026 (`service/facts.py`) | – | – |
| N5 | ~~First AWS run~~ Done 20 Nov 2026: stack `builders-lab-prod` up, server installed itself, Let's Encrypt certificate, demo data and Florin's key loaded. Still open: turn on the GitHub deploy step (repository variables) and watch its first run | Repo variables need Florin | Pushes test but do not deploy |
| N6 | OAuth login (Cognito) as the second auth layer (ADR 0007) | API keys first for the demo | One shared secret per firm |
| N7 | App alerts (lockdown, IP blocks) to the email topic. Budget alarm and server-down alarm are in the CloudFormation template | `security.alert()` only logs | Attacks go unseen |
| N8 | Backups copied off the server's account and region (now: daily dumps on the disk + daily disk snapshots in the same region) | Pilot | Region or account loss loses data |
| N9 | Evals and the Claude Code mini harness (subagents, hooks, LLM judge) | Out of scope for Saturday | No measure of answer quality |
| N10 | Claude Code plugin for testers | After the demo | Manual setup per tester |
| N11 | Data deletion per property and at contract end (design rule 10) | Not needed for mock data | Fails UK GDPR expectations with real data |
| N12 | Machine-readable "AI-generated" marker (design rule 2) | Text notice only for now | Needed if we serve EU users (Art 50) |
| N13 | Romanian answers and AI notice in Romanian (ADR 0001, design rules 1 and 11) | English-first demo | Main audience is Romanian |
| N14 | Evening summary, RAMS module, WhatsApp channel (prototype priorities 2 and 3) | After priority 1 | – |
| N15 | Corpus parser, chunker, `get_section` and `rag.search` (design: `architecture/design/regulations-corpus.md`, ADR 0010) | Design agreed 20 Nov 2026; pilot next | Server stays on the 7-passage fallback |
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
| S26 | Server role has no Bedrock or S3 rights yet (corpus embedder, re-ranker and files) | `server.yaml` | Add narrow rights when the corpus is wired in |
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
