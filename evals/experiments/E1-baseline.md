# E1 — Baseline: the live search path on the staging corpus

**Date:** 20 Nov 2026, evening. **Split:** dev (342 questions, 273 with expected sections). **Golden set:** commit
7668af2 (`questions.jsonl` sha a159a9cc7843).

## Config

As the live server: Titan V2 question embedding (London), the 50 nearest chunks from schema `corpus_next`
(11,028 chunks, 114 sources), one per section, Amazon Rerank (Frankfurt) to 5, relevance floor 0.05.
No keyword search, no query rewriting.

Re-run: `python evals/retrieval.py --run E1-baseline --schema corpus_next --split dev`
Other floors from the saved rows: `python evals/retrieval.py --rescore E1-baseline --split dev --floor 0.001`

## Results

| Floor | Questions left with no passage | Recall@5 | MRR@5 | Recall@50 |
|---|---|---|---|---|
| 0.05 (live) | 213 / 342 | 0.32 | 0.26 | 0.78 |
| 0.01 | 141 | 0.48 | 0.37 | 0.78 |
| 0.003 | 85 | 0.56 | 0.43 | 0.78 |
| 0.001 | 59 | 0.61 | 0.46 | 0.78 |
| none | 0 | 0.65 | 0.48 | 0.78 |

- Only questions whose expected sources are loaded (240): Recall@50 0.81, Recall@5 0.69 with no floor.
- Before the re-rank (first 5 by vector distance): Recall@5 0.55. The re-rank helps (+10 points) when nothing is cut.
- By role, no floor, loaded sources: fire safety 0.86, housing repairs 0.74, site safety 0.71, money 0.62,
  asbestos 0.60, building control 0.58.
- Cost: $0.34 (re-rank $0.34, embeddings under $0.01). Latency p50 1.2 s.

## What it means

1. **The live relevance floor is wrong for builders' wording.** Amazon Rerank orders well but gives chatty
   questions very low absolute scores, so the floor removes everything for 62% of questions (58% of answerable
   ones). On the live server these get "nothing found". This is the biggest single cause of poor answers.
2. **Candidates miss the law.** Most Recall@50 misses expect a regulation (CAR 2012, the Awaab regulations, CIS,
   COSHH, Work at Height): builders' words ("lad drilled through a panel") are far from legal wording. Hybrid
   keyword search (E2) and the specialist writing the search query in legal words (E3) target this.
3. Building control and money miss inside the top 50 too: short regulation paragraphs lose to longer guidance.

## Cautions

- 33 of the 273 questions expect a source not loaded yet (PDFs and Approved Documents still being parsed);
  more questions carry `missing` clauses and will be re-labelled after those parses. Numbers will move.
- The floor also protects out-of-scope questions (95% of them empty at 0.05). A lower floor must be judged with
  the answer eval (S8): does the answer model still decline when the passages do not answer?
