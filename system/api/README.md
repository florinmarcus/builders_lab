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
  `inbox.py` (sync, step 4).
- `mcp_server/`: tools over the service layer. Uses the official MCP SDK's `MCPServer` (FastMCP's successor in SDK 2.x).
  Every tool call: daily quota, one trace row, structured error. Rate limit per client on the HTTP endpoint.
- `versions/`: server instructions, tool descriptions and prompts as `<name>.v<N>.md`. Highest N is active.
  Never edit a committed file: add a new version, then `python -m builders_api.versions --lock`.
  The server refuses to start if a locked file changed. The version id goes into every trace row.
- `errors.py`: typed errors. `retry.py`: backoff with jitter, only for retryable errors.
- `tracing.py`: one row per tool or model call in `traces`. `quotas.py`: daily limits per firm.

## Tools

| Tool | Demo moment |
|---|---|
| `list_jobs` | 1: what came in, filed by job |
| `get_job` | 2: approvals with quotes; any job question |
| `search_job_documents` | 2: find an email or document |
| `list_missing_items` | 3: what's missing (incl. expired insurance) |
| `search_regulations` | 4, 7: rules with section and edition date |
| `get_payment_dates` | 7: payment notice deadlines |
| `sync_inbox` | 1: fetch new email (returns "not connected yet" until step 4) |

Demo has no login: every call acts for `DEMO_FIRM_SLUG`. Real use needs OAuth.

## Tests

`TEST_DATABASE_URL=postgresql://... pytest` (that database is wiped). Includes an end-to-end test that starts the
server over HTTP and calls tools with an MCP client.
