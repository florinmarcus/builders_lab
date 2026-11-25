# Graph-based retrieval (GraphRAG, knowledge graphs) vs vector/hybrid search: how to decide and how to test it

Research notes, 25 Nov 2026. Theory and published evidence only, not facts about Florin's work.
Source labels: [independent] = academic paper not by the method's authors; [method authors] = paper proposing the method (self-reported); [vendor] = company selling graph tech.

## 1. What GraphRAG variants exist and what each is for

### Takeaway
"GraphRAG" covers very different designs: LLM-built entity graphs with community summaries (Microsoft GraphRAG, for whole-corpus "sensemaking"), cheap concept graphs built at query time (LazyGraphRAG), graph-as-index for multi-hop passage retrieval (HippoRAG / HippoRAG 2), keyword-graph hybrids (LightRAG), and true knowledge graphs queried with Cypher/SPARQL/SQL (for structured, relationship and aggregation questions). Treat them as separate options, because the evidence differs sharply between them.

### Cited Findings
- **Microsoft GraphRAG (Edge et al. 2024)** [method authors]: an LLM extracts an entity knowledge graph from the text, pregenerates summaries of communities of related entities, then answers "global" questions map-reduce style (each community summary gives a partial answer, then these are summarised). Framed as query-focused summarisation over whole private corpora, which plain RAG handles poorly. — [Edge et al. 2024, arXiv 2404.16130](https://arxiv.org/abs/2404.16130)
- Implementation details: Leiden community detection, gpt-4-turbo, 600-token chunks, 8k context; community levels C0 (root, fewest summaries) to C3 (most detailed). — [Edge et al. 2024 (HTML)](https://arxiv.org/html/2404.16130)
- **Local vs global search** (Microsoft's framing): local questions have answers in specific passages (who, what, when, where) and vector RAG handles them well; global questions need the whole dataset ("what are the main themes?"), which GraphRAG global search targets. — [Microsoft Research blog, LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- **LazyGraphRAG** [method authors]: no LLM at indexing. NLP noun-phrase extraction builds a concept co-occurrence graph and community hierarchy; at query time an LLM expands the query into 3 to 5 subqueries, ranks chunks by embedding similarity, tests relevance with an LLM, drills into sub-communities, then map-reduces claims. One "relevance test budget" parameter sets the cost/quality trade-off. — [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- **HippoRAG 2** [method authors]: builds on HippoRAG's Personalized PageRank over an LLM-extracted graph, adding deeper passage integration and online LLM use; aims to beat standard RAG on factual, sense-making and associative (multi-hop) memory tasks. Its abstract states earlier structure-augmented methods' performance on "more basic factual memory tasks drops considerably below standard RAG". — [Gutiérrez et al. 2025, arXiv 2502.14802](https://arxiv.org/abs/2502.14802)
- HippoRAG 2 returns passages (it can be scored with passage recall@k); GraphRAG and LightRAG do not directly produce passage retrieval results, so they cannot be scored that way. — [HippoRAG 2 (HTML)](https://arxiv.org/html/2502.14802v2)
- **KG + text-to-query** (Cypher/SQL/SPARQL over a modelled schema): Sequeda, Allemang and Jacob (data.world) found GPT-4 zero-shot accuracy on 43 enterprise questions over an insurance SQL database rose from 16.7% (SQL directly) to 54.2% when the database was represented as a knowledge graph; a follow-up with ontology-based query checking and LLM repair reached 72.55%. [vendor-affiliated authors; small question set] — [Sequeda et al. 2023, arXiv 2311.07509](https://arxiv.org/abs/2311.07509)
- **Graph traversal/computation tools for an LLM** (industrial KG, aerospace supply chain, 46 nodes, 64 typed edges, 23 queries): five query classes were "structurally unreachable" for vector retrieval; an LLM query planner with 9 typed traversal primitives beat bespoke handlers (F1 0.632 vs 0.472). Thesis: the bottleneck is the set of graph operators available, not model intelligence. Tiny scale. — [arXiv 2606.06003](https://arxiv.org/abs/2606.06003)
- **Entity-linked hybrid** (vector search to find entry points, graph to expand connected context) is the pattern graph vendors themselves recommend for production, not graph-only retrieval. [vendor] — [Neo4j blog](https://neo4j.com/blog/agentic-ai/vector-rag-vs-graphrag/); [TigerGraph blog](https://www.tigergraph.com/blog/graphrag-vs-vector-rag/)

### Inferences
- There are two different families. (a) "Graph built from unstructured text by an LLM" (GraphRAG, LightRAG, HippoRAG) competes with vector search on documents. (b) "Graph that models data you already have" (KG + Cypher/SQL) competes with text-to-SQL and is about structured questions. Most benchmark arguments are about family (a).
- HippoRAG 2 is closer to "better multi-hop retriever" than to "GraphRAG" in the Microsoft sense; it is the variant that most often matches dense retrieval on simple questions.

### Gaps
- LightRAG design details (dual-level low/high keyword retrieval, incremental update claim) are from the LightRAG paper (Guo et al. 2024, arXiv 2410.05779), which I did not re-fetch in this session; verify before quoting.
- Original HippoRAG (NeurIPS 2024, arXiv 2405.14831) details not re-fetched.

## 2. Benchmark evidence: where graphs win, where vector/hybrid matches or beats them

### Takeaway
Independent evidence is consistent: plain/hybrid RAG with a good embedder and reranker wins or ties on single-hop and detail questions; graph methods help on multi-hop, comparison, temporal and whole-corpus summary questions, but gains are moderate, method-specific, and often shrink when token budgets are matched. The big headline wins (72 to 83% win rates) come from LLM-judge pairwise tests that are shown to be heavily biased.

### Cited Findings
**Original GraphRAG claim (method authors)**
- Two corpora (~1M tokens podcast transcripts, ~1.7M tokens news), 125 generated questions each, 5 repeats. Global GraphRAG beat vector RAG on comprehensiveness (72 to 83% podcast, 72 to 80% news, p<.001) and diversity (75 to 82% podcast, 62 to 71% news). Vector RAG gave the most direct answers. Root-level C0 summaries used over 97% fewer tokens than summarising all source text. — [Edge et al. 2024 (HTML)](https://arxiv.org/html/2404.16130)
- The authors' own limitations: only two ~1M-token corpora; fabrication/hallucination not measured; claim-based validation sensitive to thresholds; LLM-judge vs claim-based agreement 78% (comprehensiveness), 69 to 70% (diversity). — [Edge et al. 2024 (HTML)](https://arxiv.org/html/2404.16130)
- Questions were LLM-generated "global sensemaking" questions; no accuracy against ground truth. — [Edge et al. 2024 (HTML)](https://arxiv.org/html/2404.16130)

**Critique of LLM-judged win rates [independent]**
- "How Significant Are the Real Performance Gains?" (2025): existing GraphRAG evaluations suffer from unrelated test questions and judge bias (position, length, trial). With the original protocol, LightRAG vs an identical copy of itself scored 90% vs 10%. Swapping answer order shifted win rates by over 30 points; a 25-token length gap (answers ~200 tokens) produced a win-rate gap of over 50 points; across five trials the winner changed. — [arXiv 2506.06331](https://arxiv.org/html/2506.06331v1)
- Under their debiased protocol (questions grounded in graph and text, multiple rounds, ties allowed), LightRAG vs NaiveRAG on Agriculture fell from a reported 66.7% win rate to 39.06%; LightRAG vs Microsoft GraphRAG from 56.38% to 32.33%; ties over 20% in most cases; best method (Fast-GraphRAG) gained mostly under 10 points. — [arXiv 2506.06331](https://arxiv.org/html/2506.06331v1)
- Han et al. (RAG vs GraphRAG) found GPT-4o as judge on QMSum gave Community-Local a 97% comprehensiveness win in one order and 12% in the other; a newer judge model reduced but did not remove the bias. Recommendation: score both orders, average, use multiple judges. — [Han et al. 2025, arXiv 2502.11371 (HTML)](https://arxiv.org/html/2502.11371)

**Han et al. 2025, "RAG vs. GraphRAG: A Systematic Evaluation" [independent], unified protocol, Llama-3.1-8B unless noted**
- F1: NQ — RAG 64.78, Community-GraphRAG local 63.01, global 54.48, HippoRAG2 61.03, KG triplets-only 34.28. HotpotQA — RAG 60.04, local 61.66, global 45.16, HippoRAG2 63.01, KG triplets-only 25.02. — [arXiv 2502.11371](https://arxiv.org/html/2502.11371)
- MultiHop-RAG accuracy overall: RAG 67.02, local 69.01, global 64.40, HippoRAG2 70.27. By type: inference RAG 92.16 vs local 86.89; comparison RAG 57.59 vs global 64.02; temporal RAG 30.70 vs global 53.34; null ("insufficient information") RAG 96.01, local 80.07, global 19.27. — [same](https://arxiv.org/html/2502.11371)
- Only about 65.8% (HotpotQA) and 65.5% (NQ) of answer entities appeared in the LLM-built KG; answer-in-context rate HotpotQA RAG 88.6% vs KG triplets 39.2%. — [same](https://arxiv.org/html/2502.11371)
- Complementary: 13.6% of MultiHop-RAG queries were right only with GraphRAG, 11.6% only with RAG. Routing per query improved best baseline by 1.1%; concatenating both contexts by 6.4% (70B). — [same](https://arxiv.org/html/2502.11371)
- Token-matched check (70B): Community-GraphRAG retrieved ~9,770 tokens/query vs RAG ~3,631; giving RAG the same budget gave 71.01 vs GraphRAG 71.17, i.e. the gap mostly vanished. — [same](https://arxiv.org/html/2502.11371)
- Query-focused summarisation (ROUGE-2): RAG roughly equal to or above GraphRAG local; global search clearly worst (e.g. QMSum RAG 6.32, global 3.23). — [same](https://arxiv.org/html/2502.11371)
- Graph quality matters: graphs built with GPT-4o vs GPT-4o-mini raised MultiHop-RAG accuracy 71.17 to 75.08 (RAG 65.77). — [same](https://arxiv.org/html/2502.11371)

**GraphRAG-Bench, "When to use Graphs in RAG" (Xiang et al., ICLR 2026) [independent]**
- Motivation cites prior findings that GraphRAG had 13.4% lower accuracy than vanilla RAG on Natural Questions and a 16.6% drop on time-sensitive questions. — [arXiv 2506.05690](https://arxiv.org/abs/2506.05690v3); [ICLR 2026 poster](https://iclr.cc/virtual/2026/poster/10007992)
- Novel corpus, GPT-4o-mini: fact retrieval — RAG+rerank 60.92 best (HippoRAG2 60.14). Complex reasoning — RAG+rerank 42.93 vs HippoRAG2 53.38, MS-GraphRAG 50.93, LazyGraphRAG 49.22, LightRAG 49.07. Contextual summarise — RAG+rerank 51.30 vs MS-GraphRAG 64.40, HippoRAG2 64.10; LightRAG, HippoRAG, RAPTOR below baseline. — [arXiv 2506.05690 (HTML)](https://arxiv.org/html/2506.05690v3)
- Medical corpus: MS-GraphRAG fell far below RAG on fact retrieval (38.63 vs 64.73) and complex reasoning (47.04 vs 58.64); HippoRAG2 edged RAG on both. So the same method flips by domain. — [same](https://arxiv.org/html/2506.05690v3)
- RAG+rerank had the highest evidence recall on fact retrieval (83.21); HippoRAG led recall on reasoning and summary tasks. — [same](https://arxiv.org/html/2506.05690v3)
- Guidance: basic RAG for single-passage lookups (graph adds noise); consider graphs for complex reasoning and summarisation; weigh token overhead. — [same](https://arxiv.org/html/2506.05690v3)

**HippoRAG 2 paper (method authors, but includes others as baselines), Llama-3.3-70B reader, F1**
- NV-Embed-v2 (dense) average 57.0; Microsoft GraphRAG 49.6; LightRAG 6.6 (near zero on several sets); RAPTOR 48.8; HippoRAG 53.1; HippoRAG 2 59.8. MuSiQue: dense 45.7, GraphRAG 38.5, HippoRAG2 48.6. 2Wiki: dense 61.5, GraphRAG 58.6, HippoRAG2 71.0. HotpotQA: dense 75.3, GraphRAG 68.6, HippoRAG2 75.5. NQ: dense 61.9, GraphRAG 46.9. — [arXiv 2502.14802 (HTML)](https://arxiv.org/html/2502.14802v2)
- Paper states "all previous structure-augmented methods underperform" the strongest embedding RAG across benchmark types. Note LightRAG's near-zero scores are likely partly a setup/output-format issue in this reproduction; treat as "fragile", not as a fair estimate. — [same](https://arxiv.org/html/2502.14802v2)

**LazyGraphRAG / BenchmarkQED (method authors)**
- 5,590 AP news articles, 100 synthetic queries (50 local, 50 global), LLM pairwise judge on comprehensiveness, diversity, empowerment. LazyGraphRAG at 100 relevance tests beat all conditions on local and global queries except GraphRAG global on global; at 4% of GraphRAG global's query cost it beat all. — [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- BenchmarkQED (June 2025): AutoQ generates four query classes from local to global scope plus "assertions" as unit tests for answer accuracy; AutoE uses LLM-as-judge; headline result LazyGraphRAG best on global queries. — [Microsoft Research, BenchmarkQED](https://www.microsoft.com/en-us/research/?p=1140429); [PyPI benchmark-qed](https://pypi.org/project/benchmark-qed/)

**Vendor claims (treat with caution)**
- Neo4j cites an "NICD 2026" benchmark: 510 complex questions, 65.3% answered with vector+graph vs 28.9% vector-only; and an IDC study sponsored by Neo4j claiming 44% fewer hallucinations. The article's own headline ("more than double factual accuracy") does not match its body ("roughly 80% higher"). — [Neo4j blog](https://neo4j.com/blog/agentic-ai/vector-rag-vs-graphrag/)

### Inferences
- The pattern across three independent studies: graphs help most on multi-hop / comparison / temporal and whole-corpus summary questions; they hurt on simple facts, detail questions, and "say I don't know" (null) cases, especially global search.
- A large part of reported graph gains may be "more context tokens", not "graph structure" (Han et al. token-matched check). Always compare at matched token budgets.
- Combining both contexts beat choosing one; this supports "graph as an extra retrieval lane" over "replace vector".
- Pairwise LLM-judge win rates without order swapping, ties and repeats should not be trusted as evidence.

### Gaps
- No rigorous, independent production post-mortem found; practitioner evidence is anecdotal blogs (e.g. a hackathon over 14,247 papers where the graph found papers for one multi-hop question that hybrid missed — [DEV post](https://dev.to/mesh4567890098765/we-built-a-graphrag-system-over-14000-research-papers-heres-what-we-learned-2em7)).
- A second benchmark also called "GraphRAG-Bench" (2025) may exist; not checked.
- No independent benchmark found on long, hierarchical regulatory/legal documents specifically.

## 3. Costs: indexing, latency, maintenance, extraction errors and graph quality

### Takeaway
LLM-built graphs cost one to two orders of magnitude more to index than embeddings, add query latency (often 10x+), need care on updates because new documents can reshape communities, and silently lose about a third of answer entities at extraction. LazyGraphRAG and HippoRAG 2 are the cheaper exceptions.

### Cited Findings
- MuSiQue corpus indexing (relative): Microsoft GraphRAG 115.5M input + 36.1M output tokens, 277 min, 10.7 s per query; LightRAG 68.5M + 18.3M tokens, 235 min, 13.3 s/query; HippoRAG 2 9.2M + 3.0M tokens, 99.5 min, 1.2 s/query; NV-Embed-v2 dense: no LLM tokens, 12.1 min, 0.3 s/query. — [HippoRAG 2 (HTML), Table 12](https://arxiv.org/html/2502.14802v2)
- Han et al. (MultiHop-RAG): construction 135 s (RAG) vs 5,560 s (Community-GraphRAG) vs 7,702 s (KG-GraphRAG); retrieval 1,724 s vs 1,249 s vs 14,434 s; storage similar (117 to 165 MB). — [arXiv 2502.11371](https://arxiv.org/html/2502.11371)
- Average prompt tokens per query (GraphRAG-Bench, novel): vanilla RAG 879; HippoRAG2 1,008; RAPTOR 3,441; Fast-GraphRAG 4,204; MS-GraphRAG local 38,707; LightRAG 100,832; MS-GraphRAG global 331,375. — [arXiv 2506.05690 (HTML)](https://arxiv.org/html/2506.05690v3)
- Edge et al.: 281 minutes to index the ~1M-token podcast corpus with gpt-4-turbo. — [Edge et al. 2024 (HTML)](https://arxiv.org/html/2404.16130)
- LazyGraphRAG indexing costs match vector RAG, ~0.1% of full GraphRAG indexing; global configuration comparable to GraphRAG global quality at over 700x lower query cost. [method authors] — [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- Updates: GraphRAG 1.0 added an `update` command that computes deltas and merges them, with LLM caching to cut re-index cost; Microsoft notes new content "can alter the community structure such that much of an index needs to be re-computed". — [Microsoft Research, GraphRAG 1.0](https://www.microsoft.com/en-us/research/blog/moving-to-graphrag-1-0-streamlining-ergonomics-for-developers-and-users/)
- The archived Azure GraphRAG Solution Accelerator did not support incremental indexing. — [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/5578950/how-do-i-add-new-documents-to-my-microsoft-graph-r)
- Extraction loss: only ~65% of answer entities ended up in the LLM-built KG (HotpotQA, NQ). — [Han et al. 2025](https://arxiv.org/html/2502.11371)
- Graph quality metrics used in GraphRAG-Bench: nodes/edges per 10k tokens, average degree, clustering coefficient (HippoRAG2 densest: avg degree 8.75 vs MS-GraphRAG 1.48). — [arXiv 2506.05690](https://arxiv.org/html/2506.05690v3)
- Extractor model quality changes end accuracy (GPT-4o vs GPT-4o-mini graphs: 75.08 vs 71.17). — [Han et al. 2025](https://arxiv.org/html/2502.11371)
- Practitioners name entity resolution (merging duplicates of the same entity) and ingestion structure as common failure points. [blog, anecdotal] — [DEV post](https://dev.to/dibyanshu_mishra/beyond-vector-search-the-hidden-engineering-traps-of-graph-rag-in-production-2o5g)

### Inferences
- Practical graph-quality checks: (1) answer-entity coverage (share of gold-answer entities present as nodes), (2) precision/recall of extracted triples on a hand-labelled sample, (3) duplicate-entity rate after resolution, (4) structural stats (degree, isolated nodes). Coverage is the cheapest and most predictive given Han et al.'s 65% finding.
- For frequently changing corpora, community-summary GraphRAG is the worst fit; dense/hybrid, LazyGraphRAG, or a KG fed from source systems update more cheaply.

### Gaps
- No public figure found for what share of community summaries `graphrag update` regenerates per added document.
- No dollar figures at current model prices; token counts above must be priced by the reader.

## 4. Decision signals, and when simpler alternatives solve it

### Takeaway
Decide from failure analysis on your own questions, not from architecture fashion. Graph helps when the right facts are found but their connections are not (multi-hop, comparison, temporal, "how are X and Y related"), or for whole-corpus themes. For "list all X" or counts over structured data, SQL/metadata usually beats any retrieval. For single-passage facts, tune hybrid + rerank first.

### Cited Findings
- "Look at the retrieval failure before changing the architecture": poor semantic matches mean tune chunking, embeddings or filters; consistently finding the right facts without their connections points to GraphRAG. [vendor, but sensible] — [Neo4j blog](https://neo4j.com/blog/agentic-ai/vector-rag-vs-graphrag/)
- Vector search remains right when a question can be answered from one relevant passage. [vendor] — [Neo4j blog](https://neo4j.com/blog/agentic-ai/vector-rag-vs-graphrag/)
- Single-hop/detail: RAG wins (NQ, NovelQA detail); multi-hop, comparison, temporal: graphs help; null queries: global search fails badly (19.27% vs 96.01%). — [Han et al. 2025](https://arxiv.org/html/2502.11371)
- Basic RAG with rerank comparable or better on fact retrieval; graphs help complex reasoning and summarisation. — [GraphRAG-Bench](https://arxiv.org/html/2506.05690v3)
- Whole-corpus "themes" questions: GraphRAG global / LazyGraphRAG designed for these. [method authors] — [Microsoft Research blog](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- Existing structured data: representing a database as a KG with an ontology raised question accuracy (16.7% to 54.2%, 72.55% with query checking). — [Sequeda et al. 2023](https://arxiv.org/abs/2311.07509)
- Some query classes (traversal, path, graph computation) are unreachable by vector retrieval at all. — [arXiv 2606.06003](https://arxiv.org/abs/2606.06003)
- Applying GraphRAG as a general upgrade: one practitioner reports teams spent ~100x more on indexing with mixed results. [blog, unverified] — [Medium, GraphRAG vs PageIndex](https://medium.com/@umesh382.kushwaha/graphrag-vs-pageindex-when-knowledge-graphs-beat-vector-search-and-when-they-dont-25b10fad5fcb)

### Inferences (decision checklist, my synthesis from the above)
- **Single fact in one passage** → hybrid (BM25 + dense) + reranker. Graph adds noise.
- **Needs metadata scope** ("in the 2025 edition", "for document X") → metadata filters, not a graph.
- **Answer spans a document's structure** (section, table, definitions elsewhere) → structure-aware chunking, parent/section retrieval, a "get section"/"read document" tool for an agent. This is a document hierarchy graph, cheap and exact, not an LLM-extracted one.
- **"List all X" / counts / filters over records** → SQL or a typed index. Retrieval top-k cannot guarantee completeness.
- **Multi-hop across documents with named entities** → try HippoRAG 2-style entity linking or agentic iterative retrieval first (cheap), full GraphRAG only if those fail.
- **Relationship/path questions over known entities** (who supplies whom, what depends on what) → a modelled KG with Cypher/SQL, fed from source systems, not extracted by an LLM.
- **Whole-corpus themes** → LazyGraphRAG or GraphRAG global; or simply map-reduce over clusters/summaries.
- **Must say "not found"** reliably → avoid global community search.
- **High update frequency** → avoid community-summary GraphRAG.
- An agent with a few retrieval tools (search, get section, follow cross-reference) may capture most of the multi-hop gain without building a graph. This is a hypothesis; I found no direct benchmark of it in this session.

### Gaps
- No independent study found that compares "agentic iterative vector retrieval" vs GraphRAG head to head on the same benchmark.
- No source quantifies how often real enterprise question logs are multi-hop vs single-hop.

## 5. How to run a fair comparison on your own data

### Takeaway
Classify the golden set by question type, measure retrieval and answer quality per type, match token budgets, swap judge order and allow ties, measure cost and latency per query, use paired tests, and check per-query complementarity (route or combine). Decide per question type, not on an overall average.

### Cited Findings
- Build a test set mirroring production traffic; measure context precision, context recall, faithfulness, latency and token cost; if GraphRAG does not improve these, complexity is not justified. [vendor] — [Neo4j blog](https://neo4j.com/blog/agentic-ai/vector-rag-vs-graphrag/)
- Unified protocol: same preprocessing, retrieval configuration and generator for all systems. — [Han et al. 2025](https://arxiv.org/abs/2502.11371)
- Judge debiasing: both answer orders averaged, multiple judges; generate questions grounded in the source; multiple rounds with medians/percentiles; allow ties; control answer length. — [Han et al. 2025](https://arxiv.org/html/2502.11371); [arXiv 2506.06331](https://arxiv.org/html/2506.06331v1)
- Sanity check: run a system against an identical copy of itself; the judge should give ~50/50 (the original protocol gave 90/10). — [arXiv 2506.06331](https://arxiv.org/html/2506.06331v1)
- Token-matched baselines (give RAG the same context budget). — [Han et al. 2025](https://arxiv.org/html/2502.11371)
- Prefer assertion-based scoring ("unit tests" of facts the answer must contain) over pure pairwise preference. — [BenchmarkQED](https://www.microsoft.com/en-us/research/?p=1140429)
- Stratify by task type (fact retrieval, complex reasoning, summarise, creative) and evaluate graph construction, retrieval and generation separately. — [GraphRAG-Bench](https://arxiv.org/abs/2506.05690v3)
- Measure per-query complementarity (only-A-right vs only-B-right) and test routing vs context concatenation. — [Han et al. 2025](https://arxiv.org/html/2502.11371)
- Measure retrieval with evidence recall / passage recall@k where the method returns passages; GraphRAG/LightRAG may not, so use answer-in-context rate instead. — [HippoRAG 2](https://arxiv.org/html/2502.14802v2); [Han et al.](https://arxiv.org/html/2502.11371)

### Inferences (protocol, my synthesis)
1. **Label each golden question** with a type: single-fact, multi-hop (2+ documents), comparison, temporal/version, aggregation/"list all", relationship/path, global theme, unanswerable. Aim for 20 to 30+ per type you care about; small strata give wide confidence intervals.
2. **Strong baseline first:** hybrid BM25+dense, reranker, structure-aware chunks, metadata filters. Many "graph wins" vanish against a tuned baseline.
3. **Oracle tests:** (a) give the generator the gold evidence: if accuracy is still low, the problem is generation, not retrieval; (b) check whether gold evidence is in the top-k of each system (retrieval ceiling); (c) for the graph, check answer-entity coverage in the graph (extraction ceiling).
4. **Match token budgets** and record cost per query (input/output tokens, LLM calls), p50/p95 latency, plus one-off indexing cost and re-index cost for a typical weekly update.
5. **Score** with deterministic checks where possible (exact match, required assertions, citation correct); use LLM judges only with order swap, ties, repeats and a self-vs-self sanity check.
6. **Paired statistics:** same questions for both systems; McNemar's test for right/wrong outcomes, paired bootstrap or Wilcoxon for scores; report per-type deltas with confidence intervals, not one average.
7. **Complementarity:** count questions only one system gets right; if large, try routing by question type or union of contexts before replacing anything.
8. **Decide per type:** adopt graph retrieval only for the types where it wins by more than the noise, at acceptable cost and update burden.

### Gaps
- No published guidance found on minimum golden-set size per question type for this comparison; the 20 to 30 figure above is a rule of thumb, not sourced.
- McNemar/bootstrap recommendation is standard statistics practice, not taken from the GraphRAG papers above.
