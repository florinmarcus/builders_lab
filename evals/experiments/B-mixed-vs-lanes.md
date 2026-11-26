# B1 to B4: mixed search or lanes, with and without agent queries

**Date:** 25 Nov 2026. **Split:** dev, 299 questions with expected sections, golden sha 49174d8ea638.
**Corpus:** corpus_v2 (local copy of the live index). **Plan:** [eval design](../../architecture/design/eval/design.md).

One line per run: what it is, the code commit, the command. All runs: `CORPUS_READER_URL=<local> python evals/retrieval.py --schema corpus_v2 --split dev --run <name>` plus the switches below. Results files: `evals/results/<name>-dev.jsonl` and `.summary.json`.

| Run | What | Switches | Code |
|---|---|---|---|
| B1 | Mixed: the question as asked (live behaviour) | `EVAL_KEEP=20` | 1c3e36d |
| B2 | Four lanes by legal weight, the question as asked | `EVAL_LANES=1` | 437dd7f |
| B3 | Mixed + saved agent queries, fused (RRF), re-ranked on the question | `EVAL_FUSE=1 EVAL_QUERIES_FROM=E3-rewrite EVAL_KEEP=20` | 1c3e36d |
| B4 | Lanes + the same agent queries, fused per lane, re-ranked on the question | `EVAL_LANES=1 EVAL_FUSE=1 EVAL_QUERIES_FROM=E3-rewrite` | 85d83da |
| B5 | As B4, 8 kept per lane, then the best 8 by re-rank score over all lanes (no slots) | B4 + `EVAL_LANE_MERGE=score EVAL_LANE_KEEP=8 EVAL_KEEP=20` | dfe8805 |
| B6 | As B3, re-ranked on the agent's plain rewrite (see [R1](R1-rerank-pilot.md)) | B3 + `EVAL_RERANK_WITH=plain` | 3514665 |
| B7 | As B6, Cohere Rerank 3.5 | B6 + `RAG_RERANK_MODEL=cohere.rerank-v3-5:0` | 3514665 |

Agent queries: saved from E3 (Haiku 4.5 simulating the specialist, see [E3-E5](E3-E5-agent-queries.md)). They carry no lane tag, so B4 sends every query to every lane. A version with one query per lane needs new queries (later, if B4 helps).

## Results, strict (the labelled section is found)

Fair comparison: 8 passages each (mixed top 8; lanes 2 per lane). For lanes, "found" means a label found in its own lane's top 2.

| | B1 mixed | B2 lanes | B3 mixed + agent | B4 lanes + agent |
|---|---|---|---|---|
| Found in 8 passages | 0.756 | 0.696 | 0.776 | 0.709 |
| Found in 20 passages (lanes: 5 each) | 0.836 | 0.836 | 0.873 | 0.873 |
| Recall@5 | 0.699 | | 0.712 | |
| Recall@10 | 0.773 | | 0.803 | |
| Recall@20 | 0.836 | | 0.873 | |
| Latency p50 | 1.3 s | 3.8 s | 2.5 s | 5.4 s |

At 20 passages mixed and lanes tie, but on different questions: 16 (B1/B2) and 17 (B3/B4) found only by one side, each way.

B4 per lane, top 2 (B2 in brackets): law 0.54 (0.51), Approved Documents 0.46 (0.52), ACoP 0.60 (0.58), guidance 0.55 (0.55). Agent queries lift law's top 50 from 0.75 to 0.85.

## Is it real or noise? (paired test, `evals/paired.py`)

Same 299 questions, so we count the questions only one run found. p below 0.05 = unlikely to be luck.

| Comparison | 8 passages | 20 passages |
|---|---|---|
| Mixed beats lanes (B1 vs B2) | +6 points, 37 vs 19 questions, p 0.02: **real** | tie, 16 vs 16 |
| Same, with agent queries (B3 vs B4) | +7 points, 40 vs 20, p 0.01: **real** | tie, 17 vs 17 |
| Agent queries help mixed (B3 vs B1) | +2 points, 13 vs 7, p 0.26: **not shown** | +4 points, 19 vs 8, p 0.05: borderline |
| Agent queries help lanes (B4 vs B2) | +1 point, 12 vs 8, p 0.50: **not shown** | +4 points, 13 vs 2, p 0.007: **real** |

So: at 8 passages mixed really beats lanes. Agent queries help when we keep 20 passages; at 8 the gain is too small
to tell from noise on 299 questions. Strict labels only; the answer-set judge may change the picture.

## Regression gate

Baseline: B1 (live behaviour), found 226 of 299 at 8 passages. Against it: B2 fails (37 lost, 19 gained, 6 must-pass lost); B3 fails only on 2 must-pass questions (7 lost, 13 gained, p 0.26).

## Answer-set judge (can a builder get the full answer from the 8 passages?)

80 dev questions (spread over the 6 roles), each judged on the 8 passages of each run, blind and shuffled.
Judge opus-a on all 320 sets; opus-b and Sonnet re-judged 32 of them. Code: `evals/golden/answer_set.py`
(`packets`, `merge`, `score`, `compare`); grades in `evals/golden/pooled/answer-sets-v2.jsonl`. Brief: `evals/golden/ANSWER-SET-BRIEF.md`.

| | B1 mixed | B2 lanes | B3 mixed + agent | B4 lanes + agent |
|---|---|---|---|---|
| Full answer (2) | 78% | 60% | 81% | 61% |
| Part answer (1) | 18% | 35% | 18% | 34% |
| Nothing useful (0) | 5% | 5% | 1% | 5% |

Judge agreement on the 32 re-judged sets: opus-b and Sonnet both gave the same grade as opus-a on all 32 (kappa 1.0),
in their own words. 32 is a small sample, so read it as "the judges are not noisy", not as proof.

Paired, question by question (opus-a only):

| Comparison | Full answer only in the first | Only in the second | p |
|---|---|---|---|
| B1 mixed vs B2 lanes | 16 | 2 | 0.001: **real** |
| B3 vs B4 (both with agent queries) | 17 | 1 | <0.001: **real** |
| B3 vs B1 (agent queries help mixed) | 3 | 0 | 0.25: not shown (5 better, 0 worse on any grade) |
| B4 vs B2 (agent queries help lanes) | 2 | 1 | 1.0: no difference |

Why lanes lose: 2 slots per lane go to lanes with nothing useful for the question (an ACoP for a CIS question),
so the second rule the answer needs drops out. Lanes lose most on housing repairs (7 of 13 not full, mixed 2) and
money (7 of 13, mixed 4).

What is still missing in B3 (15 of 80 not full): nearly always the second part of the question, such as an
exception, a threshold or a follow-on rule (the £30,000 notice threshold, the 50% renovation trigger, the
domestic-client CDM duty). Two are parse gaps: a diagram with no text (stair headroom) and an edition question.

## B5: lanes merged by re-rank score instead of slots

Florin's idea: search per lane, but let the re-ranker pick the best 8 over all lanes. The re-ranker scores each
passage against the question alone (scores for the same passage match B4 to 4 digits), so scores compare across lanes.
RRF across lanes was also tried on saved rows: it behaves like 2 slots per lane (0.709), so it is dropped.

| | B3 mixed + agent | B5 lanes + agent, by score |
|---|---|---|
| Found in 8 passages | 0.776 | 0.773 |
| Recall@20 | 0.873 | 0.903 |
| Latency p50 | 2.5 s | 5.4 s |

Paired at 8: B5 vs B3 5 vs 6, p 1.0 (no difference); B5 vs B1 14 vs 9, p 0.41. Gate against B1: fails on the same
2 must-pass questions as B3. At 20 passages B5 finds more (0.903).

Cap per lane (on B5's saved rows; a lane may give at most c of the 8, then by score): c=2 0.709, c=3 0.783,
**c=4 0.816** (27 vs 15 against B3, p 0.09), c=5 0.813, c=6 0.806, c=8 0.773. A soft cap helps, hard slots hurt.
Not proven (p 0.09), and c was picked on the same dev rows, so it needs the holdout before anyone trusts it.

**Conclusion:** keep mixed search. Agent queries never made a set worse and helped 5; keep them (B3) if the
must-pass check is clean. Lanes are dropped for the 8-passage answer.
