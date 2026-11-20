# Golden set, business pass: brief for question writers

Method: agentic-rag-lab (`research/methods/agentic-rag-lab-lessons.md`, section 1), adapted for builders_lab. Written 20 Nov 2026 for the overnight run (`corpus/OVERNIGHT-PLAN.md`, S5).

## Who you are

You play a real person at a small UK building firm (role given in your task). You know your trade, not the documents by heart. You ask the questions you actually face on jobs, in your own words: short, practical, sometimes vague, sometimes with a wrong assumption.

## What you may read

Only the source documents, the way a person reads them: `python evals/tools/read_source.py <source_id>` (plain text from the raw files; `--pages 3-9` for long PDFs; `--list` for the catalogue). Also `research/domain/builder-questions.md` (which topics come up most) and `research/summary.md`.

**Never** read `corpus/parsed/`, `corpus/chunks/`, `corpus/coverage.md`, `corpus/fixes/`, `system/` code or any other golden-set file. Questions written while looking at chunks copy their wording and make retrieval too easy (the whole point is to test search fairly).

Unavailable tonight (no raw file): ba1984, ess2020, gpdo-2015, riddor2013, rbca-2024, rra2025. Do not write answerable questions that only these could answer.

## What to write

About 65 questions for your area, weighted by how often a builder meets the topic (common topics get more questions). For each, write the question as the builder would say it, then find the answer in the documents and record it.

Kinds (rough shares):
- `answerable` (about 70%): the documents answer it. Mix easy one-clause lookups with real cases ("we're doing X in a council flat, Y happened, what now?"). At least a third should need two or more clauses or documents (`multi_rule: true`).
- `negative` (about 10%): a false premise or a rule that does not apply ("Do I need a licence to drill a vinyl tile?" when the documents say it is non-licensed). The reference answer corrects the premise and cites what applies.
- `out_of_scope` (about 12%): a plausible builder question the listed documents do not answer (for example planning permission detail, Scottish or Welsh rules, product prices, BS 7671 wiring detail). Reference answer: say it is not covered and what would be needed. No cited clauses.
- `underspecified` (about 8%): too vague to answer without details ("Is this asbestos?"). Reference answer: what details are needed, plus what the documents say in general. Cite clauses if any.

Rules:
- Do not copy wording from the documents: say it as the builder would. Never repeat 5 or more words in a row from the text you cite.
- Reference answers: short (2 to 5 sentences), plain English, only what the documents say; note when the answer depends on dates (rules changing in 2026 or 2027) or on England versus Wales.
- `cited_clauses`: what a person would cite, with the source id, e.g. `"car2012 regulation 7(1)"`, `"hse-hsg264 paragraph 47"`, `"adb paragraph 3.22"`, `"hmrc-cis-340 section 3.5"`, `"awaab-guidance-phase2 Table 2"`. Most important first. Give the clause number and, where helpful, its heading words.
- `granularity`: `specific` (one rule or number) or `broad` (an overview across several rules).
- Spread across your documents; do not write more than about 8 questions from any one document unless it is central to your role.
- Business questions only: no attacks, no prompt injection, no questions about the AI itself.

## Output

One JSON object per line in `evals/golden/business/<role>.jsonl`:

```json
{"id": "<role>-001", "role": "<role>", "question": "...", "kind": "answerable", "topic": "...", "reference_answer": "...", "cited_clauses": ["car2012 regulation 7(1)", "hse-l143 paragraph 220"], "sources_read": ["car2012", "hse-l143"], "multi_rule": true, "granularity": "specific", "vague": false}
```

Write the file with the Write tool (valid JSON per line). Do not edit any other file. Do not commit.
