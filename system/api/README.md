# API (Python)

MCP server, service layer and ingestion for the demo, in one package: `builders_api`.

## Database

```
pip install -e ".[dev]"            # from the repo root
cp .env.example .env               # set DATABASE_URL
python -m builders_api.db.migrate  # create or update tables; safe to re-run
```

Migrations live in `builders_api/db/migrations/`. Never edit an applied file: add the next number.
The runner refuses to start if an applied file was changed.

Tests: `TEST_DATABASE_URL=postgresql://... pytest` (that database is wiped).
