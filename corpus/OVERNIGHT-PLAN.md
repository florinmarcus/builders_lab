# Overnight plan: whole corpus, retrieval evals, Recall@5 above 90%

**Living document.** Started 20 Nov 2026, evening, by Florin's request. Stages are changed, split or added as the work teaches us; every change is logged at the bottom with the reason. Each stage has a test that decides "done". A replanner agent is called when a stage is blocked or its test fails twice (see "Replanning").

## Goal

By the morning of 21 Nov 2026:

1. The rest of the corpus is parsed with the same engineering as the pilot (ADR 0010): structure-aware parsers, tests first, model checks for tables and figures saved as fixes, 0 open checks.
2. Chunked by structure, validated, embedded (Titan V2), loaded into a **staging** schema.
3. A business-driven golden set (agentic-rag-lab method, `research/methods/agentic-rag-lab-lessons.md`), used for **both** retrieval evals and the LLM-as-judge answer eval.
4. A loop of measured improvements (parser, chunking, hybrid, re-rank, settings) until **Recall@5 ≥ 0.90** on the dev set, with **Recall@50** tracked as the first-stage ceiling. Holdout reported, never tuned on.
5. The live demo still works, and is never worse than tonight.

## Rules for the night (do not break these)

- **The demo stays safe.** The server reads schema `corpus` on the corpus database. All new loads go to schema `corpus_next`. Promotion (stage 9) swaps schemas in one transaction, keeps the old one as `corpus_prev` for a one-command rollback, and happens only if every promotion check passes. No change to the server's settings or code paths that it uses, unless tested and needed.
- **No surprises on the phone.** Promotion requires the demo smoke set (the top builder questions, `research/domain/builder-questions.md`) to be at least as good as the live corpus, question by question.
- **Skip the 4 restricted sources** (copyrighted text would reach the public repo through `corpus/fixes/`). Link-only sources are never fetched.
- **Security out of scope** (no attack or injection questions). Business questions only.
- **Cost:** every billed call writes a cost line (model, tokens or units, cost, run label) to `evals/results/cost.jsonl`. Stop and write a note if the night's total passes £20. Prices are dated in the cost log.
- **Commits:** small and tested; `git pull --rebase` before each push (other sessions push too). Never commit raw, parsed, chunk or vector files. Every push deploys the server, so code the server imports is only pushed with its tests green in the CI recipe.
- **Never block.** When stuck: try another approach, call the replanner, or move to an independent task and come back. Leave a note in the log rather than stopping. If the session pauses, a scheduled wake-up continues it.

## Stages

Status: `todo`, `doing`, `done`, `blocked` (with reason). Each stage ends with its test passing and a log line.

### S0. Harness and safety — `done`
- Loader writes to a chosen schema (`--schema corpus_next`); `pgsearch` can read a chosen schema (setting, default `corpus`); a promote/rollback script (swap `corpus_next` → `corpus`, keep `corpus_prev`).
- Cost log helper used by embed, re-rank and judge calls.
- **Test:** unit tests for the schema option; load the current 16-document corpus into `corpus_next`; live `corpus.stats` unchanged; the same question returns the same passages from both schemas.

### S1. Coverage audit — `todo`
- For every ingest source (197, minus restricted): current version(s), media type, which parser fits (legislation XML, GOV.UK HTML, guidance PDF, Approved Document PDF), raw file present, parse result.
- Output `corpus/coverage.md`: a table with one row per source and a status.
- **Test:** every in-scope source has a row with parser and status; nothing silently missing.

### S2. Parsers for the whole corpus — `todo`
Work through families by priority (sources.yaml `priority`, 1 first), using the `corpus-document` runbook per document:
- S2a legislation XML (Acts, SIs, amending SIs): `parse_legislation`.
- S2b Approved Documents and their amendment booklets: `parse_adoc`.
- S2c HSE and other guidance PDFs: `parse_pdf`.
- S2d GOV.UK and other HTML pages: `parse_html`.
- New layouts get tests first (hand-made lines plus real-file counts), as in the pilot. Tables and figures: model checks through subagents, saved in `corpus/fixes/`.
- **Test per family:** parser tests green; every source in the family parses with 0 open checks (or is listed `blocked` in `coverage.md` with a reason and a ticket in the log); counts sanity (sections, paragraphs) recorded.

### S3. Chunking and validation — `todo`
- `python -m system.rag.chunk` over everything; a validation script (`system/rag/checks.py` or new): no empty chunks; size within bounds (splits counted and listed); every chunk has source, version, dates, country, breadcrumb, section id, URL; no header/footer/watermark text; unique ids; cross-references resolved or listed.
- **Test:** the validation passes; `corpus/chunk-report.md` regenerated; split rate per document reviewed.

### S4. Embed and load to staging — `todo`
- `python -m system.rag.embed` (only new or changed chunks cost money), then load to `corpus_next`.
- **Test:** chunk count in the database = chunk files; a sample of 10 known questions returns their expected section from `corpus_next`.

### S5. Golden set (agentic-rag-lab method) — `todo`
- **Business pass (blind):** subagents play real users (small refurbishment builder, council refurbishment contractor's site manager, asbestos surveyor, quantity surveyor handling CIS and VAT, homeowner-facing builder doing building control and fire). They read the source documents as people would, never the chunks, ids or code, and write questions in builders' words with a reference answer and the clauses they would cite. Weighted by how often the topic comes up (`builder-questions.md`).
- Kinds: answerable (about 70%), negative/false premise, out_of_scope, underspecified; flags `multi_rule`, `granularity`. Separate exact-term set (codes like "B1", "FD30", "regulation 7", "HSG264 paragraph 47").
- **Labelling pass:** a separate agent maps each question to section ids (most important first), `label_confidence`, note.
- **Copy filter:** drop questions sharing 5+ words in a row with an expected section's text or heading; fail on unknown ids; report the dropped count.
- **Holdout:** about 20% set aside **and committed before any eval run**; never used for tuning.
- **Review:** one adversarial reviewer agent checks questions and answers against the sources; removals kept in `removed.jsonl` with reasons.
- Files under `evals/golden/`; tests guard the set (ids unique, sections exist, kinds known, kept + dropped = labelled).
- Target size about 300 questions with sections (one question ≈ 0.3 points of Recall@5).
- **Test:** golden-set tests green; holdout committed (git proves it came before the first run).

### S6. Retrieval eval harness and baseline — `todo`
- `evals/retrieval.py`: runs the server's search path (`pgsearch`) against a chosen schema, and the local path for fast experiments. Metrics: Recall@50 (candidates), Recall@5 after re-rank, MRR, nDCG@5 (graded), all-in-top-5 for multi-rule, per kind, latency p50/p95, cost per question. Per-question rows saved (`evals/results/`), so new metrics need no new calls. McNemar for run-to-run comparison.
- **Test:** metric unit tests; baseline run E1 written up in `evals/experiments/E1-baseline.md` (config, golden commit, re-run command, results, cost, meaning, cautions).

### S7. Improvement loop — `todo`
Experiments, one change at a time, each written up (E2, E3, ...), kept only if McNemar or the numbers show a real gain without hurting other kinds. Candidates, cheapest first:
- re-rank on/off, candidate count (50/100), relevance floor;
- hybrid (BM25 with codes kept whole, RRF k=60) on the server path, with the exact-term set;
- one-per-section rule, date/country filters;
- chunk granularity (table rows, definitions, long paragraphs split), embed text (breadcrumb + text);
- parser fixes for the questions that fail (look at every miss, fix causes, not symptoms).
- **Gate:** Recall@5 ≥ 0.90 on dev; Recall@50 reported (target ≥ 0.97); holdout reported once at the end.

### S8. Answer eval (LLM as judge) on the same golden set — `todo`
- Answers from the top 5 passages by a pinned answer model; judged by a model from another family with a fixed prompt: correctness, grounding, completeness (1–5, reason before score, strict JSON, retry once then `unjudged`). Code checks next to it: declined rate by kind, cites only what was retrieved. Cost lines.
- **Test:** judge unit tests (parsing, anchors); a judged run written up; questions failing the judge listed with causes.

### S9. Promotion (only if every check passes) — `todo`
- Checks: S7 gate met; holdout Recall@5 reported and within 5 points of dev; demo smoke set not worse than live, question by question; judge pass rate on smoke questions not worse than live.
- Swap `corpus_next` → `corpus` in one transaction, keep `corpus_prev`; test a live question on the server; rollback command written in the log.
- **If not met by morning:** do not promote; live stays as it is; report how far it got.

### S10. Morning report — `todo`
- `corpus/OVERNIGHT-REPORT.md`: what was parsed (coverage), chunk stats, golden set, every experiment with Recall@5/@50, judge results, cost, what was promoted or not and why, open problems, next steps.

## Replanning

When a stage is blocked or its test fails twice, spawn a **replanner** subagent with: this file, the log, the failing test output and the coverage table. It returns a proposed change to the stages (split, reorder, add, drop a source to `blocked` with a reason, change approach) and the reason. Apply it here, log it, continue. The goal, the rules for the night and the gate do not change without Florin.

## Log

- 20 Nov 2026, evening: plan written. Starting state: 16 documents chunked (demo corpus, 3,141 chunks in the ADR 0013 note, more since), live server search on schema `corpus` (pgvector + Titan V2 + Amazon Rerank, BM25 tables loaded but unused). 197 ingest sources in the catalogue, 16 with a parser assigned.
- 20 Nov 2026 20:25 — S0 done. `load --schema corpus_next`, `pgsearch` RAG_SCHEMA setting (default corpus) and `candidates()` for Recall@50, `system.rag.promote status|promote|rollback`. Test: unit tests green; current 5,325 chunks loaded into corpus_next in 1m41; live corpus untouched (load time 19:19 unchanged); 3 questions give identical passages from both schemas through the reader URL and server code. Cost log helper moved to S6 (first billed eval calls).
