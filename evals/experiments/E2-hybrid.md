# E2 — Hybrid: BM25 keywords fused with vectors (RRF), then the same re-rank

**Date:** 20 Nov 2026, evening. **Split:** dev, golden commit 7668af2. **Compared with:** E1 (same questions,
same corpus_next).

## Config

E1 plus `RAG_HYBRID=1`: BM25 over English stems of breadcrumb + text and over codes (B1, FD30, 7(2) kept whole,
weight 2), top 50, fused with the vector top 50 by reciprocal rank fusion (k=60), one per section, the first 50
re-ranked by Amazon Rerank. Code: `system/rag/pgsearch.py` (`keyword`, `rrf`).

Re-run: `RAG_HYBRID=1 python evals/retrieval.py --run E2-hybrid --schema corpus_next --split dev`

## Results (273 questions with sections)

| | E1 | E2 | McNemar (gained / lost, chi2) |
|---|---|---|---|
| Recall@50 | 0.78 | 0.81 | 12 / 4, 4.0 |
| Recall@5, no floor | 0.65 | 0.67 | 13 / 6, 2.6 |
| MRR@5, no floor | 0.48 | 0.51 | |
| Recall@5 at the live floor 0.05 | 0.32 | 0.34 | |
| Recall@5, floor 0.001 | 0.61 | 0.64 | |

By role (loaded sources, no floor): asbestos 0.60 → 0.67, building control 0.58 → 0.65, money 0.62 → 0.65,
fire 0.86 → 0.88, housing 0.74 → 0.74, site safety 0.71 → 0.68.

Cost $0.35 (re-rank). Keyword query 0.5-1.9 s on the database; latency p50 about 1.6 s end to end.

## Meaning

Keyword search finds candidates the vectors miss (clear gain at 50), mainly for questions that name the thing
(AIB, CIS, F10). The top-5 gain is small and not yet clear. **Kept** for the next experiments; it stays off on the
live server until promotion.

## Cautions

Site safety lost one question (0.71 → 0.68: 1 of 28). The live floor still empties most results; the floor is
the bigger lever and is tuned with the answer eval.
