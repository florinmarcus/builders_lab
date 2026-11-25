"""Regulations corpus package. The MCP server imports it as `rag` and calls rag.search (README.md).

search and about (what the library holds) are offered only when CORPUS_READER_URL is set (the read-only corpus database, deploy/rds/) and RAG_ENABLED is
"on" (switched on after the server role has its Bedrock rights); otherwise the server keeps its small fallback set. Harvesting, parsing, chunking and loading run as `python -m system.rag.<name>`.
"""

import os

if os.environ.get("CORPUS_READER_URL") and os.environ.get("RAG_ENABLED", "").lower() == "on":
    from .pgsearch import about, search  # noqa: F401
