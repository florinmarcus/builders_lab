# Eval practice assessment: my labs against the study map

*Companion to `eval-data-science-map.md`. One section per map topic: where my two labs
stand today, what to change, and an ADR seed for builders_lab. About my own labs only
(builders_lab, agentic-rag-lab). Evidence was read from the
repos on 25 Nov 2026 (builders_lab main plus branch `claude/wonderful-wright-rd0v80`;
agentic-rag-lab default branch). Re-check paths before acting: repos move on.*

## How each section is laid out

1. **Status:** know it / know it, practice gaps / heard of it / new.
2. **Criteria table:** the practices the topic expects, one row each, with a verdict per lab:
   **STRONG**, **SO-SO**, **MISSING**, plus the evidence.
3. **Actions:** numbered `<topic code>-<n>`, each with repo, effort, depends on, and
   "done when".
4. **ADR seed (builders_lab):** context, proposed decision, options, consequences: ready
   to copy into `decisions/NNNN-*.md` once agreed.

Short names: **BL** = builders_lab, **ARL** = agentic-rag-lab.

---

## Topic 1. Error analysis (code EA)

**Status:** know it, practice gaps (25 Nov 2026).

**Summary:** both labs are good at counting failure causes and picking the right kind of fix.
Weak spots: who reads (mostly the Claude session), labels fixed before reading, a 1-5
answer judge. Missing: a stopping rule, a regular review loop, and step-level trajectory
analysis.

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Read real outputs by hand, regularly, by the domain owner | **SO-SO.** 12 of 42 never-retrieved questions read (`evals/experiments/L1-miss-analysis.md`); 50 semcheck flags hand-checked vs page image, 94% real (`P-semantic-validation.md`). Reader was the Claude session; Florin's spot check pending. | **SO-SO.** Reading per experiment, not a habit: E17 read 32 "no" claims (6 real misses, ~10 own bugs, `docs/experiments/e17-own-guards.md`); E23b read all 9 failures. 0 of 338 golden items `checked_by_hand` (ADR 0006 asks ≥ 30). |
| 2 | Open coding: free-text note on the **first** failure per trace | **SO-SO.** One cause plus free-text reason per miss (branch `evals/golden/review/e8-miss-check-2026-11-24.jsonl`, 90 rows). Semcheck allows several findings per unit, not first-failure. | **SO-SO.** Free-text notes per failure (E14, E23b), not first-failure; no labels file. |
| 3 | Axial coding: 5-10 named failure modes, counted and ranked | **STRONG.** L1 causes counted; e8 misses: label_too_narrow 38, query_wording 25, ranking 25, gold_wrong 2; semcheck round 2 ranked (headings 63, tables over pages 46). | **SO-SO.** Buckets fixed in advance (`docs/plan.md`); counted in E19 and E25; no cross-experiment taxonomy or ranking. |
| 4 | Saturation: a stopping rule | **MISSING.** Sample sizes set by statistics or time. | **MISSING.** "About 20" failed answers, no rule. |
| 5 | Per failure mode: prompt fix / code check / validated judge / ignore | **STRONG.** Parser fixes with synthetic tests; ligature fix kept on a code check; `verify_answer` is plain code; miss cause → fix route (`architecture/design/eval/flows/retrieval-run-and-gate.md`). | **STRONG in practice.** E14 prompt fix did nothing → moved to code (E18); attacks checked by code (design 07). Not written down per mode. |
| 6 | Binary pass/fail per failure mode, not one 1-5 score | **SO-SO.** Semcheck flag and decomposer judge are binary; answer judge is 1-5 × 3 criteria (`evals/judge.py`, J1, PLAN step 3). | **SO-SO.** Code checks binary; judge 1-5 × 3, pass ≥ 4 (`docs/design/0007-judge.md`); repo flags "generic 1-5 judge" itself. |
| 7 | Criteria drift: labels and rubrics versioned, re-labelled on change | **SO-SO+.** labels_version v3 with remap log (S116), golden_sha and prompt_sha in runs, judge brief v1. Open: needed-vs-alternative groups (S116), stale out_of_scope labels (S146). | **SO-SO.** Golden fix pass: 55 removed with reasons (`golden/removed.jsonl`), reviews kept; no version field, no rubric versions, no re-label step. |
| 8 | Recurring loop: new outputs reviewed, failures promoted to golden | **MISSING for answers.** No users yet; corpus scoreboard only (S140); frozen audit sample planned (S141); 38 label_too_narrow misses not folded back. | **MISSING.** Candidates noted (e.g. d-016 in E19), not promoted; online eval parked. |
| 9 | Agents: step-level analysis, transition failure matrix | **MISSING.** J1 tests search + Haiku, not the plugin → specialist → verify_answer flow; no trace linking across a conversation (S9). | **SO-SO.** Tool choice and filters scored from traces (E25), "saw every section" (E14/E18), step-limit counts (E23); no transition matrix. |
| 10 | Synthetic questions from explicit dimensions | **STRONG-ish.** `evals/golden/BUSINESS-BRIEF.md`: 6 roles, kind shares, multi_rule/vague shares. Models wrote questions and labels; no tuples; no real builders. | **SO-SO.** Topic and kind quotas, stratified sample (`lab/evals/sample.py`); no explicit tuples. |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| EA-1 | Read 20-50 answers myself; one note on the first failure in each; batches of 20; stop after two batches with no new failure mode | BL (as part of the spot check), then ARL | 3-4 h per lab | none | a notes file and a count of new modes per batch |
| EA-2 | One labels file shared across experiments: `id, run, first_failure_note, failure_mode, labelled_by, date` | BL, ARL | 1 h setup | EA-1 | a ranked failure-mode table generated from it |
| EA-3 | Write the per-mode fix decision down: prompt fix / code check / judge / ignore, with the reason | BL | 1 h | EA-2 | a table in the eval docs, one row per mode |
| EA-4 | Split the 1-5 answer judge into 3-5 binary checks, one per real failure mode (BL candidates: missed rule, wrong citation or edition, asbestos and approval rules, missing ask-back, wrong "not in sources") | BL, then ARL | 4-6 h | EA-2; topic 4 for validation | each check returns pass/fail with a critique |
| EA-5 | Fold the 38 label_too_narrow misses back into labels (also_acceptable or expected sections); I read about 20 of them | BL | 2 h | S116 groups | labels_version bumped, remap logged |
| EA-6 | Promote-to-golden step: a script that turns a labelled failure into a golden item, plus a version field on the golden set | BL, ARL | 2-3 h | EA-2 | one failure promoted end to end, old runs re-scorable |
| EA-7 | Trace 50-100 end-to-end runs through the real plugin; code the first failing step; build a transition matrix (decompose → search → rerank → answer → verify_answer) | BL | 6-8 h | S9 trace linking | a matrix with counts, top cell named |

### ADR seed (builders_lab): "Error analysis drives the answer evals"

- **Context:** retrieval misses are coded and counted well, but answer quality is judged by
  one 1-5 judge on three criteria, failure modes are fixed in advance, outputs are mostly
  read by the Claude session, and there is no stopping rule or review loop. The baseline
  is about to be measured after the gold label fix (S116).
- **Decision (proposed):**
  1. Before the baseline, Florin reads answers in batches of 20 and notes the first failure
     in each, until two batches add no new failure mode.
  2. Failure modes live in one versioned labels file; each mode has a recorded fix route
     (prompt, code check, judge, ignore).
  3. Answer evals are binary checks, one per failure mode, each validated against Florin's
     labels before it can gate (see topic 4).
  4. Every new failure found later is promoted to the golden set through one script.
- **Options considered:** keep the 1-5 judge and add human calibration only; buy an
  off-the-shelf eval library with generic metrics; the proposal above.
- **Consequences:** more of Florin's time up front (about a day); judge prompts multiply
  (one per mode) but each is simpler and testable; the baseline reflects real failure
  modes; parking-lot items to add: stopping rule, promote script, trajectory matrix (after S9).

---

## Topic 2. Uncertainty basics (code UB)

**Status:** new (25 Nov 2026). All three pieces explained.

**Summary:** builders_lab already reports Wilson intervals; agentic-rag-lab reports none.
Neither lab knows the smallest change its golden set can detect, so small gains can be
read as real when they are noise.

### Piece 1: a score is an estimate

**Idea in plain words:** the golden set is a sample of all the questions users could ask.
A different 300 questions would give a slightly different score, even with the same
system. Report the score with its range, not as a single number.

**Formula:** standard error of a pass rate = sqrt(p × (1 − p) / n), where p is the pass rate
and n the number of questions. 95% confidence interval ≈ p ± 2 × SE.

**Worked example:** 85% on 300 questions → SE ≈ 2 points → 95% CI ≈ 81% to 89%. A new
prompt at 87% sits inside that range, so on its own it proves nothing.

| Official term | Meaning |
|---|---|
| **Sampling error** | The score moves because the questions are a sample. |
| **Standard error (SE)** | How big that movement is. Four times the questions halves it. |
| **Confidence interval (CI)** | The range the true score likely sits in; usually 95%. |
| **Wilson score interval** | The recommended CI formula for a pass rate; works on small groups and near 0% or 100%. |
| **Wald interval** | The textbook formula, p ± 1.96 × SE; fails on small groups and near 0% or 100% (e.g. 30/30 gives a zero-width range). |

### Piece 2: how big a change you can see

**Idea in plain words:** when old and new versions run on the same questions, most answers
stay the same. Only the answers that flip (wrong to right, right to wrong) carry the signal.
So the smallest gain you can reliably see depends on how many answers flip, not only on
how many questions you have.

**Worked example, 300 questions, 80% power, 5% false-alarm rate:**

| Share of answers that flip | Smallest gain you can reliably see |
|---|---|
| 5% | about 3.6 points |
| 10% | about 5 points |
| 20% | about 7 points |

A small prompt tweak flips few answers, so it is easier to measure. A model swap flips many,
so it needs a bigger gain to show. A 2-point gain on 300 questions cannot be confirmed by a
test: accept it only for a named reason (it fixes a known failure) plus a check that nothing
got worse (topic 7).

| Official term | Meaning |
|---|---|
| **Minimum detectable effect (MDE)** | The smallest real change the test would reliably catch. |
| **Statistical power** | The chance of catching a real change of a given size; usually planned at 80%. |
| **Significance level (alpha, α)** | The false-alarm rate you accept; usually 5%. |
| **Power analysis / sample size calculation** | Working out the MDE, or the n needed, before the experiment. |
| **Paired design** | The same questions run through both versions. |
| **Discordant pairs** | Questions whose result differs between the two versions. McNemar's test uses only these. |
| **Discordance rate** | The share of questions that are discordant pairs. |

**Search phrases:** "standard error of a proportion", "Wilson score interval", "power
analysis for McNemar test", "minimum detectable effect". Main source: Evan Miller,
[Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640) (uses the same terms).

### Piece 3: questions that are not independent

**Idea in plain words:** the formulas in pieces 1 and 2 assume each question is
independent. In a RAG golden set many questions come from the same source document, so
their results move together. Example: a parsing fix in one Approved Document flips 15
questions at once. The plain formula counts that as 15 pieces of evidence when it is one
event, so the interval is too narrow and the change looks more significant than it is.

**Size of the problem:** in Miller's examples the corrected (clustered) standard error was
1.9 to 3 times the plain one.

**Fix:** tag each golden question with its source document. Compute the interval by
resampling whole documents with replacement (cluster bootstrap), or with clustered standard
errors. For the same total size, many documents with few questions each give more evidence
than few documents with many questions each.

**Formula:** design effect ≈ 1 + (m − 1) × ICC, where m is the average number of questions
per document. Effective sample size = n / design effect. Example: 300 questions, 10 per
document, ICC 0.2 → design effect 2.8 → worth about 107 independent questions.

| Official term | Meaning |
|---|---|
| **Independence assumption** | Each result is unrelated to the others; the plain SE formula needs it. |
| **Cluster** | A group of results that move together; here, the questions from one source document. |
| **Intra-cluster correlation (ICC)** | How strongly results in the same cluster move together (0 = not at all, 1 = fully). |
| **Design effect (Kish)** | How much clustering inflates the variance compared with independent questions. |
| **Effective sample size** | How many independent questions the set is really worth: n / design effect. |
| **Clustered standard errors** | A standard error corrected for clusters. |
| **Cluster bootstrap** | Resample whole clusters with replacement many times; read the interval from the spread of results. |

**Search phrases:** "clustered standard errors", "cluster bootstrap", "design effect Kish",
"intra-cluster correlation". Source: Miller, Adding Error Bars to Evals (clustered SE section).
The design effect formula is standard survey statistics, not from the research notes.

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Every score reported with n and a 95% CI | **STRONG.** Wilson 95% intervals in experiment write-ups (e.g. L1 recall@5 0.62-0.73) and semcheck tables. | **MISSING.** No intervals seen. |
| 2 | Wilson (not Wald) for pass rates and small slices | **STRONG.** Wilson used. | **MISSING.** |
| 3 | MDE known for the golden set, from the measured discordance rate | **MISSING.** | **MISSING.** |
| 4 | Expected effect compared with MDE before an experiment | **MISSING.** | **MISSING.** |
| 5 | Intervals account for questions from the same document | **MISSING.** Wilson intervals assume independence (piece 3). | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| UB-1 | Add a Wilson 95% CI next to every pass rate and recall figure in experiment write-ups (`statsmodels` `proportion_confint(method="wilson")`) | ARL | 1-2 h | none | every results table shows n and a CI |
| UB-2 | Measure the discordance rate: count flipped answers in past A/B runs, and run one config twice to count flips from noise alone | BL, ARL | 2 h | none | a discordance rate and a noise flip rate written in the eval docs |
| UB-3 | Compute the MDE of each golden set from UB-2 and write it in the eval README | BL, ARL | 1 h | UB-2 | one line: "this set can detect about X points" |
| UB-4 | Add an "expected effect vs MDE" line to the experiment template | BL, ARL | 30 min | UB-3 | the template asks it before each run |
| UB-5 | Tag every golden question with its source document (`source_doc` field) and report questions per document | BL, ARL | 1-2 h | none | every golden item has `source_doc`; a count per document exists |
| UB-6 | Add a cluster bootstrap by source document to the metrics code; report it next to the plain Wilson CI and note the design effect | BL, ARL | 2-3 h | UB-5 | results tables show both intervals; MDE (UB-3) recomputed with clustering |
| UB-7 | When growing the golden set, prefer new documents over more questions on documents already covered | BL | ongoing | UB-5 | the golden brief says so |

### ADR seed (builders_lab): "Every score carries its margin of error"

- **Context:** experiment write-ups already show Wilson intervals, but the golden set's
  detectable effect is unknown, and intervals assume every question is independent.
- **Decision (proposed):** every reported score shows n and a 95% Wilson CI, plus a
  cluster bootstrap CI by source document; the eval README states the set's MDE (with
  clustering), recomputed when the set changes; each experiment states its expected effect
  and whether it is above the MDE before it runs; new golden questions favour documents not
  yet covered.
- **Options considered:** point estimates only; CIs without MDE; the proposal above.
- **Consequences:** fewer false wins from small gains; small prompt fixes are accepted on
  a named reason plus a non-inferiority check (topic 7) rather than a claimed gain; the
  golden set may need to grow where the MDE is too large for the decisions it must support.

---

## Topic 3. Paired comparisons, repeats and clustering (code PC)

**Status:** McNemar known; the rest new (25 Nov 2026). All three pieces explained.

**Summary:** both labs compare versions question by question with McNemar, and
agentic-rag-lab raises the bar when several pairs are compared. Missing: the right test for
graded scores, averaging repeated runs per question before testing, and grouping questions
by document inside the test.

### Piece 1: the right test for the type of score

**Idea in plain words:** McNemar fits yes/no results per question (pass/fail, found/not
found). For graded scores (1-5 judge scores, recall with several relevant sections, MRR,
pass rate averaged over runs) take the difference per question (new minus old) and test
whether the average difference is really above zero.

**Which test:**

| Score per question | Test |
|---|---|
| Yes/no, one run | McNemar (exact form when few questions flip) |
| Graded, or averaged over runs | Paired t-test or permutation test |
| Odd statistics (median, macro-F1) | Bootstrap, resampling questions or documents |
| Any | Not Wilcoxon or sign test: unreliable on these metrics |

**Evidence:** a simulation of over 500 million p-values on search metrics found the paired
t-test and permutation test keep false alarms at the stated rate even with 25-100
questions; Wilcoxon and sign tests did not (Urbano, Lima & Hanjalic 2019,
[arXiv 1905.11096](https://arxiv.org/abs/1905.11096); Smucker, Allan & Carterette 2007).

| Official term | Meaning |
|---|---|
| **McNemar's test** | Paired test for yes/no results; uses only the discordant pairs. |
| **Per-item differences** | New score minus old score, for each question. |
| **Paired t-test** | Tests whether the mean of the per-item differences is above zero. `scipy.stats.ttest_rel`. |
| **Permutation test (randomisation test)** | Randomly swap "old" and "new" per question thousands of times to see what difference chance alone gives. `scipy.stats.permutation_test`. |
| **Wilcoxon signed-rank test** | A rank-based paired test; avoid for these metrics. |

### Piece 2: repeated runs

**Idea in plain words:** the three runs of one question are linked; it is the same question.
Never count 3 × 300 runs as 900 results. Average each question's runs first (2 of 3 = 0.67),
then work across the 300 questions with a paired t-test or permutation test (McNemar no
longer fits once scores are fractions).

**Why more runs help less:** two sources of noise: which questions were picked, and the
model's randomness per question. Repeats only shrink the second. In Miller's example, two
runs remove a third of the total noise, four remove half, and no number of runs removes
more than two thirds. After 3-4 runs, more questions help more than more runs.

**Practical points:** keep the production temperature and repeat, rather than lowering
temperature to cut noise (it can shift the score itself). Questions that sometimes pass and
sometimes fail (flaky items) hold most of the noise and are good targets for prompt work.

| Official term | Meaning |
|---|---|
| **Repeated measures** | Several runs of the same item. |
| **Within-item variance** | Noise from the model's randomness on one question. |
| **Between-item variance** | Noise from which questions happened to be picked. |
| **Variance decomposition** | Splitting total noise into the two parts above. |
| **Flaky items** | Questions whose result changes across runs. (pass@k and pass^k: topic 8.) |

### Piece 3: clustering inside the test

**Idea in plain words:** a parser fix that repairs one Approved Document can flip 15
questions together. McNemar counts 15 flips and calls it highly significant, but it is one
event. Resample whole documents instead of single questions.

**Paired cluster bootstrap, step by step:**
1. For each question, compute new minus old.
2. Group the questions by source document.
3. Resample whole documents with replacement (keep all their questions); average the
   differences. Repeat a few thousand times.
4. The middle 95% of those averages is the interval for the gain. If it excludes zero, the
   gain holds with documents counted fairly.

**What it changes:** single-document changes (parser, chunking fixes) look less certain;
changes that help everywhere (a better reranker) barely move. If a gain vanishes under the
cluster bootstrap, it came from one or two documents: look at which.

| Official term | Meaning |
|---|---|
| **Paired cluster bootstrap** | Bootstrap of per-item differences, resampling whole clusters. |
| **Cluster-robust (clustered) standard errors** | The formula version of the same correction. |
| **Resampling unit** | What gets resampled; here the source document, not the question. |
| **Percentile interval** | The interval read from the middle 95% of bootstrap results. |

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Paired, question-by-question comparison | **STRONG.** McNemar in `evals/metrics.py`, used for L1/V1, J1 and every semcheck fix. | **STRONG.** McNemar is the house rule (`docs/experiments/README.md`). |
| 2 | Test matched to score type (t-test or permutation for graded) | **MISSING.** | **MISSING.** |
| 3 | Repeats averaged per question before testing | **MISSING for answers.** Judge re-run noise measured for semcheck (high flag flips 5.3% Fable, 1.4% Opus). | **SO-SO.** 3 rounds in E4/E14, "same pass in 3 of 3" reported; no per-question averaging in the test. |
| 4 | Flaky items listed and used as targets | **MISSING.** | **SO-SO.** Consistency reported; judge all-pass flipped on 12% of answers when re-judged. |
| 5 | Clustering by document inside the test | **MISSING.** | **MISSING.** |
| 6 | Effects read against measured noise | **STRONG.** Fix effects compared with judge noise. | **SO-SO.** McNemar bar rises with number of pairs (multiple comparisons: topic 6). |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| PC-1 | Add a `paired_test(old, new, kind)` helper: McNemar for yes/no, paired t-test and permutation test for graded or averaged scores | BL, ARL | 2-3 h | none | metrics code picks the test from the score type |
| PC-2 | Average repeated runs per question before any test; report per-question pass fraction | BL, ARL | 1-2 h | PC-1 | no test pools runs as separate results |
| PC-3 | List flaky items (pass in some runs, fail in others) in every experiment report | BL, ARL | 1 h | PC-2 | a "flaky items" section in the template |
| PC-4 | Paired cluster bootstrap by `source_doc` next to McNemar; flag gains that vanish under it and name the documents behind them | BL, ARL | 2-3 h | UB-5 | reports show both results; document-driven gains are named |
| PC-5 | Re-check one past parser or chunking fix with PC-4 | BL | 1 h | PC-4 | a note on whether its significance held |

### ADR seed (builders_lab): "Paired tests matched to the score, by document"

- **Context:** McNemar is used everywhere, including on scores that are not yes/no;
  repeated runs are not combined per question; many golden questions share a source
  document, so single-document fixes can look more significant than they are.
- **Decision (proposed):** McNemar for single-run yes/no results; paired t-test or
  permutation test for graded or averaged scores; runs averaged per question first; a
  paired cluster bootstrap by source document reported next to every comparison; flaky items
  listed in every report.
- **Options considered:** McNemar only; bootstrap only; the proposal above.
- **Consequences:** one helper decides the test, so write-ups stay consistent; some past
  "significant" single-document fixes may turn out uncertain; flaky items become an explicit
  input to prompt work.

---

## Topic 4. The judge as a classifier (code JC)

**Status:** labelling known; judge metrics partly new (25 Nov 2026). Four pieces explained;
piece 4 (designing the judge) is a **priority**.

**Summary:** both labs plan a human check of the judge but have not run it.
agentic-rag-lab measures judge-vs-judge kappa only; builders_lab checks semcheck precision
by hand. Neither reports how many real failures the judge catches, nor validates a rule for
combining two judges.

### Piece 1: the labelled set

**Idea in plain words:** treat the judge prompt like a model being trained, and split the
human labels the same way.

| Split | Share | Use |
|---|---|---|
| Train | 10-20% | Few-shot examples inside the judge prompt only |
| Dev | 40-45% | Change the judge prompt and re-check here |
| Test | 40-45% | Run once with the prompt frozen; only these numbers count |

**Size:** about 100-200 labels per criterion, with 30-50 failures in each of dev and test;
below about 60 labels the intervals are too wide (practitioner rules of thumb, Husain).
**Enough failures:** oversample suspected failures (low scores, judge disagreements) for
judge validation; do not use that enriched set to estimate the real pass rate.
**Who:** one domain expert labels pass/fail per criterion with a short reason; a second
person labels a shared subset to measure human-human agreement, the ceiling for any judge.

| Official term | Meaning |
|---|---|
| **Gold labels / ground truth** | The human verdicts the judge is compared with. |
| **Train / dev (validation) / test split** | Separate label sets for examples, tuning and final measurement. |
| **Held-out test set** | Labels never used while tuning the judge. |
| **Stratified sampling / oversampling the minority class** | Picking extra rare cases (failures) on purpose. |
| **Inter-annotator agreement** | How well two human labellers agree. |
| **Annotation guidelines** | The written rules labellers follow. |

### Piece 2: the metrics

**Confusion matrix** (positive = "fail"):

| | Human: fail | Human: pass |
|---|---|---|
| **Judge: fail** | True positive (caught failure) | False positive (false alarm) |
| **Judge: pass** | False negative (missed failure: the dangerous one for a gate) | True negative (correct pass) |

**Numbers to report, each with a 95% CI, from the test set only:** true positive rate, true
negative rate, precision on "fail", Cohen's kappa; plus self-consistency (judge run twice)
and the human-human kappa as the ceiling.
**Why raw agreement misleads:** with 5% failures, a judge that always passes agrees 95% of
the time and catches nothing. 90% agreement when both say "pass" 85% of the time is kappa ≈ 0.61.
**1-5 scores:** the pass threshold is a classifier cut-off. On dev, compare TPR/TNR for
"≥ 4" vs "≥ 3", pick by error cost, lock it before the test set.

| Official term | Meaning |
|---|---|
| **Confusion matrix** | The four-box table above. |
| **True positive rate (sensitivity, recall)** | Share of real failures the judge catches. |
| **True negative rate (specificity)** | Share of good answers the judge passes. |
| **False positive / false negative** | False alarm / missed failure. |
| **Precision** | When the judge says "fail", how often it is right. |
| **Cohen's kappa** | Agreement corrected for chance. |
| **Base rate (class imbalance)** | How common failures are; drives why raw agreement misleads. |
| **Decision threshold** | The score cut-off that turns 1-5 into pass/fail. |
| **Test-retest reliability (self-consistency)** | Same verdict when the judge runs again. |

### Piece 3: judge biases and combining two judges

**Biases:** position, verbosity (length), self-preference, leniency (good at spotting good
answers, weak at spotting bad ones), being misled by confident wrong answers.
**Fixes with evidence:** reference-guided grading (maths: wrong answers accepted 70% plain
→ 15% with a reference, Zheng et al. 2023); reasoning before the verdict (for grounding:
list each claim and its passage first); one judge per criterion, pass/fail; an "unknown"
option; for A-vs-B tests swap order and allow ties.
**Two judges:** choose a rule: fail if either fails (more caught, more false alarms); fail
only if both fail (the reverse); agree = automatic, disagree = human. Each rule is its own
classifier: measure its TPR/TNR on the test set and pick by error cost (regulated content:
missed failures usually cost more). Report each judge separately to spot drift. High
disagreement on one criterion often means the criterion is unclear.
**Re-validation:** any change to judge model, prompt or scale resets its error rates;
re-run the frozen test set before it gates again.

**Real-world numbers:** published judge validations, thresholds and pass rates (Shopify,
legal benchmarks, Visa, HealthBench, Mayo Clinic, Nubank, and negative results) are in
`notes/llm-judge-case-studies/case_studies.md`. Short version: narrow binary checks
reach 85-93% agreement with experts (kappa 0.7-0.85); broad criteria kappa 0.4-0.7; almost
nobody publishes a fixed "pass >= X%" release gate.
UK government practice (`notes/uk-government-ai-evals/notes.md`): i.AI Consult sets the bar at
human-human agreement (F1 0.82 vs 0.71 between reviewers) and gates CI on regression
(tolerance max(0.05, 3 x stdev) over 3+ baseline runs), marking judge errors INVALID;
GOV.UK Chat's judge labels each fact matched / unsupported / missing and code computes the
scores. No UK team publishes a fixed judge pass-rate gate.

| Official term | Meaning |
|---|---|
| **Position bias** | Favouring the first or second answer in a comparison. |
| **Verbosity (length) bias** | Favouring longer answers. |
| **Self-preference (self-enhancement) bias** | Favouring outputs of its own model family. |
| **Leniency bias** | Passing too much. |
| **Reference-guided grading** | Judging against a reference answer. |
| **LLM jury / panel of LLM evaluators (PoLL)** | Several judges combined (Verga et al. 2024). |
| **Aggregation rule** | How several judges' verdicts become one. |
| **Judge drift / re-validation** | Judge error rates changing over time / re-measuring them. |

### Piece 4: designing the judge (PRIORITY)

*Added after Florin's question, 25 Nov 2026: "the grading system is such a black box".*
**Priority** with topic 11.

**1. Say exactly what is graded (the rubric).** One criterion per judge; a yes/no question;
written pass and fail definitions with a real example of each. Example: "Grounding: is every
claim in the answer supported by the given passages? Fail if any claim has no supporting
passage." If a scale is kept, describe each level with an example (anchored rubric). An
undefined 1-5 scale is the black box.

**2. Give the judge what it needs to decide.**

| Criterion | Inputs the judge gets | Method |
|---|---|---|
| Grounding | Answer + the passages actually given to the generator | Split the answer into claims; check each claim against the passages |
| Correctness | Answer + reference answer or list of required facts | Check each required fact is present and not contradicted (maths study: wrong answers accepted 70% → 15% with a reference) |
| Refusal / scope | Question type + expected behaviour | Did it decline, ask back, or answer as expected? |
| Safety rules (BL) | Answer + the rule text (asbestos, approvals) | Rule-by-rule check; code where possible |

Reasoning first, verdict last, structured output (JSON); 2-3 labelled examples from the train
split as few-shot.

**3. Don't overload the judge.** One judge per criterion (not three criteria in one call);
one judge per system part (retrieval: was the context sufficient? answer: grounded and
correct? safety: rules followed?); route by question type (refusal questions to the refusal
check, answerable ones to correctness and grounding); give each judge only the passages it
needs (judges degrade on long inputs).

**4. One judge or a jury?** A jury is several judges, usually from different model families,
scoring the same criterion, combined by vote. It cuts own-family bias and random noise. Three
small judges beat one GPT-4 judge on agreement with humans at 7-8x lower cost (Verga et al.
2024). Use one good judge plus code for facts with a reference or rules code can check; use a
jury of three (no ties) for subjective, high-stakes criteria. Either way, validate it on the
labels (pieces 1-2).

| Official term | Meaning |
|---|---|
| **Rubric (analytic vs holistic)** | Written grading criteria; analytic = one score per criterion, holistic = one overall score. |
| **Anchored rating scale** | Each scale level described with a concrete example. |
| **Claim decomposition** | Splitting an answer into separate factual claims. |
| **Claim-level faithfulness** | Each claim checked against the sources (as in RAGAS faithfulness). |
| **Nugget-based evaluation** | Checking an answer for a list of required facts ("nuggets"). |
| **Reference-guided grading** | Grading against a reference answer. |
| **Structured output** | Judge returns fixed fields (reasoning, verdict) as JSON. |
| **Few-shot calibration examples** | Labelled examples placed in the judge prompt. |
| **Component-level evaluation** | Separate evals for retrieval, answer, safety, rather than one end-to-end score. |
| **Routing by question type** | Sending each question to the checks that fit its type. |
| **LLM jury / PoLL, majority vote** | Several judges combined by vote. |

### Lessons from published UK government judge prompts

*Read 25 Nov 2026 from the public repos `i-dot-ai/consult` (folder `themefinder/evals/`)
and `alphagov/govuk-chat-evaluation`. Details in `notes/uk-government-ai-evals/notes.md`.*

| # | Lesson | Where seen | Use in builders_lab |
|---|---|---|---|
| 1 | Their design notes list the old judge's faults (0-5 scale "too granular", no reasoning, no shuffling) and the fixes: shuffle order, binary verdicts, variance across runs, reasoning first | Consult `evals/docs/llm-judge-improvements.md` | Same fixes as our judge-design priority: evidence a real team hit the same problems |
| 2 | Atomic tasks: one item against a candidate list, PASS or FAIL, not a whole set scored at once | Consult `prompts/binary_match.md` | One judge per criterion, one answer at a time |
| 3 | Quote the evidence verbatim: on PASS return the exact matching items, "do not paraphrase, shorten, combine, or invent" | Consult `binary_match.md` | Grounding judge quotes exact passage text; code checks each quote exists in the retrieved passages; a missing quote makes the verdict INVALID |
| 4 | One calibration example per verdict level, with reasoning | Consult `prompts/generation.md` (STRONG / PARTIAL / NO) | Anchored rubric: one real builders example per verdict |
| 5 | Judge sorts facts, code does the maths: key facts go to TP (in both), FP (answer only), FN (reference only); precision and recall computed in code; three worked examples incl. "fission vs fusion" = one FP + one FN | GOV.UK Chat `factual_precision_recall/template.py` | Correctness judge sorts facts against `required_facts`; any FP on a safety topic fails the case |
| 6 | Contradictions as a separate three-step check: extract claims from the answer, extract truths from the reference, verdict per claim | GOV.UK Chat `absence_of_factual_contradictions/template.py` | Separate contradiction check (claim decomposition) |
| 7 | Strict output: JSON only, exact shape, schema; invalid JSON retried, then marked INVALID, never counted as a fail | Both repos (`invalid_json_retry.py`) | Validate judge JSON in code; report INVALID separately |
| 8 | Survivorship: share of AI suggestions reviewers keep unchanged (73% in the DWP trial) as a cheap real-world quality signal | Consult evaluation report | Later, with users: share of drafts sent without edits |
| 9 | The bar is human-human agreement, not a fixed number (F1 0.82 judge vs 0.71 between reviewers) | Consult DWP evaluation | Measure two-human agreement on part of the golden set (JC-3) and report the judge next to it |

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Human labels split train/dev/test for the judge | **MISSING for answers.** Planned (Opus vs Sonnet on 10%, ~15 pairs for Florin, branch briefs). | **MISSING.** Hand check of 40 answers designed (ADR 0007), not done. |
| 2 | Enough failures in the labelled set | **MISSING.** | **MISSING.** |
| 3 | TPR, TNR, precision, kappa vs humans, with CIs | **SO-SO.** Semcheck precision only (94%, n = 50); answer judge none. | **SO-SO.** Judge-vs-judge kappa only (E4: correctness 0.73, grounding 0.41). |
| 4 | Self-consistency measured | **STRONG for semcheck.** High flag flips 5.3% (Fable), 1.4% (Opus). | **STRONG.** All-pass flipped on 12% when re-judged. |
| 5 | Human-human agreement as the ceiling | **MISSING.** | **MISSING.** |
| 6 | Threshold chosen on dev by error cost | **MISSING.** Fixed ≥ 4. | **MISSING.** Fixed ≥ 4. |
| 7 | Bias fixes (reference, reasoning first, per-criterion) | **SO-SO.** Gold sections given; 1-5 × 3 in one call. | **SO-SO.** Same. |
| 8 | Two-judge rule chosen and validated | **MISSING.** | **MISSING.** Two families used, no validated rule. |
| 9 | Re-validation on judge change | **SO-SO.** Opus noise re-measured on judge switch. | **SO-SO.** ADR 0007 asks for a human re-check on judge change. |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| JC-1 | Write short annotation guidelines per criterion (pass/fail + reason) | BL, ARL | 1-2 h | EA-4 (criteria) | a guidelines file per criterion |
| JC-2 | Label 100-200 answers per criterion, oversampling suspected failures; split 15/42/43 train/dev/test | BL first | 1-2 days of Florin's time | JC-1 | a labels file with split field |
| JC-3 | Second labeller (or a second pass weeks later) on ~30 shared items; compute human-human kappa | BL | 2-3 h | JC-2 | ceiling kappa recorded |
| JC-4 | Judge report: confusion matrix, TPR, TNR, precision, kappa with CIs, self-consistency, from test only | BL, ARL | 2-3 h | JC-2 | one report per judge version |
| JC-5 | Choose the 1-5 threshold on dev by TPR/TNR and error cost; lock it | BL, ARL | 1 h | JC-4 | threshold and reason in the eval docs |
| JC-6 | Choose and validate the two-judge rule (either-fails / both-fail / disagree-to-human) | BL, ARL | 2 h | JC-4 | rule with its own TPR/TNR recorded |
| JC-7 | CI step: re-run the frozen test set on any judge model, prompt or scale change; block if TPR or TNR falls outside the old interval | BL | 2-3 h | JC-4 | the check runs in CI |
| JC-8 | **(priority)** Write a rubric per criterion: yes/no question, pass and fail definitions, one real example each; retire the undefined 1-5 scale | BL, ARL | 2-3 h | EA-4 | one rubric file per criterion, versioned |
| JC-9 | **(priority)** Grounding judge reads the passages actually given to the generator and checks claim by claim | BL | 3 h | JC-8 | judge output lists each claim with its passage or "unsupported" |
| JC-10 | **(priority)** Correctness judge checks a list of required facts per golden item (add a `required_facts` field) | BL | 3-4 h + labelling | JC-8 | each golden answerable item has required facts |
| JC-11 | **(priority)** Split judges by system part (retrieval sufficiency, answer, safety) and route by question type | BL | 3 h | JC-8 | a routing table: question kind → checks |
| JC-12 | Decide one judge vs jury per criterion: one judge + code for referenced facts and rules; jury of three for subjective, high-stakes criteria; validate whichever is chosen | BL | 2 h | JC-4 | decision per criterion recorded |
| JC-13 | **(priority)** Quote-and-verify: judges return verbatim evidence; code checks each quote against the retrieved passages; a missing quote makes the verdict INVALID | BL | 2-3 h | JC-9 | INVALID count reported per run |
| JC-14 | **(priority)** Correctness as fact sorting (TP / FP / FN against `required_facts`), scores computed in code; any FP on safety topics fails | BL | 3 h | JC-10 | precision and recall per answer, from code |
| JC-15 | Shuffle passage and candidate order in every judge call; strict JSON schema with one retry, then INVALID | BL, ARL | 1-2 h | JC-8 | shuffling and schema check in the judge wrapper |
| JC-16 | Planted judge tests: tiny cases with known verdicts (one clear pass, one clear fail per criterion) run against the real judge model in CI | BL | 2 h | JC-8 | planted cases pass before any eval run |

### ADR seed (builders_lab): "The answer judge is validated as a classifier before it gates"

- **Context:** the answer judge scores 1-5 on three criteria with a fixed ≥ 4 threshold and
  has no human check; semcheck has precision only; two judge families are used without a
  validated combining rule.
- **Decision (proposed):** each criterion has a written rubric and its own judge, given the
  inputs it needs (passages for grounding, required facts for correctness), routed by question
  type and system part; one judge plus code for referenced facts, a jury of three for
  subjective high-stakes criteria; Florin labels 100-200 answers per criterion (train/dev/test);
  the judge gates only after its test-set TPR, TNR and kappa are reported with intervals;
  threshold and two-judge rule are chosen on dev by error cost (missed failures weigh more);
  any judge change re-runs the frozen test set in CI.
- **Options considered:** trust the judge as is; judge-vs-judge agreement only; the
  proposal above.
- **Consequences:** a day or two of Florin's labelling; judge numbers become trustworthy
  and comparable across versions; enables the pass-rate correction (topic 5).

---

## Topic 5. Correcting the judge's pass rate (code CR)

**Status:** written down, not discussed (25 Nov 2026).

**Summary:** once the judge's error rates are known (topic 4), its raw pass rate can be
corrected. builders_lab applies a crude correction (rate × precision) that ignores missed
failures; agentic-rag-lab applies none.

### Piece 1: the correction

**Idea in plain words:** a judge that misses some failures reports too high a pass rate; a
judge that raises false alarms reports too low a rate. Knowing both error rates, you can work
back to the true rate, with an interval that includes the uncertainty in those error rates.

**Formula (positive = "pass" here):** true pass rate = (observed pass rate + TNR − 1) /
(TPR + TNR − 1), where TPR is the share of good answers the judge passes and TNR the share of
bad answers it fails. Works only if TPR + TNR > 1 (judge better than chance); unstable when
close to 1.
**Worked example:** observed 82%, TPR 0.90, TNR 0.70 → (0.82 + 0.70 − 1) / (0.90 + 0.70 − 1)
= 0.52 / 0.60 ≈ 87%. With other error rates the correction can go down instead. Report:
"judge pass rate 82%, corrected 87% [95% CI a-b]".
**Interval:** bootstrap it (the `judgy` library), or use the closed form of Lee et al. 2025.
About 200 calibration labels give an interval under 10 points wide for a moderately good
judge. In their simulation, uncorrected intervals almost never contained the true rate;
corrected ones did about 95% of the time.
**Assumption:** the judge's error rates on production answers equal those on the labelled
set. A new generator, new question types or a new judge break it: re-validate (topic 4).
**Graded scores:** prediction-powered inference (PPI) does the same for means: a small
random human-labelled sample corrects many judge scores. PPI needs a random sample; the
formula above accepts an enriched (failure-heavy) labelled set.

| Official term | Meaning |
|---|---|
| **Rogan-Gladen estimator** | The correction formula above (from epidemiology: true prevalence from an imperfect test). |
| **Misclassification bias** | The error in a rate measured by an imperfect classifier. |
| **Prevalence estimation** | Estimating how common something is from imperfect labels. |
| **Prediction-powered inference (PPI)** | Combines many model labels with a few human labels for valid intervals on any mean. |
| **Calibration set** | The human-labelled items used to measure the judge's error rates. |

**Sources:** [judgy](https://github.com/ai-evals-course/judgy); Lee et al. 2025,
[arXiv 2511.21140](https://arxiv.org/abs/2511.21140); Angelopoulos et al. 2023,
[PPI](https://arxiv.org/abs/2301.09633).

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Pass rate corrected for both judge error rates | **SO-SO.** "rate × 0.94" in `P-semantic-validation.md`: uses precision only, ignores misses. | **MISSING.** |
| 2 | Corrected rate reported with an interval | **MISSING.** | **MISSING.** |
| 3 | Gate reads the corrected rate | **MISSING.** | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| CR-1 | Run `judgy` on each validated judge; report raw and corrected pass rates with CIs | BL, ARL | 2 h | JC-4 | both numbers in every eval report |
| CR-2 | Replace "rate × precision" in the semcheck write-up with the full correction | BL | 1 h | a sample of semcheck "ok" pages checked by hand (its missed-failure rate) | semcheck rates corrected both ways |
| CR-3 | Gate on the corrected rate (lower CI bound) | BL | 1 h | CR-1, topic 7 | gate code reads the corrected rate |

### ADR seed (builders_lab): "Gates read the corrected judge pass rate"

- **Context:** judge pass rates are reported raw; the semcheck correction uses precision only.
- **Decision (proposed):** every judge-based rate is reported raw and corrected (Rogan-Gladen,
  bootstrap CI) using the judge's test-set error rates; gates use the corrected rate.
- **Options considered:** raw rates; precision-only scaling; the proposal above.
- **Consequences:** needs a validated judge first (topic 4); numbers can move up or down;
  re-validation is required whenever the generator or judge changes.

---

## Topic 6. Many variants and held-out hygiene (code MV)

**Status:** written down, not discussed (25 Nov 2026).

**Summary:** agentic-rag-lab already raises the bar when several pairs are compared and has
a held-out gate set. builders_lab has a held-out list that has never been run and no
correction for many comparisons.

### Piece 1: trying many variants inflates the winner

**Idea in plain words:** try 20 prompt variants on the same 300 questions and keep the best:
even if none is really better, the best one looks better by chance. Each extra comparison
is another chance of a false win.
**Numbers:** 20 tests at a 5% false-alarm rate → 64% chance of at least one false win. On
300 paired questions, the best of 20 useless variants shows about +3.4 points by chance.
In IR research an estimated 40-50% of uncorrected significance claims are false (Otero et
al. 2025).
**Fixes:** Holm correction when comparing several variants with a baseline; Tukey HSD for
all pairs; write the comparison plan (metric, slices, test) before running; confirm the
winner once on held-out questions.

| Official term | Meaning |
|---|---|
| **Multiple comparisons problem** | More tests, more false wins. |
| **Family-wise error rate (FWER)** | Chance of at least one false win across a set of tests. |
| **Bonferroni / Holm correction** | Stricter thresholds per test; Holm is the less strict, still valid version. `statsmodels.stats.multitest.multipletests`. |
| **Tukey HSD** | Correction for comparing every pair. |
| **Winner's curse** | The chosen best variant's score is biased upwards. |
| **Garden of forking paths / p-hacking** | Choosing metric, slice or test after seeing the data. |
| **Pre-registration** | Writing the analysis plan before running. |

### Piece 2: held-out hygiene

**Idea in plain words:** tune on dev; look at the test set rarely. Each time you look at the
test set and change something because of it, it becomes part of tuning and loses value.
**Rules:** dev for iteration, test touched once per decision; track the dev-test gap (a large
gap means overfitting to dev); refresh and grow the test set over time. Test set size for a
single score: about 200 questions for ±5 points, about 545 for ±3 points.

| Official term | Meaning |
|---|---|
| **Overfitting to the dev set** | Improvements that do not carry over to unseen questions. |
| **Adaptive overfitting / test-set reuse** | Wearing out a holdout by looking at it repeatedly. |
| **Reusable holdout** | Methods that limit what each look reveals (Dwork et al. 2015). |
| **Dev-test gap** | Score on dev minus score on test; a warning sign when large. |

**Sources:** Otero et al. 2025, [arXiv 2501.03930](https://arxiv.org/abs/2501.03930);
Google Research, [The reusable holdout](https://research.google/blog/the-reusable-holdout-preserving-validity-in-adaptive-data-analysis/);
Sakai, IR significance testing tutorial (Tukey HSD).

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Correction when comparing several variants | **MISSING.** | **STRONG-ish.** McNemar bar rises with number of pairs (~7 flips for six pairs). |
| 2 | Plan written before the run | **SO-SO.** One change at a time per experiment file. | **STRONG.** E15: 40 exact-term questions written before the run. |
| 3 | Held-out test set, used rarely | **SO-SO.** `holdout-ids.txt` exists, never run; decomposer split 60 tune / 30 check. | **STRONG.** `golden/gate-holdout.jsonl`. |
| 4 | Dev-test gap tracked | **MISSING.** | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| MV-1 | Add Holm correction to the comparison helper when more than one variant is compared | BL, ARL | 1 h | PC-1 | helper reports adjusted p-values |
| MV-2 | Add a "plan" block to the experiment template: metric, slices, test, number of variants, decided before the run | BL | 30 min | none | template has it |
| MV-3 | Run the builders_lab holdout once, for the baseline; log each later use | BL | 1 h | label fix (S116) | holdout result and usage log exist |
| MV-4 | Report dev and test scores side by side and the gap | BL, ARL | 1 h | MV-3 | gap shown in reports |

### ADR seed (builders_lab): "Tuning on dev, confirming on a holdout"

- **Context:** experiments change one thing at a time, but several variants are sometimes
  compared without correction; the holdout has never been run.
- **Decision (proposed):** comparisons of several variants use Holm; each experiment states
  its plan before running; the holdout confirms the chosen variant once per decision and
  every use is logged; dev-test gap reported.
- **Options considered:** no holdout; uncorrected comparisons; the proposal above.
- **Consequences:** fewer false wins; holdout needs refreshing as it is used.

---

## Topic 7. Gates: "not worse beyond a margin" (code NI)

**Status:** written down, not discussed (25 Nov 2026).

**Summary:** both labs use fixed thresholds or informal "no clear change" readings. Neither
measures its noise floor with an A/A run or gates on the paired difference with a margin.

### Piece 1: non-inferiority gates

**Idea in plain words:** a gate that blocks on any drop fires on pure noise (about 1 run in
20 at a 5% false-alarm rate). Instead, block a change only if the lower end of the paired
difference's 95% interval falls below a set margin, for example −2 points. The margin comes
from measured noise, not intuition.
**How to set the margin:** run the same config twice (an A/A run) and measure how much the
score and the per-question results move. The margin must be larger than that noise and
smaller than a drop you would care about. Gate per segment (question type, document family),
not only on the average.
**Check what the set can confirm:** a 100-question holdout can only confirm large changes
(roughly 6-9 points paired); grow it if decisions need finer gates.
**Two kinds of gate:** absolute floors (recall@5 ≥ 90%) answer "is it good enough?";
non-inferiority answers "did this change make it worse?". Keep both: a floor on the corrected
rate's lower bound (topic 5) plus a non-inferiority check against the last release.

| Official term | Meaning |
|---|---|
| **Non-inferiority test** | Tests that the new version is not worse than the old by more than a margin. |
| **Non-inferiority margin (delta)** | The largest drop you accept as "not worse". |
| **Equivalence test (TOST)** | Tests that two versions are the same within a margin both ways. |
| **A/A test** | The same config run twice, to measure noise. |
| **Noise floor / flip rate** | How much results change between identical runs. |
| **Per-segment gate** | A gate per question type or document family. |

**Sources:** thin in the LLM literature; general statistics texts on non-inferiority and
equivalence testing; Miller 2024 for the paired interval.
**Real example:** i.AI Consult's CI gate checks regression against a baseline from 3+ runs,
with tolerance max(0.05, 3 x stdev), and marks judge errors INVALID
(`notes/uk-government-ai-evals/notes.md`). GOV.UK Chat's rule: a change must improve one
criterion without making the others worse.

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Noise floor measured (A/A run) | **SO-SO.** Judge re-run noise for semcheck; no A/A of the full pipeline. | **SO-SO.** Judge re-judging flip 12%; no A/A of the pipeline. |
| 2 | Gate on the paired difference with a margin | **MISSING.** | **SO-SO.** Design 07 flags a fall of 2+ per question; E21 read as "not clear". |
| 3 | Gates per segment | **MISSING.** | **MISSING.** |
| 4 | Absolute floor on a corrected rate | **MISSING.** | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| NI-1 | A/A run of the full pipeline; record score movement and per-question flip rate | BL, ARL | 2 h | none | noise floor in the eval docs (feeds UB-2) |
| NI-2 | Set a non-inferiority margin per key metric from NI-1 | BL | 1 h | NI-1 | margins written with their reason |
| NI-3 | Gate code: block if the lower CI bound of the paired difference < −margin, per segment | BL | 3 h | PC-1, NI-2 | gate runs on each release candidate |
| NI-4 | Keep absolute floors, on the corrected rate's lower bound | BL | 1 h | CR-1 | floors read corrected rates |
| NI-5 | Consult-style regression gate as a first step: baseline from 3+ runs; fail if a metric drops by more than max(0.05, 3 x run-to-run stdev); judge or evaluator errors mark the run INVALID, not failed | BL | 2-3 h | NI-1 | gate in CI with INVALID kept separate |

### ADR seed (builders_lab): "Release gates test non-inferiority with a measured margin"

- **Context:** fixed thresholds fire on noise and say nothing about whether a change made
  things worse; the noise floor of the pipeline is unknown.
- **Decision (proposed):** measure the noise floor with an A/A run; gate each change on the
  paired difference (lower 95% bound above −margin) per segment; keep absolute floors on
  corrected rates.
- **Options considered:** fixed thresholds only; any drop blocks; the proposal above.
- **Consequences:** fewer false blocks; margins need re-measuring when the pipeline changes;
  small sets may need to grow for tight margins.

---

## Topic 8. Agent reliability: pass^k and flaky items (code AR)

**Status:** new; worth using (25 Nov 2026). One piece, explained.

**Summary:** both labs already run questions several times, so the data exists.
agentic-rag-lab reports "same pass in 3 of 3" (close to pass^3) and names pass^k as a gap;
builders_lab has no per-answer repeats yet.

### Piece 1: pass@k, pass^k, flaky items, capability vs regression

**Idea in plain words:** a single-run pass rate hides reliability. A task that passes 90% of
the time fails at least once in eight runs more often than not.

| Measure | Question | Fits | As k grows |
|---|---|---|---|
| **pass@k** | Does at least one of k attempts succeed? | Retries allowed, or a person picks the best draft | Goes up |
| **pass^k** | Do all k attempts succeed? | Agent must work every time (payment dates, notices) | Goes down |

**Worked example:** pass rate 0.9 → pass^8 = 0.9^8 ≈ 0.43. On tau-bench the best mid-2024
agents were below 25% on pass^8 (Yao et al. 2024).
**Per-question buckets from 3 runs:** always passes (3/3, solid); never passes (0/3, stable
failure, easy to study); sometimes passes (1-2/3, flaky: most of the noise, shows fragile
prompts or tools).
**Capability vs regression evals:** capability = hard tasks mostly failed today (a hill to
climb); regression = tasks already passed, must stay near 100%. A capability task that passes
reliably moves to regression. Report the two separately so gains on hard tasks cannot hide
drops on easy ones.

| Official term | Meaning |
|---|---|
| **pass@k** | Chance at least one of k attempts succeeds. |
| **pass^k (pass-hat-k)** | Chance all k attempts succeed. |
| **Flaky items (non-deterministic failures)** | Items whose result changes across runs. |
| **Capability evals** | Hard tasks that measure progress. |
| **Regression evals** | Passed tasks that guard against breakage. |
| **Reliability / consistency** | Same result across repeated runs. |

**Sources:** Yao et al. 2024, [tau-bench](https://arxiv.org/abs/2406.12045); Anthropic,
[Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents).

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Repeated runs per answer | **MISSING for answers.** Judge re-runs only (semcheck). | **STRONG.** 3 rounds in E4/E14. |
| 2 | pass^k reported where reliability matters | **MISSING.** | **SO-SO.** "Same pass in 3 of 3"; pass^k named as a gap. |
| 3 | Flaky items listed | **MISSING.** | **SO-SO.** Consistency reported, items not listed as targets. |
| 4 | Capability and regression sets reported separately | **MISSING.** | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| AR-1 | Run each golden answer 3 times; report pass^3 and the always / never / flaky buckets | BL, ARL | 2 h code + run cost | PC-2 | buckets in every answer eval report |
| AR-2 | Tag golden items `capability` or `regression`; report the two separately; move items when they pass 3/3 on two releases | BL | 1-2 h | AR-1 | two scores per report |
| AR-3 | Use pass^3 for must-work flows (payment dates, delay notices, asbestos and approval rules) | BL | 1 h | AR-1 | gate lists which flows use pass^3 |

### ADR seed (builders_lab): "Must-work flows are judged on pass^k"

- **Context:** answers are scored on one run; some flows (payment dates, notices, safety
  rules) must work every time.
- **Decision (proposed):** answer evals run 3 times; must-work flows gate on pass^3; flaky
  items are listed in every report; capability and regression sets are reported separately.
- **Options considered:** single run; average of runs only; the proposal above.
- **Consequences:** 3x run cost for answer evals; reliability becomes visible; flaky items
  feed prompt work.

---

## Topic 11. Prompt experiments and abstention (code PE)

**Status:** partly known: abstention by question type yes, three-way scoring new.
**PRIORITY** (Florin, 25 Nov 2026): not only for builders_lab: this is how to eval any
prompt or agent. See action PE-6.

**Summary:** builders_lab already scores "NOT IN SOURCES" by question type and tunes the
decomposer on a fixed split; agentic-rag-lab ablated one prompt (E14, no effect). Missing:
three-way scoring with a cost for wrong answers, coverage, systematic rule ablation, a
migration checklist.

### Piece 1: a prompt change is an experiment

**Loop:** read traces, count failure types (topic 1) → pick the top one, write a hypothesis
("adding X fixes failure Y") → one change only → old vs new on dev, question by question
(topic 3) → keep only if Y improves and nothing else gets worse (topic 7) → test set at the
end (topic 6). Log per run: prompt version, model, settings, dataset version, hypothesis,
per-question scores.
**Sensitivity:** formatting alone moved one model's accuracy by up to 76 points (Sclar et al.
2023); few-shot order can swing from near best to near random (Lu et al. 2022). Frontier
models are more robust, not immune: a 2-3 point change on 300 questions is inside the noise.
**Bloat:** instruction-following falls as rules grow; best models about 68% with 500 rules,
favouring earlier ones (IFScale 2025). Fix: ablation, remove one section at a time and re-run
dev; every rule names the failure it fixes and the eval items that show it.
**Automatic optimisers** (DSPy MIPROv2, GEPA): need a validated metric and 50-200+ labels;
they exploit judge biases. Parked until topic 4 is done.

| Official term | Meaning |
|---|---|
| **Ablation (study)** | Removing one part at a time to see what it contributes. |
| **Prompt sensitivity (brittleness)** | Scores moving with changes that should not matter. |
| **Spurious features** | Formatting, order, wording details that move scores. |
| **Prompt bloat (instruction overload)** | Too many rules; later ones get ignored. |
| **Experiment tracking** | Logging every run with its exact configuration. |
| **Hypothesis-driven iteration** | Each change tests one stated hypothesis. |
| **Automatic prompt optimisation** | Tools that search prompt variants against a metric. |

### Piece 2: scoring "I don't know", and model upgrades

**Problem:** accuracy-only scoring rewards guessing. On SimpleQA one model abstained 52% with
26% errors; another abstained 1% with 75% errors, at similar accuracy (OpenAI 2025).
**Fix:** score right / wrong / abstained, wrong costing more than abstained; report coverage
(share answered) and accuracy on answered questions; include questions the sources cannot
answer, or abstention is never rewarded.
**Confidence:** stated confidence ("90% sure") is overconfident; agreement across several
runs is a better signal.
**Migrations:** same golden set and pinned judge, compared per question; read every
pass→fail flip; fresh error analysis; newer Claude models follow instructions literally, so
old emphatic rules ("CRITICAL: you MUST") cause over-reaction: often the fix is removing rules.

| Official term | Meaning |
|---|---|
| **Abstention** | The model declines to answer. |
| **Selective prediction** | Answering only when confident enough. |
| **Coverage** | Share of questions answered. |
| **Selective accuracy** | Accuracy on the answered questions only. |
| **Risk-coverage curve** | Error rate against coverage as the abstain threshold moves. |
| **Asymmetric scoring** | Wrong answers penalised more than abstentions. |
| **Verbalised confidence** | Confidence the model states in words. |
| **Self-consistency** | Agreement across several sampled answers. |
| **Migration eval** | The eval run when changing model or provider. |

**Sources:** Sclar et al. 2023, [arXiv 2310.11324](https://arxiv.org/abs/2310.11324);
IFScale, [arXiv 2507.11538](https://arxiv.org/abs/2507.11538); OpenAI,
[Why language models hallucinate](https://openai.com/index/why-language-models-hallucinate/);
Anthropic prompting best practices; DSPy optimiser docs.

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | One change per hypothesis, per-question scores logged | **STRONG.** Experiments one change at a time; decomposer drafts d1-d3 on a fixed 60/30 split. | **SO-SO.** Experiment files per change; per-question logging partial. |
| 2 | Rule ablation | **MISSING.** | **SO-SO.** E14 ablated one prompt fix (no effect). |
| 3 | Three-way scoring with a cost for wrong | **SO-SO.** "NOT IN SOURCES" scored by question kind (J1: answerable 0.58 → 0.09; out_of_scope pass 0.85). | **SO-SO.** Outcome check; out-of-scope declines rare (Sonnet 47%, GPT-OSS 17%). |
| 4 | Coverage and selective accuracy reported | **MISSING.** | **MISSING.** |
| 5 | Unanswerable questions in the golden set | **STRONG.** negative / out_of_scope / underspecified kinds. | **STRONG.** negative and out-of-scope kinds. |
| 6 | Migration checklist | **MISSING.** | **MISSING.** |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| PE-1 | Score every answer right / wrong / abstained with a cost table (e.g. right +1, abstain 0, wrong −2 for safety topics) | BL, ARL | 2 h | none | reports show the score and the cost table |
| PE-2 | Report coverage and selective accuracy next to accuracy | BL, ARL | 1 h | PE-1 | two extra columns per report |
| PE-3 | Ablate the main answer prompt: remove one section at a time on dev; drop sections that change nothing | BL | 3-4 h | PC-1 | each remaining rule names its failure and eval items |
| PE-4 | Experiment log fields: prompt version, model, settings, dataset version, hypothesis, per-question scores | BL, ARL | 1 h | none | template and results files have them |
| PE-5 | Migration checklist: same set, pinned judge, per-question compare, read every pass→fail flip, fresh error analysis, review emphatic rules | BL | 1 h | none | checklist in eval docs |
| PE-6 | **Generic prompt/agent eval recipe**, reusable beyond builders_lab: one page combining topics 1-11 into a step-by-step method for any prompt or agent | BL (`evals/knowledge/`) | 3-4 h | this walkthrough | a recipe file; builders_lab evals follow it |

### ADR seed (builders_lab): "Answers are scored right / wrong / abstained"

- **Context:** abstention is checked by question kind, but wrong answers cost the same as
  "not in sources"; coverage is not reported; prompt rules accumulate without ablation.
- **Decision (proposed):** three-way scoring with a cost table (wrong costs more, most on
  safety topics); coverage and selective accuracy in every report; prompt changes follow one
  hypothesis per change with rule ablation; model changes follow a migration checklist.
- **Options considered:** accuracy only; abstention by kind only; the proposal above.
- **Consequences:** tuning no longer rewards guessing; prompts get shorter; migrations are
  repeatable.

---

## Topic 12. Graph vs vector decision (code GV)

**Status:** piece 1 discussed, piece 2 written down (25 Nov 2026).

**Summary:** neither lab breaks results down by question type in a way that could justify a
graph. builders_lab splits by role, kind and legal weight (lanes, ADR 0016) and plans
document-structure tools (get_section, read_document): a cheap, exact structure graph.
agentic-rag-lab has `get_linked` but no per-type comparison.

### Piece 1: what the evidence says

**"Graph" means different things:**

| Variant | What it is | Competes with |
|---|---|---|
| Microsoft GraphRAG | LLM extracts entities and relations; community summaries; local and global search | Vector search over documents (strong on whole-corpus themes) |
| LazyGraphRAG | Graph built cheaply at query time | Same |
| HippoRAG 2 | Graph as an index for multi-hop across documents | Same |
| Knowledge graph (Cypher/SQL) | Data already modelled (jobs, contracts, parties) | Text-to-SQL |

**Graphs win** (independent studies): multi-hop across documents; comparison and timeline
questions (temporal: RAG 30.7 vs GraphRAG global 53.3, Han et al. 2025); whole-corpus themes.
**Graphs lose:** simple facts (NQ F1: RAG 64.8 vs GraphRAG global 54.5; GraphRAG-Bench: RAG
with reranker best on fact retrieval); saying "not found" (GraphRAG global 19% vs RAG 96%:
a red flag for builders_lab); coverage (only about 65% of answer entities reached the
LLM-built graph).
**Why reported wins shrink:** more text, not a better graph (GraphRAG gave ~2.7x the tokens;
with matched budgets 71.0 vs 71.2); biased pairwise judging (a system "beat" an identical copy
of itself 90/10; with controls a reported 66.7% win fell to 39%, arXiv 2506.06331).
**Cost:** on one corpus GraphRAG indexing took 115M tokens, 277 min, 10.7 s per query; dense
retrieval 12 min, no LLM tokens, 0.3 s per query (HippoRAG 2 paper). Document changes can
force much of the graph to be recomputed.
**Combine, not replace:** 13.6% of questions right only with GraphRAG, 11.6% only with RAG;
both contexts together beat either one (Han et al. 2025).

### Piece 2: decision by question type, and a fair test

**Decision table** (from the evidence; the mapping itself is a synthesis):

| Question type | First choice |
|---|---|
| Single fact in one passage | Hybrid search + reranker |
| Version- or edition-scoped ("in the 2025 edition") | Metadata filters |
| Depends on document structure (definition elsewhere, table under a heading) | Structure-aware chunking, section / parent retrieval, get_section-style tools |
| "List all" / count | SQL or a typed index (top-k cannot guarantee completeness) |
| Multi-hop across documents | Entity linking (HippoRAG 2 style) or agentic iterative retrieval first |
| Relationship / path over known entities | Modelled knowledge graph fed from source systems |
| Whole-corpus themes | LazyGraphRAG, GraphRAG global, or map-reduce over summaries |
| Must reliably say "not found" | Avoid global community search |

**Fair test, 8 steps:**
1. Label every golden question by type; aim for 20-30+ per type that matters (rule of thumb).
2. Tune a strong baseline first (hybrid, reranker, structure-aware chunks, filters).
3. Oracle checks: gold evidence to the generator; gold evidence in each system's top-k;
   share of answer entities present in the graph.
4. Match token budgets between systems.
5. Score with required facts or deterministic checks, not pairwise preference alone.
6. If pairwise judging is used: swap order, allow ties, repeat, run self-vs-self (should be ~50/50).
7. Paired tests per type with intervals (topics 2-3).
8. Record cost, p50/p95 latency, re-index cost; count only-A-right vs only-B-right. Adopt a
   graph only for the types where it wins by more than the noise.

| Official term | Meaning |
|---|---|
| **GraphRAG (local / global search)** | Microsoft's graph RAG; local = entity neighbourhoods, global = community summaries. |
| **Community summaries** | LLM summaries of clusters of related entities. |
| **Multi-hop question** | Needs facts from two or more passages linked together. |
| **Global sensemaking question** | About the whole corpus ("main themes"). |
| **Entity linking** | Mapping mentions in text to known entities. |
| **Matched token budget** | Both systems give the generator the same amount of text. |
| **Pairwise win rate** | Share of head-to-head comparisons a judge awards to one system. |
| **Self-vs-self (sanity) check** | Comparing a system with itself; should give ~50/50. |
| **Complementarity** | Questions only one system gets right. |
| **Oracle retrieval** | Giving the generator the gold evidence to find the ceiling. |

**Sources:** Han et al. 2025, [RAG vs GraphRAG](https://arxiv.org/abs/2502.11371);
[arXiv 2506.06331](https://arxiv.org/abs/2506.06331) (judge bias); Xiang et al.,
[GraphRAG-Bench](https://arxiv.org/abs/2506.05690); Gutiérrez et al. 2025,
[HippoRAG 2](https://arxiv.org/abs/2502.14802); Edge et al. 2024,
[GraphRAG](https://arxiv.org/abs/2404.16130).

### Criteria

| # | Practice | BL | ARL |
|---|---|---|---|
| 1 | Golden questions labelled by question type (as above) | **SO-SO.** Labelled by role and kind (answerable, negative, multi_rule, vague); not by retrieval type. | **SO-SO.** Kinds incl. multi_rule; no retrieval-type label. |
| 2 | Results broken down per type | **SO-SO.** By role and kind; lanes by legal weight. | **MISSING.** |
| 3 | Strong non-graph baseline tuned first | **STRONG.** Hybrid, rerank, top 100, lanes (E1-E8). | **STRONG.** E1 chunking, E7/E15 hybrid, E9 rerank. |
| 4 | Structure-based retrieval before LLM graphs | **SO-SO.** get_section / read_document planned (ADR 0016). | **SO-SO.** `get_linked` exists. |
| 5 | Graph test with matched tokens and debiased judging | **MISSING** (not needed yet). | **MISSING** (not needed yet). |

### Actions

| ID | Action | Repo | Effort | Depends on | Done when |
|---|---|---|---|---|---|
| GV-1 | Add a `retrieval_type` label to golden items (single fact, edition-scoped, structure-dependent, list-all, multi-hop, relationship, theme, unanswerable) | BL | 2-3 h | none | every item labelled; counts per type |
| GV-2 | Report retrieval and answer results per `retrieval_type` | BL | 1 h | GV-1 | per-type table in reports |
| GV-3 | Finish structure tools (get_section, read_document) and measure them on structure-dependent questions | BL | as planned in ADR 0016 | GV-1 | per-type gain measured |
| GV-4 | Only if multi-hop or relationship types fail after GV-3: run the 8-step fair test against one graph variant | BL or ARL | 1-2 days | GV-2 | decision per type recorded |

### ADR seed (builders_lab): "No LLM-built graph until question types justify it"

- **Context:** regulations questions are mostly single facts, edition-scoped and
  structure-dependent; the system must say "not in sources" reliably; independent studies
  show graphs help mainly on multi-hop, timeline and theme questions, hurt on facts and
  "not found", and cost far more to index and update.
- **Decision (proposed):** label golden questions by retrieval type; tune hybrid + rerank +
  metadata filters + structure tools first; consider a graph only for types that still fail,
  tested with the 8-step fair test.
- **Options considered:** build GraphRAG now; never use graphs; the proposal above.
- **Consequences:** no indexing cost now; per-type reporting makes the case (or not) with data.

---

## What does "pass >= 85%" mean? (from the case studies)

*Sources: `notes/llm-judge-case-studies/case_studies.md`, `notes/uk-government-ai-evals/notes.md`.*

- **Almost nobody publishes a fixed judge pass-rate gate.** Teams with honest numbers check
  the judge against experts first, aim for judge-human agreement close to human-human
  agreement, and gate on "no worse than last version" or on matching an expert baseline.
- **The definition decides the number.** Same legal system: 85% of rubric points vs 43% of
  questions fully correct. Same judge (Visa): 83% agreement on accept/reject vs 30% on a
  5-level scale.
- **Realistic judge agreement:** narrow binary checks 85-93% with experts (kappa 0.7-0.85,
  e.g. Mayo Clinic 93%); broad or subjective criteria kappa 0.4-0.7; experts often agree
  with each other only 80-88%.
- **UK government examples:** Consult sets the bar at human-human level; GOV.UK Chat
  requires every case to be fully faithful and factually precise; the cross-government
  testing framework gives example thresholds only (F1 >= 0.85, > 80% acceptable to humans,
  < 1% prompt-injection success, agent task success >= 90%).
- **For builders_lab:** define 85% per criterion ("share of answers passing all binary
  checks" or "share of checks passed": say which); set stricter bars for grounding and
  safety (any unsupported fact fails); report the judge's agreement with Florin next to
  human-human agreement; add a regression gate (NI-5) next to any floor; read the floor on
  the corrected rate (topic 5).

---

## Open follow-up: what applies to builders_lab

*Asked by Florin, 25 Nov 2026, after topic 8.* For every topic, sort the actions into:
**applicable to builders_lab now**, **not feasible in builders_lab** (and why: no users, no
traffic, cost, size), and **where it is feasible instead** (agentic-rag-lab, a later
production stage, or a real job). To do once all topics are walked through.

## Open follow-up: transfer to the existing tuning work

*Asked by Florin, 25 Nov 2026, after topic 4 piece 4.* Decide which of this knowledge goes
into the existing builders_lab tuning session (retrieval tuning and evals on branch
`claude/wonderful-wright-rd0v80`), and in what order. **Priority items first: topic 4 piece 4
(designing the judge) and topic 11 (prompt experiments and abstention).**
