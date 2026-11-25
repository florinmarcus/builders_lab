# R1: re-rank pilot, what we feed the re-ranker

**Date:** 25 Nov 2026. **Question:** does the re-ranker put the labelled section higher if we change its inputs
or the model? Small sample first (Florin), the full dev run only if something shows.

**Code:** `evals/rerank_pilot.py`. **Results:** `evals/results/R1-rerank-pilot-amazon.*`, `R1-rerank-pilot-cohere.*`.

## Before: is passage length the problem?

No. Half our passages are under about 470 characters (about 115 tokens); 4% are over 2,000. In B3, labelled sections
the re-ranker kept in the top 8 (370) and those it pushed out (192) are the same length: median 790 and 740
characters, 8% and 9% over 2,000. AWS documents a limit of about 500 to 512 tokens per document (pricing page
footnote, under Cohere; longer documents are split, not cut). Too few of our passages are that long to matter.

## Setup

30 dev questions from B3 (seed 7), 10 per group by where B3's re-ranker put the best label: good (rank 1-3),
middle (4-8), bad (in the 50 candidates, not in the top 8). Same 50 candidates as B3 (27 of 30 identical; 3 differ
slightly), all 50 re-ranked four ways:

- **base:** the builder's question; passage = heading path + text (B3 and live)
- **plain:** the agent's plain rewrite (saved from E3) as the re-rank query
- **title:** the question; passage starts with document title, legal weight and edition date
- **plain+title:** both

Amazon base reproduces B3's ranks exactly on all 30, so the setup matches B3.

## Results: label in the top 8, out of 30

| | Amazon Rerank 1.0 | Cohere Rerank 3.5 |
|---|---|---|
| base | 20 (good 10, middle 10, bad 0) | 19 (10, 7, 2) |
| plain | 20 (10, 7, 3) | **25** (10, 9, 6) |
| title | 20 (10, 9, 1) | 18 (10, 7, 1) |
| plain+title | 23 (10, 7, 6) | 24 (10, 9, 5) |

Rank of the label against base, per question (better / worse): Amazon plain 15 / 5, title 10 / 8, plain+title 13 / 9;
Cohere plain 11 / 6, title 5 / 7, plain+title 12 / 7.

## Reading

- The plain rewrite helps: it pulls bad-group labels into the top 8 (Cohere 2 to 6, Amazon 0 to 3). With Amazon it
  also costs 3 middle questions; with Cohere it does not.
- The title line adds nothing on its own.
- Cohere with the plain rewrite is the best cell (25 of 30), but Cohere base is no better than Amazon base.
- E6 re-ranked on the question **plus** all agent queries joined: no difference. The plain rewrite **alone** is new.

Not proof: 30 questions, and the sample is a third bad questions (about 13% in all of dev), so gains look bigger
than they will on the full set. Next: full dev runs, B3 with the plain re-rank query, Amazon and Cohere, paired
against B3, with the gate.

Cost: 120 calls each, $0.12 (Amazon) and $0.24 (Cohere), plus a few query embeddings.

## Full dev: the pilot gain does not hold

B3 with the re-rank query set to the plain rewrite, all 299 dev questions. Switches: B3 + `EVAL_RERANK_WITH=plain`
(code 3514665); B7 adds `RAG_RERANK_MODEL=cohere.rerank-v3-5:0`.

| | B3 (question, Amazon) | B6 (plain, Amazon) | B7 (plain, Cohere) |
|---|---|---|---|
| Found in 8 passages | 0.776 | 0.783 | 0.773 |
| Recall@5 | 0.712 | 0.716 | 0.669 |
| Recall@20 | 0.873 | 0.873 | 0.873 |
| Latency p50 | 2.5 s | 2.4 s | 2.0 s |

Paired at 8 against B3: B6 18 vs 16, p 0.86; B7 22 vs 23, p 1.0. B7 vs B6: 12 vs 15, p 0.70. No difference: the
plain rewrite and Cohere swap which questions are found, they do not find more. Gate against B1: both fail on
must-pass questions (B6: fire-safety-001, housing-repairs-010; B7: those and money-032).

Why the pilot looked better: the bad group was picked because B3 ranked them badly, so almost any change moves
some of them up (regression to the mean), while the losses fall on questions outside the sample. A pilot should
pick questions at random, or count losses on the whole set.

**Conclusion:** keep B3's re-rank (the question, Amazon). Changing the re-rank query or model does not help.
Cost: B6 $0.35, B7 $0.69.
