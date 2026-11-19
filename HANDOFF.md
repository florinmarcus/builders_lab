# Handoff: regulations corpus, ingestion and evals

Written 19 Nov 2026 at the end of a long session. Read this first, then `AGENTS.md`. Delete this file when its content has moved into proper docs.

## How Florin works

- Small steps. Before each step, say in a few short lines what you'll do and why, then wait for his yes.
- He often **listens** to replies: short spoken sentences, small chunks, few tables. Offer "next part?" rather than long walls of text.
- Plain English. Use the `grill-me` skill (in `.claude/skills/`) for design questions, especially parsing and chunking.
- Scope of this thread: **ingestion, chunking, vector store, retrieval and evals only.** The MCP server is built by another session and sits on top later.

## Where things are

- Branch: `claude/bold-wozniak-o6pn73` (AGENTS.md says `main`; Florin has not yet said to merge or push to `main`, so ask).
- `corpus/GOAL.md` (harvest goal, done), `corpus/README.md` (schema, known gaps), `corpus/sources.yaml` (258 documents), `corpus/versions/` (832 version records), `corpus/harvest-report.md`.
- `research/domain/corpus-inventory/` (a to d): every document, licence, dates, links. `research/methods/agentic-rag-lab-lessons.md`: what we learned from agentic-rag-lab.
- Code: `system/rag/corpus.py` (catalogue, version store), `harvest.py`, `upload_s3.py` (upload, `--download`, `--dry-run`). Tests: `tests/test_corpus.py` (12 pass).
- ADR 0005: raw files in S3 not git; modes `ingest` / `restricted` / `link_only`; history from 1 Oct 2010.
- agentic-rag-lab is a separate private repo. Add it with `add_repo` (florinmarcus/agentic-rag-lab) if you need it. Copy methods only, never facts. Its background notes mirror an employer design: nothing from Florin's employer goes into builders_lab (rule 9).

## Raw files and AWS

- Raw files (PDF, HTML, XML, about 650 MB) are **not in git**. Florin uploaded them to a private S3 bucket in eu-west-2 from his PC. He gives the bucket name in his first message; never write it into the repo.
- The cloud environment ("Trusted Environment") now has `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_DEFAULT_REGION` for an IAM user `builders-claude` that can only list, get and put in that bucket (no delete, no Bedrock).
- First job in a new session: `pip install boto3`, then `CORPUS_BUCKET=<bucket> python -m system.rag.upload_s3 --download`. Every file is checked against its record's SHA-256. If files are "not in S3", run `python -m system.rag.harvest` to fetch them again from the source sites.
- If Florin's own harvest run on his PC created new version records, ask him to commit and push them.

## Decisions made in conversation (not yet in ADRs)

1. **No Amazon Bedrock** for embeddings (this replaces "Titan V2" in the original brief). Embedding model still open; a free local model is the cheapest for tests. Needs an ADR.
2. Postgres + pgvector in Docker. Log tokens and cost for any paid model call.
3. **Chunk by structure**, not size: one chunk per regulation, Approved Document section, HSE paragraph. Every chunk keeps: source id, version, valid_from, valid_to, section or clause, heading path, page, URL.
4. **Metadata graph** next to the chunks: cross-references (AD section to regulation, regulation to Schedule 1 part), amendments (which version changed a clause), and **definitions as nodes** (e.g. "building work", reg 2/3). Definitions stay out of normal chunks but are linked so search can pull them in.
5. **Curated parsing**: drop contents pages, repeated headers and footers, page numbers, banners. **Tables** need special handling: keep the whole table and also turn each row into a meaningful sentence. Analyse how tables should be chunked. This is the biggest new piece (agentic-rag-lab had no table handling and it caused misses).
6. **Test-driven parsers**: unit tests on the real files plus small hand-made fixtures. Edge cases first.
7. **Pilot documents for the parser**: Building Regulations 2010 (legislation XML, with Welsh extent to filter out), Approved Document B volume 1 (big PDF with tables), HSG264 (asbestos guidance, scoring tables). Asbestos is the scenario most people care about.
8. **Evals before tuning.** Golden set written blind to the code (a model plays a builder or surveyor), then labelled to section ids with confidence; copy filter (drop questions that share 5+ words in a row with their section); question kinds: answerable, no answer, out of scope, attack, multi-section, exact terms, near misses; a holdout set committed before runs. Demo questions include **payment notices and pay less notices** (HGCRA 1996 Part II and the Scheme 1998 were added for this).
9. **Metrics**: Recall@k (decide 5 vs 10 from data, agentic-rag-lab never tested it), MRR, nDCG, all-sections-in-top-k for multi-section questions; compare runs question by question with McNemar. Score by section id, never chunk text, so chunkers compare fairly.
10. **Hybrid search** (BM25 that keeps codes like "7.6.3" whole, fused with vectors by RRF k=60) is to be measured, not assumed. **Reranker only after the evals** show where quality is.
11. **LLM judge**: code with a fixed prompt, three 1 to 5 scores (correctness, grounding, completeness), reason before score, strict JSON, judge model from a different family than the answer model, blind to which model answered. Can run in Claude Code on Florin's existing tokens. Do the human check this time (about 40 hand scores); agentic-rag-lab never did and its judge stayed "provisional".

## Next steps, in order (ask before each)

1. Finish telling Florin the agentic-rag-lab study: part 6, lessons and what to reuse (parts 1 to 5 done: golden set, metrics, judge, parsing, hybrid and rerank).
2. Context engineering: AGENTS.md is monolithic. Split it with a "read when you need it" table, as agentic-rag-lab does.
3. `docs/architecture.md`: **Mermaid diagrams only, no prose**: modules, system layers, deployment, runtime flow. Then zoom-in design docs, also Mermaid-led: ingestion pipeline (with entity diagram), retrieval, evals. A design agent can draft; review before showing Florin.
4. Grill session on parsing and chunking for the three pilot documents, then test-first parsers.
5. Golden set and evals.
6. Also wanted, not started: a **parking lot** file (things to improve later) and a **one-page plain summary** of what the corpus contains, for non-technical people at the builders meeting.

## Open conflicts to raise

- Push to `main` (AGENTS.md) or keep the session branch.
- ADR 0003 says Frankfurt for Bedrock; we now use London for S3 and no Bedrock for embeddings. Update ADR 0003 or supersede it.
- Legal: AD A and AD C PDFs still carry the old Click-Use licence wording. Restricted documents are prototype only; the repo should be private while they are used.
