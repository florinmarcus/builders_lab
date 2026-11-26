# Flow: search the regulations

A regulations question to cited passages. Up: [runtime design](../design.md).
How the index is built: [ingest design](../../ingest/design.md). Search contract: `system/rag/README.md`.

```mermaid
flowchart TB
    q(["Regulations question"]) --> plan["1. regs-search-plan skill<br/>1 to 3 English searches, together"]
    plan --> tool["2. search_regulations()<br/>service/regulations.py"]
    tool -->|"rag off"| fb["fallback: 7 passages<br/>regulations_fallback/"]
    tool --> cand["3. pgsearch.candidates()<br/>nearest() vectors + keyword() BM25,<br/>in force on as_of_date"]
    cand --> rrf["4. rrf() + one_per_section()"]
    rrf --> rr["5. rerank()<br/>Bedrock, drop below min_score"]
    rr --> pass["6. passage()<br/>source, section, edition date, url, text"]
    fb --> pass
    pass --> ans(["7. Answer cites each rule;<br/>nothing found: 'library does not cover that'"])
```

- **Steps 3 to 6** are `system/rag/pgsearch.py` `search()`, on `corpus-db` with the reader login. The question is
  embedded with Titan V2 (London); re-rank runs in Frankfurt.
- **Errors.** A failed search is retried (`retry.py`), then reported as `upstream_error`. If the corpus is switched
  off (`rag_enabled`), the small fallback set answers and the result says so.
- **Dates.** `as_of_date` comes from the job, so the answer uses the version in force then (ADR 0016).
- **Planned:** lanes by legal weight (`search_lanes()`, built, not live), `get_section`, `read_document` (ADR 0016).
