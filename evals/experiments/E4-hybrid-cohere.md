# E4 — Hybrid with Cohere Rerank 3.5 instead of Amazon Rerank

**Date:** 20 Nov 2026, evening. **Split:** dev, golden commit 7668af2. **Compared with:** E2.

## Config

E2 plus `RAG_RERANK_MODEL=cohere.rerank-v3-5:0` (Frankfurt, the only EU region with it).
Re-run: `RAG_HYBRID=1 RAG_RERANK_MODEL=cohere.rerank-v3-5:0 python evals/retrieval.py --run E4-hybrid-cohere --schema corpus_next --split dev`

## Results (273 questions with sections)

| | E2 Amazon | E4 Cohere |
|---|---|---|
| Recall@5, no floor | 0.67 | 0.64 |
| Recall@5 at floor 0.05 | 0.34 | 0.64 |
| Out-of-scope questions left empty at 0.05 | 95% | 13% |

McNemar on Recall@5 (no floor): E2 alone 20, E4 alone 12, chi2 2.0: no clear difference. Either finds the
section in the top 5 for 72% of questions.

## Meaning

Cohere's scores are calibrated (a floor of 0.05 removes little); Amazon's are not (the floor removes most). With
no floor Amazon is as good or slightly better, at about half the price. **Decision: keep Amazon Rerank and lower
the floor**; the answer model, not the floor, decides "not in the sources" (checked by the judge, S8). Neither
re-ranker's floor separates out-of-scope questions well.
