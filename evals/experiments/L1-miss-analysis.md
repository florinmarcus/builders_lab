# L1: full corpus, local Postgres, miss analysis (21 Nov 2026)

Plan step 1 ([../PLAN.md](../PLAN.md)). Retrieval only.

## Setup

- **Corpus:** rebuilt from Git in the cloud container: harvest, parse, chunk, then embed with Titan v2.
  - 44,737 chunks from 188 sources. The laptop build had 40,075; the difference is the fire safety collection,
    which now parses (commit 0cf3c23).
  - Loaded into a throwaway local Postgres 16 with pgvector, as `corpus_next`. Live was not touched.
- **Search:** the live settings. Hybrid keyword search on, no relevance cut-off, Amazon Rerank v1, top 50 candidates.
- **Questions:** golden set v2, dev split, 299 labelled questions. The holdout was not used.
- **Cost:** embedding $0.77; run about $0.34.
- **Latency:** p50 1.4 s, p95 1.8 s. The local database is fast: about 0.2 s of that is the database, the rest is
  the embedder and reranker.
- **Rows:** `evals/results/L1-full-hybrid-dev.jsonl`. Summary: `L1-full-hybrid-dev.summary.json`.

## Headline (strict labels)

| Metric | Value |
|---|---|
| Recall@5 | 0.68 (95% CI about 0.62-0.73) |
| Recall@5 before rerank | 0.49 |
| Recall@50 | 0.85 |
| MRR@5 | 0.48 |
| nDCG@5 | 0.32 |
| all@5 (multi-rule questions) | 0.05 |

**Recall@5 by role:**
- housing repairs 0.81
- site safety 0.71
- asbestos 0.69
- money 0.65
- building control 0.61
- fire safety 0.61

## Misses: 96 of 299 questions have no expected section in the top 5

| Cause | Count |
|---|---|
| Document not in the corpus | 2 |
| Expected section id not in the corpus (label or parse id changed) | 2 |
| Ranking: the right section is in the top 50, at rank 6-10 | 21 |
| Ranking: at rank 11-50 | 29 |
| Not retrieved: not in the top 50 | 42 |

Half the misses are a ranking problem: the right chunk is found but the reranker puts it below 5. The other half
are never found.

## What the examples show (12 of the 42 not-retrieved questions read by hand)

1. **The labels are incomplete.** In about half the examples read, the top 5 already holds a section that
   answers the question, but from another document than the one labelled. Examples:
   - The NNLW notification question: HSE's NNLW page and Asbestos Essentials A0 answer it. L143 table 7 was
     labelled.
   - The glazing-limit question: AD L table 10.1 is exactly the answer. AD L paragraphs 10.7 and 10.9 were
     labelled.
   - The Future Homes question: circular 01/2026 summarises the changes. The amending regulations were labelled.

   Strict recall under-counts. The real top-5 recall is higher than 0.68, but by how much is unknown until each
   miss is judged.
2. **Builders' words don't match the regulations' words.** "Grey board above the ceiling", "Artex", "lad drilled
   through a panel", "combi". The L143 paragraphs that answer these use formal wording and are not found.
3. **Out-of-date documents compete with current ones.** 76 of the 1,710 top-5 slots (4.4%) come from sources
   marked `out-of-date` in `corpus/sources.yaml`: `adb-historical` 61 and `manual-br` 15. Their chunks have no
   `valid_to`, so the date filter in search does not remove them. Example: the 2013 AD L amendments outrank the
   current AD L on the re-plastering question. This is a clear bug.
4. **Off-topic documents crowd in.** Tenants' guides (Homes Act, Awaab) appear for a contractor's asbestos
   question.

## Chunk structure (whole corpus; audit script in the session scratchpad, to be committed with step 2)

| Family | Chunks | Median chars | Under 150 chars | Generic heading ("Note", "Text", none) |
|---|---|---|---|---|
| Approved Documents | 18,034 | 284 | 23% | 17% |
| Guidance PDFs (Home Office, MHCLG, other) | 9,693 | 363 | 34% | 65% |
| HSE guidance PDFs | 8,182 | 337 | 20% | 19% |
| Legislation | 6,652 | 362 | 20% | 0% |
| GOV.UK pages | 2,176 | 200-650 | 9-47% | 0%; 40-84% have no number or title |

- **The worst documents:** the HHSRS operating guidance, HSE EH40, the procurement supplier guides, AD Q, the
  building regulations manual, HSE INDG344 and HSG247, and the fire safety collection.
- **Among the misses:** 77 expected chunks are under 150 characters and 83 have generic headings. Weak structure
  is part of the problem, not all of it.

## Fire safety collection

It parses now, but the structure is wrong. The guides are headed prose without paragraph numbers, and the PDF
parser expects numbered paragraphs. Results:
- 200-290 "note" sections per guide, with headings like "Note".
- Paragraph numbers jump (1.2 to 1.6), so several topics end up in one chunk.
- About 40 open model checks per guide.

It needs its own strategy: one section per real heading, with the full heading path.

## Next (each needs Florin's yes)

1. **Judge every miss.** Does any top-5 section answer the question? Use Claude locally (two judges, blind to the
   label), so we get a real recall figure and a list of label fixes.
2. **Fix the out-of-date bug.** Exclude sources marked `out-of-date`, or give them a `valid_to`.
3. **A parsing strategy per family,** starting with the Home Office guides and the GOV.UK pages.
4. **Then chunking experiments,** for the tiny chunks and the generic headings.
5. **Then the vocabulary gap:** query expansion with the glossary, or extra queries (E5).

Each change is measured on dev, the holdout is checked once at the end, and McNemar is used against L1.
