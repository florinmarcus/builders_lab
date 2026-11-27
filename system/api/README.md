# API (Python)

MCP server, service layer and ingestion for the demo, in one package: `builders_api`.

## Set up

```
pip install -e ".[dev]"            # from the repo root
cp .env.example .env               # set DATABASE_URL, then export the values
python -m builders_api.db.migrate  # create or update tables; safe to re-run
python -m builders_api.db.seed     # small mock seed (system/data/mock/db_seed.sql); re-runnable
python -m builders_api.mcp_server  # MCP server on http://HOST:PORT/mcp (streamable HTTP)
```

## Layout

- `db/`: connection pool, migrations (never edit an applied file; add the next number), seed loader.
- `service/`: the logic. `jobs.py` (list, get, missing items), `documents.py` (Postgres full-text search),
  `payments.py` (payment notice dates from contract terms), `regulations.py` (corpus contract or fallback),
  `inbox.py` (sync), `ingest.py` and `mail_sources.py` (parse, file, store), `facts.py` (save_facts), `verify.py` (verify_answer).
- `mcp_server/`: two MCP servers over the service layer, firm and regulations, one process (ADR 0015). Uses the official MCP SDK's `MCPServer` (FastMCP's successor in SDK 2.x).
  Every tool call: daily quota, one trace row, structured error. Rate limit per client on the HTTP endpoint.
- `versions/`: server instructions, tool descriptions and prompts as `<name>.v<N>.md`. Highest N is active.
  Never edit a committed file: add a new version, then `python -m builders_api.versions --lock`.
  The server refuses to start if a locked file changed. The version id goes into every trace row.
- `errors.py`: typed errors. `retry.py`: backoff with jitter, only for retryable errors.
- `tracing.py`: one row per tool or model call in `traces`. `quotas.py`: daily limits per firm.

## Tools

Firm server at `/mcp/<secret>`, regulations server at `/mcp/<secret>/regulations` (ADR 0015).

| Tool | Server | Demo moment |
|---|---|---|
| `list_jobs` | firm | 1: what came in, filed by job |
| `get_job` | firm | 2: approvals with quotes; any job question |
| `search_job_documents` | firm | 2: find an email or document |
| `list_missing_items` | firm | 3: what's missing (incl. expired insurance) |
| `search_regulations` | regulations | 4, 7: rules with section and edition date |
| `get_payment_dates` | firm | 7: payment notice deadlines |
| `sync_inbox` | firm | 1: fetch new email from the mail source, store, file by job, hand over emails needing facts |
| `save_facts` | firm | 1: record job, document types and facts for one email (server-checked) |
| `verify_answer` | firm | all: deterministic checks on a draft answer (`architecture/design/runtime/design.md`, contracts) |
| `lookup_terms` | both | Romanian questions: glossary lookup (`terminology/`, ADR 0012) |
| `about_regulations_library` | regulations | what the library holds: version loaded, documents by type, gaps and why, quality (S100). `part`: summary, contents, gaps |
| `get_firm_profile` | firm | start of a conversation: who we are, jobs, contacts, what is due |
| `get_job_timeline` | firm | delays, "what have I sent?": everything on a job in date order |
| `show_today` | firm | "show me today": jobs by days left, due jobs, emails of the last 7 days; opens a card in the chat (MCP Apps, `mcp_server/ui/today.html`), plain data elsewhere |

## Security (ADR 0007)

- `mcp_server/gateway.py` runs before the MCP layer: `/healthz`, kill switch, lockdown, IP block, rate limits,
  secret paths (`/mcp/<MCP_PATH_SECRET>` and `/mcp/<MCP_PATH_SECRET>/regulations`, anything else is 404), API key (`Authorization: Bearer` or `X-API-Key`).
- The key decides the firm. Expiring keys add a plain `access_notice`; ended keys get a plain `access_ended` message.
- Admin commands (on the server):

```
python -m builders_api.admin keys create --firm oakline --label "Florin, Claude app" --expires 2026-12-31
python -m builders_api.admin keys list
python -m builders_api.admin keys extend --prefix <prefix> --expires 2027-01-31   # renewal, same key
python -m builders_api.admin keys revoke --prefix <prefix>
python -m builders_api.admin kill on|off|status                                  # manual off switch
```

## Tests

`TEST_DATABASE_URL=postgresql://... pytest` (that database is wiped). Includes an end-to-end test that starts the
server over HTTP and calls tools with an MCP client.
