# L1: pooled labels, do other passages also answer the question?

**Date:** 25 Nov 2026. **Split:** dev only. **Why:** "found" counts only the labelled section. The E8 miss check
(Opus on 90 top-5 misses) found that in 38 of them a passage in the top 5 did answer, from another place than the label.
Old "also acceptable" grades came from a model on AWS (before ADR 0017) and only covered older runs: they are removed.
Method: `evals/knowledge/eval-practice-assessment.md`, topics 2, 3, 4 and 6.

**Code:** `evals/golden/pool_local.py`, brief `evals/golden/POOL-JUDGE-BRIEF.md`. Verdicts: `evals/golden/pooled/judgments.jsonl`
(primary judge), `recheck.jsonl` (re-check), `human.jsonl` (Florin). Packets hold corpus text and stay in the scratchpad.

## Plan, written before the run

**How small a change can we see?** Share of questions where two runs disagree, and the smallest gap a paired test can
show (80% power, p 0.05, questions treated as independent):

| Pair | Disagree | Smallest gap, 299 questions | Smallest gap, 60 questions |
|---|---|---|---|
| B1 / B3 | 6.7% | 4.2 points | 9.3 points |
| B3 / B6 | 11.4% | 5.5 points | 12.2 points |
| B3 / B7 | 15.1% | 6.3 points | 14.0 points |
| B6 / B7 | 9.0% | 4.9 points | 10.9 points |

So dev cannot show the 1 to 2 point gaps between B3, B6 and B7: they were never testable. Questions from one document
move together (93 documents for 299 questions), so the real smallest gaps are larger still.

**Step 1, sample:** 60 dev questions at random (seed 25, `--sample 60`), every passage in the first 8 of B1, B3, B6
and B7 that does not touch a labelled section. About 750 passages.

**Step 2, judge:** one yes/no question per passage (the brief), reason first, verdict last. Opus judges all. 10% are
judged again by a second Opus and by Sonnet, in other batches: self-consistency and agreement across models.

**Step 3, Florin's check:** about 100 passages, with extra cases where the judges disagree and where the judge said
yes (the verdict that changes scores). Half (dev) to fix the brief if needed; half (test), with the brief frozen,
for the numbers: share of Florin's "yes" the judge finds, share of his "no" it rejects, precision on "yes", kappa,
each with a 95% interval. The judge's "yes" counts only after this.

**Step 4, score:** "found" = a labelled section or a passage judged yes, in the first 8. On the 60 questions:
how many misses turn into found, per run. The 60 cannot rank the runs (table above); it tells us whether labels
change the picture enough to judge all of dev.

**Step 5, only if step 4 moves things:** judge the rest of dev (about 3,000 passages), then compare all four runs
with the paired test, questions grouped by source document, Holm correction for the 6 pairs. Then the holdout, once.

## Results (25 Nov, steps 1, 2 and a first step 4; step 3 still to do)

**Step 1:** 746 passages for the 60 questions (all 60 have at least one), 38 packets of 20. Re-check: 75 passages.

**Step 2:** opus-a said yes to 114 of 746 (15%), for 46 of the 60 questions. Agreement on the 75 re-judged passages:

| | Same verdict | Kappa | "Yes" given |
|---|---|---|---|
| opus-a and opus-b (second Opus) | 74 of 75 | 0.94 | 9 and 10 |
| opus-a and Sonnet | 72 of 75 | 0.82 | 9 and 10 |
| opus-b and Sonnet | 73 of 75 | 0.88 | 10 and 10 |

So the judge is consistent with itself and with another model. That is not the same as being right: step 3 checks that.

**Step 4, provisional (judge's "yes" not yet checked by Florin):** found in the first 8, same 60 questions.

| | B1 | B3 | B6 | B7 |
|---|---|---|---|---|
| Labelled section only | 0.733 | 0.700 | 0.767 | 0.767 |
| Labelled or judged yes | 0.867 | 0.850 | 0.917 | 0.917 |
| Misses that turn into found | 8 of 16 | 9 of 18 | 9 of 14 | 9 of 14 |

About half the misses are passages that do answer, from another place than the label. Paired by document (41
documents), Holm over 6 pairs: no pair differs (all p_holm 1.0; largest gap B3 to B6/B7, 4 points either way on
this sample). As planned, 60 questions cannot rank the runs. They show the labels move every score by 13 to 15
points, so step 5 is worth doing once step 3 passes.

**Step 3, Florin's check:** 100 passages from 48 questions, split by question: 47 dev (19 judged yes, 28 no),
53 test (32 yes, 21 no); the 3 re-check disagreements are in. Judge "yes" is over-sampled (51% against 15% in the
pool), so the judge's error rates are weighted back to the pool when computed. Results go to
`evals/golden/pooled/human.jsonl` (ids, sections, Florin's verdict; no corpus text).
