# J1 — Answer eval (LLM as judge): live setup against E5

**Date:** 21 Nov 2026, about 00:45. **Split:** dev, all 342 questions (every kind). Golden commit 00d1a55.

## Config

- Answers: Claude Haiku 4.5 on Bedrock (`eu.anthropic.claude-haiku-4-5-20251001-v1:0`), from the 5 passages
  search returned; told to cite, correct false premises, ask back when vague, and say "NOT IN SOURCES" otherwise
  (`evals/judge.py`). Haiku 5.5 is not enabled on the AWS account.
- Judge: `openai.gpt-oss-120b-1:0` (another family), temperature 0, three 1-5 scores with reasons first, against
  the golden reference answer. Pass = correctness ≥ 4 and grounding ≥ 4.
- **Live:** E1 rows (vector + Amazon Rerank) with the live relevance floor 0.05.
- **E5:** hybrid + the specialist's two extra queries fused, re-ranked against the question, **no floor**.

Re-run: `python evals/judge.py --retrieval E1-baseline --split dev --floor 0.05 --tag=-live` and
`python evals/judge.py --retrieval E5-fused --split dev --floor 0.0`

## Results

| | Live | E5 |
|---|---|---|
| Pass rate, all | 0.31 | **0.58** |
| Correctness / grounding / completeness (mean) | 2.7 / 3.2 / 2.4 | 3.7 / 4.2 / 3.1 |
| Answerable: pass | 0.22 | 0.50 |
| Answerable: "NOT IN SOURCES" | 0.58 | 0.09 |
| Negative (false premise): pass | 0.44 | 0.76 |
| Out of scope: pass | 0.64 | **0.85** |
| Underspecified: pass (asked back) | 0.52 (0.48) | 0.57 (0.90) |
| Citations to passages that do not exist | 0 | 0 |

McNemar on pass: live alone 16, E5 alone 107, chi2 67: a clear gain. Cost: live $0.60, E5 $1.03.

## Meaning

- On the live server today most builders' questions get "not in the sources": the relevance floor removes the
  passages (E1). This is the main cause of poor answers.
- Without the floor the answer model still declines or asks back on out-of-scope questions (85% pass, up from
  64%), so the floor is not needed as a safety net.
- Half the answerable questions still fail the judge: missing documents (L143, HSG150, Approved Documents being
  parsed tonight), passages that hold only part of the answer, and judge strictness. Failing rows are in
  `evals/results/E5-fused-judge-dev.jsonl` with the judge's reasons.

## Cautions

- One judge model, no human calibration yet; a sample of judged rows should be read by a person.
- The answer model is Haiku 4.5, not the product's Haiku 5.5.

## Addendum: hybrid with no floor (two server settings, no code change)

`python evals/judge.py --retrieval E2-hybrid --split dev --floor 0.0`: settings `RAG_HYBRID=1`, `RAG_MIN_SCORE=0`.

| | Live | Hybrid, no floor | E5, no floor |
|---|---|---|---|
| Pass rate, all | 0.31 | 0.57 | 0.58 |
| Answerable pass ("NOT IN SOURCES") | 0.22 (0.58) | 0.52 (0.07) | 0.50 (0.09) |
| Negative pass | 0.44 | 0.66 | 0.76 |
| Out of scope pass | 0.64 | 0.77 | 0.85 |
| Underspecified pass | 0.52 | 0.67 | 0.57 |

McNemar on pass: live → hybrid 13 lost / 103 gained, chi2 70 (clear); hybrid → E5 30 / 31, chi2 0.02 (no
difference in answers, though E5 retrieves better and does better on false-premise and out-of-scope questions).

**Meaning:** the quick, reversible fix for the demo is two settings on the server (hybrid on, floor 0). The
search-tool change for the specialist's extra queries (E5) is the next step, not a precondition.
