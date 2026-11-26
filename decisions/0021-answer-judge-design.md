# 0021: Answer judge: search plus Sonnet, pass or fail per criterion, judge chosen by human labels

Date: 26 Nov 2026. Status: accepted (Florin, 26 Nov 2026). Plan: `evals/PLAN.md` step 3.

## Context

Retrieval has a gate (rule coverage, `evals/gate.py`), but answers have no trusted judge and no baseline. The first
answer judge (`evals/judge.py`, 21 Nov) used Bedrock models and 1-5 scores, with no human check and no noise number.
C1 (25-26 Nov) judged Opus answers side by side with an Opus judge, one run. A baseline needs each answer judged on
its own, three runs, and a judge checked against a person.

## Decision

1. **What we judge:** search plus a fixed answer model. Sonnet 5.5 answers with `search_regulations` and
   `lookup_terms` on the live regulations server only. Not the plugin or the firm server (demo work). Sonnet is an
   assumption about what builders run (S160).
2. **Criteria:** pass or fail each, reason first: correct, grounded, complete (the question's rules), right
   behaviour for the kind, no serious error. Pass only if all five pass.
3. **Out of scope:** the server rule wins. A correct answer from memory on an out-of-scope question is a fail.
   This replaces the C1 judge rule of 26 Nov.
4. **The judge is chosen by Florin's labels, not up front:** candidates Opus 5.5, Fable 5.2, maybe Haiku 5.5, never
   the answer model. Order: catch rate on Florin's fails and kappa, then noise (flip rate between two runs), then cost.
5. **Baseline:** three Sonnet runs on dev, judged once each, majority vote per question, stored. Changes are compared
   question by question (must-pass, floor, McNemar on the votes). Holdout once per milestone.

## Options considered

- The real plugin flow as the thing judged: closer to the product, but the plugin is demo work and slower to run.
- Opus as the answer model: matches C1, but uses much more of Florin's plan and would judge its own model.
- 1-5 scores: people agree less on a 3 or a 4 than on pass or fail, and the gate needs pass or fail.

## Consequences

- Florin labels 60-100 answers before any judge is trusted.
- Stale reference answers had to be fixed first (S146, `evals/golden/rescope.py`).
- `evals/judge.py` stays only as a record; new answer runs follow this ADR.
