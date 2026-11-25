# Eval data science: study map

*A to-do list for my own practice, not interview prep and not facts about me. It lists
the data-science ideas behind evals, prompt and retrieval tuning, and graph vs
vector choices: what each is, the terms to search, where it helps in a production
agent workflow, how deep to go, and the best sources. Built 25 Nov 2026 from
`systematic-evals-report.md` (full evidence and links there).*

## The budget and the honest limits

- **About 45 hours in total**: roughly 1.5 weeks full time, or 2 weeks next to other work.
- **The goal is working knowledge, not a data science degree.** Know what to compute,
  which library does it, and how to read the result. No derivations.
- **Things these tools will not do:**
  - Make a 2-point gain on 300 questions provable. At that size you can reliably see
    about 5 points. Small prompt tweaks are accepted for a named reason plus a "not
    worse" check, not as a measured win.
  - Replace reading traces. The statistics only tell you how far to trust a number;
    error analysis tells you which number to build.
  - Give one answer for graph vs vector. It is decided per question type.
- **Libraries to use instead of formulas:** `scipy.stats` (t-test, permutation,
  bootstrap), `statsmodels` (Wilson interval, McNemar, Holm, Cohen's kappa),
  `judgy` (corrected judge pass rate). Optional: `ranx` for IR metrics with built-in
  significance tests (not from the research; check before relying on it).

## How to use this file

- One topic per session. Each topic has a "done when" line: a small exercise on one of
  my labs (`agentic-rag-lab`, `kb-knowhow`) or on builders_lab.
- The **Status** column is for triage: *know it*, *know it, practice gaps*, *heard of it*,
  or *new*. Topics I already know drop to a quick skim.
- Where my labs stand on each topic, with actions and ADR seeds for builders_lab:
  `eval-practice-assessment.md`.

## Overview

| # | Topic | Week | Hours | Status |
|---|---|---|---|---|
| 1 | Error analysis | 1 | 4 | know it, practice gaps ([assessment](eval-practice-assessment.md#topic-1-error-analysis-code-ea)) |
| 2 | Uncertainty basics: standard error, intervals, power | 1 | 4 | new ([assessment](eval-practice-assessment.md#topic-2-uncertainty-basics-code-ub)) |
| 3 | Paired comparisons, repeats and clustering | 1 | 5 | McNemar known; rest new ([assessment](eval-practice-assessment.md#topic-3-paired-comparisons-repeats-and-clustering-code-pc)) |
| 4 | The judge as a classifier | 1 | 5 | labelling known; metrics partly new; judge design **priority** ([assessment](eval-practice-assessment.md#topic-4-the-judge-as-a-classifier-code-jc)) |
| 5 | Correcting the judge's pass rate | 1 | 3 | written, not discussed ([assessment](eval-practice-assessment.md#topic-5-correcting-the-judges-pass-rate-code-cr)) |
| 6 | Many variants and held-out hygiene | 2 | 3 | written, not discussed ([assessment](eval-practice-assessment.md#topic-6-many-variants-and-held-out-hygiene-code-mv)) |
| 7 | Gates: "not worse beyond a margin" | 2 | 3 | written, not discussed ([assessment](eval-practice-assessment.md#topic-7-gates-not-worse-beyond-a-margin-code-ni)) |
| 8 | Agent reliability: pass^k and flaky items | 2 | 2 | new; worth using ([assessment](eval-practice-assessment.md#topic-8-agent-reliability-passk-and-flaky-items-code-ar)) |
| 9 | Retrieval evaluation done properly | 2 | 6 | not walked through yet |
| 10 | Retrieval tuning experiments | 2 | 3 | not walked through yet |
| 11 | Prompt experiments and abstention | 2 | 3 | partly known; **priority** ([assessment](eval-practice-assessment.md#topic-11-prompt-experiments-and-abstention-code-pe)) |
| 12 | Graph vs vector decision | 2 | 4 | piece 1 discussed, piece 2 written ([assessment](eval-practice-assessment.md#topic-12-graph-vs-vector-decision-code-gv)) |

## Week 1: measuring well

### 1. Error analysis (4 h)

- **What it is:** read real traces, note the first failure in each, group the notes
  into 5-10 failure modes, count them. Stop when new traces show nothing new.
- **Terms:** open coding, axial coding, failure taxonomy, theoretical saturation,
  first-failure coding, transition failure matrix, criteria drift.
- **Where it helps:** decides which evals to build at all, and which failures need a
  code check, an LLM judge, or just a prompt fix. Stops eval sets from being generic.
- **How deep:** the workflow and the "code check vs judge vs nothing" rule. Skip the
  qualitative-research theory.
- **Sources:** Husain & Shankar, [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/);
  Husain, [Field Guide](https://hamel.dev/blog/posts/field-guide/);
  Shankar et al., [Who Validates the Validators?](https://arxiv.org/abs/2404.12272) (criteria drift).
- **Done when:** I have coded 50 traces from one system and have a counted list of
  failure modes, each marked code check / judge / prompt fix.

### 2. Uncertainty basics: standard error, intervals, power (4 h)

- **What it is:** every score is an estimate with a margin of error. How big the margin
  is, and how many questions you need to see a given change.
- **Terms:** standard error (SE), 95% confidence interval, Wilson interval (vs Wald),
  statistical power, minimum detectable effect (MDE), sample size planning.
- **Where it helps:** knowing what a 300-question golden set can and cannot show;
  reporting "85% ± 4" instead of "85%"; deciding when to grow the set.
- **How deep:** compute SE and a Wilson interval; read a power table. Know that 4x
  the questions halves the SE.
- **Sources:** Miller, [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640)
  (the core paper for this whole map); Brown, Cai & DasGupta 2001 on Wilson (skim only).
- **Done when:** I can say, for one of my eval sets, the SE of its main score and the
  smallest change it can detect.

### 3. Paired comparisons, repeats and clustering (5 h)

- **What it is:** comparing two versions on the same questions, question by question;
  combining repeated runs correctly; handling questions that share a source document.
- **Terms:** paired difference, discordant pairs, McNemar (exact), paired t-test,
  permutation test, bootstrap, cluster bootstrap, clustered standard errors,
  variance decomposition.
- **Where it helps:** every A/B of a prompt, model or retrieval setting. Shows why a
  model swap needs more questions than a small tweak (more answers change), and why
  15 questions from one broken document are one event, not 15.
- **How deep:** which test fits which score (McNemar for one-run pass/fail; paired t or
  permutation for averaged or graded scores; avoid Wilcoxon); average runs per
  question first, never pool 3 x 300 as 900.
- **Sources:** Miller 2024 (paired and clustered sections);
  Urbano et al. 2019, [Statistical significance testing in IR](https://arxiv.org/abs/1905.11096)
  (which tests behave); Smucker, Allan & Carterette 2007 (same, earlier).
- **Done when:** I report one past A/B as "+X points, 95% CI a to b", with the
  discordant counts and clustering by document.

### 4. The judge as a classifier (5 h)

- **What it is:** an LLM judge predicts a human verdict, so it has error rates like any
  classifier. Measure them on a frozen, labelled test set.
- **Terms:** confusion matrix, true positive rate (TPR, failures caught), true negative
  rate (TNR), precision on "fail", Cohen's kappa, inter-annotator agreement,
  Krippendorff's alpha, train/dev/test split for the judge prompt, judge biases
  (position, verbosity, self-preference, leniency), reference-guided grading, juries.
- **Where it helps:** knowing whether the judge can be trusted as a release gate;
  choosing a 1-5 threshold; deciding how to combine two judges; knowing when a model
  or prompt change means re-validating.
- **How deep:** build the labelled set (100-200 labels per criterion, enough fails),
  report TPR/TNR/kappa, treat a combining rule as its own classifier. Know why raw
  agreement misleads.
- **Sources:** Husain, [Creating an LLM judge](https://hamel.dev/blog/posts/llm-judge/);
  Eugene Yan, [Evaluating LLM evaluators](https://eugeneyan.com/writing/llm-evaluators/);
  Zheng et al. 2023 (MT-Bench biases); Verga et al. 2024, [Juries](https://arxiv.org/abs/2404.18796).
- **Done when:** one judge on one criterion has a frozen test set and a reported
  TPR, TNR and kappa with intervals.

### 5. Correcting the judge's pass rate (3 h)

- **What it is:** if the judge misses some failures or flags some good answers, its
  raw pass rate is biased. Correct it using the measured TPR and TNR.
- **Terms:** Rogan-Gladen correction, prediction-powered inference (PPI).
- **Where it helps:** reporting a release score that means what it says, e.g.
  "82% raw, 76% corrected (70-82)".
- **How deep:** use `judgy`; know the formula exists and when it breaks
  (judge near chance). PPI: concept only, for graded scores.
- **Sources:** [judgy](https://github.com/ai-evals-course/judgy);
  Lee et al. 2025, [arXiv 2511.21140](https://arxiv.org/abs/2511.21140);
  Angelopoulos et al. 2023, [PPI](https://arxiv.org/abs/2301.09633) (abstract and intro).
- **Done when:** I have run `judgy` on the judge from topic 4.

## Week 2: applying it

### 6. Many variants and held-out hygiene (3 h)

- **What it is:** trying many variants and keeping the best inflates the winner by
  chance. Each look at the holdout wears it out.
- **Terms:** multiple comparisons, family-wise error, Holm correction, garden of
  forking paths, adaptive overfitting, reusable holdout, dev-test gap.
- **Where it helps:** prompt and retrieval tuning sessions where I try 10-20 settings.
- **How deep:** Holm in `statsmodels`; write the comparison plan before running;
  one final check on held-out questions.
- **Sources:** Otero et al. 2025, [arXiv 2501.03930](https://arxiv.org/abs/2501.03930);
  Google Research, [The reusable holdout](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/).
- **Done when:** my experiment log has a dev/test split rule and a Holm step.

### 7. Gates: "not worse beyond a margin" (3 h)

- **What it is:** a fixed threshold fires on noise. A non-inferiority gate blocks a
  change only if the lower end of the paired difference falls below a set margin.
- **Terms:** non-inferiority test, margin, A/A test (same config run twice), flip rate,
  noise floor, per-segment gates.
- **Where it helps:** CI release gates for prompts, models and documents.
- **How deep:** run an A/A test to measure the noise floor; set the margin from it;
  gate per question type, not only on the average.
- **Sources:** thin in the LLM literature; the report's gate section and Miller 2024.
  Search "non-inferiority margin" in general statistics texts.
- **Done when:** one gate is written as a non-inferiority check with a margin from an
  A/A run.

### 8. Agent reliability: pass^k and flaky items (2 h)

- **What it is:** an agent that works 90% of the time works 8 times in a row only
  about 43% of the time. Repeats show which questions are flaky.
- **Terms:** pass@k, pass^k, flaky items, capability evals vs regression evals,
  judge self-consistency.
- **Where it helps:** agent workflows that must work every time; finding prompt work
  targets (flaky items hold most of the noise).
- **Sources:** Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents);
  Yao et al. 2024, [tau-bench](https://arxiv.org/abs/2406.12045).
- **Done when:** an eval report shows pass^k and lists flaky items.

### 9. Retrieval evaluation done properly (6 h)

- **What it is:** labels that survive re-chunking, fair comparison of new retrievers,
  and splitting retrieval faults from generation faults.
- **Terms:** span-level labels (document, version, span), pooling, incomplete
  judgments, graded relevance, nDCG, candidate recall vs final recall, eRAG,
  sufficient context, oracle context run, no-context run.
- **Where it helps:** every chunking, embedding or reranker change; deciding whether a
  wrong answer is a search problem or a prompt problem; making recall@k a gate that
  predicts answer quality.
- **How deep:** span labels and pooling in practice; the 2x2 table (context sufficient?
  x answer correct?); recall gate with k = real context size and "all spans" for
  multi-hop.
- **Sources:** Chroma, [Evaluating chunking](https://www.trychroma.com/research/evaluating-chunking)
  (span labels); Thakur et al., [BEIR](https://arxiv.org/abs/2104.08663) (pooling lesson);
  Joren et al. 2024, [Sufficient context](https://arxiv.org/abs/2411.06037);
  Jason Liu, [Systematically improving RAG](https://jxnl.co/writing/2025/01/24/systematically-improving-rag-applications/).
- **Done when:** one gold set is stored as spans, and I have run oracle and
  no-context passes on it. (builders_lab's gold label fix, S116, is a natural place.)

### 10. Retrieval tuning experiments (3 h)

- **What it is:** which knobs matter, in which order, and how to test them.
- **Terms:** hybrid search, BM25, reciprocal rank fusion (RRF) vs weighted fusion,
  cross-encoder reranker, contextual retrieval, ablation, one-knob-at-a-time.
- **Where it helps:** planning a tuning round cheaply: knobs that need no re-index
  (reranker, fusion weights, k, query rewriting) first, re-index knobs (chunking,
  embeddings) after.
- **How deep:** know the evidence for each knob and the miss categories that point to it.
- **Sources:** Anthropic, [Contextual retrieval](https://www.anthropic.com/news/contextual-retrieval);
  Bruch et al. 2022, [arXiv 2210.11934](https://arxiv.org/abs/2210.11934) (fusion).
- **Done when:** I have a miss-category count and a ranked list of knobs to try.

### 11. Prompt experiments and abstention (3 h)

- **What it is:** treating prompt changes as experiments; scoring "I don't know"
  so tuning doesn't push the model toward guessing.
- **Terms:** prompt ablation, prompt sensitivity, prompt bloat, selective accuracy,
  coverage, abstention, migration eval.
- **Where it helps:** prompt changes, removing old rules, model upgrades.
- **How deep:** one change per hypothesis; per-item scores logged; score correct /
  wrong / abstained; a migration checklist.
- **Sources:** Sclar et al. 2023, [Prompt sensitivity](https://arxiv.org/abs/2310.11324);
  OpenAI, [Why language models hallucinate](https://openai.com/index/why-language-models-hallucinate/);
  Anthropic prompting best practices; IFScale, [arXiv 2507.11538](https://arxiv.org/abs/2507.11538) (bloat).
- **Done when:** one prompt has had its rules ablated, and the golden set scores abstention.

### 12. Graph vs vector decision (4 h)

- **What it is:** graphs help on multi-hop, comparison, timeline and whole-corpus
  questions; they do worse on simple facts and on "not found", and cost far more.
  Many reported wins shrink when token budgets are matched and judges debiased.
- **Terms:** GraphRAG (local, global), LazyGraphRAG, HippoRAG 2, question-type
  taxonomy, matched token budget, pairwise judge bias, self-vs-self check,
  complementarity (only-A-right vs only-B-right).
- **Where it helps:** deciding before building a graph; judging vendor claims.
- **How deep:** the decision table by question type and the 8-step fair test in the
  report. Do not learn graph databases for this.
- **Sources:** Han et al. 2025, [RAG vs GraphRAG](https://arxiv.org/abs/2502.11371);
  [arXiv 2506.06331](https://arxiv.org/abs/2506.06331) (judge bias in GraphRAG evals);
  Xiang et al., [GraphRAG-Bench](https://arxiv.org/abs/2506.05690).
- **Done when:** a golden set is labelled by question type and I can say which types,
  if any, would justify a graph.

## Parked (awareness only, not in the 2 weeks)

| Topic | Why parked | Revisit when |
|---|---|---|
| Automatic prompt optimisers (DSPy MIPROv2, GEPA, TextGrad) | Need a validated metric and 50-200+ labels first (topics 4-5) | Migrating to a cheaper model, or a judge is validated |
| Calibration metrics (ECE, coverage-risk curves) | Topic 11's abstention scoring covers the practical need | A product needs confidence scores shown to users |
| Bayesian evaluation, item response theory | Useful for big benchmarks, not a 300-question set | Eval sets reach thousands of items |
| Causal inference, online A/B testing at scale | Needs real traffic volume | A product has enough users for online tests |
| Graph databases and Cypher | Only needed after topic 12 says a graph wins | A question type clearly needs a modelled graph |
