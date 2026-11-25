# B1 to B4: mixed search or lanes, with and without agent queries

**Date:** 25 Nov 2026. **Split:** dev, 299 questions with expected sections, golden sha 49174d8ea638.
**Corpus:** corpus_v2 (local copy of the live index). **Plan:** [retrieval-tuning.md](../../architecture/design/retrieval-tuning.md).

One line per run: what it is, the code commit, the command. All runs: `CORPUS_READER_URL=<local> python evals/retrieval.py --schema corpus_v2 --split dev --run <name>` plus the switches below. Results files: `evals/results/<name>-dev.jsonl` and `.summary.json`.

| Run | What | Switches | Code |
|---|---|---|---|
| B1 | Mixed: the question as asked (live behaviour) | `EVAL_KEEP=20` | 1c3e36d |
| B2 | Four lanes by legal weight, the question as asked | `EVAL_LANES=1` | 437dd7f |
| B3 | Mixed + saved agent queries, fused (RRF), re-ranked on the question | `EVAL_FUSE=1 EVAL_QUERIES_FROM=E3-rewrite EVAL_KEEP=20` | 1c3e36d |
| B4 | Lanes + the same agent queries, fused per lane, re-ranked on the question | `EVAL_LANES=1 EVAL_FUSE=1 EVAL_QUERIES_FROM=E3-rewrite` | 85d83da |

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

Still to come: the answer-set judge (can a builder get the full answer from the 8 passages?) on 80 questions.
