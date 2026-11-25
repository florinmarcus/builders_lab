# Statistics for evals: telling a real improvement from noise

Scope: the statistical tools an AI engineer needs to judge whether a change to an LLM system (prompt, model, retrieval setting) is a real improvement. Reader already runs McNemar and regression gates on a ~300-question golden set.

Note on worked numbers: numbers marked "(computed)" were calculated for these notes in Python from the cited formulas (normal approximation, two-sided alpha = 0.05, power 80%, so z_alpha/2 = 1.96 and z_beta = 0.84). They are arithmetic, not quotes from a source. They sit in the Inferences sections.

## 1. Sample size, standard error and minimum detectable effect

### Takeaway
The standard error of an accuracy p on n independent questions is sqrt(p(1-p)/n): at 85% it is about 3.6 points for n=100, 2.1 for n=300 and 1.1 for n=1000. Because both systems answer the same questions, the real driver of power is the share of questions where the two systems disagree, not n alone: with 300 questions and 10% disagreement you can reliably detect about a 5-point gain, not a 2-point one.

### Cited Findings
- Standard error of a mean score over n questions: SE = sqrt(Var(s)/n); for 0/1 scores SE = sqrt(p(1-p)/n); 95% CI = mean +/- 1.96 x SE. Miller recommends reporting the SE in brackets under each score, with the question count. — [Miller 2024, Adding Error Bars to Evals](https://arxiv.org/html/2411.00640v1)
- Sample size formula for a paired comparison with minimum detectable effect delta: n = (z_alpha/2 + z_beta)^2 (omega^2 + sigma_A^2/K_A + sigma_B^2/K_B) / delta^2, where omega^2 = Var(x_A) + Var(x_B) - 2Cov(x_A, x_B) is the variance of the per-question difference in expected scores, sigma^2 are the within-question (sampling) variances and K the number of samples per question. Inverted: MDE delta = (z_alpha/2 + z_beta) sqrt((omega^2 + sigma_A^2/K_A + sigma_B^2/K_B)/n). — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Miller's worked example: with sigma^2 = 0 and omega^2 = 1/9, detecting delta = 0.03 at 80% power and alpha = 0.05 needs n ~ 969 questions; he suggests new evals have at least 1,000 questions. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Second worked example: sigma_A^2 = sigma_B^2 = 1/6, omega^2 = 1/9, correlation 0.5, n = 198; raising samples per question K from 1 to 10 cuts the MDE from 13.2% to 7.5%. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- In IR, Sakai's "topic set size design" picks the number of queries from a pilot topic-by-run score matrix (within-system variance), a target alpha, power and minimum difference; different metrics have very different variances and so need very different topic counts. — [Sakai 2016, Information Retrieval Journal](https://link.springer.com/article/10.1007/s10791-015-9273-z); [Sakai ICTIR 2016 tutorial](https://www.slideshare.net/slideshow/ictir2016tutorial-65845256/65845256)

### Inferences
- SE of one accuracy figure (computed): p=0.85: n=100 -> 3.57 pts; n=300 -> 2.06 pts; n=1000 -> 1.13 pts. p=0.90: 3.0 / 1.73 / 0.95 pts. Worst case p=0.5: 5.0 / 2.89 / 1.58 pts. So "86.3% vs 85.0%" on 300 questions is well inside one SE.
- Unpaired (two different question sets, or ignoring pairing) sample size to detect 85% -> 90% (computed): about 683 questions per arm. Unpaired MDE at ~85%: n=100 -> 14.2 pts, n=300 -> 8.2 pts, n=1000 -> 4.5 pts.
- Paired MDE (same questions, both systems), approx (z_alpha/2 + z_beta) x sqrt(psi/n) where psi = share of questions where the two systems disagree (computed):
  - psi = 5%: n=100 -> 6.3 pts; n=300 -> 3.6 pts; n=1000 -> 2.0 pts
  - psi = 10%: n=100 -> 8.9 pts; n=300 -> 5.1 pts; n=1000 -> 2.8 pts
  - psi = 20%: n=100 -> 12.5 pts; n=300 -> 7.2 pts; n=1000 -> 4.0 pts
- McNemar sample size for an 85% -> 90% change (delta = 5 pts), Connor-style formula n = (z_a sqrt(psi) + z_b sqrt(psi - delta^2))^2 / delta^2 (computed): psi=7% -> 217; psi=10% -> 312; psi=15% -> 469; psi=20% -> 626 questions. Rule of thumb: on a 300-question set, a prompt tweak that changes 10% of answers can only be "proven" if it moves accuracy by about 5 points.
- Practical rule: estimate psi from past runs (count discordant pairs in old A/B comparisons). Small tweaks usually have small psi, which helps; model swaps have large psi, which hurts.
- To halve the MDE you need 4x the questions (MDE scales with 1/sqrt(n)).

### Gaps
- No source found giving a canonical table of MDE by n for LLM evals; the table above is computed. The Connor (1987) McNemar sample-size formula was used from standard knowledge, not fetched.

## 2. Confidence intervals for pass rates and for paired differences

### Takeaway
Use Wilson (or Jeffreys) intervals for a single pass rate, especially near 0% or 100% or with small n; the textbook normal (Wald) interval misbehaves there. For a difference between two systems on the same questions, use the paired SE (SD of per-question differences / sqrt(n)), which is usually much smaller than the unpaired one.

### Cited Findings
- Brown, Cai and DasGupta (2001) show the Wald interval's coverage is "persistently poor"; for n <= 40 they recommend Wilson or the equal-tailed Jeffreys interval; for larger n Wilson, Jeffreys and Agresti-Coull are very similar. — [Brown, Cai, DasGupta 2001, Statistical Science](https://projecteuclid.org/euclid.ss/1009213286)
- Agresti-Coull ("add two successes and two failures") behaves similarly to the Wilson interval and is somewhat more conservative. — [Agresti & Coull 1998](https://math.unm.edu/~james/Agresti1998.pdf); [Brown et al. 2001](https://projecteuclid.org/euclid.ss/1009213286)
- Unpaired SE of a difference: sqrt(SE_A^2 + SE_B^2). Paired SE: SD of per-question differences / sqrt(n), equivalently sqrt(SE_A^2 + SE_B^2 - 2 SE_A SE_B Corr(s_A, s_B)). Pairing is "free" variance reduction when scores are positively correlated, which Miller expects for most model pairs. Report the difference, its SE, the CI and the correlation. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Miller's fictional example table: MATH +2.5% (SE 0.7%), CI (+1.2, +3.8), corr 0.50 -> significant; HumanEval -3.1% (SE 2.1%), CI (-7.2, +1.0), corr 0.64 -> not significant; MGSM -2.7% (SE 1.7%), CI (-6.1, +0.7), corr 0.37 -> not significant. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- For binary metrics the analytic CI 1.96 x sqrt(S(1-S)/N) converges to the bootstrap CI with enough bootstrap samples. — [Madaan et al. 2024, Quantifying Variance in Evaluation Benchmarks](https://arxiv.org/html/2406.10229v1)

### Inferences
- Wald vs Wilson, 95% (computed):
  - 255/300 (85%): Wald 81.0-89.0; Wilson 80.5-88.6 (similar at this n).
  - 98/100: Wald 95.3-100.7 (goes past 100%); Wilson 93.0-99.5.
  - 29/30: Wald 90.2-103.1; Wilson 83.3-99.4.
  - 30/30: Wald 100-100 (zero width, nonsense); Wilson 88.7-100.
  - Lesson: for per-category slices (e.g. 30 fire-safety questions) or near-perfect scores, Wilson matters a lot; for the whole 300-question set at 85% it barely matters.
- Paired difference worked example (computed): 300 questions; B fixes 25 that A got wrong and breaks 10 that A got right (b=25, c=10). Difference = +15/300 = +5.0 pts. Paired SE = sqrt((b+c)/n - d^2)/sqrt(n) = 1.95 pts -> 95% CI about +1.2 to +8.8 pts. McNemar chi-square (b-c)^2/(b+c) = 6.43; exact binomial p = 0.017. The unpaired SE would be about 2.8 pts, so pairing shrinks the SE by roughly a third here.
- Always report the CI of the difference, not just a p-value: "+5.0 pts (95% CI +1.2 to +8.8)" tells you both that it is probably real and that it might be small.

### Gaps
- No specific paper found on Newcombe's paired-difference interval (a Wilson-style interval for paired proportions); worth using for small b+c but not sourced here.

## 3. Paired tests: McNemar vs paired bootstrap vs paired t-test / permutation

### Takeaway
All three answer the same question ("is the mean per-question difference zero?") and on a few hundred questions they usually agree. Use McNemar (exact version when b+c is small, say under ~25) for binary pass/fail; use the paired t-test or a paired permutation (randomization) test for graded scores (judge scores 1-5, nDCG, F1). Avoid Wilcoxon and sign tests for claims about mean quality, and be wary of the bootstrap-shift test on small sets.

### Cited Findings
- Smucker, Allan and Carterette (CIKM 2007) compared Student's t, Wilcoxon signed-rank, sign, bootstrap and randomization tests on TREC data: t, bootstrap and randomization largely agree; Wilcoxon and sign diverge and "should no longer be used" by IR researchers. — [Smucker, Allan, Carterette 2007](https://ciir-publications.cs.umass.edu/getpdf.php?id=744); [Waterloo summary](https://uwaterloo.ca/data-systems-group/node/4915)
- Their 2009 follow-up at varying sample sizes: randomization and t agree with each other much more than the bootstrap agrees with either, and agreement drops with smaller samples. — [Smucker et al. 2009](https://uwaterloo.ca/data-systems-group/node/4913)
- Urbano, Lima and Hanjalic (SIGIR 2019) simulated over 500 million p-values with known null hypotheses (topic set sizes 25, 50, 100; measures AP, nDCG@20, ERR@20, P@10, RR): t-test and permutation test hold Type I error at the nominal alpha across measures and sizes; t-test is "remarkably robust to sample size" and is their top recommendation for hypotheses about mean effectiveness; permutation test for other statistics; bootstrap-shift test is biased towards small p-values (more false positives) unless samples are very large; Wilcoxon and sign tests are unreliable. Type III errors (right rejection, wrong direction) reached about 2% for P@10, RR and small topic sets. — [Urbano, Lima, Hanjalic 2019](https://arxiv.org/abs/1905.11096)
- Miller notes bootstrapping is generally unnecessary for eval error bars unless the sampling scheme or estimator is complicated; the CLT-based SE is enough for means. — [Miller 2024](https://arxiv.org/html/2411.00640v1)

### Inferences
- On 0/1 scores, a paired t-test on the per-question differences (values -1, 0, +1) gives nearly the same answer as McNemar for n in the hundreds; McNemar uses only the discordant pairs, which is why its power depends on psi.
- For graded scores (e.g. judge 1-5, recall@k per query), McNemar does not apply; use paired t or permutation on per-question differences.
- The bootstrap is still the easiest way to get CIs for odd statistics (median, ratio of two means, a metric computed over the whole set like macro-F1). Use the percentile or BCa interval and resample questions (or clusters), not individual runs.
- One-tailed tests in a regression gate ("did it get worse?") are legitimate if decided before looking; switching tails after seeing data is a forking path.

### Gaps
- I found no LLM-specific simulation study comparing these tests' error rates; the evidence is from IR, where per-query scores are similar in shape.

## 4. Non-determinism: repeated runs, variance decomposition, pass@k vs pass^k

### Takeaway
Total variance of an eval score = question variance (which questions you happened to pick) + sampling variance (the model's randomness on each question). Repeated runs only reduce the second part, so they help but have a ceiling. Average the K runs per question first, then compute the SE across questions; never treat K x N answers as K x N independent samples. Use pass^k when you need reliability (every attempt must work), pass@k only when a verifier can pick the one good attempt.

### Cited Findings
- Law of total variance view: each question has a conditional mean and a conditional (sampling) variance sigma_i^2; drawing K samples per question cuts the sampling part to sigma_i^2/K. In Miller's example (uniform difficulty, binary scores) K=2 removes 1/3 of total variance, K=4 removes 1/2, K=6 removes 5/9, and the limit is 2/3. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Pooling all K x N answers into one SE is wrong because they are not independent; compute the SE over question-level means. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- For non-chain-of-thought evals, scoring with the probability of the correct token removes the sampling variance entirely (Var = Var(p)/n). — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Do not lower temperature to cut variance: it can shift the expected score or raise the variance of the conditional means (his examples: variance rising from 1/12 to 1/4, and from 1/27 to 3/16). — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- tau-bench defines pass^k as the chance that all k i.i.d. trials of a task succeed, averaged over tasks, for agents that must be reliable (e.g. customer service); pass@k is the chance that at least one of k succeeds. pass^1 = pass@1 = average reward. pass^8 fell below 25% for the best mid-2024 models. — [Yao et al. 2024, tau-bench](https://arxiv.org/pdf/2406.12045); [Phil Schmid summary](https://www.philschmid.de/agents-pass-at-k-pass-power-k)
- Unbiased per-task estimators from n trials with c successes: pass^k = C(c,k)/C(n,k); worked example: 10 runs, 3 successes -> pass^2 = 3/45 ~ 0.07. — [Phil Schmid](https://www.philschmid.de/agents-pass-at-k-pass-power-k). The standard pass@k estimator 1 - C(n-c,k)/C(n,k) is from the Codex paper (Chen et al. 2021); not fetched here.
- Training-seed variance on standard benchmarks for 7B models (std, points): MMLU 0.57, GSM8K 0.41, HellaSwag 0.21, ARC-C 0.80, HumanEval 1.11, COPA 2.15; compared with bootstrap 95% CI half-widths of 0.72, 0.87, 0.93, 2.74, 3.98, 8.30. Continuous metrics (probability of the right answer) give better signal-to-noise; IRT-based question subsets increased seed variance (e.g. HellaSwag 0.21 -> 2.06). — [Madaan et al. 2024](https://arxiv.org/html/2406.10229v1)

### Inferences
- pass^k falls fast (computed): a task passing 90% of the time has pass^8 = 0.43; at 70% per trial pass^8 = 0.06. A system at "90% accuracy" can still fail a user who asks the same thing eight times.
- Practical recipe for a 300-question set: run K = 3-5 times per question at production temperature; per question record mean score and whether it was always right / always wrong / flaky. Flaky questions (sometimes right) are where most sampling variance lives and are the best candidates for prompt work.
- Comparing two systems with repeats: compute per-question mean for A and for B, take differences, paired t-test or bootstrap over questions. McNemar no longer applies directly once scores are fractions.
- The 2/3 ceiling means: if the set is too small, more repeats will not rescue it; you need more questions.

### Gaps
- No source found giving typical sampling variance for RAG answer correctness specifically; measure it on your own set (run the same config twice and count flips: that flip rate is your noise floor for psi).

## 5. Clustered questions and clustered standard errors

### Takeaway
If many questions come from the same document (or are paraphrases of one question), their results are correlated, and the naive SE is too small. Use clustered SEs, or bootstrap whole clusters. Real-world inflation in Miller's examples was about 2-3x.

### Cited Findings
- Clustered SE: SE_clustered = (SE_CLT^2 + (1/n^2) sum_c sum_i sum_{j != i} (s_ic - mean)(s_jc - mean))^(1/2). Report the number of clusters with the number of questions. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Paired and clustered: SE = (1/n) (sum_c sum_i sum_j (d_ic - mean_d)(d_jc - mean_d))^(1/2), where d is the per-question A-B difference. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Examples: DROP clustered SE 1.34 vs naive 0.44 (ratio 3.05); MGSM 1.62% vs 0.86% (ratio 1.88). — [Miller 2024](https://arxiv.org/html/2411.00640v1)

### Inferences
- Rule of thumb via the design effect (standard survey statistics, not from the fetched sources): DEFF = 1 + (m - 1) x ICC, where m = questions per cluster and ICC = within-cluster correlation. Computed: m=5, ICC=0.1 -> DEFF 1.4, effective n of 300 = 214, SE x1.18; m=10, ICC=0.2 -> DEFF 2.8, effective n = 107, SE x1.67; m=10, ICC=0.3 -> effective n = 81, SE x1.92.
- For a regulations corpus golden set (many questions per Approved Document), cluster by source document. A retrieval change that breaks one document's parsing can flip 15 questions together; naive McNemar would call that highly significant when it is really one event.
- Simple implementation: cluster bootstrap (resample documents with replacement, keep all their questions), or compute per-cluster sums of differences and treat clusters as the unit in a t-test.
- Design lesson: more documents with fewer questions each beats few documents with many questions, for the same total.

### Gaps
- No source fetched for the design-effect formula (Kish); it is standard survey sampling.

## 6. Miller (Anthropic, 2024), "Adding Error Bars to Evals": main recommendations

### Takeaway
Treat eval questions as a sample from a larger "super-population" of possible questions; report SEs; cluster when questions are related; reduce variance by resampling or token probabilities (not by lowering temperature); compare models with paired differences; plan sample size with power analysis.

### Cited Findings
- Five recommendations, in order: (1) report CLT standard errors, (2) use clustered SEs when questions are grouped, (3) reduce within-question variance by resampling answers or using next-token probabilities, (4) analyse paired differences when models share questions, (5) use power analysis to decide eval size and whether a comparison can answer the question. — [Miller 2024, arXiv 2411.00640](https://arxiv.org/html/2411.00640v1)
- Specific advice: report the mean, SE, n, number of clusters; for comparisons report difference, SE, 95% CI and correlation; do not pool K x N answers; do not lower temperature to cut variance; at least ~1,000 questions for new evals targeting 3-point differences. — [Miller 2024](https://arxiv.org/html/2411.00640v1)
- Source quirk: Table 1 lists a HumanEval score of 87.7% while Table 2 gives 86.7%; the -3.1% difference matches 86.7%, so Table 1 is likely a typo. — [Miller 2024](https://arxiv.org/html/2411.00640v1)

### Inferences
- For a 300-question golden set, Miller's framework says: expect to detect only about 4-7 point paired differences reliably (depending on discordance), so either grow the set toward 1,000, use repeats to shave sampling noise, or accept that small tweaks will be judged on direction and qualitative review rather than significance.

### Gaps
- Appendix C (cluster-adjusted power formulas) not read in detail.

## 7. Multiple comparisons, forking paths, dev-set overfitting and held-out test sets

### Takeaway
If you try 20 prompt variants on the same 300 questions and keep the best, the winner's gain is inflated even if none is truly better. Correct for multiple tests (Holm or Bonferroni against a baseline; Tukey HSD for all pairs), and confirm the chosen variant once on a held-out test set that was not used for choosing.

### Cited Findings
- Sakai's tutorial: for differences between every pair of m systems (m(m-1)/2 p-values), use a multiple comparison procedure such as Tukey HSD; no need to run ANOVA first. — [Sakai SIGIR 2018 tutorial](https://es.slideshare.net/TetsuyaSakai/sigir2018tutorial)
- Multiple testing on the same dataset is valid only with a correction (Bonferroni or Bonferroni-Holm); Tukey HSD for all pairs. — [Otero, Parapar, Barreiro, ECIR 2025](https://arxiv.org/html/2501.03930v1)
- Sanderson and Ferro estimated that 40-50% of uncorrected significance tests in IR research are likely Type I errors (as reported by Otero et al.); Otero et al. find unadjusted tests give very high Type I error rates and most adjustment procedures do not hit the designed rate exactly. — [Otero et al. 2025](https://arxiv.org/html/2501.03930v1)
- Carterette (2012, ACM TOIS) studied inference procedures for IR experiments with multiple comparisons against a baseline. — [Carterette 2012](https://ir.webis.de/anthology/2012.tois_journal-ir0anthology0volumeA30A1.3)
- Adaptive reuse of a holdout set (changing the model based on its holdout score) creates dependency and overfitting to the holdout itself; the "reusable holdout" (Dwork et al., Science 2015) uses differential privacy to allow safe reuse, and the number of safe reuses grows roughly with the square of the holdout size. — [Google Research blog](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/); [Dwork et al. arXiv 1506.02629](https://arxiv.org/abs/1506.02629)
- Prompt-format overfitting is real: perturbing MMLU prompts modestly dropped accuracy by 2.15% on average across 26 models, with 20 of 26 showing significant drops. — [C-BOD, arXiv 2502.07445](https://arxiv.org/html/2502.07445)

### Inferences
- Computed: 20 independent tests at alpha 0.05 give a 64% chance of at least one false "win"; Bonferroni alpha per test = 0.0025.
- Computed winner's curse: with paired SE ~1.8 pts (n=300, psi 10%), the best of 20 truly-null variants shows an expected gain of about +3.4 pts. So a "+3 pt winner out of 20 tries" on 300 questions is what pure noise looks like.
- Holm is uniformly better than Bonferroni and just as simple: sort p-values, compare the smallest to alpha/m, the next to alpha/(m-1), and stop at the first failure.
- Forking paths (choices made after seeing results: which metric, which subset, drop "bad" questions, one- vs two-tailed) inflate false positives without any explicit multiple tests. Fix: write the comparison (metric, test, threshold) before running, and keep the gate rules fixed in code.
- Held-out test set size (computed from SE formula): to know a final accuracy within +/- 5 pts (95%) at ~85% needs about 200 questions; within +/- 3 pts needs about 545. For a 300-question set, a common split is ~200 dev (iterate freely) and ~100 test (touch rarely), but a 100-question test can only confirm big changes (paired MDE ~6-9 pts); better to grow the test set over time, and refresh it with new questions when it has been looked at too often.
- Regression gate design: gate on "not significantly worse beyond a margin" (non-inferiority) rather than "any drop", or the gate will fire on noise about once every 20 runs at alpha 0.05.

### Gaps
- No LLM-specific study found quantifying how much dev-set prompt tuning overfits a golden set; the adaptive data analysis results are general.

## 8. Ranking metrics: confidence intervals for recall@k, MRR, nDCG

### Takeaway
Recall@k, MRR and nDCG are per-query scores averaged over queries, so the same machinery applies: SE = SD of per-query scores / sqrt(n), paired t-test or permutation test on per-query differences, cluster bootstrap if queries share documents. These metrics are noisier per query than accuracy (RR and P@10 especially), so they need more queries.

### Cited Findings
- On IR metrics (AP, nDCG@20, ERR@20, P@10, RR) the paired t-test and permutation test keep the false-positive rate at alpha for 25-100 topics; ERR@20 was the most stable measure; P@10 and RR had the most wrong-direction errors (up to ~2% on small topic sets). — [Urbano, Lima, Hanjalic 2019](https://arxiv.org/abs/1905.11096)
- Different metrics have very different within-system variances, so under the same alpha, power and minimum difference they need substantially different numbers of topics; pilot about 25 topics to estimate variance (hint from Sakai's talk, not a firm rule). — [Sakai 2016](https://link.springer.com/article/10.1007/s10791-015-9273-z); [Sakai AIRS 2016 slides](https://www.slideshare.net/slideshow/airs2016/69517852)
- Standardising scores per topic substantially reduces variance and so the topics needed. — [Sakai AIRS 2016](https://www.slideshare.net/slideshow/airs2016/69517852)

### Inferences
- Recall@k with one relevant chunk per query is 0/1, so it is just a pass rate: Wilson for the CI, McNemar for paired comparisons. With several relevant chunks it is graded; use paired t or permutation.
- MRR is dominated by the jump from rank 1 to rank 2 (1.0 -> 0.5), so a reranker that swaps ranks 1 and 2 on a few queries can move MRR a lot; check differences with a paired test, not eyeballing.
- If the gold labels are incomplete (unlabelled relevant chunks), apparent drops in recall may be label gaps; fixing gold labels before baselining (as planned in the builders_lab S116 item) is a precondition for meaningful significance tests.

### Gaps
- No source fetched giving typical per-query SD of nDCG@10 for RAG retrieval; compute it from your own baseline run.

## 9. Inter-annotator agreement: Cohen's kappa, Krippendorff's alpha

### Takeaway
Gold labels and LLM judges have errors too. Measure agreement beyond chance (kappa or alpha) on a doubly-labelled sample before trusting labels as ground truth. When most items are "pass", raw agreement looks high even if raters barely agree, which is why chance correction matters.

### Cited Findings
- Cohen's kappa = (p_o - p_e) / (1 - p_e), observed agreement corrected for chance agreement; it penalises a judge whose positive-label rate drifts from the human's, which accuracy-style measures miss. — [Agreement Metrics for LLM-as-Judge Evaluation, arXiv 2606.00093](https://arxiv.org/html/2606.00093v1)
- Kappa is more sensitive to marginal distributions than Krippendorff's alpha, so the two can rank judges differently. — [arXiv 2501.08167](https://arxiv.org/pdf/2501.08167)
- Krippendorff's alpha handles missing data and more than two raters; conventional bands: alpha >= 0.800 reliable; 0.667-0.800 tentative conclusions only; < 0.667 discard. These are conventions, not derived thresholds. — [Wikipedia: Krippendorff's alpha](https://en.wikipedia.com/wiki/Krippendorff%27s_alpha); [CASRAI guide](https://casrai.org/guides/krippendorffs-alpha)
- A context-specific reliability threshold is preferable to a universal cutoff. — [PMC article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6245899)
- Reported LLM-judge vs human kappas in a 2026 healthcare review ranged 0.59-0.88 (median 0.78 over 10 studies). — [arXiv 2605.25273](https://arxiv.org/pdf/2605.25273)

### Inferences
- Worked example (computed): two raters, 300 items, agree on 270 (90%), each says "pass" 85% of the time -> p_e = 0.85^2 + 0.15^2 = 0.745 -> kappa = 0.61. "90% agreement" is only moderate-to-substantial agreement beyond chance.
- Landis & Koch bands (0.41-0.60 moderate, 0.61-0.80 substantial, 0.81-1.00 almost perfect) are widely used but were not verified from the original in this research; Krippendorff's bands are stricter.
- Why it matters for significance: label noise caps measurable accuracy and adds variance. If 5% of gold labels are wrong, a system that is "really" better on those items cannot show it, and a 3-point "gain" may be partly label noise. Before chasing small deltas, audit the disagreements between system and gold on the discordant questions; many will be label errors.
- For an LLM judge: report judge-human kappa on a held-out labelled sample (say 100-200 items), and check it again when the judge model or prompt changes.

### Gaps
- Hamel Husain's and Eugene Yan's specific statistical advice was not retrieved (searches did not surface it); Chip Huyen not checked. No source found that quantifies how label noise changes test power in LLM evals.
