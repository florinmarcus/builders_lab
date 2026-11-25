# C1: Opus from memory against Opus with our regulations connector (25 Nov 2026)

**Question (Florin, 25 Nov):** how do our answers compare with a standard Opus that has no MCP and no vector search?

**Answer, on a 60-question sample:** the connector wins. Pass rate 0.95 against 0.82 (paired: B alone 10, A alone 2,
p = 0.04). Opus from memory made 6 wrong claims and cited one wrong document; with the connector it made none. Opus
from memory never said "I don't know": on out-of-scope questions it gave figures from memory (Scottish payment
periods, cable sizes). The gap is real but smaller than the J1 numbers suggested, because Opus already knows a lot.

## What was run

- Script: `evals/closed_book.py` (`sample`, `packets`, `score`). Answers and judge files stay in the session
  scratchpad, not git (they can quote corpus passages).
- Questions: 60 dev questions, stratified by kind (42 answerable, 8 false premise, 6 out of scope, 4 vague), seed
  20261125. Holdout never used.
- Same rules for both agents (cite, correct false beliefs, ask back when vague, say when not known, about 200 words).
  - **A:** Opus 5.5 helper, no tools, answers from memory.
  - **B:** Opus 5.5 helper with `search_regulations` on the live London server (1 to 3 searches per question, 75
    searches in all), told to answer only from the passages.
- Judge: Opus 5.5, blind. It saw both answers to a question as X and Y in random order, with the reference answer
  and the question's rules (`golden/pooled/rules.jsonl`), plus its own knowledge of the law. Pass = correctness ≥ 4
  and no serious error.
- Opus on Bedrock is not allowed for the eval user, so the helpers ran in a Claude Code session on Florin's plan.

## Results

| | A: memory | B: connector |
|---|---|---|
| Pass rate | 0.82 | **0.95** |
| Correctness (1-5) | 4.28 | **4.63** |
| Rules covered | 0.74 | **0.83** |
| Wrong claims | 6 | **0** |
| Serious errors | 0 | 0 |
| Wrong or made-up citation | 1 | 0 |

By kind (pass rate, A then B): answerable 0.81 / 0.93; false premise 0.88 / 1.00; out of scope 0.67 / 1.00;
vague 1.00 / 1.00 (rules covered 0.88 / 0.71: B asked back more and said less).

Where they differ:
- **B better (10):** HSE says no water suppression on electric cut-off saws (A allowed it); the CIS group exemption
  (A denied it exists); VAT on renovating empty homes (A cited the conversions group); joined towers as separate
  higher-risk buildings; Awaab's Law and cladding; the 2026 procurement Order (A gave the wrong law and date);
  tenure scope of the consumer standards; and two out-of-scope questions where A gave figures from memory.
- **A better (2):** CIS gross payment after a reorganisation (B said it did not know the second half); asbestos
  short-duration work (B misread the job as licensed).

## Meaning

- The library adds most where Opus's memory is thin or out of date: HSE detail, CIS and VAT rules, 2025 and 2026
  changes (Awaab's Law, the procurement Order, the new regime for higher-risk buildings).
- The safety gain is in what A does not do: it never declines, so out-of-scope questions get confident figures.
- B's two losses are reading errors on passages it had, not missing documents.

## Cautions

- 60 questions: the confidence interval is wide. The full 299 would firm it up.
- The judge is Opus, the same model as both agents. It is blind and the same for both, but it may share Opus's gaps:
  some of A's errors may go unseen. Not checked by a person.
- The rules were written from our library, which may favour B slightly. The wrong-claims count does not depend on
  them.
- Helpers answered 15 questions each in one go, not one at a time as a user would ask.
