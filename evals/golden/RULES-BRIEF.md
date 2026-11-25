# Rules brief (25 Nov 2026)

Given unchanged to the rules writer. One call per question set, done once; the rules are stored in
`evals/golden/pooled/rules.jsonl` and every pool judge call for that question gets the same list (the first step of
GOV.UK Chat's context relevancy judge, `evals/knowledge/notes/uk-government-ai-evals/prompts/govuk-chat/`).
Florin checks them before they are used. The writer sees the question, the reference answer and the label note,
never a retrieved passage, so the rules cannot lean towards what search found.

---

You write down what a correct answer to a builder's question rests on.

For each question you get `id`, `question`, `reference_answer` (an expert's answer) and `label_note` (the labeller's
note on which provisions hold the answer). Write two things.

**1. scope:** one line: who is asking or acting, where (England, Wales, UK), and what work or building. Only what
the question says or clearly implies; write "not stated" for a part it does not give. Example: "contractor; England;
kitchen refit in occupied council flats".

**2. rules:** the 1 to 3 rules the reference answer rests on. A rule is one duty, limit, threshold, time, exception
or test that a source states, and that the answer needs to be right.
- One rule per item, as a plain sentence in your own words, with its specific point (the number, the time limit,
  who must do what).
- Only rules the reference answer uses. No background, no next steps, no advice.
- Most questions need 1 or 2. Use 3 only when the answer truly combines three separate rules.
- If the answer is "no" or "not allowed", the rule is still a rule ("A management survey is not enough before
  refurbishment where it was not intrusive in the area to be disturbed").
- Do not name a document or section: the rule must be checkable against any source that states it.

Write one JSON line per question, in the same order, to the output file you are given:
`{"id": "...", "scope": "...", "rules": ["...", "..."], "judge": "<name you are given>"}`

Write nothing else to the file. Reply with only the number of lines written.
