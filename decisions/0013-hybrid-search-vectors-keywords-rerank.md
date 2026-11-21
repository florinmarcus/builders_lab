# 0013: Regulations search is hybrid: vectors and BM25 keywords, top 50 each, merged, re-ranked to 5

Date: 20 Nov 2026. Status: accepted. Changes the "Search" part of ADR 0010 and `architecture/design/regulations-corpus.md` ("vector now; keyword and re-rank after evals").

## Context

The corpus now has 12 documents in 3,141 chunks (`corpus/chunk-report.md`). A local keyword-only search (`system/rag/localsearch.py`, BM25 through SQLite FTS5) finds the right documents for most builder questions, but misses when the builder's word differs from the document's ("licence" vs "licensable work"). Florin decided keyword search alone is not enough: the product needs vector search, hybrid search and re-ranking.

Florin's own lab (`agentic-rag-lab`, ADRs 0010 and 0012, experiments E7, E9, E15) built the same pattern on another public corpus of 174 chunks: keyword top 50 and vector top 50, merged with reciprocal rank fusion, re-ranked to 5. Its findings we reuse as ideas, not code:
- No Bedrock re-rank model in London or Ireland (checked 14 Oct 2026 with `aws bedrock list-foundation-models`); the lab runs everything in Frankfurt.
- Postgres `ts_rank` is not BM25; a fair keyword test needs real BM25.
- Amazon Rerank costs about half of Cohere Rerank 3.5 with similar results on its test set.
- On its corpus, keywords added nothing. Ours is full of codes ("B1", "FD30", "regulation 7"), so this must be measured here.

## Decision

- **Embeddings:** Amazon Titan Text Embeddings V2, 1,024 dimensions, normalised, in **London** (eu-west-2). Text embedded is the chunk's `embed_text` (breadcrumb + text).
- **Keywords:** real BM25 (not `ts_rank`), with codes kept whole in their own field, as in `localsearch.py`.
- **Merge:** top 50 from vectors and top 50 from BM25, reciprocal rank fusion with k = 60 (fixed), after the date and country filters.
- **Re-rank:** Amazon Rerank (`amazon.rerank-v1:0`) in **Frankfurt** (eu-central-1), 50 candidates down to 5. Cohere Rerank 3.5 is a setting, not a rebuild.
- **Where vectors live (updated 20 Nov 2026):** Postgres with pgvector on Florin's existing RDS instance (the lab's), in its own database `builders_corpus` (schema `corpus`), not on our Docker Postgres (its image has no pgvector). The loader writes as `builders_corpus_owner`; the Builders server connects only as `builders_corpus_reader`: SELECT only, read-only transactions by default, 5 connections, 5-second queries. Set-up: `deploy/rds/`. The local index stays for building and testing.
- **Settings, not code:** region, models, top-k and the keyword switch are configuration, so evals can compare keyword only, vector only, hybrid, with and without re-rank.
- **Permissions:** the deploy user (for building the index) and later the server role (for questions) get `bedrock:InvokeModel` on Titan V2 in London and on the re-rank model in Frankfurt, plus `bedrock:Rerank`. Managed policy `deploy/iam/corpus-bedrock-policy.json` (separate from the inline deployer policy, which is at the 2,048-byte limit); the server role change stays in parking lot S26.

- **Server, first version (20 Nov 2026):** vector top 50, re-rank to 5, relevance floor; keyword (BM25) postponed at Florin's request. Switched on by `rag_enabled` in Parameter Store after the server role has its Bedrock rights.
- **Update 21 Nov 2026 (Florin's yes):** keyword (BM25) search on by default, fused with vectors by RRF (k=60); relevance floor off (`RAG_MIN_SCORE` 0). On 342 builder test questions the floor of 0.05 made 58% of answerable questions get "not in the sources"; answers judged correct and grounded went from 31% to 57% (`evals/experiments/J1-answers-live-vs-E5.md`). Out-of-scope questions now reach the answer model with weak passages; it declined them in 77-85% of cases in the evals.

## Options considered

- **pgvector in our Docker Postgres:** no new dependency on the lab's instance, but the live database image would have to change. **A new RDS for Builders:** clean, but a second monthly cost now.
- **Everything in Frankfurt, as the lab:** one region, but Titan costs twice as much there ($0.0002 vs $0.0001 per 1,000 tokens, `research/hosting-costs/claude-app-vs-bedrock.md`) and the corpus would be embedded outside the UK for no gain.
- **No re-rank until evals ask for it:** keeps every call in London, but Florin wants re-ranking, and the lab already showed it is cheap (one search unit per question).
- **Keyword only:** free and in place, but misses paraphrases (above).
- **Vector only:** simpler, but codes like "B1" and "7(2)" are where vectors are weakest.

## Consequences

- The corpus database shares an instance with the lab: a lab outage or a stopped instance stops regulations search (the server then falls back to its small passage set). The instance may be in another region (the lab uses Frankfurt); search adds a few milliseconds per question. The Builders server reaches it through one security-group rule for its Elastic IP, with SSL. It also starts on parking lot S28 (a managed database).

- Each question sends its text and up to 50 passages (public regulations) to Frankfurt for re-ranking. The question can mention a firm's job; Frankfurt is in the EU, not the UK. Re-check if a customer asks for UK-only processing, and re-check the London model list when permissions are in place (regions change).
- Building the index costs about 10 cents for today's corpus (about a million tokens). Each question costs one Titan call and one re-rank search unit (Amazon Rerank about $1 per 1,000; verify current prices before quoting).
- The 20 builder questions (`research/domain/builder-questions.md`) become the first test set: keyword vs vector vs hybrid vs hybrid with re-rank.
