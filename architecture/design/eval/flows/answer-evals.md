# Flow: answer evals

Two checks on what a builder would get: the passages one search returns, and the answer Claude writes.
Up: [eval design](../design.md). Both use dev questions only and one Opus judge.

```mermaid
flowchart TB
    q[("Dev questions")] --> s1["1. answer_set.py packets<br/>80 questions, 8 passages per run<br/>(top 8, or 2 per lane)"]
    s1 --> j1["2. Opus judge, blind, packets of 4:<br/>2 full, 1 partly (what is missing), 0 none"]
    j1 --> m1["3. answer_set.py merge, score, compare<br/>share of full answers, kappa on the re-check"]
    q --> s2["4. closed_book.py sample"]
    s2 --> a2["5. Opus answers twice:<br/>from memory, and with the connector"]
    a2 --> j2["6. closed_book.py packets: one Opus judge, blind"]
    j2 --> m2["7. closed_book.py score<br/>pass rates, McNemar"]
```

- **Answer sets.** The same number of passages per run, so lanes do not win only by showing more. "What is
  missing" points at the fix: a missing law at lanes, a missing second rule at the decomposer. Grades:
  `pooled/answer-sets-v2.jsonl`; brief: `evals/golden/ANSWER-SET-BRIEF.md`.
- **Closed book (C1)** shows what the connector adds over the model's memory. Answers and packets stay out of git.
