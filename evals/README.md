# Evals

Quality checks for retrieval and answers: test questions, expected answers or sources, and scoring. Include Romanian and English questions.

How the evals work: [eval design](../architecture/design/eval/design.md). Plan and status: [PLAN.md](PLAN.md). Latest status: [REPORT-2026-11-21.md](REPORT-2026-11-21.md).

Regression gate for search: `python evals/gate.py check <run>` compares a dev run with the baseline question by question on rule coverage (lost, gained, paired test, must-pass list). Rule coverage (`evals/paired.py`) is the share of a question's rules (`golden/pooled/rules.jsonl`) that the first n passages state; it replaced yes/no "found" on 25 Nov 2026. Shown passages without a pool verdict make the check fail: judge them first. Run it before keeping any change to search, chunks or agent prompts; set a new baseline with `gate.py baseline <run>` when a change is kept. Files: `evals/gate/`.
