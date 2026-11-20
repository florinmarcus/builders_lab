# Design: regulations corpus and search

**Owner: the corpus session.** Placeholder written 20 Nov 2026 by the server session. Up: [architecture](../ARCHITECTURE.md).

To fill in (diagrams first, little text): harvesting, storage (S3), chunking, embeddings, hybrid search, re-ranking, edition history.

## Agreed interface with the server

```mermaid
flowchart LR
    tool["search_regulations<br/>(server)"] -->|"search(question, as_of_date)"| rag["rag package<br/>system/rag/"]
    rag -->|"passages: text, source,<br/>section, edition_date, url"| tool
    tool -.->|"if rag missing"| fb["fallback passages"]
```

Contract: [system/rag/README.md](../../system/rag/README.md).
