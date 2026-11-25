# LLM-as-judge case studies: what people really report

Research notes, 25 Nov 2026. Question: is a judge gate of "pass >= 85%" for RAG and agent systems reasonable, and what do others report?

Legend:
- **Measured** = the source gives the number and says how it was measured.
- **Claimed** = a number without method, or a qualitative claim.
- **Vendor** = the team grades its own product. **Independent** = academic or third party.
- "Agreement" = raw percent agreement unless stated. κ = Cohen's kappa (chance-corrected; 0.41-0.60 moderate, 0.61-0.80 substantial).

Theory, not facts about my own work.

---

## 1. Industry write-ups

### Shopify Sidekick (Aug 2025), vendor, measured
- Domain: merchant assistant agent (multi-skill).
- Judge scored conversations on several criteria. Labels from at least three product experts per conversation.
- Agreement: first judges κ = 0.02 ("barely better than random"). After prompt iteration κ = 0.61. **Human-human baseline κ = 0.69.**
- Gate: no number. Rule: human agreement is the ceiling; success = you cannot tell whether a human or the judge was in the rater group.
- Labelled set size: not given.
- Link: https://shopify.engineering/building-production-ready-agentic-systems

### Honeycomb Query Assistant, via Hamel Husain (Oct 2024), practitioner, measured but thin
- Judge scored natural-language-to-query outputs, pass/fail with critique.
- Agreement: > 90% with one domain expert after three prompt iterations. Raw agreement, used because the data was roughly balanced.
- Set size not given. Hamel's guidance in the same post: about 100 labelled examples per failure mode; below about 60 the confidence intervals are too wide. Report TPR and TNR separately. A judge that always says "pass" gets 95% agreement when failures are 5%.
- Link: https://hamel.dev/blog/posts/llm-judge/

### Nurture Boss, via Hamel Husain (Mar 2025), practitioner
- Domain: AI leasing assistant for apartment complexes.
- Not a judge-validation number. Error analysis found three issues caused over 60% of problems. Date handling failed 66% of the time; after fixes, date handling success went from 33% to 95%.
- No judge agreement figure published for Nurture Boss.
- Link: https://hamel.dev/blog/posts/field-guide/

### Visa, vRAG-Eval (arXiv 2406.18064, v3 Nov 2024), vendor research, measured
- Domain: enterprise RAG over payment network documents. 155 Q&A pairs, 14 subject areas.
- Judge: GPT-4 on a 5-level rubric (correctness, completeness, honesty). Levels 4-5 = accept.
- Agreement with human experts: **29.7% on the 5-level scale, 82.6% when collapsed to accept/reject.** Llama 3 8B: 36.8% binary. No human-human agreement, no kappa.
- System result: the traditional RAG baseline was rejected 77% (GPT-4) and 72% (humans). So only about 23-28% accepted.
- Lesson: the same judge looks bad or good depending on the scale. And a first RAG system can be far below 85%.
- Link: https://arxiv.org/abs/2406.18064

### Databricks docs bot (2023 blog), vendor, measured (light)
- Judge graded RAG answers for correctness, readability etc. on 0-3.
- GPT-4 vs humans: > 80% exact agreement, > 95% within one point.
- Recommends low-precision scales (0-3 or 1-5) and binary where possible.
- Link: https://www.databricks.com/blog/LLM-auto-eval-best-practices-RAG

### Nubank customer support agents (arXiv 2606.08867, Jun 2026, KDD 2026), vendor, measured
- Domain: support agents for 100M+ users (card delivery, debt, credit limit...).
- Labels: three analysts, majority vote. No human-human kappa reported.
- Labelled sets per eval: 888, 90, 816, 246, 90 samples (binary). Split 40/30/30.
- Judge vs human accuracy on test sets after prompt optimisation (GEPA): 82%, 89%, 73%, 77%. Starter prompts: 78%, 69%, 58%, 74%. Majority-class baselines: 51%, 78%, 57%, 51%. Note eval E2: the starter judge (69%) was worse than always guessing the majority (78%).
- Judge-to-judge κ on one eval went from about 0.1 to 0.75-0.95 after optimisation.
- Mentions κ or α > 0.8 as an example of "high agreement", not as a hard gate.
- Offline failure rate drops of 20-25 points matched the biggest online gains (tNPS +37 points).
- Link: https://arxiv.org/abs/2606.08867

### Deployed food ordering agent, "Catching One in Five" (arXiv, 2026), independent-ish, measured
- Measured judge **recall of real defects**, not agreement. Ground truth: exhaustive human transcript review.
- The built-in judge found 2 of 9 systematic problem patterns (22%). In one batch its gate flagged 0 of 100 rounds while humans found 23 distinct defects.
- Cause: the rubric had only three coarse axes (intent, brand voice, personalisation). Cross-turn state bugs had no category, so they were filed as "brand voice". The gate was wired to hangs and hard assertions, not the rubric.
- Lesson: a high pass rate can mean the judge does not look for the failures you have.
- Link: https://consensus.app/papers/details/w:3ab10165-df98-4517-b0c4-441f4afaa2c3/

### Uber Genie on-call copilot (May 2025), vendor, claimed
- Golden set of 100+ SME queries. LLM judge scores 0-5 against SME reference answers.
- Results only as relative changes: acceptable answers +27% relative, incorrect advice -60% relative. No absolute pass rate. No judge validation numbers. "Acceptable" not defined.
- Link: https://www.uber.com/en-GB/blog/enhanced-agentic-rag/

### DoorDash Dasher support (Sep 2024), vendor, claimed
- Online guardrail (semantic similarity, then an LLM checker) plus an offline LLM judge.
- Claims: hallucinations -90%, severe compliance issues -99%. No baseline, no judge agreement numbers in the sources I could reach.
- Link: https://careersatdoordash.com/?p=12568 (blocked to my fetcher; figures via secondary summaries)

### Thomson Reuters CoCounsel (2024-2026), vendor, claimed
- Attorney-written ideal answers; LLM judge "aligned with our SME scores", tests dropped when attorneys disagree. Hundreds of tests per skill.
- No agreement numbers, thresholds or pass rates published in the posts I found.
- Links: https://www.thomsonreuters.com/en-us/posts/innovation/legal-ai-benchmarking-evaluating-long-context-performance-for-llms/ and https://www.thomsonreuters.com/en-us/posts/innovation/when-legal-ai-is-evaluated-like-legal-work-the-results-change/

### Intercom Fin, LinkedIn: searched, no judge-validation numbers found
- Intercom: resolution rates quoted as 51%, 67% or 76% average in different pages, and Intercom itself warns the definitions differ. Their judge-based comparison admits judges "might not perfectly match human judgment". No agreement figure.
- LinkedIn: no engineering post with a judge agreement number found.

---

## 2. Legal

### Vals Legal AI Report, VLAIR (Feb 2025), independent benchmark firm, measured scores, judge not validated
- 240 questions over 7 tasks (Am Law 100 style). Tools: Harvey, CoCounsel, Vincent AI, Oliver. Plus a lawyer baseline.
- Grading: LLM judge. Each reference answer has several pass/fail "checks"; score = % of checks passed. Humans re-checked only failing scores.
- **No judge-vs-human agreement reported.** Report says the judge "is not sufficient to replace an expert human grader".
- Scores (% of checks): Harvey Document Q&A 94.8, CoCounsel 89.6; summarisation best 77.2; data extraction best 75.1; redlining best 65.0. **Lawyer baseline: 50-80% by task** (Q&A 70.1, summarisation 50.3, redlining 79.7).
- Lesson: on a "% of checks" score, real lawyers land at 50-80%.
- Link: https://www.vals.ai/industry-reports/vlair-2-27-25

### Legal Research Bench (arXiv 2610.00609, Oct 2026), independent, measured. Best single case for this question
- 413 expert-written US legal research questions, each with gold answer and binary rubric.
- Judge calibration set: 341 rubric items from 45 responses to 15 questions, graded by three attorneys.
- **Attorney vs attorney: 83.4% agreement, κ = 0.644.** Response level 87.9%, κ = 0.735.
- Chosen judge (GPT-5.4): 87.4%, κ = 0.715, false positive rate 5.6%, false negative rate 7.0%. Judge pass rate 66.3% vs expert majority 67.7% (so it is not lenient overall).
- **Same system, two definitions:** best model (Claude Opus 4.8) is fully correct ("all-pass": every criterion met, and cited sources verify) on **42.9%** of questions, but earns **85.4%** of rubric weight.
- Link: https://arxiv.org/html/2610.00609

### Harvey Legal Agent Benchmark (May 2026), vendor, measured scores, judge not validated publicly
- Long agent tasks, expert rubrics, all-pass scoring, graded several times by different model families and averaged.
- All-pass on holdout: best 7.1% (Claude Opus 4.7). "Less than 10% of tasks end-to-end."
- No grader-vs-lawyer agreement published.
- Link: https://www.harvey.ai/blog/legal-agent-benchmark-initial-results

### Stanford RegLab, "Hallucination-Free?" (2024 preprint, JELS 2025), independent, human graders
- 200+ preregistered legal queries. Human grading, not an LLM judge, but useful for definitions and the human ceiling.
- Inter-rater check: 48 responses re-graded blind. **85.4% agreement, κ = 0.77.**
- "Accurate" = correct AND grounded. Lexis+ AI 65% accurate, ~17% hallucinated; Westlaw AI 41-42% accurate, ~33% hallucinated; Ask Practical Law 19-20% accurate, 62% incomplete.
- Vendors had claimed "hallucination-free". Lesson: "accurate" here needs both truth and correct citations.
- Link: https://arxiv.org/abs/2405.20362

---

## 3. Medical

### OpenAI HealthBench (May 2025), vendor-built benchmark, measured
- Rubric criteria written by physicians; a model grader marks each criterion met / not met.
- Meta-eval: 60,896 physician judgments over 34 consensus criteria.
- GPT-4.1 grader macro F1 = 0.709. **Physician-physician macro F1 by theme: 0.569 to 0.730.** Grader above average physician in 5 of 7 themes.
- Best model (o3) scored 60% overall; 32% on HealthBench Hard.
- Lesson: in open medical answers, even doctors only reach F1 0.57-0.73 against each other.
- Link: https://arxiv.org/abs/2505.08775

### Mayo Clinic perioperative patient questions (Bioengineering, 2026), independent clinical, measured
- 1,285 real patient-assistant interactions, 112 patients, physician labels.
- Judge vs physicians: 93.1% four-class agreement, κ = 0.852. Binary correctness: accuracy 93.4%, sensitivity 94.6%, specificity 90.2%, precision 96.2%.
- Best-case example: narrow task, clear criteria, large labelled set.
- Link: https://consensus.app/papers/details/w:288b0368-13d2-4a32-8e88-cc272199740e/

### Clinical EHR summaries, Croxford et al. (npj Digital Medicine, 2025), independent, measured
- Judge scored summaries on a validated instrument (PDSQI-9).
- Best judge (o3-mini) ICC = 0.818 with human evaluators; median score difference 0.
- Link: https://consensus.app/papers/details/w:3b24f3b8-ed0e-4f3b-b871-34f153ec9476/

### PANDA pediatric RAG decision support, Gershon et al. (npj Digital Medicine, 2026), independent, measured
- 118 clinician-written queries to a deployed RAG system. 5 physicians, 7 LLM judges, 7 rubrics.
- High agreement on text-comparison rubrics (faithfulness, completeness). Weaker on reasoning and safety.
- Repeated runs and judge panels did not beat the best single judge. **Binary pass/fail showed misalignments that ordinal scales hid.**
- Link: https://consensus.app/papers/details/w:6a490b97-ebd0-4ab4-86aa-5946ec30a865/

### Rwanda clinical answers, Williams et al. (npj Digital Medicine, 2026), independent, measured
- 524 query-response pairs, 11 criteria, local GPs as raters.
- Best single judge matched clinicians on only 4 of 11 criteria; best jury 5 of 11.
- Link: https://www.news-medical.net/news/20260721/Human-experts-remain-essential-for-checking-clinical-AI-outputs.aspx

### Medical completeness, DeLucia et al. (arXiv, 2026), independent, negative result
- Judges detecting incomplete answers (incl. HealthBench data): AUC 0.49-0.66, near chance. At 90% recall of incomplete answers, clinicians still had to review most of the data.
- Link: https://arxiv.org/abs/2604.16383

---

## 4. RAG faithfulness and general studies

- **RAGAS (2023):** agreement with humans 0.95 faithfulness, 0.78 answer relevance, 0.70 context relevance. Human-human about 95% / 90%. Caveat: WikiEval is small (50 pages) and pairwise on deliberately contrasted answers, an easy setting. https://arxiv.org/abs/2309.15217
- **TREC 2024 RAG Track, support judging (2025):** 45 runs, 36 topics. Human and GPT-4o labels match exactly on 56% (3-level scale), 72% when humans post-edit LLM labels. An independent human agreed better with GPT-4o than with the first human. https://consensus.app/papers/details/w:ee8697b1-0518-456d-be1d-6b124bd3fda3/
- **LLM-AggreFact (grounded fact-checking):** best checkers around 77% balanced accuracy across 11 datasets. https://llm-aggrefact.github.io/blog
- **Luo et al. (via Eugene Yan):** gpt-3.5 found >95% of consistent summaries but only 30-60% of inconsistent ones. Typical judge failure: lenient, misses the failures. https://eugeneyan.com/writing/llm-evaluators/
- **MT-Bench (Zheng et al. 2023):** GPT-4 vs experts 85% (ties excluded), human-human 81%. Chat preference, not domain correctness.
- **Judging the Judges (Thakur et al. 2024):** simple QA where humans agree κ = 0.97. GPT-4 κ = 0.84. A small model had 80% agreement but κ = 0.62. Judges lean lenient. https://arxiv.org/abs/2406.12624
- **Judge's Verdict (NVIDIA, Oct 2025):** 54 judges on RAG/agent answers; 27 passed the first correlation tier, 23 "human-like". https://arxiv.org/abs/2510.09738
- **EvalGen (Shankar et al. 2024):** 84 medical and 100 product samples. Defect recall 0.73 on product task; false failure rate 0.10 medical, 0.39 product. Criteria drift: people change their criteria while grading. (Numbers via Eugene Yan's summary.)
- **Rating indeterminacy (Guerdan et al., NeurIPS 2025):** when several ratings are reasonable, forced single-label validation can pick judges up to 31% worse. https://consensus.app/papers/details/w:3585839c-543d-4e77-8ae0-20bd49a9df9f/

---

## 5. Human-human ceilings seen

| Setting | Human-human |
|---|---|
| Simple QA correctness (Thakur) | κ 0.97 |
| Legal research hallucination (Stanford) | 85.4%, κ 0.77 |
| Legal rubric items (LRB) | 83.4%, κ 0.64 |
| Shopify agent conversations | κ 0.69 |
| HealthBench physician criteria | macro F1 0.57-0.73 |
| MT-Bench chat preference | 81% |
| RAGAS pairwise (easy) | 90-95% |

---

## 6. Synthesis

**Realistic judge agreement.**
- Narrow, clear, binary checks: 85-93% agreement, κ 0.7-0.85 (Mayo, LRB, Stanford-style labels).
- Broad or subjective criteria: κ 0.4-0.7, F1 0.6-0.7 (Shopify, HealthBench, Williams).
- Good judges sit near the human ceiling, rarely above it. The ceiling itself is often only 80-88% raw.
- Starter prompts are often near chance (Shopify κ 0.02, Nubank E2 below majority baseline). Several prompt iterations are normal.
- Percent agreement hides failure detection. The honest numbers are TPR/TNR or recall on failures; several studies show judges miss 40-80% of real failures when not built for them.

**Pass thresholds people use.**
- Almost nobody publishes a hard release gate like "pass >= X%". Gates are relative: beat the last version, match the lawyer or physician baseline, regression checks.
- Judge trust gates are about agreement: "near human baseline", κ > 0.8 as a nice-to-have, > 90% raw agreement on a balanced set.

**System pass rates actually reached.**
- First RAG builds: 23-28% accepted (Visa).
- Legal tools on "% of checks": 50-95% by task; lawyers 50-80%.
- Legal research all-pass: 43% best; long legal agent tasks all-pass under 10%.
- Medical open answers: 60% (HealthBench), 32% on hard cases.
- Narrow product sub-skills after focused fixes: 95% (Nurture Boss date handling).

**What "accuracy" means differs a lot.**
- % of rubric checks passed (Vals) vs all checks passed (LRB, Harvey). Same system: 85% vs 43%.
- Correct only vs correct AND grounded (Stanford).
- Binary vs 5-level scale: same judge 83% vs 30% agreement (Visa).
- Accept threshold on a Likert scale (4+ of 5) is itself a choice.
- Resolution rate in support: definitions vary even inside one vendor (Intercom).

**Is "pass >= 85%" a reasonable gate?**
- Depends on the definition. 85% of rubric weight or per-check pass rate: reachable for strong systems (LRB best = 85.4%). 85% of answers fully correct on every check: rarely reported, on hard sets well out of reach.
- Judge error matters at that level. With judge FPR 5-7% and FNR 7%, a measured 85% can hide a true rate several points either way. With n = 100, the 95% interval on 85% is about ±7 points.
- Better pattern from these cases: (1) validate the judge first, per criterion, with TPR/TNR on at least ~100 labelled items per failure mode; (2) gate on binary per-criterion checks; (3) set different bars for critical criteria (e.g. groundedness, safety near 95-100%) and softer ones; (4) gate on "no regression vs last release" plus the critical bars, not one overall %.
