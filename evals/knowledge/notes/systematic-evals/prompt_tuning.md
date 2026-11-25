# Prompt tuning and calibration as an experimental discipline

Scope: how an AI engineer running a RAG/agent system on Claude (Bedrock), with a golden set and a regression gate, should change prompts systematically. Research done 25 Nov 2026. Theory only, not facts about Florin's work.

## 1. A disciplined prompt iteration loop (error analysis first, dev/test splits, versioning)

### Takeaway
The loop practitioners recommend is: read real traces, build a failure taxonomy, fix obvious prompt gaps first, build cheap targeted checks for failures that remain, change one thing at a time on a dev split, and touch the held-out test split only for a final check. What to change next comes from the frequency and impact of failure categories, not from single bad examples.

### Cited Findings
- Start with error analysis, not evaluators: review 20-50 outputs (about 30 minutes) after every significant change; build a pool of about 100 diverse traces and annotate at least 30 yourself before using an agent's suggestions, because early suggestions bias you — [Hamel Husain & Shreya Shankar, LLM Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Method: free-text notes on failures (open coding), group into a failure taxonomy, stop at "theoretical saturation" when new traces show no new failure modes. Do not write the rubric first; it hides problems outside the rubric — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- The authors report spending 60-80% of development time on error analysis and evaluation — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- "Fix obvious problems first": if the prompt never states a constraint (length, format, step-by-step), add it rather than building test data for it. Build automated evaluators only for failures that persist after prompt fixes — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Prefer code assertions/regex for objective rules; an LLM judge needs about 100-200 labelled examples per failure mode; use one judge per failure mode, not one "overall quality" judge; track both TPR and TNR of each judge as prompts change — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Binary pass/fail beats Likert; for gradual progress use binary sub-checks ("4 of 5 expected facts present") — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Prioritise failures by frequency, impact and whether they survive simple fixes. Re-run error analysis after prompt changes, model switches or bug fixes; review at least 100 fresh traces per cycle (every 2-4 weeks) and 10-20 outlier traces weekly — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Split labelled data into train/dev/test: refine on dev, use test once at the end. A test score much lower than dev means overfitting; revise and check against a fresh test set — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- A ~100% pass rate may mean the evals are too easy; around 70% can be more informative — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Start with small, targeted edits; usually begin by making instructions more specific and removing ambiguity; be careful not to overfit; start zero-shot before adding examples; include messy real-world inputs and edge cases in the eval set — [web.dev, Evaluation-driven development](https://web.dev/learn/ai/evaluation-driven-development)
- Anthropic: give the reason behind an instruction ("explaining to Claude why such behavior is important") so the model can generalise; use 3-5 examples, chosen for relevance and diversity — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Prompt chaining pattern (generate → review against criteria → refine), each step a separate call "so you can log, evaluate, or branch at any point" — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)

### Inferences
- A practical loop for a Claude RAG/agent stack: (1) sample production/golden traces, (2) label failures and count per category, (3) pick the top category, (4) write a hypothesis and one prompt change, (5) run dev split with paired comparison against the current prompt (see section 2 for statistics), (6) keep the change only if the target category improves without regressions elsewhere, (7) version the prompt (immutable versioned files, e.g. `name.vN.md`, with the eval run ID and score logged next to it), (8) the regression gate runs the test split on merge.
- Ablations: when a prompt has grown many rules, remove one section at a time and re-run dev; sections whose removal changes nothing are bloat candidates.
- Each experiment log row should carry: prompt version hash, model ID, sampling settings, dataset version, per-item scores (not just the mean), and the hypothesis. Per-item scores are needed for paired tests.

### Gaps
- No primary source fetched on specific experiment-tracking tools (Langfuse, Braintrust, promptfoo, MLflow) or OpenAI's eval-driven cookbook; their recommendations are not cited here.
- Eugene Yan's and Jason Liu's write-ups were not reached in the search budget.

## 2. Prompt sensitivity and brittleness: how much do spurious changes move scores?

### Takeaway
Spurious changes (separators, casing, spacing, example order) can move scores by tens of points, especially for smaller models and few-shot formats, and the best format does not transfer across models. So a single-run score difference of a few points between two prompts is often noise; measure with error bars, paired comparisons and, where cheap, several format variants.

### Cited Findings
- Sclar et al. (ICLR 2024): small formatting changes in few-shot settings gave differences of up to 76 accuracy points on LLaMA-2-13B. Sensitivity persists with larger models, more few-shot examples and instruction tuning. Format rankings correlate only weakly across models. They propose FormatSpread: sample plausible formats and report an expected performance interval; recommend reporting a range rather than one format, since model rankings can flip with format — [Sclar et al. 2023, arXiv:2310.11324](https://arxiv.org/abs/2310.11324)
- ProSA (EMNLP Findings 2024): introduces PromptSensiScore; sensitivity varies by dataset and model; larger models are more robust; few-shot examples reduce sensitivity; subjective (LLM-judge) evaluations are also prompt-sensitive, especially on complex reasoning tasks; higher decoding confidence goes with more robustness — [Zhuo et al., ProSA, arXiv:2410.12405](https://arxiv.org/abs/2410.12405)
- Lu et al. (ACL 2022): few-shot example order alone can take performance from near state-of-the-art to near random; persists across model sizes; good orderings don't transfer between models; an entropy-based ordering method gave about 13% relative improvement across 11 classification tasks — [Lu et al., arXiv:2104.08786](https://arxiv.org/abs/2104.08786)
- Anthropic: long documents at the top and the query at the end "can improve response quality by up to 30 percent in tests", especially with complex multi-document inputs — a concrete example of placement sensitivity — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Statistics for comparing two prompts/models (Miller, "Adding Error Bars to Evals", 2024):
  - Report SE = sqrt(p(1-p)/n) next to each mean; e.g. 83.6% (3.2%) on HumanEval's 164 items — [Miller, arXiv:2411.00640](https://arxiv.org/html/2411.00640v1)
  - Use clustered SEs when items share a source (e.g. several questions on one document, as in RAG): naive SEs understated uncertainty by about 3x on DROP and 1.9x on MGSM — [Miller](https://arxiv.org/html/2411.00640v1)
  - Compare with paired per-item differences: with correlation 0.5, variance falls by a third. Example: a -3.1% difference on HumanEval had CI (-7.2%, +1.0%), not significant — [Miller](https://arxiv.org/html/2411.00640v1)
  - Resample each item K times: K=2 cuts within-item variance contribution by 1/3, K=4 by 1/2, ceiling 2/3. Do not lower temperature to reduce variance; it can add bias — [Miller](https://arxiv.org/html/2411.00640v1)
  - Power: detecting a 3-point difference at 80% power, alpha 0.05, needs about 969 independent questions; with 198 questions, raising K from 1 to 10 lowers the minimum detectable effect from 13.2% to 7.5% — [Miller](https://arxiv.org/html/2411.00640v1)

### Inferences
- With a golden set of a few hundred items, a typical prompt tweak worth 2-3 points is below the detectable effect. Either run K>1 samples per item, use paired tests, or accept the change on qualitative grounds (fixes a named failure category) plus "no significant regression".
- In RAG goldens, many questions come from the same document: treat the document as the cluster for SEs.
- Frontier Claude models should be less format-sensitive than LLaMA-2-13B (per ProSA's size finding), but the judge prompt is also sensitive, so judge prompt changes need their own validation against human labels.
- The regression gate threshold should be set from the measured run-to-run noise (run the same prompt 3-5 times and look at the spread) rather than a fixed number.

### Gaps
- No 2025-2026 measurement of format sensitivity specifically on Claude 4.x/5.x models was found.

## 3. Automatic prompt optimisation (DSPy BootstrapFewShot / MIPROv2 / GEPA, TextGrad, OPRO, APE)

### Takeaway
All optimisers need the same two things: a programmatic metric and a training set (from about 10 examples for few-shot bootstrapping to 200+ for long MIPROv2 runs). Reported gains are large on weak baselines (10-27 points) and smaller on strong ones; a typical DSPy run costs a few dollars. They pay off when you already have a trustworthy metric and dataset, many prompts/modules to tune, or a model migration; they overfit small sets and can encode label noise.

### Cited Findings
- DSPy optimisers and data guidance: BootstrapFewShot (~10 examples), BootstrapFewShotWithRandomSearch (50+), MIPROv2 0-shot for instruction-only, MIPROv2 longer runs (40+ trials) with ~200+ examples "to limit overfitting", BootstrapFinetune for weights; GEPA needs a reflection LM and can use domain-specific textual feedback; all need program + metric + trainset — [DSPy optimizers docs](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md)
- Cost: a typical simple run about $2 and ~10 minutes; from cents to tens of dollars depending on LM, data and settings — [DSPy optimizers docs](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md)
- DSPy informal gains: ReAct agent on HotPotQA with MIPROv2 24% → 51%; RAG over StackExchange 53% → 61%; Banking77 classification with BootstrapFinetune (GPT-4o-mini) 66% → 87% — [DSPy optimizers docs](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md)
- MIPRO (EMNLP 2024): jointly optimises instructions and few-shot demos per module without module-level labels; uses stochastic mini-batch evaluation and a surrogate model of the objective (Bayesian-style search), plus meta-optimisation of the proposer; beats baselines on 5 of 7 multi-stage programs with Llama-3-8B, up to 13% accuracy gain — [Opsahl-Ong et al., arXiv:2406.11695](https://arxiv.org/abs/2406.11695)
- GEPA (2025): reflects in natural language on trajectories (reasoning, tool calls, outputs), proposes prompt updates, keeps a Pareto frontier of candidates; about 6% better than GRPO on average across six tasks (up to 20%) with up to 35x fewer rollouts; over 10% better than MIPROv2, including +12% on AIME-2025 — [Agrawal et al., arXiv:2507.19457](https://arxiv.org/abs/2507.19457)
- OPRO (Google, 2023): the LLM sees previous prompts with their scores and proposes new ones; best prompts beat human-written ones by up to 8% on GSM8K and up to 50% on Big-Bench Hard tasks — [Yang et al., arXiv:2309.03409](https://arxiv.org/abs/2309.03409)
- TextGrad (2024): "automatic differentiation via text", passing LLM feedback backwards through a compound system; GPT-4o zero-shot GPQA 51% → 55%; ~20% relative gain on LeetCode-Hard solutions — [Yuksekgonul et al., arXiv:2406.07496](https://arxiv.org/abs/2406.07496)
- Before automated tuning, inspect disagreements manually, or you miss non-prompt problems such as missing context or bad labels — [Hamel Husain, Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)

### Inferences
- Gains are biggest on small open models and weak starting prompts; a carefully hand-written Claude prompt has less headroom. Expect single-digit gains on a mature system; verify on the held-out test split, not the optimiser's validation set.
- Overfitting risks: the optimiser maximises the metric, so a leaky or gameable metric (e.g. LLM judge that likes length) gets exploited; small trainsets lead to demos that memorise particular cases; GEPA/OPRO can produce long, case-specific instructions (prompt bloat by machine). Mitigate with a separate test split, a length/cost penalty in the metric, and human review of the final prompt diff.
- When worth it: (a) you have a reliable metric and 50-200+ labelled examples, (b) a multi-step pipeline where hand-tuning each module is slow, (c) migrating to a cheaper model (e.g. tuning a Haiku prompt to match Sonnet), (d) the goal is extraction/classification with exact-match metrics. Not worth it when the metric is still being defined or the dataset is under 30-50 items.
- Optimiser output should be treated like any other prompt change: new version file, same regression gate.

### Gaps
- APE (Zhou et al. 2022) not fetched; its numbers are not cited here.
- Exact token/dollar cost of GEPA and MIPROv2 runs at production scale on Claude was not found.
- No independent replication of GEPA's gains was found in the budget.

## 4. Calibration of confidence: abstaining and "I don't know"

### Takeaway
Large models are fairly well calibrated on multiple-choice when asked in the right format, but verbalised confidence is overconfident, and accuracy-only scoring rewards guessing. To get correct abstention, score errors worse than abstentions, measure selective accuracy (accuracy on answered items) alongside coverage, and prefer sampling-consistency signals over a single stated confidence number.

### Cited Findings
- Kadavath et al. (2022): larger models are well calibrated on multiple-choice and true/false when the format is right; P(True) (model judges its own proposed answer) works and improves when the model sees several of its own samples first; P(IK) ("do I know this?") can be trained and partly transfers, but calibration on new tasks is weaker; P(IK) rises appropriately when relevant source material is put in context — [Kadavath et al., arXiv:2207.05221](https://arxiv.org/abs/2207.05221)
- Xiong et al. (ICLR 2024): verbalised confidence is overconfident; calibration improves with model capability; human-inspired prompts, consistency across sampled answers and better aggregation each reduce overconfidence; white-box methods are only slightly better (AUROC 0.522 → 0.605 for failure prediction); no single technique wins and all struggle on professional-knowledge tasks — [Xiong et al., arXiv:2306.13063](https://arxiv.org/abs/2306.13063)
- OpenAI (Sept 2025): accuracy-only evals reward guessing. SimpleQA example: gpt-5-thinking-mini abstains 52%, accuracy 22%, errors 26%; o4-mini abstains 1%, accuracy 24%, errors 75%. Recommendation: penalise confident errors more than uncertainty and give partial credit for appropriate uncertainty, by changing the main evals' scoring — [OpenAI, Why language models hallucinate](https://openai.com/index/why-language-models-hallucinate/)
- Larger models with higher decoding confidence are more prompt-robust — [ProSA](https://arxiv.org/abs/2410.12405)

### Inferences
- For a RAG system: score each golden item as correct / wrong / abstained, with wrong costing more than abstained (e.g. +1, -2, 0). Report coverage (share answered) and selective accuracy; plot a coverage-risk curve if you have a confidence score (from sampling agreement, or retrieval score), and choose the operating point by business cost of a wrong answer.
- Include unanswerable items in the golden set (questions the corpus does not cover), otherwise abstention is never rewarded and prompt tuning will drift toward guessing.
- Calibration metrics: ECE (bin by confidence, average |accuracy - confidence|) needs many items per bin, so with a few hundred goldens, selective accuracy at fixed coverage and AUROC of confidence-vs-correctness are more stable. (General knowledge, not from a fetched source.)
- Verbalised "confidence: 0.9" from Claude should be validated against observed accuracy before being used for gating; agreement across K samples is the more evidence-backed signal (Xiong; Kadavath).

### Gaps
- No primary source fetched defining ECE, coverage-risk curves or selective prediction (e.g. Geifman & El-Yaniv); the definitions above are standard but uncited.
- No Claude-specific calibration measurements were found.

## 5. Prompt changes across model upgrades and portability

### Takeaway
Prompts do not port cleanly: best formats and example orders don't transfer between models, and newer Claude models follow instructions more literally, so emphatic language written for older models now causes over-triggering. Treat every model upgrade as a migration: re-run the full golden set, look for new failure categories, and remove compensating rules rather than adding more.

### Cited Findings
- Format rankings correlate only weakly between models — [Sclar et al.](https://arxiv.org/abs/2310.11324); good few-shot orderings don't transfer between models — [Lu et al.](https://arxiv.org/abs/2104.08786)
- Anthropic: where a technique names a specific model, "treat it as measured on that model and re-check it against your own evals before applying it to another" — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Newer Claude models are more responsive to the system prompt; prompts written to fight under-triggering can now over-trigger. Replace "CRITICAL: You MUST use this tool when..." with "Use this tool when..."; remove "If in doubt, use [tool]"; use a lower `effort` setting as fallback — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Migration checklist items: be specific about desired output; update thinking config (adaptive thinking and `effort` replace `budget_tokens`, which returns a 400 error on 4.7+); move away from prefilled assistant responses (unsupported from 4.6) to structured outputs or direct instructions; reduce anti-laziness prompting — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Third-party migration guides recommend a regression eval set plus shadow traffic or canaries before full rollout; prompt caches are per-model so expect cache misses after switching — [wavespeed.ai](https://wavespeed.ai/blog/ai-workflows/sonnet-4-6-to-sonnet-5-api/); AWS notes existing prompts may not perform as well on a new model and persona system prompts may need adjusting — [AWS ML blog](https://aws.amazon.com/jp/blogs/machine-learning/migrate-from-anthropics-claude-3-5-sonnet-to-claude-4-sonnet-on-amazon-bedrock/) (search snippet only; page body not retrieved)
- Re-run error analysis after a model switch — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)

### Inferences
- Migration eval = same golden set, same judge (judge model pinned separately from the system model), paired comparison old vs new per item, plus a manual read of items that flipped from pass to fail.
- Keep model-specific prompt patches labelled as such (comment or separate section) so they can be removed when the model changes.
- Automatic optimisers (section 3) are a reasonable tool for re-tuning after a downgrade to a cheaper model, because they re-fit demos/instructions to the new model.

### Gaps
- No quantitative study of how much score is lost when moving a tuned prompt between Claude and GPT/Gemini families was found beyond the format/order studies above.

## 6. Tuning other knobs (temperature, max tokens, few-shot count, placement) and search strategy

### Takeaway
Few sources give hard numbers for sampling knobs on frontier models. The evidence-backed points are: placement matters (documents first, query last), 3-5 diverse examples is Anthropic's default, few-shot reduces sensitivity, and lowering temperature is not a fix for noisy evals. For search, structured Bayesian-style search (as in MIPROv2) is used for the combinatorial prompt space; for a handful of numeric knobs a small grid with repeated runs is enough.

### Cited Findings
- Documents at the top, query at the end: up to 30% better in tests — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- 3-5 examples recommended; ask Claude to check examples for relevance and diversity — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Few-shot examples reduce prompt sensitivity — [ProSA](https://arxiv.org/abs/2410.12405); but example order can swing results widely — [Lu et al.](https://arxiv.org/abs/2104.08786)
- Thinking depth on current Claude models is controlled by `effort` (adaptive thinking), not token budgets — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Don't lower temperature to reduce eval variance; resample instead — [Miller](https://arxiv.org/html/2411.00640v1)
- MIPRO searches instruction × demo combinations with a surrogate model over mini-batch evaluations — [Opsahl-Ong et al.](https://arxiv.org/abs/2406.11695); DSPy suggests 40+ trials for longer MIPROv2 runs — [DSPy docs](https://github.com/stanfordnlp/dspy/blob/main/docs/docs/learn/optimization/optimizers.md)

### Inferences
- Budget: the cost of one eval run = items × K samples × (system calls + judge calls). With a 300-item golden set and K=3, each candidate costs ~900 system runs plus judging; plan the number of candidates from that, and screen on a cheap subset before running the full set.
- Knobs to search for a Claude RAG agent, in order of likely impact: retrieval settings (k, rerank), prompt placement/structure, effort level, few-shot count (0/3/5), max tokens (mainly a truncation guard). Temperature mostly matters for diversity, not accuracy.
- Random search beats grid when several knobs matter unequally (Bergstra & Bengio 2012, not fetched); Bayesian search pays off only when each evaluation is expensive and there are many candidates.

### Gaps
- No 2022-2026 source with measured temperature/top-p effects on Claude accuracy was found.
- System vs user placement of instructions: no quantitative source found.

## 7. Anti-patterns

### Takeaway
The common failures are tuning on the test set, fixing single examples with narrow rules, rule accumulation (instruction-following degrades as rule count grows), trusting generic metrics or vibes, and chasing a 100% pass rate.

### Cited Findings
- Tuning on test: refine on dev, use test once; a big dev-test gap signals overfitting — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Narrow-rule patching: instead of banning a recurring stock phrase, adjust the higher-level instruction (e.g. emphasise originality) — [web.dev](https://web.dev/learn/ai/evaluation-driven-development)
- Prompt bloat: IFScale (NeurIPS 2025) shows instruction-following accuracy falls as the number of simultaneous instructions rises (10 to 500); the best frontier models reach only about 68% at 500; models show a bias toward earlier instructions — [Jaroslawicz et al., arXiv:2507.11538](https://arxiv.org/abs/2507.11538) (via search summary and NeurIPS listing)
- Emphatic rule language causes over-triggering on newer Claude models — [Claude prompting best practices](https://platform.claude.com/docs/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Generic metrics (helpfulness, coherence, ROUGE, BERTScore) give false confidence; use them only to find traces to review — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Optimising for high pass rate: 100% may mean the evals are too easy — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Single-format comparisons can flip model rankings; one prompt variant is not a measurement — [Sclar et al.](https://arxiv.org/abs/2310.11324)
- Ignoring noise: small eval sets cannot detect few-point differences (969 items for 3 points at 80% power) — [Miller](https://arxiv.org/html/2411.00640v1)
- Accuracy-only scoring that pushes the model to guess instead of abstain — [OpenAI](https://openai.com/index/why-language-models-hallucinate/)

### Inferences
- A useful rule: every new prompt rule must name the failure category it fixes and the eval items that show the fix; rules with no linked failure are removed in the next ablation pass.
- Keep a separate "canary" set of known-hard items that are never used for tuning decisions.

### Gaps
- IFScale per-model numbers at lower densities (e.g. 20-50 rules, typical of production prompts) were not retrieved.
