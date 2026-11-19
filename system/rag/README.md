# Regulations search: contract with the MCP server

Agreed 19 Nov 2026. The corpus session owns `corpus/` and this folder. The MCP server (`system/api`) only calls the one function below.

## The function

`system/rag/` is a Python package named `rag`. It exposes:

```python
def search(question: str, as_of_date: datetime.date | None = None) -> list[dict]:
    ...
```

- `question`: the user's question in plain words.
- `as_of_date`: if given, return the text that applied on that date (edition history). `None` means current.
- Returns passages, best first (the server shows at most 5). Each passage is a dict with:

| Key | Type | Required | Example |
|---|---|---|---|
| `text` | str | yes | exact text of the passage |
| `source` | str | yes | "The Building Regulations 2010 (SI 2010/2214)" |
| `section` | str | yes | "Regulation 3 Meaning of building work" |
| `edition_date` | str, `YYYY-MM-DD` | yes | "2026-11-06" |
| `url` | str | yes | link to the source section |
| `score` | float | no | relevance score |
| `edition_note` | str | no | "Revised text, valid from 6 Nov 2026" |

Passages missing a required key are dropped by the server.

## Errors

- Raise any exception on failure. If it has `retryable = True` (throttling, timeouts, 5xx), the server retries with backoff and jitter; otherwise it reports a clear error to the user.
- Return `[]` when nothing matches. The server then tells Claude to say so, not to answer from memory.

## How the server finds it

The server adds `system/` to `sys.path` (override with `RAG_PARENT_DIR`) and imports `rag`. If the import fails or `rag.search` is missing, it uses a small fallback: `system/api/builders_api/regulations_fallback/passages.json` (Construction Act ss110A, 110B, 111; Building Regulations 2010 reg 3; GOV.UK "Building regulations approval"). Exact text, Open Government Licence v3.0, downloaded 19 Nov 2026.

Dependencies of `rag` must be added to the root `pyproject.toml`.
