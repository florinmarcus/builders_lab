# C1: Opus from memory against Opus with our regulations connector (25-26 Nov 2026)

**Question (Florin, 25 Nov):** how do our answers compare with a standard Opus that has no MCP and no vector search?

**Answer, on the whole dev set (342 questions, 26 Nov):** the connector wins clearly. Pass rate 0.93 against 0.82.
On the same questions, B alone passed 52 and A alone 16 (p < 0.0001). Opus from memory made 47 wrong claims and 8
serious errors; with the connector, 13 and 3. Without the out-of-scope questions (303), the pass rate is 0.93 against
0.80 and the wrong claims 9 against 47.

The first run on 60 questions (25 Nov) gave the same picture: 0.95 against 0.82, p = 0.04.

## What was run

- Script: `evals/closed_book.py` (`sample --all`, `packets`, `score`). Answers and judge files stay in the session
  scratchpad, not git (they can quote corpus passages).
- Questions: all 342 dev questions (241 answerable, 41 false premise, 39 out of scope, 21 vague). The 60 answers
  from the first run were reused; the other 282 were new. Holdout never used.
- Same rules for both agents (cite, correct false beliefs, ask back when vague, say when not known, about 200 words).
  - **A:** Opus 5.5 helper, no tools, answers from memory.
  - **B:** Opus 5.5 helper with `search_regulations` on the live London server, told to answer only from the
    passages.
- Judge: Opus 5.5, blind. It saw both answers to a question as X and Y in random order, with the reference answer
  and the question's rules (`golden/pooled/rules.jsonl`), plus its own knowledge of the law. Pass = correctness ≥ 4
  and no serious error. All 342 were judged again with one rule set, including the first 60.
- Changed judge rule (Florin, 26 Nov): on out-of-scope questions, a correct answer from memory counts as good. "I
  don't know" is not required there. That is why the headline is also given without those questions.
- Opus on Bedrock is not allowed for the eval user, so the helpers ran in a Claude Code session on Florin's plan.

## Results

| | A: memory | B: connector |
|---|---|---|
| Pass rate, all 342 | 0.82 | **0.93** |
| Pass rate, without out of scope (303) | 0.80 | **0.93** |
| Correctness (1-5), all | 4.17 | **4.44** |
| Rules covered | 0.66 | **0.78** |
| Wrong claims, all | 47 | **13** |
| Serious errors, all | 8 | **3** |
| Wrong or made-up citation | 1 | 1 |

Paired: both passed 265, B alone 52, A alone 16, neither 9 (exact McNemar p < 0.0001). Without out of scope: B
alone 52, A alone 13.

By kind (pass rate, A then B):
- answerable 0.77 / **0.92** (wrong claims 41 / 8, serious errors 8 / 1)
- false premise 0.93 / 0.98
- vague 0.90 / 0.95
- out of scope **1.00** / 0.92: here memory wins. B made 2 serious errors on topics outside the library (planning
  limits for a rear extension, UN numbers for asbestos waste).

## Where they differ

**B better (52).** Mostly out-of-date or half-remembered rules in A:
- Old figures: flat roof and rooflight U-values, trickle vent sizes, the old HHSRS bands and 29-hazard list (changed
  in 2026), the electrical safety catch-up date for social housing.
- 2025 and 2026 changes: Approved Document B amendments, evacuation lifts, second staircase, the procurement Order.
- Detailed scope rules: Awaab's Law (tenant-caused hazards, fire doors, district heating), joined towers as higher-risk
  buildings, storey counting.
- CIS and asbestos: labour agencies under CIS, the group exemption, the licence for scaffolding next to licensed work,
  notifying a programme of Artex jobs once.
- Several where A declined or hedged on a question the library answers.

**A better (16; 13 without out of scope).** Mostly where B said "the library does not say" or read a passage wrongly:
- Missing points: the 42 degree stair pitch, duties at the lower noise action value, resident duties in higher-risk
  buildings, the sleeving method for pipes, flat front doors under the Fire Safety Act.
- Reading errors: the short-duration asbestos test (read as licensed work), CIS verification timing.
- Out of scope: 3 questions where B answered outside the library and got it wrong.

## Meaning

- The library adds most where Opus's memory is out of date or thin: 2025 and 2026 changes, exact figures, HSE and HMRC
  detail, Awaab's Law. These are also where a builder gets hurt by a wrong answer.
- Wrong claims drop by about three quarters (47 to 13; 41 to 8 on answerable questions).
- B's losses are mostly retrieval misses (the passage was not found, so B said it did not know) and a few reading
  errors. That is the target for the retrieval work in ADR 0016 and the baseline (S151).
- Outside the library, B should say so and not answer from memory: its 2 serious errors there break the server rule.

## Cautions

- The judge is Opus, the same model as both agents. It is blind and the same for both, but it may share Opus's gaps:
  some of A's errors may go unseen. Not checked by a person.
- The rules were written from our library, which may favour B slightly. The wrong-claims count depends on them less.
- Helpers answered 15 questions each in one go, not one at a time as a user would ask.
- The first 60 answers were written a day earlier than the other 282, with the same rules and the same server.
