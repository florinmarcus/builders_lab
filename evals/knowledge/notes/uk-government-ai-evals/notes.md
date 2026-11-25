# UK government AI evals: what public teams publish

Research notes, 25 Nov 2026. Theory and public sources only, not facts about Florin's work.
"Measured" = a number from a real run or study. "Claimed" = stated without figures or method.
Repo content was read from shallow public clones (i-dot-ai/consult, redbox, lex, minute, caddy; alphagov/govuk-chat-evaluation; UKGovernmentBEIS/inspect_ai docs).

## 1. i.AI Consult / ThemeFinder (DSIT, i.AI): the richest public example

### 1a. Live evaluations against humans (measured)

| Evaluation | Date | Set size | Metric | Consult vs human | Human vs human |
|---|---|---|---|---|---|
| Scottish Gov non-surgical cosmetics | ~May 2025 | 2,000 responses, all reviewed; 6 reviewers | mean multi-label F1 | 0.76; 60% of responses unchanged | not reported |
| DWP Pathways to Work | 27 Aug 2025 | 87,738 responses, 125 reviewers, 17 questions | mean per-response F1 (95% CI by bootstrap) | 0.816 [0.813, 0.818]; 73% identical | 0.710 [0.703, 0.717]; 65% identical (17,000 double-reviewed) |
| DWP "Dip Test" (after close) | 2025 | 3,400 responses | F1 | 0.849; 73% identical | - |
| Independent Water Commission call for evidence | 16 Oct 2025 | 50,000+ responses, two expert groups | F1 | 0.79 and 0.82; ~83% agree with one or both groups | 0.74; 55% agreement |

Method (DWP report):
- Human in the loop at two stages: experts sign off themes; reviewers check and edit Consult's mapping in the app.
- Reviewer = reference label. But they say plainly the reviewer is not "correct": the task is subjective.
- **The pass bar is the human-human baseline, not a fixed number.** Quote: "There is no set definition of a 'good' F1 score ... the fact that Consult achieves a higher score than the person-to-person baseline suggests that, at minimum, Consult's mapping performance is as good as a human process."
- F1 per response, then averaged, so long answers don't dominate. Rows with no themes on both sides are dropped "to avoid biasing our performance estimates upwards".
- Decision-level check: do theme **rankings** change? Themes under 5% frequency excluded. Average move 0.5 rank; max 3; 4 of 140 themes moved more than 2 places.
- Coverage proxy: reviewers' "None of the above" rate 4.5% (under 5% taken as "theme list sufficiently exhaustive").
- Error direction: reviewers added 19,047 themes, removed 6,498. So Consult under-assigns.
- Equality analysis: F1 and change rate by self-reported disability; chi-squared plus effect size (Cramer's V 0.02). They report effect size because big samples make p-values meaningless.
- Cost of review: median 19 seconds per response; 78% under one minute.
- Water Commission: about 2 hours AI run, 22 hours expert checking, £240 AI cost (press release).
- My caveat (not stated in the report): reviewers edited Consult's suggestions rather than labelling blind, so anchoring could inflate agreement. The double-review phase also started from Consult's mapping.

Sources:
- DWP report: https://assets.publishing.service.gov.uk/media/68f63fe01c9076042263f0bd/evaluation-report.pdf
- Water Commission press release: https://www.gov.uk/government/news/ground-breaking-use-of-ai-saves-taxpayers-money-and-delivers-greater-government-efficiency
- Scottish evaluation: https://digitalgovernmenthub.org/wp-content/uploads/2026/02/Scot_Gov_NSCP_Evaluation_Report.pdf (via secondary coverage, Civil Service World, PublicTechnology)
- ATRS record: https://www.gov.uk/algorithmic-transparency-records/dsit-consult

### 1b. Offline eval framework in the repo (measured baselines, code read)

Repo: https://github.com/i-dot-ai/consult , folder `themefinder/evals/`.
- ADR 0010 (5 Aug 2026): Langfuse for runs and datasets, pydantic-evals for LLM-as-judge, LiteLLM gateway. Main driver: **model deprecation** - they need a repeatable suite to pick a replacement model. Aim: get anonymised real data from departments instead of fully synthetic.
- Per stage evals: mapping, generation, find_themes, condensation, refinement. Mix of deterministic metrics (F1, accuracy, redundancy via embeddings) and judge metrics (groundedness, information retention, clarity, specificity, information equivalence).
- Datasets: small and synthetic or public. `gambling_XS` = 200 responses over 2 questions; `XXS` = 30 responses. Three topics in CI: gambling, health, housing.
- Judge: gpt-4.1, one judge for all task models for consistency. Structured JSON output only; unstructured judge text is rejected.
- Judge prompt style now **binary PASS/FAIL per item, with reasoning and the matched items quoted**, not 1-5 for a whole list.
- **CI gate is regression against a baseline, not an absolute threshold.**
  - Smoke tier on PRs: every stage runs end to end on XXS; scores ignored.
  - Regression tier on main and nightly: 3 runs per case on 3 datasets; fail if any metric drops below baseline minus tolerance.
  - Tolerance = max(0.05 for 0-1 metrics, 0.5 for 1-5 metrics, 3 x stdev across runs). Baselines built from at least 3 runs (5+ better).
  - Any case or evaluator error makes the run INVALID (exit 2), separate from REGRESSION (exit 1). Missing baseline = invalid.
  - DVC pins code, data and params per result. Failures post to Slack.
- Example baselines (generation, gpt-4.1, Nov 2026): groundedness 0.87-0.99, information retention 0.85-0.88, clarity 0.91-1.0, specificity 0.78-0.89, F1 0.86-0.92, redundancy ~0.01 (lower is better).
- Mapping baselines are much lower: F1 0.63-0.69, exact-set accuracy 0.26-0.33. They still gate on them. Lesson: a gate holds the line at the current level; it is not a "good enough" bar.
- They also store F1 confidence-interval bounds as gated metrics.
- Live judge-prompt tests (`test_live_judge_prompts.py`): a tiny planted scenario (one valid rewording, one LOST theme, one INVENTED theme) run against the real judge to prove the prompt separates them. A cheap "judge unit test".

Judge design doc (`themefinder/evals/docs/llm-judge-improvements.md`, Feb 2026, internal-style notes in the public repo):
- Advice from an expert call: make judge tasks atomic ("The closer your judgment task is to the original task, the harder it is for you to have any faith that the judge can more meaningfully do the task"); one call per theme; binary instead of 1-5; shuffle order to cut position bias; measure variance across runs (themes "sometimes 10, sometimes 60").
- User research drove the metrics: "titles too vague" -> specificity metric; "themes essentially the same" -> redundancy metric; "agree and disagree grouped together" -> sentiment separation (planned).
- Known gap they name: ground truth was "100% LLM-generated", so "circular evaluation (LLM vs LLM)". Planned fixes: human spot checks of 5% of ground truth, intruder tests, tracking agreement over time.
- The bias percentages in that doc (position bias ~40%, CoT +10-15%, GPT-4 ~85% human agreement) are quoted from outside research, not measured by i.AI.
- I found no published judge-vs-human agreement number for ThemeFinder's judges.

## 2. Other i.AI repos

- **Redbox** (`notebooks/evaluation/`): DeepEval + RAGAS. Versioned immutable datasets ("Data is immutable"), synthetic Q&A from RAGAS, a baseline.csv to improve on. Metrics: contextual precision/recall/relevancy, faithfulness, answer relevancy, hallucination, bias. Thresholds left at the library default 0.5. No published offline numbers found. Redbox closed Dec 2025.
- **Redbox@DBT trial evaluation** (DBT, Dec 2024 - May 2025, mixed methods): self-reported only. 59% satisfied; ~20% of respondents reported seeing hallucinations, "with no direct impact observed on the satisfaction levels"; diary response rate 28%. Modest self-reported time savings (largest 1.8 hours on frameworks). https://www.gov.uk/government/publications/redboxdbt-trial-evaluation-report
- **Lex** (UK law MCP/API): an agent-skill eval file `.claude/skills/lex-uk-law/evals/evals.json`. Each case has a prompt, expected output and named **assertions**, including tool-trajectory checks ("Called search_for_legislation_sections", "Used provision_id containing ukpga/1998/42/section/3") and anti-hallucination checks ("Actual amendment details from API, not hallucinated"). No scores published.
- **Minute** (transcription/summaries, 400 users, 22 councils): no public accuracy numbers found. Follow-on "Local Transcribe" (MHCLG, Jul 2026) plans continuous automated evals of transcription accuracy, summary quality and bias by protected characteristic (a plan, not results). Ada Lovelace Institute found councils evaluate efficiency more than accuracy or harm.
- **Caddy, Parlex**: nothing on evaluation found.

## 3. GDS GOV.UK Chat (RAG over ~100k GOV.UK pages, ~700k chunks)

Published results (blog, 16 Mar 2026), measured:
- Accuracy rose from 76% (earliest benchmark) to 90% (latest), "across all topics".
- An answer counts as accurate only if it meets all the standards of published content. Answering only part of a question is a common failure.
- In-scope answer rate 88% (after adding clarifying questions).
- 508 jailbreak attempts in pilots; guardrails stopped all of them.
- Average response time 10.7 s.
- 73% found it useful, 64% satisfied (app survey).
- Scale: 10,000+ users, 26,000 questions. Manual review: 419 conversations, 1,084 Q&A pairs (web pilot); 1,338 in-scope answers (app pilot).
- Claimed only: "in line with industry benchmarks"; "scores higher than widely used consumer AI assistants" (no figures).
- Not disclosed: how 76% was computed, sampling, intervals, number of experts.
- https://insidegovuk.blog.gov.uk/2026/03/16/5-things-we-learned-testing-gov-uk-chat-an-ai-assistant-for-government

Method (blog, 15 May 2026): three pillars - automated eval on ground-truth datasets (LLM-as-judge for answers, classic precision/recall for classifiers), manual expert review against a quality framework, live monitoring flagging items for human review. Six criteria: groundedness, relevance and answer rate, factual accuracy, factual completeness, reliability, reputational safety. Rule: "Each iteration aimed to improve at least one criterion without compromising the others." Red teaming with i.AI and AISI. No judge-human agreement published.
https://insidegovuk.blog.gov.uk/2026/05/15/developing-gov-uk-chat-our-data-science-and-ai-engineering-journey/

Eval code (https://github.com/alphagov/govuk-chat-evaluation), code read:
- Separate tasks per component: question router, retrieval, rag_answers, jailbreak guardrails, output guardrails, topic tagger. Classifiers get precision/recall/F1 (sklearn); retrieval gets per-query precision/recall/F1 with mean, median, stdev.
- RAG answers via DeepEval plus custom metrics. **Per-case thresholds are strict**: faithfulness 1.0, factual precision 1.0, factual recall 1.0, absence of factual contradictions 1.0, bias 0.0; relevance, context relevancy, coherence 0.8. So one unsupported or missing fact fails the case.
- Factual precision/recall judge: list key facts, classify each as TP / FP / FN against a ground-truth answer, then compute tp/(tp+fp) and tp/(tp+fn) in code. The judge labels; code does the maths.
- Judge models on Bedrock or OpenAI (default gpt-oss-120b, temperature 0); `n_runs: 2`, reports mean and std per input.
- Internal datasets are "not publicly available at present" (ATRS).

## 4. ATRS records (what they report)

- **DSIT GOV.UK Chat** (7 Oct 2025): hybrid eval; automated precision/recall for classifiers; LLM-as-judge for "factual precision, factual recall, relevancy, groundedness"; manual accuracy, completeness, interaction quality; red teaming with AISI. Says "it's not possible to guarantee no jailbreaking attempts will be successful". No scores, thresholds or sample sizes. https://www.gov.uk/algorithmic-transparency-records/dsit-gov-dot-uk-chat
- **DBT business.gov.uk Webchat** (30 Jul 2026): ~5,000 users, 8-week private beta, autumn 2025. Automated word overlap and semantic similarity to sources, link validity; expert quality score; malicious-question testing. No numbers. https://www.gov.uk/algorithmic-transparency-records/dbt-ai-chatbot
- **DSIT Consult**: describes pipeline; numbers live in the separate evaluation reports.
- Pattern: ATRS lists methods, rarely results. Numbers appear in blogs and evaluation reports instead.

## 5. AI Security Institute: Inspect (inspect_ai)

- Scorers: text match (match, includes, pattern, exact, f1, choice) and model-graded (`model_graded_qa`, `model_graded_fact`).
- Model graders return C / I, or C / P / I with `partial_credit=True` (P = 0.5). A panel of grader models can vote, default reducer "majority" (a grade must have more than half the votes).
- Metrics default to accuracy plus **stderr**. Epochs (repeats) with reducers.
- Scoring policy treats the grader as "part of the measurement instrument": a grader that fails gives `Score.unscored()` (NaN, excluded and counted separately) or `grader_failed`, not a silent 0 or 1. Model failures (`invalid_response_format`, `refusal`, `no_response`) stay in the denominator.
- Deferred scoring: run with `--no-score`, then re-score logs with a new scorer. Useful for judge development without re-generating answers.
- Reliability advice: temperature 0, seed, and "Run multiple epochs and inspect grade variance - setting temperature=0 reduces, but does not always eliminate, run-to-run disagreement."
- No built-in judge-vs-human validation step; that is left to the eval author.
- https://inspect.aisi.org.uk/scorers.html ; docs in repo `docs/model-graded.qmd`, `docs/scoring-policy.qmd`.

## 6. Guidance

- **AI Playbook for the UK Government** (10 Feb 2025): principles, no numbers. "Fully test the product before deployment"; "regular checks of the live tool"; monitor drift, bias and hallucinations; "be clear about what objective measures you're assessing the AI outputs against"; test accuracy and relevance "with a sample of your users"; model metrics vs service metrics (a high-accuracy model users ignore). https://www.gov.uk/government/publications/ai-playbook-for-the-uk-government
- **Cross-Government AI Testing Framework** (xGov Testing Community, GDS, mid-2025): the only UK doc with example thresholds. Labelled as examples, "not a checklist or a rigid standard". Relevant ones: label audit 95% agreement; ML F1 >= 0.85; generative: >80% of sampled outputs rated acceptable by humans; prompt injection success <1%; known attacks <2% success; 0/50 adversarial prompts unsafe; agent task success >= 90%; >= 85% generated content rated neutral and fair; 100% of LLM responses traceable to logged prompts; integration end-to-end success >= 95%; quarterly re-tests. No mention of LLM-as-judge. https://testing-ai-standards.github.io/cross-gov-ai-testing-framework ; CDDO blog https://cddo.blog.gov.uk/2025/09/22/how-do-we-test-and-assure-ai-in-government/
- **Magenta Book annex: Guidance on the impact evaluation of AI interventions** (Evaluation Task Force with Frontier Economics, Nov 2024 / 2025): explicitly not about quality, safety or accuracy of the tool; about impact on decisions and outcomes. Recommends RCTs where possible, quasi-experimental otherwise, evaluating through the life of the tool. https://www.gov.uk/government/publications/the-magenta-book/guidance-on-the-impact-evaluation-of-ai-interventions-html
- **NAO** "Use of AI in government" (Mar 2024): AI early stage; asked Cabinet Office to set metrics and monitoring. No tool-level eval numbers. NAO good practice guide (May 2026) exists; not read in detail.

## 7. Comparison, brief

- **Singapore GovTech, RubricBench** (Kaleidoscope): 108 Q&A pairs from 4 government chatbots, 14 binary dimensions, 2 human annotators. Human-human agreement 87.10% overall; factual correctness 82.41%, specificity 70.37%, bias 99.07%. Built to benchmark LLM judges; no judge results on the card. Useful as a ceiling: a judge cannot be expected to beat human agreement. https://huggingface.co/datasets/govtech/RubricBench
- GovTech also has LionGuard 2 (safety classifier) and RabakBench (multilingual safety benchmark, majority-voted LLM labels); no product-eval pass rates found.
- **US NIST GenAI** (pilot report NIST AI 700-1, 2025): about telling AI text from human text (generator vs discriminator, AUC/Brier), not product quality gates. Not comparable.

## Synthesis

What UK teams value:
1. **Human baseline as the bar.** Consult never sets "F1 >= X". It asks: is AI-vs-human at least as good as human-vs-human? (0.816 vs 0.710; 0.79/0.82 vs 0.74.)
2. **Decision impact over raw score.** Did the headline findings (theme rankings) change? Is anything big missing (None-of-the-above rate)?
3. **Strict per-fact grounding.** GOV.UK Chat fails a case on one unsupported fact (thresholds 1.0) and counts "accurate" only if all parts are answered.
4. **Regression gates, not absolute gates,** with tolerance from measured run-to-run noise, and errors kept separate from regressions.
5. **Fairness by subgroup** (effect size, not p-values), red teaming with AISI, and live monitoring with human review.
6. **Honesty about gaps.** i.AI names its own circular LLM-made ground truth. Nobody publishes a judge-vs-human agreement number.

Versus "judge pass >= 85%":
- No UK team publishes a fixed judge pass-rate gate. The closest are the Testing Framework's examples (F1 >= 0.85; >80% human-rated acceptable) and GOV.UK Chat's 90% expert-assessed accuracy as a result, not a gate.
- 85% is near the human-human ceiling seen in public data (GovTech 87%; Consult reviewer pairs 65% identical, F1 0.71-0.74). On subjective dimensions, a fixed 85% may be above what two humans reach.
- UK practice gates on "no worse than baseline minus noise" and on per-case strictness for facts.

Ideas worth borrowing:
1. Measure human-human agreement on a slice of the golden set, and report judge-human agreement next to it. Treat that as the ceiling for the gate.
2. Add a regression gate beside the 85% bar: baseline from 3-5 runs, tolerance max(0.05, 3 x stdev), and an INVALID state for judge errors (never count a failed judge call as pass or fail).
3. Split factual scoring: judge labels each key fact TP/FP/FN against the reference; code computes precision and recall; fail a case on any FP (unsupported fact).
4. Make judge calls atomic and binary (one claim or one item per call, PASS/FAIL with reasoning and quoted evidence), shuffle order, and keep a few planted cases (one correct, one missing, one invented) as a live judge unit test.
5. Add a decision-level check: would the user's decision change? (For RAG: is the cited section the right one; for summaries: do top items rank the same.) And slice results by subgroup or topic.
