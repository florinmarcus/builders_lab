# Systematic retrieval tuning and evaluation for RAG

Context for the reader: the target engineer already measures recall@k and MRR on ~300 golden questions, vector-only and after a reranker, with recall moving 70% -> 82% (chunking) -> 93% (reranker). These notes cover what the "data-science version" of that work looks like. Graph-based retrieval is out of scope (covered elsewhere).

## Building retrieval test sets (labels, grading, pooling, synthetic queries, label stability)

### Takeaway
Label relevance at the document or text-span level, not by chunk id, so labels survive re-chunking; Chroma's token-span method is a working template. Expect your judgments to be incomplete and biased toward the systems that built the pool (BEIR showed this changes rankings), and treat synthetic queries as good for comparing systems but biased for absolute numbers.

### Cited Findings
- Chroma's chunking study defines relevance by the tokens of a generated "relevant excerpt", not by chunk ids; retrieved chunks are scored against those tokens (token-level recall, precision, IoU). The reason given: MTEB-style benchmarks score whole-document relevance and cannot see chunking effects. — [Chroma, Evaluating Chunking Strategies for Retrieval (2024)](https://www.trychroma.com/research/evaluating-chunking)
- Chroma's synthetic pipeline: an LLM writes a factual question plus verbatim excerpts; a query is rejected if excerpts do not match the corpus exactly; prompt discourages compound ("and") questions; up to 50 earlier queries are shown to push variety; near-duplicate queries removed by embedding similarity; queries with low excerpt-to-query similarity dropped. About $0.01 per question with GPT-4. 472 queries over 328k tokens in 5 corpora. — [Chroma](https://www.trychroma.com/research/evaluating-chunking)
- Chroma's own stated biases: the similarity filter may cause sampling bias; only the generated excerpts count as relevant (other relevant passages are missed, i.e. incomplete judgments); LLMs produce a narrow question style; small, low-diversity set. — [Chroma](https://www.trychroma.com/research/evaluating-chunking)
- Pooling bias evidence (BEIR, TREC-COVID): Hole@10 (share of a system's top-10 never judged) was 6.4% for BM25 but 31.8% for TAS-B and 30.6% for DPR, 14.4% for ANCE. After the authors judged 980 missing pairs, ANCE nDCG@10 rose 0.654 -> 0.735 (now 6.7 points above BM25's 0.668), TAS-B 0.481 -> 0.555, DPR 0.332 -> 0.445, while BM25 moved only 0.656 -> 0.668. The original pool favoured lexical systems. — [BEIR, Thakur et al. 2021](https://arxiv.org/html/2104.08663v4)
- BEIR recommends diverse pooling across many retrieval system types so non-lexical systems are judged fairly. — [BEIR](https://arxiv.org/html/2104.08663v4)
- Fully synthetic test collections (LLM queries and LLM judgments) were found reliable for ranking systems (Rahmani, Craswell, Yilmaz, Mitra, Campos, SIGIR 2024); a later summary reports Kendall's tau about 0.857 with human-based system rankings. — [Rahmani et al. 2024](https://export.arxiv.org/abs/2405.07767); tau figure via [secondary summary, arXiv 2604.00731](https://arxiv.org/pdf/2604.00731) (not verified in the original)
- Bias follow-up on TREC DL 2023: synthetic queries are longer than real ones, and LLM-based systems score higher under synthetic labels. Conclusion: bias can substantially shift absolute scores but matters less for relative system comparisons. Note the set is small (82 queries: 51 human, 18 GPT-4, 13 T5). — [Rahmani et al. 2025, Towards Understanding Bias in Synthetic Data for Evaluation](https://arxiv.org/html/2506.10301v2)
- Jason Liu's recipe: generate about 5 questions per chunk, check whether retrieval returns the source chunk; synthetic questions tend to paraphrase the text, so mix in real user queries over time. — [Jason Liu, Systematically improving RAG applications (2025)](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/); [RAG flywheel (2024)](https://jxnl.co/writing/2024/08/19/rag-flywheel/)
- BEIR chose nDCG@10 because it handles graded as well as binary relevance (MAP and MRR do not handle grades). — [BEIR](https://arxiv.org/html/2104.08663v4)

### Inferences
- For a 300-question golden set whose labels are chunk ids, every chunking experiment silently invalidates labels. The fix is to store each gold answer as (document id, version, character or token span) and map to "relevant chunk = any chunk overlapping the span by more than X%" at evaluation time. This is what makes chunking experiments comparable.
- "Paraphrase bias" of synthetic questions inflates dense retrieval scores (the question reuses the chunk's words and meaning) and hides vocabulary-mismatch failures that real users cause. Report synthetic and real-user slices separately.
- Incomplete judgments mean a new system (e.g. a new embedding model or hybrid) may retrieve unjudged but relevant chunks and be scored as worse. Practical pooling: when comparing systems, judge (with a human or LLM judge) the union of top-k from all variants for a sample of questions before concluding.
- Graded labels (e.g. 2 = contains the answer, 1 = useful context, 0 = not relevant) let nDCG distinguish "found the answer chunk at rank 1" from "found a related chunk".

### Gaps
- Did not fetch Manning et al. (IIR) or Sakai's texts directly; metric definitions below are standard textbook material, not quoted from them.
- No source found giving a recommended golden-set size for RAG specifically.

## Metrics: which to use when, link to answer quality, is recall@5 = 90% a sensible gate?

### Takeaway
Recall@k is the right gate for "can the generator possibly answer"; nDCG/MRR measure ordering, which matters once you feed few chunks; context precision matters for cost and distraction. Classic relevance-label metrics correlate only weakly with end answer quality (eRAG), so a recall gate must be paired with end-to-end checks, and the right k depends on how many chunks the generator actually sees.

### Cited Findings
- RAGAS Context Precision@K = sum over k of (Precision@k x v_k) / number of relevant items in top K, where v_k is 0/1 relevance at rank k (a rank-aware, AP-like measure). Variants: LLM judges each chunk against the reference answer, or against the generated response (no reference), a non-LLM string-similarity variant against reference contexts, and an ID-based variant. — [RAGAS docs, Context Precision](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/)
- RAGAS is framed as reference-free evaluation of RAG pipelines that does not need human ground-truth annotations. — [Es et al., RAGAS (2023)](https://arxiv.org/abs/2309.15217)
- eRAG (Salemi and Zamani, SIGIR 2024): feed each retrieved document alone to the RAG LLM, score its output with the downstream task metric, and use those scores as document labels. It correlates better with downstream RAG performance than baselines, Kendall's tau gains of 0.168 to 0.494; conventional relevance labels showed only minor correlation with downstream performance. Up to 50x less GPU memory than end-to-end evaluation. — [Salemi and Zamani 2024](https://arxiv.org/abs/2404.13781v1)
- BEIR: precision and recall ignore rank; MRR and MAP do not handle graded judgments; nDCG@k handles both. — [BEIR](https://arxiv.org/html/2104.08663v4)
- Chroma shows recall and precision trade off sharply: at n=5 retrieved chunks, recall ranged 83.6-91.9% while token precision ranged only 1.4-8.0%; smaller chunks raised precision and IoU, recall peaked at intermediate sizes. — [Chroma](https://www.trychroma.com/research/evaluating-chunking)
- Jason Liu: prioritise recall (a missed key chunk is usually fatal), track precision too; averages hide failures, e.g. 70% overall recall masking 5% on multi-hop or date-filter queries. — [Jason Liu 2025](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/)
- "Sufficient context" (Google, ICLR 2025): an autorater judges whether retrieved context is sufficient to answer (93% accuracy). Strong proprietary models answer well when context is sufficient but often answer wrongly instead of abstaining when it is not; selective generation using sufficiency improved correct-answer share among answered questions by 2-10%. — [Joren et al. 2024](https://arxiv.org/abs/2411.06037v3); [Google Research page](https://research.google/pubs/sufficient-context-a-new-lens-on-retrieval-augmented-generation-systems/)
- Anthropic's Contextual Retrieval uses 1 - recall@20 ("failure rate") as its metric and found passing 20 chunks beat 5 or 10. — [Anthropic, Contextual Retrieval (2024)](https://www.anthropic.com/news/contextual-retrieval)

### Inferences
- Which metric when: recall@k (k = number of chunks the generator really gets) is the gate; MRR if one answer chunk matters and you show few chunks; nDCG@k with graded labels when several chunks contribute; MAP / context precision when you care about noise in the prompt (cost, distraction, lost-in-the-middle). MRR alone hides cases with multiple needed chunks.
- Recall@5 at 90% as a gate: sensible as a regression gate, but (a) define recall per question as "all required spans found" for multi-hop questions, otherwise partial hits look like success; (b) gate per segment (question type, document family), not only on the average; (c) set k to the real post-rerank context size; (d) check uncertainty: with 300 questions, a 90% estimate has a 95% binomial interval of roughly +/-3.4 points (standard calculation, sqrt(0.9*0.1/300) x 1.96), so a 1-2 point change is noise unless a paired test says otherwise.
- Because relevance labels correlate only weakly with answer quality (eRAG), add a "sufficient context" check or an eRAG-style utility label on a sample, so the gate measures "the generator can answer from this", not "a labelled chunk appeared".

### Gaps
- RAGAS paper's WikiEval human-agreement numbers and context recall formula were not retrieved (abstract page only).

## Tuning knobs and how to search them (chunking, embeddings, hybrid, fusion, top-k, rerankers, query rewriting, filters, ablations, cost)

### Takeaway
The largest, best-evidenced levers are hybrid lexical+dense retrieval, a cross-encoder reranker over a wide candidate set, contextualising chunks, and chunking without heavy overlap; tune them one factor at a time against a fixed baseline, and use cheap retrieval-only metrics for the grid, saving end-to-end evals for finalists.

### Cited Findings
- Anthropic Contextual Retrieval (top-20 failure rate = 1 - recall@20, averaged over codebases, fiction, arXiv and science papers): baseline embeddings 5.7%; contextual embeddings 3.7% (-35%); contextual embeddings + contextual BM25 2.9% (-49%); plus reranking 1.9% (-67%). Reranker took top 150 candidates down to 20. Gemini Text 004 and Voyage embeddings performed best; Cohere reranker used. Contextualisation cost about $1.02 per million document tokens one-off with prompt caching; added context about 50-100 tokens per chunk. — [Anthropic 2024](https://www.anthropic.com/news/contextual-retrieval)
- Chunking (Chroma, text-embedding-3-large, n=5): recall varies up to about 9 points between strategies. OpenAI-style default (800 tokens, 400 overlap) had the worst efficiency metrics (recall 87.9, IoU 1.4). Recursive 400/0 overlap: recall 89.5, IoU 3.6; Recursive 200/0: recall 88.1, IoU 6.9; ClusterSemantic 400: recall 91.3; LLM chunker: recall 91.9 (best) but slow and costly. Overlap hurts IoU. The best chunker changed with the embedding model (with all-MiniLM-L6-v2, TokenText 250/125 overlap had the best recall, 82.4). — [Chroma](https://www.trychroma.com/research/evaluating-chunking)
- Hybrid fusion (Elastic, BM25 + its learned sparse ELSER on BEIR subset, nDCG@10): RRF improved about 1.4% over ELSER alone and about 18% over BM25 alone, and was at least as good as BM25 on every dataset; a well-calibrated weighted linear combination beat RRF on average but was less consistent and the best weight depended on the model. RRF used k=20, N=1000 (original RRF paper suggests k=60). Vendor result with its own model. — [Elastic Search Labs, Hybrid retrieval](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid)
- Bruch, Gai, Ingber (2022): RRF is sensitive to its parameters (contrary to earlier claims); convex combination of normalised scores beats RRF in- and out-of-domain, is robust to the normalisation chosen, and its single weight can be tuned with a small set of examples. — [An Analysis of Fusion Functions for Hybrid Retrieval](https://arxiv.org/abs/2210.11934)
- Rerankers: BM25 + cross-encoder was +11% over BM25 on average across BEIR (beating it on 16/18 datasets), the best zero-shot system, but costs about 450 ms GPU / 6,100 ms CPU per query on 1M DBPedia docs. — [BEIR](https://arxiv.org/html/2104.08663v4)
- Top-k: Databricks (text-embedding-3-large, 512-token chunks) average retrieval recall by context budget: 2k 0.468, 4k 0.702, 8k 0.788, 16k 0.839, 32k 0.894, 64k 0.927, 128k 0.950; saturation point differs by dataset (NQ at about 8k, FinanceBench and DocsQA about 96k). — [Databricks, Long Context RAG Performance of LLMs (2024)](https://www.databricks.com/blog/long-context-rag-performance-llms)
- Answer accuracy does not follow recall: most models peaked between 4k and 32k tokens of retrieved context and then degraded (e.g. gpt-4-turbo 0.641 at 16k -> 0.560 at 125k; llama-3.1-405b 0.623 -> 0.426); gpt-4o and claude-3.5-sonnet degraded little. Databricks advises choosing the number of retrieved documents per model and task by evaluation. — [Databricks](https://www.databricks.com/blog/long-context-rag-performance-llms)
- Self-Route paper top-k table (LC baseline 45.53): RAG score at k=1 20.24, k=5 37.92, k=10 41.20, k=50 44.06, k=100 44.12. — [Li et al., EMNLP 2024](https://arxiv.org/html/2407.16833v2)
- Lost in the Middle: models do best when relevant text is at the start or end of the context and degrade when it is in the middle, even long-context models. — [Liu et al. 2023](https://arxiv.org/abs/2307.03172)
- Embedding choice: MTEB (8 tasks, 58 datasets, 112 languages, 33 models) found no single embedding method dominates all tasks. — [Muennighoff et al., MTEB](https://arxiv.org/abs/2210.07316)
- Fine-tuning embeddings on synthetic (question, chunk) pairs, user feedback and hard-negative triplets is claimed to give 10-30% recall gains (no example counts given, practitioner claim). Metadata filters: extract dates, authors, status into columns and apply hard filters; keep tables structured. — [Jason Liu 2025](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/)
- Jason Liu's repository-issues experiment: full-text search about 55% recall vs embeddings about 65%. — [Jason Liu 2024](https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/) (seen via search snippet only)

### Inferences
- Experiment design for a 300-question set: fix a baseline config, change one knob at a time (ablation), record recall@{5,10,20,50}, nDCG@10 and MRR, per segment. Run a small grid only where knobs interact (chunk size x embedding model is known to interact, per Chroma; candidate k x reranker cut-off interacts).
- Order of cost: re-ranking, fusion weights, top-k and query rewriting need no re-index (cheap, seconds-minutes); chunking, contextual chunk text and embedding model changes need a re-embed of the corpus (costly; cache embeddings per (chunk config, model) key); fine-tuning embeddings is the most expensive.
- Separate "candidate recall" (recall@100-150 before rerank) from "final recall" (recall@k after rerank). If candidate recall is low, only first-stage changes (hybrid, chunking, embeddings, query rewrite) help; if candidate recall is high but final is low, tune the reranker or k.
- For the engineer's current 93%: the remaining 7% is likely a long tail; the next step is failure categorisation (below), not more grid search. Hybrid BM25 is particularly worth testing for domains with exact codes, section numbers and regulation names.
- Compare variants with a paired test per question (see significance note below); with 300 questions, many "gains" of 1-2 points will not be significant.
- Statistical testing: Urbano et al. found the paired t-test and permutation test hold Type I error at alpha across measures and topic-set sizes; t-test recommended for simplicity; permutation test allows other statistics. Other authors disagree on Wilcoxon/sign tests. — [Urbano, Lima, Hanjalic, SIGIR 2019](https://arxiv.org/pdf/1905.11096)

### Gaps
- No primary 2024-2026 numbers fetched for HyDE or LLM query rewriting gains; no independent (non-vendor) dense+BM25 RRF benchmark found in this pass (Pinecone/Weaviate data not retrieved).
- No published cost-per-experiment benchmarks; cost ordering above is reasoning, not sourced.

## Failure analysis for retrieval (categories and fixes)

### Takeaway
Classify every miss into a small set of causes and attack the largest bucket; each cause has a typical fix (BM25/hybrid for vocabulary, chunking/contextualisation for boundaries, metadata filters for versions, decomposition or long context for multi-hop, ingestion for missing data).

### Cited Findings
- Inventory vs capability: inventory problems mean the data is not indexed (fix ingestion); capability problems mean data exists but search cannot surface it (fix search, filtering, metadata). — [Jason Liu 2025](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/)
- Segment queries (topic, complexity, user role, or cluster them) and measure recall per segment. — [Jason Liu 2025](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/)
- Chunk boundary / missing context: Anthropic's contextual retrieval prepends 50-100 tokens of document context to each chunk because chunks lose context; it cut failures 35% (embeddings) and 49% with contextual BM25. — [Anthropic 2024](https://www.anthropic.com/news/contextual-retrieval)
- Vocabulary/lexical: BM25 remains a robust baseline; dense models often underperform it out of domain (TAS-B beat BM25 on 8/18 BEIR datasets, ANCE 4/18, DPR 1/18 by a count from Table 2). — [BEIR](https://arxiv.org/html/2104.08663v4)
- RAG failure causes vs long context (Self-Route analysis): multi-step reasoning dominates on HotpotQA, 2WikiMultihopQA, MuSiQue; implicit queries on NarrativeQA; general (summary-type) queries on QMSum; "other" was mostly ambiguous multi-step questions. — [Li et al. 2024](https://arxiv.org/html/2407.16833v2)

### Inferences
- Suggested miss taxonomy and fix:
  - Vocabulary mismatch (user words differ from document words, or exact codes/identifiers): hybrid BM25 + dense, query rewriting/expansion, glossary-based term mapping, embedding fine-tuning.
  - Chunk boundary (answer split across chunks, table split from heading): structure-aware chunking, parent/neighbour expansion, contextual chunk headers.
  - Wrong document or version (superseded edition retrieved): version and date metadata with hard filters; deduplicate near-identical versions; label gold at (document, version, span).
  - Multi-hop (needs two or more spans): query decomposition, larger k, or route to long context; score as "all spans found".
  - Broad or summary questions: retrieval is the wrong tool; route to document-level reading or long context.
  - Inventory (not in the corpus) / parse errors (text lost in parsing): fix ingestion; these show as unfixable by any retrieval knob.
  - Label error (gold is wrong or incomplete; system found another valid passage): fix labels (pooling).
- Practical process: for each miss in the 300-set, log top-20 results and assign one category; usually 2-3 categories cover most misses.

### Gaps
- No source gave measured distributions of these miss categories in production RAG.

## Retrieval problem or generation problem? (component vs end-to-end, oracle context)

### Takeaway
Run the generator three ways (retrieved context, oracle/gold context, no context) and add a sufficiency judgment on retrieved context; the 2x2 of "context sufficient?" x "answer correct?" localises the fault.

### Cited Findings
- Sufficient-context framework: classify each instance by whether the retrieved context is sufficient (autorater 93% accurate), then analyse errors separately; models often give wrong answers rather than abstain when context is insufficient; and they still answer correctly 35-62% of the time with insufficient context (snippet, partially verified), so end-to-end accuracy can hide retrieval failures. — [Joren et al. 2024](https://arxiv.org/abs/2411.06037v3)
- eRAG evaluates each retrieved document by whether the LLM, given only that document, produces a correct output: a component metric tied to the generator. — [Salemi and Zamani 2024](https://arxiv.org/abs/2404.13781v1)
- Retrieval recall keeps rising with more context while answer accuracy drops after 4k-32k tokens for many models, so retrieval and generation can fail independently. — [Databricks 2024](https://www.databricks.com/blog/long-context-rag-performance-llms)
- RAGAS splits evaluation into retrieval-side (context precision/recall) and generation-side (faithfulness, answer relevance) metrics. — [RAGAS docs](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/); [RAGAS paper](https://arxiv.org/abs/2309.15217)

### Inferences
- Oracle test: answer with gold spans only. If oracle accuracy is low, the generator or prompt is the problem (or the question/label is bad). If oracle is high but real-retrieval accuracy is low, it is retrieval. If both high but users complain, it is the eval set.
- No-context test shows how much the model answers from memory (it can mask retrieval failure and is risky for regulated content).
- Diagnostic 2x2: sufficient + wrong = generation fault; insufficient + wrong = retrieval fault; insufficient + right = luck or memory (risky); sufficient + right = OK.
- Distractor test: oracle context plus top retrieved non-relevant chunks shows sensitivity to noise and ordering (lost in the middle).

### Gaps
- No numbers found on typical shares of retrieval vs generation faults in deployed systems.

## Long-context models vs retrieval: when to skip RAG

### Takeaway
For small corpora (Anthropic: under about 200k tokens / 500 pages) put everything in the prompt; for larger ones, RAG is much cheaper, and long context helps as a complement (larger k) or as a fallback route for hard queries (Self-Route).

### Cited Findings
- Anthropic: if the knowledge base is under 200,000 tokens (about 500 pages), include it all in the prompt; prompt caching cuts latency more than 2x and cost up to 90%. — [Anthropic 2024](https://www.anthropic.com/news/contextual-retrieval)
- Li et al. (EMNLP 2024 industry): with enough resources, long context beats RAG on average (Gemini-1.5-Pro 49.70 vs 37.33; GPT-4o 48.67 vs 32.60; GPT-3.5-Turbo 32.07 vs 30.33) but RAG is far cheaper. Self-Route lets the model decide if retrieved chunks suffice, else falls back to long context: GPT-4o 48.89 (above LC) using about 61% of LC tokens; Gemini 46.41 using about 38% of tokens; roughly 57-77% of queries answered by RAG; reported cost cuts about 65% (Gemini) and 39% (GPT-4o). The paper's text and table disagree slightly on some shares. — [Li et al. 2024](https://arxiv.org/html/2407.16833v2)
- Databricks: long context and RAG are synergistic; most models degrade beyond a model-specific context size; newer models (gpt-4o, claude-3.5-sonnet) hold up. — [Databricks 2024](https://www.databricks.com/blog/long-context-rag-performance-llms)
- Lost in the middle effect persists in long-context models. — [Liu et al. 2023](https://arxiv.org/abs/2307.03172)

### Inferences
- A corpus of tens of thousands of chunks (e.g. a regulations library) is far above the 200k-token threshold, so RAG remains necessary; long context is useful per query (read a whole section or document once retrieval has found it).
- Self-Route is a cheap production pattern: answer from retrieval, and when the model or a sufficiency check says "not enough", fetch the whole document.

### Gaps
- 2025-2026 results for million-token models vs RAG were not collected in this pass.

## Benchmarks and evidence (BEIR, MTEB, reported hybrid and rerank gains)

### Takeaway
BEIR's lessons still hold: BM25 is a strong out-of-domain baseline, rerankers give the most reliable gains at latency cost, benchmark leaderboards (MTEB) do not transfer reliably to your domain, so always evaluate candidate models on your own set.

### Cited Findings
- BEIR: 18 datasets, 10 systems, nDCG@10. Average vs BM25: BM25+CE +11%, ColBERT +2.5%, docT5query +1.6%, TAS-B -2.8%, GenQ -3.6%, ANCE -7.4%, DPR -47.7%. Dense models often underperform BM25 out of distribution. — [BEIR](https://arxiv.org/html/2104.08663v4)
- MTEB: no embedding method dominates across tasks. — [MTEB](https://arxiv.org/abs/2210.07316)
- Hybrid gains: RRF +18% nDCG@10 over BM25, +1.4% over the learned sparse model (Elastic, vendor). — [Elastic](https://www.elastic.co/search-labs/blog/improving-information-retrieval-elastic-stack-hybrid)
- Contextual BM25 + contextual embeddings + reranker cut top-20 failures by 67% vs plain embeddings. — [Anthropic 2024](https://www.anthropic.com/news/contextual-retrieval)
- Chunking choice: up to about 9 recall points difference. — [Chroma](https://www.trychroma.com/research/evaluating-chunking)

### Inferences
- The engineer's observed gains (chunking +12 points, reranker +11 points) are in line with or larger than published deltas, which suggests the baseline had headroom; further gains will be smaller and need significance testing.
- Domain shift lesson: an embedding model's MTEB rank is a prior, not a decision; shortlist 2-3 models and test them on the golden set (it needs a re-embed per model, so cache).

### Gaps
- No independent 2025-2026 benchmark of hybrid vs dense with modern embedders (e.g. E5/BGE/Voyage) was retrieved; MTEB's later versions (MMTEB) not covered.
