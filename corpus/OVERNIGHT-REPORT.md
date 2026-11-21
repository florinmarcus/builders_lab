# Overnight report — 20/21 Nov 2026

The night stopped early, at about 01:15: the usage limit was reached. **Live search is unchanged and nothing was
promoted.** Details are in `corpus/OVERNIGHT-PLAN.md` (log) and `evals/experiments/`.

## The headline: the live server gives poor answers, and a two-setting fix exists

- Judged answers on 342 dev questions: **live setup passes 31%**. For answerable questions, 58% get "not in the
  sources", because the relevance floor (0.05) drops every passage for builders' wording.
- **Hybrid search with no floor passes 57%** (103 questions gained, 13 lost, McNemar 70). Out-of-scope answers
  also improve (64% → 77%): the answer model declines by itself.
- It needs two server settings, no code: `RAG_HYBRID=1`, `RAG_MIN_SCORE=0`. It is reversible. **Your decision**:
  it is a live change, and the recall gate (below) is not met.

## Retrieval (dev, 273 labelled questions)

| Setup | Recall@5 strict | Recall@5 pooled | Recall@50 pooled |
|---|---|---|---|
| E1 live path, live floor | 0.32 | – | – |
| E1 live path, no floor | 0.65 | 0.75 | 0.84 |
| E2 hybrid | 0.67 | 0.78 | 0.87 |
| **E5 hybrid + specialist's extra queries, fused** | **0.70** | **0.82** (0.85 on loaded sources) | **0.93** (0.96) |

Gate: Recall@5 ≥ 0.90 on dev. **Not met.** E4 (Cohere re-rank), E6 and E7 gave no gain. "Pooled" adds sections a
blind judge model confirmed answer the question (TREC-style pooling, `evals/golden/pool_judge.py`); strict uses
the original labels only. The holdout (49 questions) has not been run.

## What was built

- Golden set v1: 412 business questions by six role-played users, labelled in a separate pass, adversarially
  reviewed, holdout committed before any run (`evals/golden/`).
- Retrieval eval (`evals/retrieval.py`), metrics with McNemar, answer eval with an LLM judge (`evals/judge.py`).
- Hybrid BM25 search on the server path (off by default). Multi-page HTML ids fixed.
- Parsers committed: Approved Documents A, B, C, F, G, J, K, L, P, 7, F-2026; HSE L143, HSG150, L153, HSG248,
  INDG453, Asbestos Essentials A0/EM1, CIS80, Awaab consolidated, MS34; 9 HSE sources now harvest their PDF.

## Not done

1. Staging is not reloaded with the new parses. Next: `python -m system.rag.chunk`,
   `python -m system.rag.validate_chunks`, `python -m system.rag.embed`, `python -m system.rag.load --schema corpus_next`.
2. Re-label questions whose documents are now parsed (rows with `missing`), then re-run E5 and the judge.
3. E5 product change: an optional `queries` list on `search_regulations` (add-mcp-tool runbook) and a new step 1
   in `plugin/agents/regulations.md`. Run the three searches in parallel (4.9 s now).
4. Still to parse: AD L-2026, M, E, H; HSE L56, 8 S2e PDFs, decent-home-2006, priority 2/3. 6 sources blocked
   (raw files missing).
5. Claude Haiku 5.5 is not enabled on the AWS account; the evals used Haiku 4.5.
6. A person should read a sample of judged answers (one judge model, not calibrated).

Cost: about **$6.25** (cap £20), in `evals/results/cost.jsonl`.
