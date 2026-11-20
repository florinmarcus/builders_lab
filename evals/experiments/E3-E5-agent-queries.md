# E3 and E5 — The regulations specialist writes the search queries

**Date:** 20 Nov 2026, late evening. **Split:** dev, golden commit 2fa9ba2 (with pooled labels).
**Compared with:** E2 (hybrid).

## Idea

Builders write "lad drilled through a panel"; the law says "uncontrolled release of asbestos". In the product,
Claude (the plugin's `regulations` specialist) calls `search_regulations`, so Claude can write the search words.
No model runs on our server (ADR 0006). Proposed specialist instruction, simulated with Claude Haiku 4.5 on
Bedrock (`REWRITE_PROMPT` in `evals/retrieval.py`): write two queries, the question in plain complete words and
the same need in the words of the law and official guidance.

- **E3:** each query searched separately (hybrid + re-rank), passages merged by re-rank score.
- **E5:** one search: candidates of the original question and of both queries, fused by RRF, one per section, the
  first 50 re-ranked against the builder's original question. Server side this is an optional `queries` list on
  `search_regulations`.

Re-run E5: `RAG_HYBRID=1 EVAL_FUSE=1 EVAL_QUERIES_FROM=E3-rewrite python evals/retrieval.py --run E5-fused --schema corpus_next --split dev`

## Results (273 questions, no floor)

| | E2 | E3 | E5 |
|---|---|---|---|
| Recall@5 strict | 0.67 | 0.67 | **0.70** |
| Recall@5 pooled | 0.78 | 0.79 | **0.82** |
| Recall@50 strict | 0.81 | 0.86 | **0.88** |
| Recall@50 pooled | 0.87 | 0.92 | **0.92** |
| Pooled, loaded sources: Recall@5 / @50 | 0.82 / 0.91 | 0.82 / 0.95 | **0.85 / 0.95** |

McNemar E2 → E5: Recall@5 strict 12 gained / 4 lost (chi2 4.0), pooled 13 / 2 (8.1); Recall@50 strict 20 / 0
(20.0), pooled 16 / 1 (13.2). Clear gains. E3 alone gains candidates but not the top 5: re-rank scores from
different queries are not comparable, so merging by score fails; E5 re-ranks one pool against one question.

Cost: rewrite about $0.0006 per question (Haiku 4.5), re-rank unchanged (one call), embeddings three per question.

## Meaning

**Kept.** The search tool should take the specialist's extra queries and fuse them. This is a product change in
two places, prepared but not live until promotion: `search_regulations` (optional `queries`, add-mcp-tool runbook,
new versioned description) and `plugin/agents/regulations.md` step 1.

## Cautions

- The rewrite model is Haiku 4.5 (Haiku 5.5 is not enabled on the AWS account); the product's specialist may
  write different queries.
- Pooled labels come from sections the runs found (E1-E5); a later system may find unjudged sections, so the pool
  is judged again after each run.
