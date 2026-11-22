# 0016: Retrieval strategy: measure first, four legal lanes, complete recall

Date: 22 Nov 2026. Status: accepted (Florin, grilling session 22 Nov). Changes ADR 0013 (one mixed search) and
ADR 0008 (how far back), and adds tools to ADR 0015.

## Context

Parsing is nearly complete (`evals/PLAN.md`). Before re-chunking, Florin and Claude worked through the chunking,
storage and retrieval strategy, as a design tree. The starting assumption: the parsed trees are accurate. The aim:
the highest recall and MRR.

What is built today (`architecture/design/regulations-corpus.md`, "Search"): one hybrid search (vector top 50 and
BM25 top 50, merged by RRF), one chunk per section, Amazon Rerank to 5. Cross-references are stored in each
chunk's `meta` but never used at search time. There is no parent-section return. The vector-only baseline on the
dev questions is R@5 0.51, R@50 0.80. 9% of dev gold labels (94 of 1,063) point to section ids that no longer
exist after re-parsing.

Florin's main worry: the re-ranker gives accuracy, not completeness. An answer can be right but incomplete, and a
top 5 that looks confident can hide that.

## Decision

**How we measure**
1. **Complete recall is the main measure.** Each expected section is marked as a *needed part* or an
   *alternative* within a group. A question is a hit only if every needed group has at least one section in the
   results. Partial recall (share of needed groups found) and MRR@10 are reported too, at 5 and at 10.
2. **Gold labels are fixed first.** Ids that changed shape are remapped by code; moved content is checked by a
   model against the text. Remapped labels are marked.
3. **Every comparison** reports totals with margins of error, and question by question: which questions were
   fixed and which were broken, with McNemar on the questions both runs share. The question set has a version;
   changed questions are compared only where shared. The holdout is never used for tuning.
4. **Tuning queries are the real agent's searches.** Run the plugin's regulations specialist on the dev
   questions, record every search call (query, date, how many searches), tune on those. Re-record on every model
   or prompt change. Raw builder questions stay as a robustness check.
5. **Personas are tested, not assumed.** Start with a mixed expert (a chartered building surveyor who also knows
   site safety, fire safety, housing standards and payment law) who knows how our search works; compare one or
   two others by recall.

**Order of work**
6. **Measure first, then design.** Fix labels, record queries, run today's search, find where recall is lost
   (not found in 50, or found but below 5) and how many sections questions need. Then choose.

**Search design (the target, each step proven by the measures above)**
7. **Legal strength per chunk.** Each chunk carries the strength of its own text, from the parser's marks:
   quoted regulations and requirement boxes are law, ACOP text is an approved code, the rest takes its document's
   level.
8. **Four lanes, searched in parallel:** law (Acts and regulations), Approved Documents, approved codes of
   practice, plain guidance. Each lane returns its own short list; an empty lane is reported as empty. Lane sizes
   are tuned on dev.
9. **Return the section.** Parent sections, neighbouring paragraphs and following cross-references to the law
   are tuning levers, tried only if the measures show the need. If answer quality (the judge) is poor, retrieval
   is the first place to look, and these levers are the first things to try.
10. **"Too broad" is its own reply.** When strong results spread over several distinct meanings, search returns
    no answer passages, only the meanings found (a label and one example each) and "narrow your search". The
    agent then asks the builder or narrows the query itself. The threshold is found from search behaviour on dev;
    a model and Florin's spot checks confirm which flagged questions really are broad, so the search does not
    judge itself. "Vague" (the question cannot be understood) is different: the agent asks before searching.
11. **Every search takes the job's date** and shows the date it used. With no date, today, said in the reply.
12. **Three regulations tools** (ADR 0015): `search_regulations` (meaning and keywords, four lanes),
    `get_section` (exact lookup by document and section number, optionally with parent and neighbours) and
    `read_document` (contents page first, then the chapters or pages asked for; never a whole document at once).
    Restricted sources stay restricted in every tool.

**Chunking and scope**
13. **Today's chunks are the baseline.** Then one change at a time, each measured: tables (whole only, rows only,
    both), size (split long, merge tiny), breadcrumb in the embedded text or not, neighbouring text added.
14. **History: 2025 and 2026 only.** Keep every version in force at any time from 1 January 2025, including the
    editions in force on that day. Versions superseded before then leave search and the checking work; their raw
    files stay in S3. Gold questions on 2025 and 2026 changes are added.

## Options considered

- **Follow cross-references first (law as the hub).** Matches how the documents are built, but today's links are
  thin (in AD B, 60 of 736 references point to another document), popular law sections would flood results, and
  following links drifts off topic. Kept as a lever (9), only after measuring.
- **One mixed search (today).** Law and guidance compete for the same 5 places, and a missing level cannot be
  told from a gap in the library.
- **A count of further relevant passages.** Says "there is more" but not "your question could mean other
  things". Replaced by the "too broad" reply.
- **Tuning on saved test queries.** Not what the real agent sends, and drifts when the model changes.
- **Keeping history back to 2010 (ADR 0008).** About 250 old versions and about 1,000 open model checks (AD B
  editions back to 2006) for jobs the pilot does not have.

## Consequences

- `evals/PLAN.md` gets the measure-first steps before any chunking change.
- Gold set work: label groups (needed or alternative), remapping, a version number, change questions; later a
  broad-question set found from search behaviour.
- Server work (after the measures): per-chunk legal strength in `chunk.py` and the database, lanes in
  `pgsearch.py`, the "too broad" reply, the date argument, `get_section` and `read_document` (ADR 0015).
- The retrieval levers in (9) and the chunking tests in (13) are the first places to look when answers are poor.
- ADR 0008's "how far back" changes to 2025; the old AD B editions' open checks are not worked.
- Built 22 Nov 2026 (`corpus.in_scope`): 4 of the 17 adb-historical files are in force from 1 January 2025 (the
  2019 edition with the 2020 and 2022 amendments, and the text collated with the 2025, 2026 and 2029 amendments,
  both volumes), so their 379 checks were worked; the other 13 keep 629 checks open. 210 of 841 versions are out.
