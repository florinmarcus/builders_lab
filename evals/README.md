# Evals

Quality checks for retrieval and answers: test questions, expected answers or sources, and scoring. Include Romanian and English questions.

Plan for retrieval and answer quality: [PLAN.md](PLAN.md). Latest status: [REPORT-2026-11-21.md](REPORT-2026-11-21.md).

Regression gate for search: `python evals/gate.py check <run>` compares a dev run with the baseline question by question (lost, gained, paired test, must-pass list). Run it before keeping any change to search, chunks or agent prompts; set a new baseline with `gate.py baseline <run>` when a change is kept. Files: `evals/gate/`.
