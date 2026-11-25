# Designing evals from error analysis (practitioner methodology)

Scope: the applied workflow (Husain / Shankar, Eugene Yan, Jason Liu, Anthropic) for finding what actually fails in an LLM, RAG or agent system and turning that into evals. Researched 25 Nov 2026. Dates given per source. Theory only, not facts about Florin's work.

Main sources used:
- Husain and Shankar, "AI Evals: Everything You Need to Know" (FAQ), published 18 Sep 2026, modified 21 Sep 2026 — https://hamel.dev/blog/posts/evals-faq/
- Husain, "A Field Guide to Rapidly Improving AI Products", 24 Mar 2025 — https://hamel.dev/blog/posts/field-guide/
- Husain, "Using LLM-as-a-Judge For Evaluation: A Complete Guide", 29 Oct 2024 (modified 1 Sep 2026) — https://hamel.dev/blog/posts/llm-judge/
- Husain, "Your AI Product Needs Evals", 29 Mar 2024 — https://hamel.dev/blog/posts/evals/
- Orosz and Husain, Pragmatic Engineer, 2 Dec 2025 (partly paywalled) — https://newsletter.pragmaticengineer.com/p/evals
- Shankar et al., "Who Validates the Validators?", arXiv 18 Apr 2024, UIST '24 — https://arxiv.org/abs/2404.12272 , https://arxiv.org/html/2404.12272v1
- Eugene Yan, "Product Evals in Three Simple Steps", 23 Nov 2025 — https://eugeneyan.com/writing/product-evals/
- Jason Liu, "Systematically Improving Your RAG", 22 May 2024 — https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/
- Anthropic, "Demystifying evals for AI agents", 9 Jan 2026 — https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

## 1. The error analysis workflow: reading traces, open coding, axial coding, counting, saturation; how many traces, who reads

### Takeaway
Read real (or synthetic) traces first, write free-text notes on the first failure in each (open coding), group the notes into 5-10 failure modes (axial coding), count them, and keep going until new traces stop revealing new modes (theoretical saturation). Review at least ~100 traces, done by one domain expert ("benevolent dictator"), not outsourced; repeat every 2-4 weeks in production.

### Cited Findings
- Steps: (1) build a dataset of representative traces (synthetic if no real data); (2) open coding: a human, ideally a "benevolent dictator", writes open-ended journal-style notes on issues, a method borrowed from qualitative research; (3) axial coding: group notes into a "failure taxonomy", called the most important step, then count failures per category (an LLM can help); (4) iterate until theoretical saturation, "new reviews stop revealing failure modes or changing existing ones" — [Husain/Shankar FAQ: error analysis](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)
- Annotate the "first failure" in each trace, because upstream errors cause downstream ones; tagging all independent failures is optional — [same](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html); Pragmatic Engineer version: "review at least 100 diverse traces and add open-ended notes on any undesirable behavior", axial coding into "roughly 5-10 themes", LLM may suggest clusters but humans review, count with a pivot table or script — [Orosz & Husain, Dec 2025](https://newsletter.pragmaticengineer.com/p/evals)
- Using AI in the loop: annotate at least 30 traces yourself before looking at agent suggestions; then let an agent search the rest for likely instances of the failures you described and accept/reject; keep a working pool of about 100 diverse traces — [FAQ: error analysis](https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html)
- Numbers: minimum setup is 30 minutes reviewing 20-50 outputs after each significant change, with one domain expert as decision maker; review at least 100 traces and continue while still learning; in production review 100+ fresh traces every 2-4 weeks, plus 10-20 outlier traces weekly; new systems need weekly analysis — [Husain & Shankar FAQ, Sep 2026](https://hamel.dev/blog/posts/evals-faq/)
- Record problems that are not the model's fault (e.g. missing features) — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Sampling: keep some random traces in every batch; move from exploratory sampling (random, clustering) to targeted (classification, user feedback, high-probability failure patterns) as you learn — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Time budget: the authors report spending "60-80% of our development time" on error analysis and evaluation; "Start with error analysis, not infrastructure." — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Who reads: "Start with a benevolent dictator whenever feasible. Only add complexity when absolutely necessary." One domain expert as final quality decision maker is "the most effective approach" for small/medium companies; with several annotators measure Cohen's Kappa; outsourcing error analysis is usually a mistake except for mechanical tasks needing no product context — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- "Principal domain expert": one (maybe two) people whose judgment defines success; avoid developers or convenient proxies; solo founders may fill the role; check leadership opinions against user feedback — [Husain, LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/)
- Worked example (Nurture Boss, apartment leasing assistant): bottom-up notes, LLM-built taxonomy, label and count; three issues made up over 60% of problems; date handling failed 66% of the time; after targeted tests success went from 33% to 95% — [Field Guide, Mar 2025](https://hamel.dev/blog/posts/field-guide/). The three issues were date handling, handoff failures and conversation flow; date handling tested with a golden set and code assertions using a fixed "current date" (2025-08-28) — [Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/evals)
- Tooling: a custom data viewer (full context in one screen, one-click pass/fail, free-text notes, filters, hotkeys) makes teams iterate "10x faster" (Husain's claim); buildable in hours with AI coding; a spreadsheet beats nothing — [Field Guide](https://hamel.dev/blog/posts/field-guide/). Show outputs in their familiar format, show progress ("45 of 100 examples reviewed") — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Framing: the "three gulfs": comprehension (developer vs understanding data at scale), specification (what you want vs what the prompt says: "LLMs cannot read our minds"), generalization (good prompt vs reliable across all inputs) — [Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/evals)

### Inferences
- Error analysis is essentially qualitative research (grounded theory) applied to traces; the output is a ranked, counted list of failure modes, which becomes the eval backlog.
- "First failure only" keeps counts honest in pipelines/agents, where one upstream error creates many downstream symptoms.

### Gaps
- No source gives an empirical rule for when saturation is reached (e.g. "N traces with no new code"); it is a judgement call.

## 2. Binary pass/fail vs Likert 1-5; per-failure-mode evaluators vs one overall score

### Takeaway
Practitioners converge on binary pass/fail (or win/lose/tie for pairwise) with a written critique, and one evaluator per failure mode combined by simple rules (e.g. pass only if all pass), not a single 1-5 "quality" score.

### Cited Findings
- Use pass/fail; Likert scales create inconsistent distinctions and annotators default to middle values; detecting differences with Likert needs larger samples; build a separate judge per failure type rather than one overall judge; summarise multiple checks with a "pass all" rate — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Why not 1-5: a 3 vs 4 is not actionable and the boundary is unclear; expert judgements often do not correlate with multi-dimension scores — [LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/). "the distinction between a '3' and a '4' is often subjective"; "a 'fail' is a clear signal to fix a bug" — [Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/evals)
- Nuance goes in the written critique, not the score — [Field Guide](https://hamel.dev/blog/posts/field-guide/)
- Yan: binary pass/fail for objective criteria, win/lose/tie for subjective; avoid 1-5; avoid a single "God Evaluator"; one evaluator per dimension, combined with rules like "pass only if all dimensions pass" — [Yan, Nov 2025](https://eugeneyan.com/writing/product-evals/). He has his evaluators return binary outputs, which "improves model performance while making it easier to apply classification metrics" — [Yan, LLM-evaluators](https://eugeneyan.com/writing/llm-evaluators/)
- Anthropic: grade each dimension with a separate judge; allow an "Unknown" answer to reduce hallucinated verdicts — [Anthropic, Jan 2026](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Counterpoint (vendor test): Arize's earlier tests found score-based evals less consistent than binary; a 2025 retest says that for checklist-style labels non-reasoning judges often give similar signals at lower cost — [Arize](https://arize.com/blog/testing-binary-vs-score-llm-evals-on-the-latest-models/) (seen via search snippet only)

### Inferences
- Binary labels turn judge validation into a classification problem (TPR/TNR, precision/recall on the fail class, kappa), which is why they pair naturally with per-failure-mode judges.

### Gaps
- No controlled study found that directly compares business outcomes of binary vs Likert eval programmes; the evidence is practitioner experience plus small vendor tests.

## 3. Criteria drift ("Who Validates the Validators?")

### Takeaway
Criteria drift: "users need criteria to grade outputs, but grading outputs helps users define criteria." You cannot fully specify a rubric before reading outputs, so rubrics, labels and judges must be revised iteratively, and old labels re-checked when criteria change.

### Cited Findings
- Definition and claim that some criteria depend on the specific outputs observed; approaches assuming criteria are independent of outputs "may face serious questions" — [Shankar, Zamfirescu-Pereira, Hartmann, Parameswaran, Arawjo, arXiv Apr 2024 / UIST '24](https://arxiv.org/abs/2404.12272)
- Study: 9 industry practitioners (engineers, ML scientists, execs, consultants). Observed drift: several added criteria after seeing new failure types; P2 and P8 loosened a "all entities must be proper nouns" rule to "most"; P7 reconsidered hashtag handling; P8 twice gave a bad grade only to stay consistent with earlier grades. Quote: "I think it's hard to know until you see it" — [paper HTML](https://arxiv.org/html/2404.12272v1)
- EvalGen vs SPADE baseline, 16 graded outputs per pipeline: medical pipeline alignment 48.3% both (3 vs 5 assertions); product pipeline 66.5% vs 54.4% (4 vs 9 assertions) — [paper HTML](https://arxiv.org/html/2404.12272v1)
- Design implications: iterate criteria and implementations together; elicit grades per criterion, not just thumbs up/down; allow different false-failure tolerances per criterion; let users add criteria mid-grading and prompt re-grading; show code for code assertions; handle inter-rater disagreement; periodically re-align LLM assertions in production — [paper HTML](https://arxiv.org/html/2404.12272v1)
- Practitioner uptake: "it is impossible to completely determine evaluation criteria prior to human judging of LLM outputs" — [LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/); don't write a detailed rubric before reviewing examples — [FAQ](https://hamel.dev/blog/posts/evals-faq/); Honeycomb's Phillip Carter found his own judging inconsistent until he saw the LLM's reasoning — [Field Guide](https://hamel.dev/blog/posts/field-guide/)

### Inferences
- Implication for eval design: treat gold labels and judge prompts as versioned artefacts with a review loop; when a criterion changes, re-label affected examples rather than keep stale labels; expect early judge alignment numbers to move as the human's own standard settles.

### Gaps
- The paper's study is small (9 people) and qualitative; no large-scale measure of how often drift happens.

## 4. Code check vs LLM judge vs nothing (just fix it); cost vs value

### Takeaway
First fix obvious problems (often a specification gap in the prompt) without building an eval. Build evaluators only for failures that persist and that you will iterate on; use code assertions whenever the failure can be checked deterministically; reserve LLM judges (validated against expert labels) for subjective failures; retire evals that always pass.

### Cited Findings
- "Fix these obvious gaps first before building complex evaluation infrastructure"; "Only build expensive evaluators for problems you'll iterate on repeatedly"; some issues are engineering or design issues needing no automated evaluator; don't generate synthetic data for problems you can fix immediately — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- "If a failure can be verified with code, always use a code-based eval"; code evals are "cheaper to create and maintain"; example split: date extraction = code; when to hand off to a human = LLM judge — [Pragmatic Engineer](https://newsletter.pragmaticengineer.com/p/evals)
- Eval-driven development (writing evals before seeing errors) is "generally not recommended": write evaluators for errors you find, not imagine — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Retirement: if everything keeps passing, run less often or retire; phase out expensive LLM judges faster than cheap checks; "If you're passing 100% of your evals, you're likely not challenging your system enough." — [FAQ](https://hamel.dev/blog/posts/evals-faq/). "The more expensive the eval, the greater benefit it needs to provide to justify running it frequently." — [FAQ, part 2](https://hamel.dev/blog/posts/evals-faq/)
- Three levels by cost: L1 unit-test assertions on every code change (e.g. Rechat's regex check that no UUIDs leak); L2 human + model eval on a cadence; L3 A/B tests only after significant product changes — [Husain, Mar 2024](https://hamel.dev/blog/posts/evals/)
- Judge building ("critique shadowing"): expert gives pass/fail + detailed critique; ~30 examples to start; ~100 per failure mode to validate; fix pervasive errors before building a judge; write the judge prompt after seeing data, using critiques as few-shot; Honeycomb reached >90% agreement in three iterations — [LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/)
- Judge data: 100-200 labelled examples per failure mode (at least 50 pass / 50 fail); split 10-20% train (few-shot pool), 40-45% dev, 40-45% test; report TPR and TNR, not raw agreement; start with the most capable judge model, optimise cost later; give each judge only the trace parts it needs (ablate); inspect disagreements manually before automated prompt tuning — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Yan's alternative numbers: 200+ labelled samples with 50-100 fails; ~75% for alignment, ~25% held out; precision and recall on the fail class (recall first) and Cohen's kappa (0.4-0.6 substantial, >0.7 excellent); human annotators often only reach 0.2-0.3 kappa and can miss up to 50% of defects: "The benchmark is human performance, not perfection." — [Yan](https://eugeneyan.com/writing/product-evals/)
- Correcting judge bias: with known TPR/TNR, correct the observed pass rate (Rogan-Gladen style): theta = (p_obs + TNR - 1) / (TPR + TNR - 1), valid only if TPR + TNR > 1, with bootstrap confidence intervals; implemented in the `judgy` library — [judgy on PyPI](https://pypi.org/project/judgy/), [DeepWiki](https://deepwiki.com/ai-evals-course/judgy); formal treatment in "How to Correctly Report LLM-as-a-Judge Evaluations" (arXiv 2511.21140, Nov 2025) — [arXiv](https://arxiv.org/html/2511.21140v1). The FAQ links this to RAG: "Once you know your judge's True Positive and True Negative rates, you can correct its estimates." — [FAQ](https://hamel.dev/blog/posts/evals-faq/). (Attribution of `judgy` to the Husain/Shankar course is suggested by the "ai-evals-course" GitHub org name only; not otherwise confirmed.)
- Judges can show high TPR (>96% on valid outputs) but low TNR on invalid ones — [arXiv 2510.11822](https://arxiv.org/pdf/2510.11822.pdf) (via search snippet)
- Guardrails vs evaluators: guardrails are inline, fast, deterministic; evaluators run after and don't block; "you would almost never use a slow or non-deterministic LLM-as-Judge as a synchronous guardrail" — [FAQ](https://hamel.dev/blog/posts/evals-faq/)

### Inferences
- A practical decision order per failure mode: (a) is it a spec gap? fix the prompt/code and re-read traces; (b) still recurring and checkable by rule? assertion in CI; (c) still recurring and subjective? build a per-mode judge, validate TPR/TNR on held-out expert labels, correct reported rates; (d) rare and cheap to tolerate? note it, no eval.

### Gaps
- No source gives a monetary cost model for evals; guidance is qualitative (cheap checks often, expensive judges rarely).

## 5. Building eval datasets when real data is thin (synthetic via dimensions/tuples)

### Takeaway
Define the dimensions along which inputs vary (feature, scenario, persona, complexity), hand-write ~20 tuples, have an LLM generate more tuples, then turn each tuple into a natural query in a separate prompt. Generate inputs, not expected outputs; check that each query really triggers its scenario; replace with real traces as soon as you have them.

### Cited Findings
- Recipe-bot example: dimensions Dietary Restriction (vegan, gluten-free, none), Cuisine (Italian, Asian, comfort food), Query Complexity (simple, multi-step, edge case); hand-write ~20 tuples; two-step: tuple first, then query in a separate prompt, e.g. (Vegan, Italian, Multi-step) -> "I need a dairy-free lasagna recipe that I can prep the day before." — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Cross product then filter "guarantees coverage including edge cases. Use when most combinations are valid"; asking the LLM for tuples directly "tends toward generic outputs and misses rare scenarios", use when many combinations are invalid — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- When synthetic data is unreliable: specialised documents, low-resource languages, high-stakes domains, underrepresented user groups, cases where validation is impossible — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Rechat example: features/scenarios/personas, e.g. first-time-buyer persona in a multiple-matches scenario; "generate user inputs, not expected outputs", and verify each query triggers the intended scenario — [Field Guide](https://hamel.dev/blog/posts/field-guide/); Rechat generated 50 contact-creation instructions each paired with a lookup query; tests should be challenging yet representative; 100% pass is not required, the target is a product decision — [Husain, Mar 2024](https://hamel.dev/blog/posts/evals/)
- Keep generating until new failure modes stop appearing; mix real logs with synthetic — [LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/)
- Prefer organic failures (from smaller models or production) over synthetic defects when labelling judge data — [Yan](https://eugeneyan.com/writing/product-evals/)
- RAG-specific: generate questions each chunk should answer, check that retrieval returns that chunk, record recall/precision as baseline; Liu says synthetic data should reach "around 97% recall precision"; examples: on essays full-text ≈ embeddings but full-text ~10x faster; on GitHub issues full-text recall ~55% vs embeddings ~65% — [Liu, May 2024](https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/)
- Agents: start with 20-50 tasks from real failures; convert user bug reports into tasks; each task unambiguous (two experts would agree) with a reference solution; balanced sets testing where a behaviour should and should not occur ("a search tool that searches for everything") — [Anthropic, Jan 2026](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- The dimension/tuple step is what prevents the typical "LLM-generated, all-similar, too-easy" synthetic set; the verification step (does the query hit the scenario?) is what keeps it representative.

### Gaps
- No quantitative guidance found on how synthetic-vs-real distribution mismatch biases eval scores.

## 6. Eval-driven improvement loop: prioritising, knowing it's real, anti-patterns

### Takeaway
Rank failure modes by frequency (and severity), fix upstream ones first, re-run the per-mode evals on each config change, and judge improvement against confidence intervals and the previous config, not point estimates. Anti-patterns: generic metrics ("helpfulness"), similarity scores, off-the-shelf eval suites as quality measures, dashboards with no narrative, metric sprawl, eval sets that never change or always pass.

### Cited Findings
- Prioritise: errors compound, so fix earlier ones first; process failures are easier to debug (more deterministic) so tackle them first; "Start with error analysis ... before considering model switching." — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Count to prioritise: three issues > 60% of problems (Nurture Boss) — [Field Guide](https://hamel.dev/blog/posts/field-guide/). Liu: segment queries into topic clusters and capability gaps, model each cluster's count and probability of dissatisfaction; example where deadline questions jumped from 2% to 80% of traffic after a new client — [Liu](https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/)
- Feedback design: generic thumbs up/down mixed correctness with tone and latency; replacing it with "Did we answer the question correctly? Yes or no." gave a usable eval set — [Liu](https://jxnl.co/writing/2024/05/22/systematically-improving-your-rag/)
- Is it noise? Yan's numbers: 200 samples at 3% defect rate gives about ±2.4% (upper bound 5.4%, fails a 5% requirement); 400 samples gives ±1.7% (upper 4.7%, passes); halving the margin needs ~4x samples; compare against previous config; guardrail metrics are release blockers; for pairwise, run both orderings and count flips as ties — [Yan](https://eugeneyan.com/writing/product-evals/). FAQ: track confidence intervals for production metrics, investigate if the lower bound crosses your threshold — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Non-determinism: run multiple trials per task; pass@k (at least one success in k) vs pass^k (all k succeed); 75% per trial over 3 trials gives ~42% pass^k; use pass^k for customer-facing consistency — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- Capability vs regression evals: capability evals start low ("a hill to climb"); regression evals sit near 100%; graduate passed capability tasks into regression; "An eval at 100% tracks regressions but provides no signal for improvement"; 0% across many trials usually means a broken task or grader — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- CI: CI evals "protect against known regressions"; often 100+ purpose-built examples (core features, past bugs, edge cases); favour deterministic checks over judges; feed production failures back into the CI set — [FAQ](https://hamel.dev/blog/posts/evals-faq/)
- Experiment-based roadmaps: count experiments, not features; Yan's time boxes (2 weeks data feasibility, 1 month technical feasibility, 6 weeks prototype); GitHub Copilot used repositories' existing unit tests to evaluate thousands of experiments — [Field Guide](https://hamel.dev/blog/posts/field-guide/)
- Anti-patterns: a client celebrated a 10% gain in "helpfulness score" while users still struggled; tools-first thinking; metric sprawl; fixed AI feature deadlines; trusting automated judges without human validation — [Field Guide](https://hamel.dev/blog/posts/field-guide/). "Generic evaluations waste time and create false confidence when you use them as quality measures" (they can still help find traces to review); BERTScore/ROUGE generally not useful for LLM outputs; dashboards rarely helpful, prefer custom visuals plus a narrative of what changed — [FAQ](https://hamel.dev/blog/posts/evals-faq/). Off-the-shelf metrics tend to mislead — [LLM-judge guide](https://hamel.dev/blog/posts/llm-judge/)
- Ownership: give the eval suite clear owners, let product/domain experts contribute tasks, maintain like unit tests; "You won't know if your graders are working well unless you read the transcripts" — [Anthropic](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents). "You can never stop looking at data—no free lunch exists." — [Husain 2024](https://hamel.dev/blog/posts/evals/)
- Let domain experts edit prompts directly ("integrated prompt environments") instead of passing PowerPoint specs to engineers — [Field Guide](https://hamel.dev/blog/posts/field-guide/)

### Inferences
- The loop is: error analysis -> counted failure modes -> fix spec gaps -> per-mode evals (code first, judges where needed) -> run on every change with CIs -> new error analysis on fresh traces every few weeks -> add new modes, retire saturated ones.

### Gaps
- No source covers paired statistical tests (e.g. McNemar on the same examples across two configs) explicitly; Yan's CI approach is the closest.

## 7. Evaluating multi-step agents: trace vs step level, transition failure matrices

### Takeaway
Start end-to-end (did the agent meet the user's goal, pass/fail), then drill to step-level checks only where error analysis shows failures cluster. Use a transition failure matrix (last successful state x first failing state) to locate where agents break. Grade outcomes/state rather than exact tool-call sequences.

### Cited Findings
- Two phases: treat the agent as a black box and judge goal success; then step-level diagnostics (tool choice, parameter extraction, error handling, context retention, efficiency, goal checkpoints) once you know which workflows fail; test tool name, arguments, result and resulting state as separate checks — [FAQ, part 2](https://hamel.dev/blog/posts/evals-faq/)
- Transition failure matrix: "rows represent the last successful state and columns represent where the first failure occurred"; in the example GenSQL -> ExecSQL caused 12 failures vs DecideTool -> PlanCal only 2 — [FAQ, part 2](https://hamel.dev/blog/posts/evals-faq/)
- Multi-turn: first a pass/fail on whether the conversation met the user's goal; annotate only the first failure; reproduce failures with the simplest test case; generate tests with simulated users or "N-1 testing" (replay first N-1 turns of a real conversation) — [FAQ, part 2](https://hamel.dev/blog/posts/evals-faq/)
- RAG as a two-stage pipeline: debug retrieval first with IR metrics (Recall@k, Precision@k, MRR), then generation with error analysis and validated judges — [FAQ, part 2](https://hamel.dev/blog/posts/evals-faq/)
- Anthropic: avoid rigid checks on a specific tool-call sequence; grade the final outcome (e.g. database state); partial credit for multi-part tasks; shortcut-resistant graders; isolate trials (an agent gained an unfair edge reading git history from earlier trials); mix code, model and human graders, humans mainly to calibrate model graders — [Anthropic, Jan 2026](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

### Inferences
- Tension to note: Husain's step-level checks (tool name/args) vs Anthropic's warning against path-rigid grading. Reconciled: use step checks for diagnosis and for steps with one correct answer; use outcome/state grading for the pass/fail headline.

### Gaps
- No source gives guidance on sample sizes for filling a transition matrix reliably.
