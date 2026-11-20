# Golden set: labelling pass brief

The second, separate step of the golden set (agentic-rag-lab method, `research/methods/agentic-rag-lab-lessons.md`).
The business pass wrote questions and reference answers from the documents, blind to the parser. This pass maps
each question to the **section ids** in the parsed trees that hold its answer, so retrieval can be scored.

## Input and output

- Input: `evals/golden/business/<role>.jsonl`. Use `question`, `kind`, `reference_answer`, `cited_clauses`, `sources_read`.
- Output: `evals/golden/labelled/<role>.jsonl`, one line per question, every id:

```json
{"id": "asbestos-007", "expected_sections": ["car2012:regulation-8", "hse-l143:para-123"],
 "label_confidence": "high", "label_note": "reg 8 is the licence duty; L143 para 123 lists licensable work",
 "missing": []}
```

- `expected_sections`: keys `"<source_id>:<section_id>"`. **First** the one section that best answers the question
  (it gets the higher grade in nDCG), then any others the answer truly needs (a multi-rule question needs all of them).
  Usually 1 to 4 keys. Not a list of everything related.
- `label_confidence`: `high` (the section plainly states the answer), `medium` (it holds the answer, but other
  sections could also do), `low` (a best guess).
- `missing`: cited clauses you could not find in any parsed tree, as `"<source_id>: <clause>"`, e.g. a PDF that has
  no current tree yet. Still label what you can find.
- `negative` questions (false premise): label the section that shows the premise is wrong.
- `out_of_scope` and `underspecified` questions: `expected_sections: []`, unless an underspecified question has a
  clear section that would answer every reading (then label it, `medium`).

## How to find sections

```
python evals/tools/find_sections.py <source_id> <words...> [--text]
python evals/tools/find_sections.py <source_id> --ids <section_id> ...
```

Run it from the repo root with the venv Python (the lead gives you the path) and `PYTHONUTF8=1`. Or read
`corpus/parsed/<source_id>/*.json` directly (only trees whose `valid_to` is empty are current).

- Prefer the most specific section that holds the answer: a regulation paragraph, a numbered guidance paragraph,
  a table. Not the chapter, part or heading above it. A whole regulation is fine when the answer spans its paragraphs.
  Scoring counts a parent or child of the expected section as a hit ("touches the section").
- Check the section's text really says it. Do not label from the title alone.
- If the reference answer looks wrong against the document, keep the label, set `low`, and say so in `label_note`.

## Rules

- Do not run any search, embeddings or the retrieval eval. Do not open `evals/results/`.
- Do not change the business files, parsers, trees or anything outside your one output file.
- Every key must exist (`python evals/golden/build.py` fails on unknown ids). Check them with `--ids` before you finish.
- Report counts: labelled, by confidence, questions with `missing`, and the sources that were missing most.
