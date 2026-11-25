# P: small-to-big passages (25 Nov 2026)

Offline test. The live search is unchanged.

## Question

If each shown chunk is swapped for a bigger passage, does rule coverage go up, and at what cost in text and time?

## Method

- Runs: B1-v2-mixed-k20-dev-dev (live setup) and B3-v2-fused-k20-dev-dev, 299 dev questions, rule coverage from `evals/paired.py`.
- Expansion, for each shown chunk: the parent block if it is 3,000 characters or less (a clause gets its whole regulation); otherwise the chunk plus one sibling either side. Breadcrumb on top, cut at 6,000 characters. A plain lookup in the document tree, so the same query gives the same passages.
- The same pool judge ("opus-a", same prompt) judged each bigger passage: 1,639 pairs (953 parent, 686 neighbours), 55 packets, 2 planted lines each. Verdicts in `evals/golden/pooled/judgments-s2b.jsonl` (section key + `@s2b`).
- Only questions that missed a rule were judged. This is fair: the bigger passage contains the chunk, so coverage can only rise.
- Coverage after: the union of the chunk's verdict and the bigger passage's verdict.

## Results

| Run | n | Before | After | Better / worse | p |
|---|---|---|---|---|---|
| B1 | 5 | 0.606 | 0.692 | 48 / 0 | 0.0001 |
| B1 | 8 | 0.654 | 0.754 | 57 / 0 | 0.0001 |
| B3 | 5 | 0.624 | 0.713 | 51 / 0 | 0.0001 |
| B3 | 8 | 0.684 | 0.781 | 55 / 0 | 0.0001 |

- B3 vs B1, both bigger, at 8: +0.028, p 0.03.
- Same text budget: bigger at 5 (about 10,200 characters) vs plain at 8 (about 8,500): B1 +0.038 (p 0.02), B3 +0.030 (p 0.08).

## Cost

- Characters per question at 8: B1 8,500 → 16,200 (median 7,400 → 15,200), B3 8,600 → 16,400. About 2k → 4k tokens per search.
- Lookup time per chunk: p50 under 0.02 ms, p95 under 0.6 ms, worst 154 ms (first, cold load of a tree). Nothing next to the 1.3 s search.

## Caveats

- One judge, not yet checked by Florin (S153).
- Planted yes judged no: 10 of 55, all look like label problems (for example party-wall-act-1996:section-10-1 on building-control-041, cdm2015:regulation-15 on site-safety-009, hmrc-cis-340:para-6.3 on money-002). Go to S116.

## Next

Build it into the live search (S154) after the baseline (S151).
