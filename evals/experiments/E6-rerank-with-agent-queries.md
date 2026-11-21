# E6 — Re-rank against the question plus the agent's queries

**Date:** 21 Nov 2026, just after midnight. **Split:** dev. **Compared with:** E5.

Config: E5, but the re-rank query is the builder's question followed by the specialist's two queries
(`EVAL_RERANK_WITH=all`).

| | E5 | E6 |
|---|---|---|
| Recall@5 strict | 0.70 | 0.71 |
| Recall@5 pooled | 0.82 | 0.82 |
| MRR@5 pooled | 0.65 | 0.67 |

McNemar pooled Recall@5: E5 alone 13, E6 alone 14, chi2 0.04: no difference. **Not kept**: E5 is simpler (the
re-rank sees only what the builder asked).
