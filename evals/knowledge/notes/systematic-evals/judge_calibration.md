# Calibrating and validating an LLM-as-judge against human labels

Context: the engineer already runs two judges from different model families. They score correctness, grounding and completeness on 1-5 with a pass threshold, and have compared a sample with analyst scores, but without a formal method. These notes cover the rigorous version. Sources were checked on 25 Nov 2026. Where a number comes from a secondary summary (Eugene Yan's survey), that is marked.

## 1. Building the human-labelled set (size, splits, who labels, guidelines)

### Takeaway
Treat the judge prompt as a model. Label a set with one trusted domain expert, binary per criterion with a written critique. Split it train / dev / test (about 10-20 / 40-45 / 40-45%), with 30-50 passes and 30-50 fails in each of dev and test. Plan on about 100-200 labels per failure mode or criterion. Below about 60 examples the confidence intervals are too wide to be useful. Size the test set from the CI width you need (see section 3).

### Cited Findings
- Start with about 30 examples and keep adding until no new failure modes appear. To validate a judge, aim for "about 100 examples per failure mode", with enough Pass and Fail examples to measure both classes. "Below 60 examples, the confidence intervals are often too wide to support a useful conclusion." — [Hamel Husain, Creating a LLM-as-a-Judge that drives business results](https://hamel.dev/blog/posts/llm-judge/)
- Splits: train 10-20% (used only as few-shot examples in the prompt), dev about 40-45% (iterate the prompt on it, never put it in the prompt), test about 40-45%. "Freeze the prompt, run the judge on the test set once." Aim for 30-50 examples of each label in each set. — [Hamel Husain, llm-judge](https://hamel.dev/blog/posts/llm-judge/)
- The evals FAQ says to label "100 to 200 examples for each failure mode" for LLM judges, with at least 50 passing and 50 failing when you debug disagreements. — [Hamel Husain & Shreya Shankar, Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Who labels: for small and medium companies, one domain expert as a "benevolent dictator" who sets the quality bar. Use several annotators only in larger or multi-domain organisations. If you do use several, measure their agreement with a chance-corrected metric (Cohen's kappa), hold alignment sessions on disagreements, update the rubric, and let the expert make the final call with recorded reasoning. — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Labels should include a written critique, detailed enough to reuse as a few-shot example ("Being too terse is a common mistake"). Common judge-prompt mistakes: no or terse critiques, missing context that the expert used to judge, examples that are not diverse enough. — [Hamel Husain, llm-judge](https://hamel.dev/blog/posts/llm-judge/)
- Process: send the expert a spreadsheet of input, output, judge critique and judge verdict. The expert writes their own critique and verdict. Refine the prompt and track agreement over iterations. After the first iterations, focus on error cases but keep some random sampling. Honeycomb's query assistant reached ">90% agreement" with the expert in three iterations, on a roughly balanced (about 50% fail) set. — [Hamel Husain, llm-judge](https://hamel.dev/blog/posts/llm-judge/)
- Criteria drift: "users need criteria to grade outputs, but grading outputs helps users define criteria." In a study of 9 practitioners, people added criteria after seeing new bad outputs and reinterpreted existing criteria, and often said they could not fully define criteria before seeing outputs. Recommendations: grade per criterion, not one thumbs up/down; set a false-failure threshold per criterion; reuse the user's good/bad grades as few-shot examples; revisit criteria when pipeline outputs change; attend to inter-rater reliability when several people grade. — [Shankar et al. 2024, Who Validates the Validators? (EvalGen)](https://arxiv.org/html/2404.12272)
- Labelled set sizes in published judge studies (secondary, via Yan): MT-Bench 3k expert votes; Judging the Judges 400 TriviaQA questions; a QA correctness/faithfulness study of 1.2k responses (961 correct, 239 incorrect); a factual consistency study of 373 samples; EvalGen 84 (medical) and 100 (product) labelled outputs. — [Eugene Yan, Evaluating the effectiveness of LLM-evaluators](https://eugeneyan.com/writing/llm-evaluators/); MT-Bench count confirmed in [Zheng et al. 2023](https://arxiv.org/abs/2306.05685)
- Anthropic: calibrate model graders closely against human experts, expect several rounds of refinement, and keep reading transcripts. Once the system is stable, occasional human review is enough. — [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- For three criteria (correctness, grounding, completeness), the labelling budget is per criterion. 100-200 labels each, with fails over-sampled, is a realistic target. The same items can carry all three labels.
- The current "compared a sample with analyst scores" is effectively one dev-set pass. The rigorous version adds a frozen, unseen test set, and the judge's error rates are reported only from that set.
- Fails are usually rare, so random sampling gives too few. Stratify or over-sample suspected fails (for example, items the judges disagree on, or low scores) to reach 30-50 fails per split. Then use TPR/TNR, which do not depend on prevalence (section 2), not raw accuracy on the enriched set.

### Gaps
- I found no peer-reviewed study that derives the 100-200 per failure mode figure. It is practitioner guidance (Husain/Shankar), not an empirical result.
- I found no source that gives specific guidance on judging grounding against retrieved context in regulated domains.

## 2. Which agreement metrics to use

### Takeaway
Report the judge as a classifier for "fail": TPR (recall on true fails), TNR (correct passes), plus precision for "fail", from the frozen test set with CIs. Add Cohen's kappa as one chance-corrected summary. Use Spearman/Kendall (or weighted kappa / Krippendorff's alpha) only if you keep graded scores. Raw agreement misleads when classes are imbalanced.

### Cited Findings
- Why raw agreement misleads: if 5% of examples fail, a judge that always says pass gets 95% agreement and catches no errors. Report TPR and TNR separately. — [Hamel Husain, llm-judge](https://hamel.dev/blog/posts/llm-judge/)
- TPR (recall) = share of real failures caught. TNR = share of good outputs correctly passed. Low TNR means false alarms and wasted reviewer time. Track both as you change the prompt, because catching more failures can raise false alarms. Set acceptable levels from the cost of each error type. — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- EvalGen uses the same idea under different names: coverage (share of bad outputs failed), false failure rate (share of good outputs failed), and alignment (harmonic mean of the two). Product pipeline: EvalGen coverage 0.73, FFR 0.39, alignment 66.46% vs SPADE 0.49 / 0.39 / 54.35%. Medical pipeline: both 0.33 / 0.10 / 48.29%. — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)
- Kappa vs raw agreement in practice (secondary, via Yan): on Judging the Judges (TriviaQA), GPT-4 kappa 0.84 and Llama-3-70B 0.79, vs human-human 0.97. Llama-3-8B had 80% raw agreement but kappa of only 0.62. On UMbrela relevance, kappa was 0.3-0.5 while Kendall/Spearman were 0.8-0.9: rank correlation looks much better than exact-agreement kappa. Bands: 0.21-0.40 fair, 0.41-0.60 moderate. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Graded-score correlations (secondary, via Yan): GPT-4 QA correctness Spearman 0.67, faithfulness 0.55. G-Eval average Spearman 0.514. A ChatGPT factual-consistency evaluator had Spearman 0.27-0.46, with sensitivity above 95% on consistent summaries but only 30-60% on inconsistent ones. That is the classic lenient-judge pattern: high TNR, low TPR. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Per-label accuracy can be very uneven (UMbrela): non-relevant about 75%, relevant 50%, highly relevant 30%, perfectly relevant 45%. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Recommendation: use kappa for binary and pairwise agreement, and Spearman/Kendall for Likert. Prefer binary outputs so precision and recall can be used. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Self-consistency is a separate metric. Report intra-rater reliability (Krippendorff's alpha over repeated runs with identical settings). Binary SummaC alpha: Llama 3.1 0.326, DeepSeek-R1 0.628, Qwen 3 0.788 (0.8 is the common threshold). MT-Bench 3-way: 0.265 / 0.507 / 0.563. Qwen 3 gave the same verdict on all three runs for only 61.3% of items. For reference, human inter-rater alpha was 0.798 for experts and 0.48-0.51 for crowd workers on SummEval. — [Haldar & Hockenmaier 2025, Rating Roulette](https://arxiv.org/html/2510.27106)

### Inferences
- Minimum report per criterion and per judge: n test items (fails/passes), TPR, TNR, precision(fail), kappa, each with a 95% CI (Wilson or bootstrap). Also run-to-run consistency on a subset.
- Compare the judge's kappa with the human-human kappa on a doubly-labelled subset. That is the ceiling: no judge can be expected to agree with the analyst more than a second analyst does.

### Gaps
- No source gives a universal "good enough" TPR/TNR threshold. It depends on the cost of each error type.

## 3. Correcting the measured pass rate for judge error, with confidence intervals

### Takeaway
The judge's raw pass rate is biased whenever TPR or TNR is below 1. Correct it with the Rogan-Gladen estimator θ = (p_obs + TNR − 1) / (TPR + TNR − 1), and give a CI that includes the uncertainty in TPR and TNR (bootstrap, as judgy does, or the closed-form interval in Lee et al. 2025). Prediction-powered inference (PPI) is the general alternative: it combines a small human-labelled set with many judge labels for any mean, including graded scores.

### Cited Findings
- judgy (Husain/Shankar course library): estimates TPR and TNR on a human-labelled test set, then corrects with "θ̂ = (p_obs + TNR − 1) / (TPR + TNR − 1)", then bootstraps (default 20,000 iterations, 95%) for a CI. Inputs are test_labels, test_preds and unlabeled_preds. It requires TPR + TNR > 1 (a judge better than chance). The README does not recommend a label count. — [ai-evals-course/judgy on GitHub](https://github.com/ai-evals-course/judgy)
- Lee et al., "How to Correctly Report LLM-as-a-Judge Evaluations" (arXiv 2511.21140): the same estimator (Eq. 7) with q1 = sensitivity and q0 = specificity, and a closed-form adjusted CI θ̃ ± z√V, where V = [p̃(1−p̃)/ñ + (1−θ̃)²·q̃0(1−q̃0)/m̃0 + θ̃²·q̃1(1−q̃1)/m̃1] / (q̃0+q̃1−1)². The adjustments are ñ=n+z², m̃=m+2 (Agresti-Coull style). It accounts for both test-set and calibration-set uncertainty. — [arXiv 2511.21140](https://arxiv.org/html/2511.21140v3)
- Sizing: as the unlabelled set grows, the CI width depends only on the calibration counts m0 and m1. Example: with p̂=0.3, q0=0.7, q1=0.9, a CI narrower than 0.1 needs about 200 calibration examples. Fewer are needed for accurate judges, many more near chance. — [arXiv 2511.21140](https://arxiv.org/html/2511.21140v3)
- Adaptive allocation: take a pilot of about 10 per label, compute κ = (1−q0)/(1−q1), then set m1* = m / (1 + (1/p̂ − 1)·√κ). This beats an equal split. — [arXiv 2511.21140](https://arxiv.org/html/2511.21140v3)
- Simulation (n=1000, m=200, q0=0.7, q1=0.9, 10,000 repetitions): the naive p̂ overestimates θ at low values, and its CI has near-zero coverage. The corrected CI stays near 95%. On Chatbot Arena with a GPT-4.1-mini judge, coverage was 95-99% and CI length 0.18-0.27. The corrected estimator stays unbiased when prevalence differs between the calibration set and the test set. With q = 0.9, judge plus correction beats human-only variance for θ roughly in [0.17, 0.83]. — [arXiv 2511.21140](https://arxiv.org/html/2511.21140v3)
- PPI (Angelopoulos et al. 2023): valid CIs for means, quantiles and regression coefficients when a small labelled set is supplemented with ML predictions. It makes no assumptions about the predictor, and more accurate predictions give narrower intervals. — [Angelopoulos et al., Prediction-Powered Inference](https://arxiv.org/abs/2301.09633)
- PPI mean estimator as applied to LLM labels: U_PPI = (1/N)Σ judge(x_i) over all N items + (1/n)Σ [human(x_j) − judge(x_j)] over the n labelled items (the "rectifier"). It is unbiased. 95% CI = U_PPI ± 1.96·√(σ²_error/n + σ²_pred/N). In IR evaluation, PPI reached 95% coverage with fewer than 20 labelled queries on TREC-DL and fewer than 40 on Robust04, vs at least 40 (TREC-DL) and about 100 (Robust04) for the empirical bootstrap. PPI lowers variance "only if predictions are somewhat accurate." — [Oosterhuis et al. 2024, arXiv 2407.02464](https://arxiv.org/html/2407.02464v1)
- Extensions (seen in search results, not read in full): Bayesian PPI (Hofer et al. 2024, with a 100-example human set in its motivating example); Confidence-Driven Inference (NAACL 2025), which uses judge confidence to pick which items to send to humans; GLIDE (2026), a library of PPI variants for GenAI evaluation. — [Bayesian PPI](https://arxiv.org/pdf/2405.06034); [Confidence-Driven Inference, NAACL 2025](https://preview.aclanthology.org/fix-sig-urls/2025.naacl-long.179.pdf); [GLIDE, arXiv 2605.31278](https://arxiv.org/html/2605.31278)

### Inferences
- Rogan-Gladen/judgy fits a binary pass/fail per criterion. PPI fits a mean of graded scores (for example, average 1-5 correctness) or a pass rate, and needs paired human and judge labels on a random (not enriched) labelled subset. Rogan-Gladen only needs TPR/TNR, which can come from an enriched set.
- Practical: report "judge pass rate 82%, corrected 76% [95% CI 70-82%]" rather than the raw number. When comparing two system versions, the difference between corrected rates (with bootstrap over both) is what matters.
- The correction assumes TPR/TNR transfer from the calibration set to production data. A new system version with new failure types breaks this, so re-validate (section 6).

### Gaps
- I did not verify the PPI++ power-tuning formula from a primary source in this pass.
- No source here compares judgy's bootstrap with the Lee et al. closed form on the same data.

## 4. Known judge biases and mitigations

### Takeaway
The documented biases are: position (pairwise), verbosity, self-preference, leniency (missing real errors), being misled by the answer under review, and sensitivity to scale and prompt wording. The best-supported mitigations are: reference answers, having the judge solve or reason before the verdict, swapping position, few-shot examples from expert labels, specific binary criteria, one judge call per criterion, and an "Unknown" exit.

### Cited Findings
- Position bias (MT-Bench): only GPT-4 gave consistent results in more than 60% of swapped-order cases. Most judges favour the first position, and Claude-v1 also showed a name bias toward "Assistant A". Mitigation: call the judge twice with the order swapped and count a win only if both orders agree (otherwise a tie). Three few-shot examples raised GPT-4 consistency from 65.0% to 77.5%, at 4x API cost, with a warning that consistency is not the same as accuracy. — [Zheng et al. 2023, MT-Bench / Chatbot Arena (PDF)](https://arxiv.org/pdf/2306.05685)
- Verbosity ("repetitive list" attack, 23 answers): failure rate 91.3% for Claude-v1 and GPT-3.5, 8.7% for GPT-4. — [Zheng et al. 2023](https://arxiv.org/pdf/2306.05685)
- Self-enhancement: GPT-4 gave itself a 10% higher win rate and Claude-v1 25%, but the authors say they could not establish the bias from their data. — [Zheng et al. 2023](https://arxiv.org/pdf/2306.05685)
- Self-preference, controlled study: GPT-4 and GPT-3.5 rate their own summaries higher than others' that humans rate as equal. Models recognise their own text above chance, and self-recognition ability correlates linearly with the strength of self-preference. — [Panickssery, Bowman & Feng, NeurIPS 2024](https://arxiv.org/abs/2404.13076v1)
- PoLL: each judge's most positive deviation from human labels came when it judged its own family's outputs. GPT-4 ranked a GPT-4 variant 2nd, against 4th in the real Arena. — [Verga et al. 2024](https://arxiv.org/html/2404.18796v2)
- Misled by the answer under review / grading reasoning: on 10 math questions (20 judgments with swapped positions), GPT-4 called incorrect answers correct 14/20 times with the default prompt, 6/20 with chain-of-thought (solve first), and 3/20 reference-guided (the judge's own answer generated first, then shown as a reference). That is 70% to 15%. — [Zheng et al. 2023](https://arxiv.org/pdf/2306.05685)
- Leniency (secondary, via Yan): Shepherd found GPT-4 gave alpaca-7b an average of 4.7 vs 2.9 from humans. A blind-spots study found GPT-4-turbo failed to lower scores for perturbed answers more than 50% of the time on coherence, factuality and instruction following. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Prompt sensitivity: GPT-4 kappa on NQ was 0.518 zero-shot, 0.627 few-shot, and 0.725 with a "don't overthink" instruction. The same instruction lowered PoLL to 0.699. — [Verga et al. 2024](https://arxiv.org/html/2404.18796v2)
- Scale wording: specific criteria gave the highest agreement with humans and general criteria the lowest (EvalLM, via Yan). — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Anthropic: grade each dimension with its own isolated judge, use clear structured rubrics, give the judge an "Unknown" exit to prevent made-up grades, and read transcripts. A grading bug (rigid matching that rejected "96.12" when "96.124991…" was expected) held Opus 4.5 at 42% on CORE-Bench, and it scored 95% after the grader fixes. — [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- For correctness, the reference-guided result is the strongest lever. Give the judge a gold answer or the source passages, and have it state the expected answer before it scores.
- For grounding, the judge should list each claim and the supporting passage before the verdict (reason before verdict). That mirrors CoT/reference-guided grading.
- Self-preference matters if either judge shares a family with the generator. Having the two judges from different families helps, but check the judge's error rates on outputs from its own family separately.

### Gaps
- I found no study on verbosity bias in absolute (non-pairwise) correctness and completeness scoring specifically, as opposed to pairwise.

## 5. Using two judges: combining, disagreement, juries

### Takeaway
A panel of judges from different families beats one big judge on agreement with humans and on own-family bias, at lower cost (PoLL). Combine binary verdicts by vote (with two judges: "fail if either fails" or "send to a human if they disagree") and graded scores by averaging. Validate the combined rule as its own classifier on the test set. Use disagreement as the signal for which items humans should label.

### Cited Findings
- PoLL panel = Command R, Claude 3 Haiku, GPT-3.5. Kappa vs humans: NQ 0.763 vs GPT-4 0.627; TriviaQA 0.906 vs 0.841; HotpotQA 0.867 vs 0.830. Chatbot Arena Hard rank correlation: Pearson 0.917 vs 0.817, Kendall tau 0.778 vs 0.667. — [Verga et al. 2024, Replacing Judges with Juries](https://arxiv.org/html/2404.18796v2)
- Aggregation: max (majority) voting for binary QA judgments, average pooling for 1-5 scores. Cost: $1.25 / $4.25 per million input / output tokens vs GPT-4 Turbo $10 / $30, which is 7-8x cheaper. — [Verga et al. 2024](https://arxiv.org/html/2404.18796v2)
- Bias spread: PoLL had the smallest standard deviation of accuracy deviation from humans (2.2), against GPT-3.5's 6.1. The paper attributes this to disjoint model families. — [Verga et al. 2024](https://arxiv.org/html/2404.18796v2)
- Repeated runs of one judge, majority-voted, also help. Over 3 runs, SummaC balanced accuracy rose from 59.1 to 61.4 (Llama), 69.8 to 72.3 (DeepSeek-R1) and 79.4 to 80.6 (Qwen 3). Turning sampling off slightly lowered accuracy. — [Rating Roulette](https://arxiv.org/html/2510.27106)
- Using the same model for the task and the judge is "usually fine". If alignment is poor, try another model, and measure cost, speed and agreement of candidate judges on your own labels. — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Judges from different families use scales differently, so the same item can get very different numeric scores. Discrete labels are more comparable across judges. — [Arize, Testing binary vs score evals](https://arize.com/blog/testing-binary-vs-score-llm-evals-on-the-latest-models/)

### Inferences
- With two judges, a majority vote is not defined. The options are "fail if either fails" (higher TPR, lower TNR), "fail only if both fail" (the reverse), or "agree = auto, disagree = human review". Each rule has its own TPR/TNR on the test set, so pick by error cost, then apply the Rogan-Gladen correction with the combined rule's rates.
- Inter-judge kappa is a cheap proxy for item difficulty or rubric ambiguity. Low judge-judge agreement on a criterion often means the rubric is unclear, not that one judge is wrong. Check the analyst-analyst kappa on the same items.
- Report each judge's TPR/TNR separately as well as the combined rule's, so that a drop in one judge after a model update is visible.

### Gaps
- PoLL used three judges. I found no source that measures a two-judge panel specifically, or that compares "either fails" with "both fail" rules empirically.

## 6. Re-validating when the model or prompt changes; judge drift

### Takeaway
Any change to the judge model, the judge prompt, the scale or the generator's output distribution invalidates the measured TPR/TNR. Re-run the frozen test set after every judge change. Refresh labels on a schedule, because criteria drift and new failure modes appear. Version judge prompts, and track agreement over time.

### Cited Findings
- Re-run the alignment process after material changes such as a model update. — [Hamel Husain, llm-judge](https://hamel.dev/blog/posts/llm-judge/)
- Validate any model against human labels before trusting it, and re-run error analysis after model switches. — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Numeric judge scores drifted with prompt, model or configuration changes. Binary labels reproduced across prompts and models. — [Arize](https://arize.com/blog/testing-binary-vs-score-llm-evals-on-the-latest-models/)
- Criteria drift is inherent: re-grade or revisit criteria when pipeline outputs change. Participants doubted that LLM validators would hold up in production and wanted realignment over time, possibly with grades from end users. — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)
- Calibrate rubrics against experts often for subjective tasks. A 0% pass rate across many trials usually means a broken task or grader. — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Small prompt edits move agreement a lot (GPT-4 NQ kappa 0.518 to 0.725 from prompt changes alone). — [Verga et al. 2024](https://arxiv.org/html/2404.18796v2)

### Inferences
- A practical protocol: (1) pin the judge model version and prompt version; (2) a CI gate re-runs the frozen test set on any judge change and blocks it if TPR or TNR falls outside the previous CI; (3) each month (or each release) have the analyst label a fresh random sample of about 30-50 production items, which catches distribution shift; (4) promote fresh disagreements into dev, and rotate a new test set once dev has absorbed the old one; (5) watch the inter-judge agreement rate in production as an unlabelled drift alarm.
- Keep the test set unseen. Once you tune on it, it becomes dev.

### Gaps
- I found no published study that measures judge drift across vendor model updates over time with fixed prompts.

## 7. Score calibration: Likert vs binary, thresholds, reliability of 1-5

### Takeaway
Practitioners (Husain/Shankar, Arize, Anthropic's per-dimension guidance) favour binary or small categorical labels per criterion. They are more stable across runs, judges and prompts, and they make TPR/TNR and the correction above possible. Some 2025-2026 academic work finds 0-5 scales give the best human agreement in some tasks, so the evidence is mixed. If 1-5 is kept, treat the pass threshold as a classifier cut-off and pick it on dev labels (ROC style), not by intuition.

### Cited Findings
- Binary "forces clearer thinking and more consistent labeling". With Likert, the difference between adjacent points (3 vs 4) is subjective and inconsistent across annotators, who also drift to the middle. For gradual progress, use binary sub-checks (for example "4 of 5 expected facts included"). — [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/); [FAQ entry on binary vs Likert](https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html)
- Arize experiment (GPT-5-nano, Claude Opus 4, Qwen3-235B, o3; scales 1-10, 0-1, −1 to 1, A-E): numeric scores plateaued and collapsed into narrow bands, varied widely across runs, and were not comparable across judges. On 0-1, scores went to the extremes. Binary separated clean from corrupted text consistently, with low variance. A-E was stable but behaved like coarse bins (mostly A-C). Recommendation: binary or categorical by default, numeric scores only in tightly calibrated, fixed-judge settings, and check distribution plots across repeated runs. — [Arize](https://arize.com/blog/testing-binary-vs-score-llm-evals-on-the-latest-models/)
- Counter-evidence: a January 2026 preprint found a 0-5 scale gave the highest human-LLM absolute agreement across tasks and 0-10 the lowest, and warned that pooled reliability hides benchmark-level differences. An AgentJudgeBench table found that collapsing {0, 0.5, 1} to binary lowered alignment for some judges. A NeurIPS 2026 paper ("Ask, Then Grade") reports cases where graded scales beat binary decomposition (abstract only seen). — [arXiv 2601.03444](https://arxiv.org/html/2601.03444v1); [AgentJudgeBench, arXiv 2608.26623](https://arxiv.org/pdf/2608.26623); [NeurIPS 2026 listing](https://neurips.cc/virtual/2026/161241)
- Rubric binary grading reached 0.72-0.76 macro F1 (ResearchRubrics), close to the best LLM judges on rubric benchmarks (from search snippet). — [ResearchRubrics, arXiv 2511.07685](https://arxiv.org/pdf/2511.07685)
- 1-5 self-consistency is lower on more complex scales and tasks. Few-shot and CoT did not meaningfully improve self-reliability. — [Rating Roulette](https://arxiv.org/html/2510.27106)
- Graded agreement figures are modest even for strong judges: average Spearman 0.514 for G-Eval, and 0.55-0.67 for GPT-4 on QA faithfulness and correctness (secondary). — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)
- Use direct scoring for objective criteria (correctness, grounding) and pairwise comparison for subjective ones. — [Eugene Yan](https://eugeneyan.com/writing/llm-evaluators/)

### Inferences
- The pass threshold on a 1-5 scale already turns it into a binary classifier, so validate at the threshold. Compute TPR/TNR at each cut-off (≥3, ≥4) on dev, choose by error cost, and lock it before running on test.
- A cleaner redesign: replace each 1-5 score with binary sub-checks. For correctness, "any factual error vs the reference: yes/no". For grounding, "every claim supported by a cited passage: yes/no". For completeness, "covers items X, Y, Z: n of k". Keep the 1-5 only as a secondary diagnostic.
- Before changing the scale, test it on your own labels: run both formats on dev and compare kappa and run-to-run alpha. The evidence is task dependent.

### Gaps
- The 0-5 vs binary papers are 2026 preprints or abstracts that I did not read in full. Treat their numbers as provisional.

## 8. EvalGen / "Who Validates the Validators?" findings

### Takeaway
Judge alignment is iterative and subjective. People cannot fully specify criteria before seeing outputs (criteria drift), so validation sets and rubrics must evolve. A small number of user grades (16 per pipeline) was enough to select evaluators as well aligned as a baseline that used all 84-100 labels, measured by coverage of bad outputs and false failure rate.

### Cited Findings
- EvalGen generates candidate criteria and evaluator implementations (prompts or code), asks the user to grade a subset of outputs, and picks the implementations that best match those grades. — [Shankar et al. 2024 abstract](https://arxiv.org/abs/2404.12272)
- 9 industry practitioners, sessions of 45-75 minutes. — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)
- EvalGen used 16 graded outputs per pipeline. SPADE used all labels (84 medical with 27 bad, 100 product with 49 bad). EvalGen matched SPADE on medical with 3 vs 5 assertions, and beat it on product (coverage 0.73 vs 0.49, alignment 66.46% vs 54.35%) with 4 vs 9 assertions. SPADE had to relax its FFR threshold from 10% to 40% to find a viable set. — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)
- Criteria drift had two forms: adding criteria after new bad outputs appeared, and reinterpreting criteria to fit the LLM's behaviour. Some criteria depend on the outputs seen, which "challenges approaches that assume evaluation is independent of observing model outputs." — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)
- Recommendations: grade per criterion; per-criterion FFR thresholds; editable, exportable code assertions; good/bad grades used as few-shot examples; re-grade when outputs change; inter-rater reliability for collaborators; realign over time. — [Shankar et al. 2024](https://arxiv.org/html/2404.12272)

### Inferences
- For this engineer: per-criterion labels and per-criterion error tolerances (for example, a high TPR required for grounding failures, more false alarms tolerated on completeness) map directly onto EvalGen's per-criterion FFR thresholds.
- Where a criterion can be checked deterministically (citation present, cited passage ID exists, required fields present), use a code assertion instead of an LLM judge. EvalGen mixes both.

### Gaps
- EvalGen's quantitative comparison is small (two pipelines, 84 and 100 items). It is not a large benchmark.
