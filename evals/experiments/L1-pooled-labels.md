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

## Judge v2 (25 Nov, evening): rules, scope first, quotes, planted lines

Brief `evals/golden/POOL-JUDGE-BRIEF.md` (v2), rules per question in `pooled/rules.jsonl` (opus-r, Florin has not
checked them yet). Same 746 passages and 75 re-check passages as v1, same judge names, so the two can be compared
pair by pair. v2 replaces v1 in `pooled/judgments.jsonl` and `pooled/recheck.jsonl` (v1 is in git history).

**Checks in code:** 0 INVALID lines (every "yes" quote was found in the passage). Planted "no": 38 of 38 right in
the main run, 4 of 4 in each re-check. Planted "yes": only 29 of 38 (main) and 2 of 4 (each re-check). The 9 packets
with a missed plant were judged again by fresh judges: the same 9 plants missed again, with the same reasons, and
179 of the 180 other verdicts the same (one yes became no). So the judge is steady; the plants are the problem.

**The plants are labelled sections that do not state the rule themselves.** This is a finding about the gold labels
(S116), not about the judge. A missed planted "yes" no longer fails a packet; it is listed as a label to check:

| Question | Labelled section | Why the judges said no |
|---|---|---|
| money-018 | cis-regs-2005:regulation-28 | amounts only by reference to Schedule 11 |
| site-safety-008 | hse-l153 regulation 7, domestic clients | says who takes on the duties, not who is a domestic client |
| site-safety-008 | cdm2015:regulation-4 | client duties, not who is a domestic client (both re-check judges) |
| building-control-048 | party-wall-act-1996:section-2-2 | the right to cut a chimney breast, no notice or two months |
| building-control-006 | adl:v1-para-10.3 | points to Table 4.2, gives no U-value |
| building-control-043 | pd-householder-guide class A | height and eaves limits, not the rear depth |
| asbestos-044 | car-amd-2026:regulation-2-3 | changes a cross-reference only, no commencement dates |
| asbestos-029 | car2012:regulation-22-3 | medical examination timing, not the record rules |
| building-control-022 | br2010:schedule-1-J3 | general requirement, no specific alarm or position |
| housing-repairs-045 | hfhh-act-2018:section-1-4 | amending text, not the duty (both re-check judges) |

**v1 against v2 (opus-a, 746 passages):** yes 114 against 125 (43 of 60 questions have one). 14 went yes to no:
4 because the passage's scope did not fit (gas regulations, a revoked 1983 regime), 10 because no rule was stated
(a table heading, a cross-reference, a table split into columns). 25 went no to yes: almost all state one of the
question's two or three rules but not all of them (weekends count in the 30 days, but no thresholds). v2 says yes
when a passage states at least one rule; v1 asked for "the answer". That rule is a choice for Florin.

**Agreement on the 75 re-check passages:**

| | v1 kappa | v2 kappa | v2 same verdict |
|---|---|---|---|
| opus-a and opus-b | 0.94 | 0.95 | 74 of 75 |
| opus-a and Sonnet | 0.82 | 0.72 | 70 of 75 |
| opus-b and Sonnet | 0.88 | 0.77 | 71 of 75 |

Sonnet is stricter under v2 (9 yes against 12 and 11 for the two Opus judges). The judge stays Opus.

**Found in the first 8, same 60 questions:**

| | B1 | B3 | B6 | B7 |
|---|---|---|---|---|
| Labelled section only | 0.733 | 0.700 | 0.767 | 0.767 |
| Labelled or judged yes, v1 | 0.867 | 0.850 | 0.917 | 0.917 |
| Labelled or judged yes, v2 | 0.867 | 0.867 | 0.933 | 0.900 |

v2 moves no run by more than one question. The size of the label effect (13 to 17 points) stands.

**Not yet done:** `questions.jsonl` was not rebuilt. It still holds `also_acceptable` from the earlier pool
(S5/S7, 2,474 pairs, 135 questions), which v1 had already replaced in `judgments.jsonl` (S152). It is rebuilt once,
after Florin's check, together with the gate baseline (S151). Florin's 100-passage sample was drawn on v1 verdicts;
the judge's error rates are weighted to the v2 pool rate (17% yes).

**Next, after Florin's check:** apply his rule fixes and re-judge only those questions; `human.jsonl`; true
positive and true negative rates against him; fix or downgrade the labels in the table above (S116); rebuild
`questions.jsonl`; set the gate baseline again.
