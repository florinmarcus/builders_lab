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

## What the library holds: `rag.about()` (25 Nov 2026, S100)

```python
rag.about() -> {"loaded_at", "schema_version", "passages",
                "sources": [{"source_id", "title", "legal_weight", "passages", "versions",
                             "edition_date", "next_from", "url"}]}
```

Read from `corpus.stats` and `corpus.chunks` (versions that ended before today left out). The server's
`about_regulations_library` tool merges it with `regulations_fallback/library.json`: publisher, type, topics, the
documents we do not hold and why, scope and weak parts. Rebuild that file after any change to `corpus/sources.yaml`
or to the scope lines in `system/rag/library.py`: `python -m system.rag.library` (`tests/test_library.py` fails
when it is stale). Exported with `search`, under the same two settings.

## Errors

- Raise any exception on failure. If it has `retryable = True` (throttling, timeouts, 5xx), the server retries with backoff and jitter; otherwise it reports a clear error to the user.
- Return `[]` when nothing matches. The server then tells Claude to say so, not to answer from memory.

## How the server finds it

The server adds `system/` to `sys.path` (override with `RAG_PARENT_DIR`) and imports `rag`. If the import fails or `rag.search` is missing, it uses a small fallback: `system/api/builders_api/regulations_fallback/passages.json` (Construction Act ss110A, 110B, 111; Building Regulations 2010 reg 3; GOV.UK "Building regulations approval"). Exact text, Open Government Licence v3.0, downloaded 19 Nov 2026.

Dependencies of `rag` must be added to the root `pyproject.toml`.

## Server integration: what is still needed (server session, 20 Nov 2026)

The live MCP server still answers from the fallback. Testing in the Claude app found: asbestos (CAR 2012 reg 5) and Approved Document B missing, Approved Document A and Part P partial, `as_of_date` empty. To switch the server to the corpus:

1. **Expose the function the contract names.** The server does `import rag` (with `system/` on the path) and calls `rag.search(question, as_of_date=...)`. Today `system/rag/__init__.py` is empty and `localsearch.py` imports `system.rag...`, so the import fails and the server falls back. Either export `search` from `rag/__init__.py` with imports that work as `rag`, or tell us to import `system.rag.localsearch` instead (one line in `system/api/builders_api/service/regulations.py`).
2. **Make the index available on the server.** `search()` reads `corpus/search.sqlite` (or `RAG_INDEX`). The server image copies `system/rag` but not `corpus/`. Say where the index should come from (S3 download at deploy, or a file in the image) and its size.
3. **Re-rank and vectors need Bedrock.** The server role has no Bedrock rights (parking lot S26). For tomorrow, `RAG_MODE=keyword` and `RAG_RERANK=0` avoid Bedrock; or add `bedrock:InvokeModel` for the re-rank and embedding model ARNs to `deploy/cloudformation/server.yaml` (the server session can do that).
4. **Dependencies** that `search()` needs at query time (numpy etc.) go in the root `pyproject.toml` main dependencies, not only the `corpus` extra.
5. **Return `[]` below a relevance floor.** The server's fallback now does this: at least half of the question's words must match.

## Answers (corpus session, 20 Nov 2026)

1. **Import:** `rag/__init__.py` now exports `search` from `rag/pgsearch.py`, which uses no `system.rag` imports, so `import rag` works in the container. It is offered only when `CORPUS_READER_URL` is set **and** `RAG_ENABLED=on`; otherwise `rag.search` is missing and the server keeps its fallback. No change needed in `service/regulations.py`.
2. **Index:** not a file. The corpus is in Postgres with pgvector on Florin's RDS instance, own database `builders_corpus` (`deploy/rds/`). The server connects only as `builders_corpus_reader` (SELECT only, read-only transactions, 5 connections, 5 s queries). `deploy/scripts/env-from-ssm.sh` puts `/builders-lab/prod/secrets/corpus_reader_url` into `CORPUS_READER_URL`, and `/builders-lab/prod/rag_enabled` into `RAG_ENABLED`. Loaded 20 Nov 2026 with `python -m system.rag.build --load`.
3. **Bedrock:** semantic search from the start (Florin): the question is embedded with Titan V2 (London), pgvector gives the 50 nearest chunks valid on the date and in the country, Amazon Rerank (Frankfurt) picks the best 5. `deploy/cloudformation/server.yaml` now gives the server role `bedrock:InvokeModel` on those two models and `bedrock:Rerank`, and sets the instance metadata hop limit to 2 so the container can use the role. Needs one stack update (Florin), then `rag_enabled=on`. Keyword (BM25) search is postponed; the tables already hold its data.
4. **Dependencies:** `boto3` in a new `search` extra; the `Dockerfile` installs `.[demo,gmail,search]`. `psycopg` is already a main dependency. No numpy on the server.
5. **Relevance floor:** passages with a re-rank score below `RAG_MIN_SCORE` are dropped. **Off since 21 Nov 2026** (default 0): Amazon Rerank scores are not calibrated, and 0.05 emptied 58% of answerable builders' questions (`evals/experiments/J1-answers-live-vs-E5.md`). An unrelated question now returns passages, and the answer model says the sources do not cover it. Keyword (BM25) search is on by default (`RAG_HYBRID=1`).

Errors: AWS or network trouble raises `SearchError` with `retryable = True`. Passages also carry `legal_weight` ("law", "statutory-guidance", "approved-code", "guidance") and `printed_page`; the server's output currently keeps only `source, section, edition_date, url, text, score, edition_note`. Passing `legal_weight` through would let answers say "the law requires" vs "the guidance says". `as_of_date` empty means today.

## Requested next (server session, 21 Nov 2026): extra queries in `search`

The best eval setup (E5: Recall@5 pooled 0.82, Recall@50 0.93) fuses the builder's question with two extra queries the regulations specialist writes (plain words, legal words), then re-ranks against the original question. Today that fusion lives only in `evals/retrieval.py` (`fused_search`).

Please add to `system/rag/pgsearch.py`:

```python
def search(question, as_of_date=None, country="E", limit=5, embed=None, rerank_fn=None, url=None, queries=None) -> list[dict]
```

`queries`: optional list of up to 2 extra search strings. Candidates from the question and each query are fused (RRF, one per section, top_k), then re-ranked against `question` only. Without `queries`, behaviour is unchanged. When it is in, the server session adds an optional `queries` argument to the `search_regulations` tool and step 1 in `plugin/agents/regulations.md` (write a plain-words and a legal-words query). After the demo; not before 7:30 on 21 Nov.
