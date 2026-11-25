# Query decomposer: prompt tuning

Goal: one fixed prompt that turns a builder's question into search queries with kinds (lanes, ADR 0016). It becomes
`versions/prompts/query_decomposer.v1.md` once tuned. Tune the prompt first, then the search.

- `split.json`: 60 dev questions to tune on, 30 others to check the winner (fixed seed, by kind). Holdout never used.
- `prompt-dN.md`: drafts. Only the winner is copied into `versions/prompts/` and locked.
- `haiku-runner.md`: the fixed brief each Haiku subagent gets (10 questions per subagent, each handled on its own;
  small risk that one question colours the next).
- `judge-v1.md`: the fixed judge instructions (Opus). It sees the question, Haiku's output, the reference answer,
  the expected sections with their kinds and the label, and checks coverage, invented facts, kinds, ask_back,
  outside_library and format. Verdict good, partly or bad, with a cause tag. Same judge every round.
- `run.py`: writes the batch inputs and scores the outputs. Results go to `evals/results/D-decompose-<draft>-<set>.jsonl`,
  each row with the prompt draft and its hash.

Model work runs as Claude Code subagents on the user's plan, not on our server (ADR 0006, ADR 0017).
