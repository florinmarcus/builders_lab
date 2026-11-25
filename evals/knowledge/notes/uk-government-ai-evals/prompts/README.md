# Published UK government judge prompts (copies)

Copied 25 Nov 2026, unchanged, so we can read them next to our own judge briefs. Both repos are MIT licensed:
- `consult/`: i.AI Consult, https://github.com/i-dot-ai/consult (commit 448549a), folder
  `themefinder/evals/adapters/evaluators/prompts/`. MIT License, Copyright (c) 2024 i.AI.
- `govuk-chat/`: GDS GOV.UK Chat, https://github.com/alphagov/govuk-chat-evaluation (commit 394ce0b), folder
  `govuk_chat_evaluation/rag_answers/custom_deepeval/metrics/*/template.py` (Python wrapped in Markdown).
  MIT License, Copyright (c) 2025 Crown Copyright (Government Digital Service).

The pattern: each criterion has its own judge, and each judge does one narrow job.

| File | What it judges | Verdict shape |
|---|---|---|
| `consult/binary_match.md` | Does one item match any item in a list? Quote the matches word for word | PASS / FAIL + matched items + reasoning |
| `consult/generation.md` | How well each topic in list 1 is caught by list 2 | STRONG / PARTIAL / NO, one calibration example each |
| `consult/condensation.md`, `consult/refinement.md` | Did merging or rewriting themes lose or invent anything? | per item |
| `consult/clarity.md`, `consult/title_specificity.md` | Are theme titles clear and specific? | per title |
| `consult/planted-judge-test.md` | Test: one valid rewording, one lost theme, one invented theme, run on the real judge | test asserts |
| `govuk-chat/context_relevancy.md` | Do the retrieved passages meet the question? Three calls: question to information needs; passages to facts with their scope; yes / no / idk per need | per need |
| `govuk-chat/factual_precision_recall.md` | Answer against reference: each key fact sorted TP / FP / FN; code computes precision and recall | fact lists |
| `govuk-chat/absence_of_factual_contradictions.md` | Claims from the answer, truths from the reference, verdict per claim | per claim |
| `govuk-chat/coherence.md` | Is the answer coherent? | score |

Lessons drawn from them: `../../../eval-practice-assessment.md`, "Lessons from published UK government judge prompts".
