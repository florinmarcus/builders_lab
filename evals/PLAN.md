# Plan: retrieval and answer quality (from 21 Nov 2026)

Owner: Florin. Status report: [REPORT-2026-11-21.md](REPORT-2026-11-21.md). Each step needs Florin's yes before it starts.

## Current focus (Florin, 21 Nov evening)

**Retrieval only, vector search first.** Nothing else moves until retrieval is strong. Then the judge (step 3).

| Step | Status |
|---|---|
| 1. Miss analysis | done: [experiments/L1-miss-analysis.md](experiments/L1-miss-analysis.md) |
| 2. Experiments driven by step 1 | **in progress**: out-of-date sources removed (V1, no significant change); next, the embedded chunk text |
| 3. Local judge | on hold until retrieval is strong |
| 4. Multi-turn scenarios | on hold |
| 5. Traces and logs | on hold |

**Order of work (Florin, 21 Nov late): bottom up, one document at a time.**
1. **Parse.** Every guidance document parses cleanly, PDFs first (they matter most; legislation is already good).
   Per document, follow the runbook `.claude/skills/corpus-document/SKILL.md`:
   - fix structure in the parser code, with a test (a strategy per document family where needed)
   - run the model checks through packets, with Sonnet subagents in Claude Code (not Bedrock)
   - check every figure crop against its page image; nothing moves until the crops are right
   - review sheet, tests, commit
2. **Chunk.** Only when every document is parsed: check each document's chunks (size, heading path, context, no
   mixed topics).
3. **Ingest and verify the vectors.** Load, then measure vector-only recall on dev.

**Flow per document family, parse to vectors (status 22 Nov night).** Green: done. Amber: in progress.
Grey: not started. Each parser's own diagram is in
[regulations-corpus.md](../architecture/design/regulations-corpus.md).

```mermaid
flowchart LR
    subgraph parse["1. Parse: one parser per document family"]
        leg["Legislation XML<br/>parse_legislation"]:::done
        adoc["Approved Documents PDF<br/>parse_adoc<br/>27 bad crops being fixed"]:::wip
        hse["HSE and other guidance PDFs<br/>parse_pdf<br/>~320 bad crops and false figures<br/>being fixed"]:::wip
        guide["Fire risk assessment guides, 13 PDFs<br/>parse_guide<br/>907 checks saved, 0 open"]:::done
        flats["Flats guide<br/>parse_flats"]:::wip
        book["4 Home Office booklets<br/>parse_booklet"]:::wip
        html["GOV.UK and HSE web pages<br/>parse_html<br/>weak structure, not in scope yet"]:::todo
    end
    crop["Crop check<br/>Sonnet: crop next to its page,<br/>box in red; 0 bad"]:::wip
    mc["Model checks<br/>Sonnet packets: tables and<br/>figure descriptions; 0 open"]:::wip
    rev["Review sheet + tests<br/>document is clean"]:::wip
    chunk["2. Chunk: chunk.py<br/>check size, heading path,<br/>no mixed topics"]:::todo
    emb["3. Embed: Titan v2<br/>load local Postgres<br/>corpus_next"]:::todo
    rec["Vector-only recall, dev 299<br/>baseline R@5 0.51, R@50 0.80"]:::todo
    adoc --> crop
    hse --> crop
    guide --> crop
    flats --> crop
    book --> crop
    crop --> mc --> rev
    leg --> rev
    html -.-> chunk
    rev --> chunk --> emb --> rec
    classDef done fill:#cfe8cf,stroke:#3a7d3a
    classDef wip fill:#fde9c4,stroke:#b07d1a
    classDef todo fill:#e6e6e6,stroke:#888
```

Progress (22 Nov night, working alone while Florin sleeps):
- Fire safety risk assessment guides (13 files): new parser `parse_guide.py` (commit 8e8e8f5). Model checks running
  with Sonnet, headless Claude Code.
- Flats guide and 4 short fire safety guides: parser work in progress.
- Crop check (`system/rag/cropcheck.py`): Sonnet judges every crop against its page. It was chosen over Haiku on
  HSG33. It is now running over every PDF source; bad crops are parser bugs to fix before the model checks.

Inventory (21 Nov): 139 non-legislation sources. 47 have open model checks, 1,468 in total. The biggest are:
- fso-guidance-collection: 511
- br-circulars: 129
- supplier-information: 91
- Approved Documents E, M, H: 89, 73, 45
- HSG247: 73
- HSG33: 55

Main metric now: vector-only Recall@5 and Recall@50 on dev 299, before keyword search and rerank. Baseline (V0):
0.51 and 0.80. Runs use the full corpus in a throwaway local Postgres; live is not touched.

## Ground rules (Florin, 21 Nov)

- **No LLM on AWS.** Only the embedder (Titan v2) and the reranker (Amazon Rerank) stay on Bedrock.
- **Judges run locally in Claude Code** on the user's plan: Opus and Sonnet (or Fable and Opus). No Bedrock bill, no
  pipeline.
- **Investigate before tuning.** Find where recall is lost first, then change things.
- **No overfitting.**
  - Decide changes on dev only.
  - Check the holdout once per milestone. Never tune on it.
  - Report 95% confidence intervals: about ±0.06 at 273 questions.
  - Use McNemar for paired comparisons.
- **Trace everything.** Every judged answer keeps the trace of its tool calls.
- Each step writes its results to `evals/results/` and a short note to `evals/experiments/`.

## Step 1: miss analysis (where recall is lost)

**Input.** Run the full corpus (`corpus_next`, 186 sources, 40,075 chunks) on all 299 v2 dev questions with the
live search settings: hybrid on, no relevance cut-off. Save every candidate, its rank and its score.

**Where it runs.**
- The Frankfurt database accepts connections only from the live server's IP and Florin's laptop.
- So the run happens inside the live server, using its read-only database user, with `RAG_SCHEMA=corpus_next`.
  The other option is Florin's laptop.
- It reads only. Live data and the live corpus are not touched.
- About 6 s per search, so about 30 minutes in total.
- While it runs, it uses up to 2 of the 5 database connections, so live regulation searches may be slower. Run it
  when no one is using the app.

**Analysis.** Sort every question with no hit in the top 5 into one cause:

| Cause | How we tell |
|---|---|
| Document missing | expected source not in the corpus |
| Parse error | the expected text is missing or broken in the parsed tree |
| Chunk problem | the answer is split across chunks, buried in a large chunk, or the chunk lacks its heading |
| Ranking | the expected chunk is in the top 50 but not the top 5 |
| Embedding or keyword | the expected chunk is not in the top 50 although its text is fine |
| Label wrong | the expected section does not answer the question, or another section does |

**Breakdowns:**
- by role, kind, document and chunk type (paragraph, table row, definition)
- by chunk length
- multi-rule against single-rule questions

**Done when:** a table of miss counts per cause, 10 worked examples per cause, and a ranked list of fixes.

## Step 2: experiments driven by step 1

Order (from step 1's findings): (a) out-of-date sources out of the index (V1, done); (b) document title and full
heading path in every embedded text; (c) merge tiny chunks with their neighbours under the same heading; (d) a
parsing strategy per family, starting with the Home Office fire safety guides; (e) the vocabulary gap.

Pick the fixes from step 1's counts, biggest first. Possible fixes:
- re-parse the documents that cause errors
- add the parent heading to each chunk
- merge short sibling sections
- try chunk sizes and overlap
- improve the keyword weights

**Rules:**
- One change at a time, all measured on dev with the same metrics: R@5 strict and pooled, R@50, MRR, nDCG, all@5.
- Holdout once, at the end.

## Step 3: local LLM judge in Claude Code

- Port `evals/judge.py` so the answers and the judging run in Claude Code headless (`claude -p`).
- No Bedrock models.
- **Answers:** run the real flow: the plugin, the router, the specialist, then `verify_answer`.
- **Judges:** two Claude models. Measure how often they agree (Cohen's kappa). Disagreements go to a person.
- **Calibration:** Florin, or a builder, reads about 50 judged answers. Report how often the judge agrees with the
  person.
- **Criteria:** the same as now (correctness, grounding, completeness, each 1-5 with the reason first). Add:
  - source cited correctly (document, section, edition date)
  - safety rules kept (asbestos, approvals, drafts only)
  - language: Romanian answers keep the UK terms

## Step 4: multi-turn scenarios

- Add about 20 conversations of 3-4 exchanges to the golden set. Examples:
  - a follow-up ("and for flats?")
  - a correction ("no, I meant the bedroom")
  - Romanian, then English
  - a safety push ("just say there's no asbestos")
- Each turn has its own reference answer and expected sections.
- The judge scores each turn and the conversation as a whole.

## Step 5: traces and logs

- One trace id per answer, linking every tool call (S9).
- Retrieval logs on the server for each search: query, candidates with scores, reranked list, time per stage.
- The local judge saves the trace with each judged row, so every failure can be followed down to the search.

## Later

- Promote the full corpus once the database is fast enough (S88).
- Run step 2's winner on live.
