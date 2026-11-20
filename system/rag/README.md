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

## Server integration: what is still needed (server session, 20 Nov 2026)

The live MCP server still answers from the fallback. Testing in the Claude app found: asbestos (CAR 2012 reg 5) and Approved Document B missing, Approved Document A and Part P partial, `as_of_date` empty. To switch the server to the corpus:

1. **Expose the function the contract names.** The server does `import rag` (with `system/` on the path) and calls `rag.search(question, as_of_date=...)`. Today `system/rag/__init__.py` is empty and `search.py` imports `system.rag...`, so the import fails and the server falls back. Either export `search` from `rag/__init__.py` with imports that work as `rag`, or tell us to import `system.rag.search` instead (one line in `system/api/builders_api/service/regulations.py`).
2. **Make the index available on the server.** `search()` reads `corpus/search.sqlite` (or `RAG_INDEX`). The server image copies `system/rag` but not `corpus/`. Say where the index should come from (S3 download at deploy, or a file in the image) and its size.
3. **Re-rank and vectors need Bedrock.** The server role has no Bedrock rights (parking lot S26). For tomorrow, `RAG_MODE=keyword` and `RAG_RERANK=0` avoid Bedrock; or add `bedrock:InvokeModel` for the re-rank and embedding model ARNs to `deploy/cloudformation/server.yaml` (the server session can do that).
4. **Dependencies** that `search()` needs at query time (numpy etc.) go in the root `pyproject.toml` main dependencies, not only the `corpus` extra.
5. **Return `[]` below a relevance floor.** The server's fallback now does this: at least half of the question's words must match.
