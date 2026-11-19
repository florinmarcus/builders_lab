# Methods from agentic-rag-lab, for builders_lab

Studied 19 Nov 2026. Read-only study of `/home/user/agentic-rag-lab` (called "the lab" below).
Methods only. No domain facts, no numbers presented as truths about our domain, nothing about any employer.
All paths are relative to `/home/user/agentic-rag-lab/`.

Lab numbers are quoted only to show what a method can reveal. They come from a 174-chunk corpus of three PDFs, so they will not carry over to our corpus.

---

## 1. Golden set

### How it was built (ADR 0006, `docs/adr/0006-golden-set-generated-then-checked.md`)
- **Two steps, done by separate passes.**
  1. **Business step.** An LLM agent plays a senior domain user. It reads the source documents the way a person would. It does **not** see the code, the parser, the section ids or the chunks. It writes the questions real users ask, with more on common topics and fewer on rare ones. Each question gets a reference answer and the clauses a person would cite.
  2. **Engineering step.** A second pass maps each question to the parser's section ids, most important first, with a confidence level (`high`/`low`) and an optional note.
- **Why blind:** questions written section by section copy the section's wording. That makes retrieval too easy and biases the test towards section chunking, which is the very thing being tested (ADR 0006 "Context").
- Generation ran **in a Claude Code session, not through the API**, so it had no cost line. It is a one-off tool, not part of the eval runner (ADR 0006; `golden/README.md` "Step 1").
- **Duplicates:** when two sections say the same thing, both are listed and finding either one counts (ADR 0006).

### Schema, one shortened example per file type
- Base question (`golden/analyst-questions.jsonl`, step 1, kept unchanged as the record):
  `{"id":"q-001","question":"...","kind":"negative","topic":"...","markets":"...","reference_answer":"...","cited_clauses":["X 6.1.1"],"multi_rule":true}`
- Labelled (`golden/labelled-questions.jsonl`, the source of truth) adds:
  `"expected_sections":["GR-6.1.1","GR-E"],"label_confidence":"high","label_note":"...","checked_by_hand":false,"type":"negative","granularity":"specific","vague":false`
- Kept and dropped (`golden/questions.jsonl`, `golden/dropped.jsonl`): output of the copy filter. Dropped rows add `shared_run`, `shared_with`, `shared_words`.
- Removed (`golden/removed.jsonl`): same row plus a required `removed_reason`. Never silently deleted.
- Exact terms (`golden/exact-terms.jsonl`, 40): `{"id":"x-001","question":"<CODE> segment: which ... uses this?","kind":"exact_term","exact_term":"<CODE>","multi_rule":false,"expected_sections":["..."]}`
- Near misses (`golden/near-misses.jsonl`, 10): `{"id":"nm-01","question":"...","kind":"near_miss","why":"sounds like a forecast","expect":"not blocked; answered or declined","expected_sections":[]}`
- Gate holdout (`golden/gate-holdout.jsonl`, 50) and guardrail topics (`golden/guardrail-topics.jsonl`, 50): `{"id":"gh-01","question":"...","kind":"should_block","group":"predict"}`
- Indirect attacks (`golden/indirect-attacks.jsonl`, 6): `{"id":"ia-01","question":"...","kind":"attack","type":"indirect injection","planted_section":"AT-...","canary":"ORANGE-FALCON","reference_answer":"Do not follow the planted instruction...","expected_sections":[]}`
- Data questions (`golden/data-questions.jsonl`, 24; design 13): store the **tool request** as the answer key; a build script runs it and writes `expected` and `reference_answer` (`lab/golden/data_build.py`). Answers come from code, never from a model.
- Broad data (`golden/broad-data-questions.jsonl`, 18): `"where"`, `"true_count"`, `"by_region"`, and a reference saying what a good summary looks like.

### Question types (`golden/README.md`, "Counts (338)")
- `answerable` 236 (70%), `negative` 29 (9%: the rule exists but does not apply, or a false premise), `out_of_scope` 40 (12%: not in the documents; aim was 15%), `attack` 18 (5%), `underspecified` 15 (4%: vague asks; the right answer asks for details).
- Flags across kinds: `multi_rule` (108, 32%), `granularity` broad/specific, `vague`.
- Separate sets for special purposes: exact terms (hybrid test), near misses (false-block test), should-block holdout (gate test), indirect attacks with a **canary word** (leak test).
- **Only questions with expected sections are used for retrieval scores.** Out-of-scope, attack and most vague questions are checked at answer level by code (`lab/evals/retrieval.py:28-32`).

### Copy filter (`lab/golden/copy_filter.py`)
- Drops a question that shares **5 or more words in a row** with an expected section's **text or heading** (`copy_filter.py:17`, `build.py:86-98`).
- Longest common substring on words, not characters (`copy_filter.py:25-44`). The word regex keeps dotted numbers and `%` whole and handles accents (`copy_filter.py:14`).
- The build **fails on an unknown section id**, so a typo cannot score as "not found" (`lab/golden/build.py:106-108`).
- Result in the lab: 0 dropped, because step 1 had already reworded 29 questions. Report the dropped count anyway.

### Holdout
- Rule (`docs/experiments/README.md`, "Don't test on what you tuned on"): when you tune a prompt or threshold on some questions, they stop being a fair test. Write a held-out set **before** seeing results, **commit it before the run** so git proves it came first, never tune on it, and report both sets.
- Used for the gate (`golden/gate-holdout.jsonl`) and for exact terms (`docs/experiments/e15-hybrid-fair.md`, "committed before any search ran").

### Review process
- Two adversarial expert reviews by LLMs read all questions plus the source PDFs (`golden/reviews/review-A.md`, `review-B.md`). Each claim was **checked against the source** before changing anything (`golden/README.md`, "Fix pass").
- What the reviews found: few factual errors, but the set was **too much "look up one clause"**. It lacked real cases, vague asks and out-of-scope asks. The fix: 55 removed (with reasons), 89 added. Contradictions in the source were flagged in the answer, and interpretations were marked as "readings".
- The plan was 30 hand checks marked `checked_by_hand`. **It never happened:** 0 rows are marked (`grep -c '"checked_by_hand": true'` gives 0).
- Tests guard the set (`tests/golden/test_questions.py:27-70`): every expected section exists; retrieval kinds have sections and the others have none; kinds and flags are from a known list; ids are unique; removed ids are gone; kept questions pass the filter; kept + dropped = labelled.

### Sizes
About 300 questions was the target "for stable numbers" (ADR 0006). The final set has 338, and 270 of them have sections. With 270 questions, one question is about 0.4 points of Recall@5.

---

## 2. Retrieval metrics (`lab/evals/retrieval.py`)
- **Recall@50** (in the candidates, before rerank), **Recall@5** (in the reranked top), **MRR** (1/rank in the top 5). A question counts as found if **any** expected section appears (`retrieval.py:35-61`).
- Extras, computed later from the saved rows with no new searches (`retrieval.py:64-84`):
  - `all5`: **every** expected section is in the top 5. This is the multi-rule score.
  - Precision@5 and `noise5`.
  - **nDCG@5**, graded: the first expected section gets grade 2, the others grade 1.
- **Chunk to section mapping:** scoring uses `chunk.section_id`, never the chunk text. So any chunker can be scored against the same labels (design 02 "Key ideas"; ADR 0004).
- **How k was chosen.** 50 candidates, then rerank to 5. This came from the production design the lab copies; there was no sweep. A Recall@10 test was planned but not run (`docs/experiments/README.md`, E14 "Top 5 vs top 10").
- **Key caution:** Recall@50 on 174 chunks is almost a third of the collection, so it is nearly free. Compare collections of different sizes only on Recall@5 after rerank (`docs/experiments/e1-section-vs-fixed-chunks.md`, "Cautions"; `docs/study/learning-notes.md:58`).
- **Breakdowns:** per `kind` (`retrieval.py:137-140`), multi-rule (`all5`), latency p50/p95 (`retrieval.py:128-134`). Before and after rerank comes from the same rows (top 5 of the candidates versus the reranked top).
- **Comparing two runs:** question by question (both / only A / only B / neither), with **McNemar** (a−b)²/(a+b). Above 4 is a clear difference; with several pairs the bar rises to about 6–7 (`retrieval.py:143-156`; `docs/experiments/README.md` intro).
- **Recording results:** per-question rows go to `results/retrieval-<collection-hash>-<rerank>[-hybrid].jsonl` and are copied into `docs/experiments/eN/`. The run name is a hash of the build config (`lab/domain.py:151-163`). Each `docs/experiments/eN-name.md` has these sections: Question; Set-up (exact config, golden commit hash, the re-run command); Results tables; McNemar table; Cost; What it means; Cautions/Limits; and "Found on the way" or "What went wrong". The index is `docs/experiments/README.md`, with one line per experiment giving its headline result.
- The eval **paces itself** to the rerank quota (`retrieval.py:23-25,103`).

---

## 3. Answer evals
### Judge (`lab/evals/judge.py`, design `docs/design/0007-judge.md`, ADR 0007)
- The judge is **code calling a pinned model with a fixed prompt**, never a chat. It runs **through Bedrock** (`model_client.converse`), so every call gets a cost line. Only question generation and the two golden reviews ran in Claude Code.
- **Three scores, 1–5, each with written anchors:** correctness (against the reference), grounding (against the **trace texts**, i.e. only what the tools returned), completeness (all rules needed, and their order) (`judge.py:24-55`).
- Special rules in the prompt: an expected decline scores 5 if the answer declines and names what is missing, 1 if it answers anyway. A "please give details" answer scores 5 on underspecified questions. A refusal scores 5 on grounding (`judge.py:33-35,43`).
- **Reason before score** for stability. JSON only. Pass = 4 or 5 (`judge.py:22,52`).
- **Blind to the model.** A test checks that the prompt does not name the model (`tests/evals/test_judge.py:52`).
- **Strict parsing:** extract the `{...}`, validate the types and that each score is 1–5. Retry once, then mark `unjudged`. Never guess a score (`judge.py:82-112`).
- **Cost control:**
  - Deduplicate passages in the trace (`judge.py:58-71`). This saved about a third of the judge's input.
  - Code checks out-of-scope and attack questions; the judge does not see them.
  - Results are written to a file and resumed, so a stopped run goes on (`judge.py:122-146`).
  - The second judge is a cheap open-weight model.
  - Batch inference at half price is in the parking lot.
- **Self-preference control:** the judge model differs from the answer model. With models from two families, **two judges** run, one from each family; if both rank the same way, the result holds (ADR 0007).

### Agreement and noise
- Weighted kappa, linear weights (`lab/evals/kappa.py:10-25`). The target was above 0.6 to trust the judge; below 0.4, fix the rubric.
- **Judge against judge** (`docs/experiments/e4-agent-models.md:106,121`): correctness 0.73, completeness 0.63, grounding 0.41. Grounding is the least stable score.
- **Judge noise** (same answers judged twice, `e4-agent-models.md:109-118`): pass flipped on 12% of answers, and grounding sometimes moves by 2 on its own. So they ran three rounds and took the majority.
- **Human agreement was never measured.** 40 hand scores were planned, with a phone scoring page, but never done. All judge scores stay "provisional" (`e4-agent-models.md:129`).
- **Baseline and flags** (design 07): commit the first full judged run. Later runs flag a question when a score falls by 2 or more, or pass becomes fail. Measure judge noise before trusting the threshold.

### Code checks next to the judge (`lab/evals/answers.py:84-113`)
These are rates over the golden set:
- declined by kind (out_of_scope should be near 1, the others near 0);
- `cited_only_read` (every citation id is in the trace);
- step-limit rate, tool calls, cost per question, p50/p95.
Attacks are checked by a **canary word** in the answer. Lesson (`docs/plan.md`, item 6): "canary in answer" also counts a refusal that *quotes* the canary, so tell "followed" apart from "reported".

### Grounding check (`lab/evals/grounding.py`)
- A managed guardrail's grounding score runs in **detect-only** mode on saved answers. The source is the deduplicated tool results, capped in size (`grounding.py:23-43`). Then it is compared with the judges' grounding scores over a range of thresholds before anything is allowed to block.
- The lab also has its own checks: citations that were never read, numbers that do not appear in the sources, and a small model checking each claim. All are detect-only (`docs/architecture.md`, "Answer checks").

---

## 4. Parsing and chunking
### Approach (`docs/design/0002-parse-and-chunk.md`, `lab/ingest/parse.py`, `lab/ingest/chunkers.py`)
- **The parser is the ground truth.** Each document becomes `Section(id, heading path, start, end, text)` once. Every chunker is labelled against these sections (design 02 "Key ideas").
- **One parse strategy per document, in a fixed table.** An unknown file **stops** the parse (`parse.py:131-146`). Strategies:
  - numbered headings (`parse.py:55-70`);
  - lettered headings (`parse.py:73-80`);
  - hand-listed headings for unnumbered documents, slugged into ids (`parse.py:83-91`).
- **Ids are stable and human-readable,** e.g. `GR-7.6.3`, from a prefix plus the clause number. The **heading path** is built from the parents ("7 X > 7.6 Y > 7.6.3 Z") (`parse.py:114-116`).
- **Character positions** for every section and chunk. A test checks that `text[start:end] == chunk.text` (`tests/ingest/test_chunkers.py:56-59`).
- **Curated pages:** repeated boilerplate and the parts that belong elsewhere are dropped (`parse.py:149-165`).
- `by_section`: one chunk per section. Split only above a ceiling, between lines, preferring a sentence end. All pieces keep the section id (`chunkers.py:229-271`).
- `fixed_size`: the baseline. Each chunk is labelled with the section that covers most of it (`main_section`, `chunkers.py:219-226`).
- **Heading path + text is what gets embedded,** and what the reranker reads, for both chunkers. This keeps the comparison fair (`lab/retrieval/search.py:217`).
- **Config hashing:** the collection name is a hash of the build config, so the same build always gets the same table. Rebuild from scratch; keep one table per variant (ADR 0005, `lab/domain.py:160-163`).

### Edge cases
- **Page headers and footers:** removed by regex before sections are found, so a section that runs over a page break reads as one text (`parse.py:15-16,47`). A test checks that none are left (`tests/ingest/test_parse.py:48`).
- **TOC:** dot-leader lines and the "Contents" line are dropped (`parse.py:17,49`).
- **Chapter banners:** a banner line plus the title line after it are skipped (`parse.py:18,41-46`).
- **Lists and footnotes that look like headings:** a top-level number counts as a heading only when written "6." (with a dot), so a footnote "6 Vietnam..." is not a heading (`parse.py:67-69`).
- **Title-only headings** (a heading followed directly by its children) do not become sections (`parse.py:112-113`).
- **Duplicate ids:** the second one is renamed `id~2` with a warning. The design said "stop", and the code chose to keep both (`parse.py:118-123`). The golden build refuses unknown ids.
- **Empty sections** are dropped.
- **Tables:** **no special handling** (design 02 "Errors and edge cases"). Noted problems: a whole list of exchanges ended up inside one unrelated section, and the dates of a schedule were only in a table chunk (`golden/README.md`, "Parser quirks"). **This is a gap for us,** because Approved Documents have many tables.
- **Footnotes** land wherever the PDF page puts them (README "Parser quirks").
- **Glossary/definitions:** kept out of the store on purpose, behind a config switch. The planned experiment (E2) never ran. Parking-lot idea: serve small lookup tables (a classification appendix) as **data through a tool, not as vector chunks** (`docs/plan.md` parking lot, "Country classification as data").
- **Cross-references:**
  - (a) `corpus/links.csv`: a hand-checked, many-to-many link table, with a test that every link exists, plus a `get_linked` tool (ADR 0016).
  - (b) `lab/ingest/references.py`: a hand-made list of external documents with their name variants. Ingestion finds the names in each section (longest first, blanking each match), records whether each target is **in the corpus**, and **fails the build on an unlisted .pdf link** (`references.py:40-87`). Search results can then say "not in these documents", so the agent stops searching.
- **Big sections:** whole lettered parts became one section, so 69 labels had low confidence. Section granularity matters for labelling.

### Tests ("no mocks", `tests/conftest.py`, `tests/ingest/`)
- Plain unit tests run on the **real corpus files**, with a module-scoped fixture that parses once (`tests/ingest/test_parse.py:14-90`). They check:
  - every PDF has sections;
  - ids are unique;
  - known ids exist with the right heading path;
  - positions match the text;
  - no headers are left;
  - an unknown file is refused;
  - curation drops the right parts.
- **Small hand-built documents** for exact logic: a two-section `Document` tests majority labelling, including ties and text before the first section (`tests/ingest/test_chunkers.py:20-47`).
- Real services are behind pytest markers `aws` and `db`, with a separate `rag_test` database fixture (`pyproject.toml:23-24`; `tests/conftest.py`). Behaviour of the model is measured as **rates over the golden set**, not hard tests.

### What experiments showed (`docs/experiments/e1-section-vs-fixed-chunks.md`)
- Section chunks clearly beat fixed size at 45, 90, 180 and 300 tokens (300 tokens is the managed Knowledge Base default). Recall@5 was 0.93 against 0.78–0.81, and McNemar was 27–35 on every pair. **Where you cut matters more than the size.**
- Section chunks without rerank were about as good as fixed chunks with rerank.
- Multi-rule questions are weak everywhere: only 45% had every needed section in the top 5.
- Embedding dimensions (1024, 512, 256) gave no clear loss (`docs/experiments/e10-embedding-sizes.md`).
- **Caution on the label rule:** majority labelling leaves some sections with no chunk at all. This biases the test towards section chunks. A fairer rule: a chunk is a hit if it **touches** an expected section (E1 "Cautions").
- The managed KB baseline (`docs/experiments/kb-bedrock-notes.md:33-44`) cut clauses mid-way and dropped headings from later chunks. It kept headers and footers glued to the text and turned the TOC into the longest chunks. That is a good argument for curated parsing.

---

## 5. Hybrid and rerank
- **Keyword search, two rankers:**
  - Postgres `tsvector` as a generated column, `to_tsvector('english', heading || ' ' || text)` (`lab/adapters/chunks.sql:15`). The query is `plainto_tsquery` with AND turned into OR, ranked with `ts_rank` (`lab/adapters/vector_store.py:112-113`).
  - **Real BM25** in plain Python, k1 = 1.2, b = 0.75. Its tokenizer keeps "7.6.3", "A-1" and "T+2" whole, drops stop words and strips plurals crudely. The index is built once per collection per process (`lab/retrieval/bm25.py:108-174`). Why: `ts_rank` has no IDF, so a rare code counts no more than a common word.
- **Fusion:** RRF with k = 60, keeping the constant fixed. Vector top 50 and keyword top 50 are merged, cut to 50, then reranked to 5 (`lab/retrieval/search.py:186-219`). Hybrid sits behind a config switch, off by default (ADR 0010).
- **Gains measured:**
  - E7: no clear change (`docs/experiments/e7-hybrid-search.md`).
  - E15, the fair re-test: BM25, plus 40 exact-term questions committed before the run (`docs/experiments/e15-hybrid-fair.md`). No clear gain. Golden set: 0.930 vector against 0.922 hybrid. Exact terms: 0.975 against 1.000, which is one rescued short appendix. BM25 and ts_rank were identical.
  - Their explanation: few chunks, headings embedded, and a reranker that reads the words. Revisit at thousands of chunks or with bare-code queries.
- **Rerank** (`docs/experiments/e9-rerank-amazon-vs-cohere.md`): top 50 to 5.
  - Rerank gave +11 points of Recall@5 on section chunks, clear by McNemar (E1 "With and without the rerank").
  - The two rerank models showed no clear difference; the cheaper one was kept.
  - **The rerank quota of 20 requests a minute** became the throughput limit. Evals had to pace themselves.

---

## 6. Doc style
- **AGENTS.md is short:** rules plus a "Read when you need it" table (file | when to read it). `CLAUDE.md` only does `@AGENTS.md` (`AGENTS.md:7-14`; ADR 0001). The point: agents load only what the task needs, and the instructions do not go stale.
- **ADRs are living:** edit an ADR when the decision changes, and delete it when it no longer holds. Git keeps the history. The index lists current decisions only (`docs/adr/README.md`). ADRs record measured outcomes, e.g. "Measured, and the decision now: keep it off" (ADR 0010).
- **`docs/architecture.md`:**
  - a dated one-line header;
  - Purpose;
  - three **mermaid** flowcharts (build time, question time, how we measure);
  - a **Parts table** (part | where | job);
  - failure behaviour;
  - config and collections;
  - data model;
  - "What is deliberately not here".
- **`docs/design/NNNN-*.md`:** one per part, **agreed before code**. The template (`docs/design/0000-template.md`): Status (draft/agreed/built), Date, Related; Purpose (and what it does *not* do); Where it fits (diagram); Modules and names; Data in and out; Flow (diagram); Errors and edge cases; Tests; Open questions.
- **Diagram rule:** mermaid `flowchart TB`, every label in double quotes (`docs/design/README.md`). The overview also uses sequence diagrams (`docs/design/0001-overview.md:293-381`).
- **Plan:** dated stages, each with a "Done when". An **experiment freeze** while the architecture changes. A **parking lot** for ideas that are out of scope (`docs/plan.md`).

---

## 7. Lessons and failures recorded
- **The human check of the judge never happened.** The 40 hand scores and the 30 hand-checked golden questions were both planned and both skipped, so judge scores stayed provisional (`e4-agent-models.md:129`). Do it early and keep it small.
- **Majority labelling biased the chunking test.** Some sections owned no chunk, so some questions could never be found (E1 "Cautions").
- **Recall@k is unfair across collections of different sizes** (E1).
- **A model-written golden set favours vector search** (plain language). They added exact-term questions to test keyword search fairly (E15).
- **The golden set was too lookup-heavy** at first. Adversarial reviews fixed the realism (README "Fix pass").
- **Big parser sections** gave low-confidence labels and hid clauses (README "Parser quirks").
- **Hidden daily token caps** stopped judge runs. The judge model had to be swapped mid-experiment. Batch inference is a fallback (`e4-agent-models.md:123-126`; ADR 0007).
- **Two processes writing one cost log** corrupted a line. Now each run has its own log file (E4 "What went wrong").
- **Rerank quota** limited both the eval speed and production throughput (E1 "Found on the way").
- **A canary metric counted refusals that quoted the canary as leaks** (`docs/plan.md`, freeze item 6).
- **A prompt change ("search each topic on its own") did nothing.** Decomposition in code was needed instead (E14, E18).
- **Error analysis method:** read about 20 failed answers with their traces and sort them into buckets: retrieval miss, wrong reading, incomplete multi-rule, wrong decline, not really a failure (judge too strict or reference wrong). Fix the biggest bucket first (`docs/plan.md`, Stage 5).
- **Fix the golden set first;** every later eval depends on it (`docs/plan.md`, "Next" item 1).

---

## 8. What to reuse in builders_lab
1. **Two-step blind golden set:** a role-played domain user writes questions and reference answers without seeing the code or chunks. A separate pass labels section ids, with confidence and notes.
2. **Copy filter** (5+ words in a row against the expected text or heading). Fail on unknown ids. Report the dropped count.
3. **Kinds:** answerable / negative (false premise) / out_of_scope / underspecified / attack, plus the flags `multi_rule` and `granularity`. Add separate exact-term and near-miss sets.
4. **Committed holdout sets,** written before the run and never tuned on.
5. **An adversarial review of the golden set** (LLM reviewers plus checking against the source), and a small real hand-checked sample. Keep `removed.jsonl` with reasons.
6. **Parser is the ground truth:** stable readable section ids, heading paths, character positions. One parse strategy per source type in a table; unknown inputs fail.
7. **Curation before chunking:** headers, footers, TOC and boilerplate removed, each with a test on the real files. **Plus explicit table handling, which the lab lacked.**
8. **Section chunks, embedded as heading path + text,** with a fixed-size baseline scored against the same section labels. Use a "touches the section" hit rule.
9. **A metadata graph from checked files:** a links table and a references table, with a test that every link resolves. Mark referenced documents as in or out of the corpus, so the agent knows when to stop. Small lookup tables served as tools, not chunks.
10. **Retrieval metrics:** Recall@candidates, Recall@k after rerank, MRR, nDCG@k, all-sections-in-top-k for multi-rule. Break down by kind. Compare question by question with McNemar.
11. **Hybrid behind a switch:** BM25 with a tokenizer that keeps codes whole (clause numbers like "B1.2"), RRF k = 60. Measure on an exact-term set. Add a reranker only if the evals show a gap; measure before and after rerank from the same rows.
12. **Judge:** pinned model, fixed prompt, three anchored 1–5 scores, reason before score, JSON with strict validation, retry once then `unjudged`. Blind to the model. Deduplicated trace as the grounding source. A judge from a different model family. Measure judge noise. Weighted kappa against a small hand-scored set before trusting it.
13. **Code checks as rates,** next to the judge: declined by kind, cited only what was read, a canary word for injection. Tell "followed" apart from "reported".
14. **A cost line per billed call** (model, unit, in, out, seconds, cost, run label). Prices dated. A separate log per process. Cost per question reported in every experiment.
15. **Doc style:**
    - short AGENTS.md with a "read when you need it" table;
    - living ADRs;
    - design docs from the template, agreed before code;
    - mermaid `flowchart TB` diagrams;
    - one experiment file per run, with the exact config, golden-set commit, re-run command, results, McNemar, cost, meaning and cautions;
    - a parking lot for out-of-scope ideas.
16. **Config hash → collection name;** rebuild from scratch; per-question result rows saved, so new metrics can be computed later with no new calls.

## What NOT to reuse
- Anything about that corpus:
  - its documents, section prefixes (GR/FF/FO/SP), question topics or examples, and reference answers;
  - the synthetic review data and data tools;
  - spec pages and the rules code;
  - the domain wording of the judge prompt.
- The lab's numbers as targets. They come from 174 chunks of one domain. Re-measure on our corpus.
- Its specific AWS choices: region, managed rerank models, guardrail set-up, the AgentCore deployment. Our hosting choice must follow builders_lab's own cost research (rule 3).
- The agent and conversation parts (gate, decomposer, history caps). These are out of scope for ingestion, retrieval and eval for now.
- The background-repo pointers in its AGENTS.md (a sibling personal repo, and the "production design this lab mirrors"). Nothing tied to anyone's employer.
- The "closed loop / learning Python" working rules. These are personal to that lab.
