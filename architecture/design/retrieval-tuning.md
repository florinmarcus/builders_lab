# Regulations search: aim, two options, how we tune (25 Nov 2026)

What we are building for the firm visits on 28 Nov and 5 Dec, and how we decide. Search details: [regulations-corpus.md](regulations-corpus.md#search). Lanes: [ADR 0016](../../decisions/0016-retrieval-strategy-lanes-measure-first.md) point 8. Eval runner: `evals/retrieval.py`. Pooling: `evals/golden/pool_local.py`.

## Aim

```mermaid
flowchart LR
    q["Builder's question<br/>(through Claude)"] --> s["search_regulations<br/>(MCP server)"]
    s --> p["The passage that<br/>answers it, with its<br/>legal weight"]
    p --> a["Claude answers,<br/>cites document,<br/>section, date"]
    goal["Target: the right passage<br/>in the top 5 for most questions,<br/>in the top 10 for nearly all"]:::goal
    goal -.- p
    classDef goal fill:#fff4d6,stroke:#c99a00
```

- Measured as recall at 5, 10 and 20 on the golden set, strict (expected sections only) and pooled (also passages a judge says answer the question).
- Top 5 is not fixed. If top 10 is clearly better and fits, we show 10.

## Two options for one search call

The server takes one question. Inside the tool, search runs one of two ways.

```mermaid
flowchart TB
    q["search_regulations(question, as_of_date, country)"] --> emb["Embed the question once<br/>(Titan v2)"]

    emb --> A
    emb --> B

    subgraph A["Option A: mixed"]
        direction TB
        a1["Vector top 50 + keyword top 50<br/>over ALL documents"] --> a2["Merge (RRF)"] --> a3["Re-rank (Amazon Rerank)"] --> a4["One list: top k<br/>(law and guidance mixed)"]
    end

    subgraph B["Option B: four lanes by legal weight"]
        direction TB
        b0["Same search, run 4 times in parallel,<br/>each limited to one weight"]
        b0 --> L1["Law<br/>Acts, regulations"]
        b0 --> L2["Approved Documents<br/>statutory guidance"]
        b0 --> L3["Approved codes<br/>HSE L books (ACoP)"]
        b0 --> L4["Guidance<br/>HSE, GOV.UK, other"]
        L1 --> r1["re-rank, top n"]
        L2 --> r2["re-rank, top n"]
        L3 --> r3["re-rank, top n"]
        L4 --> r4["re-rank, top n"]
        r1 & r2 & r3 & r4 --> b5["Four short lists,<br/>an empty lane says 'nothing found'"]
    end

    a4 --> out["Passages to Claude"]
    b5 --> out
```

| | Option A: mixed | Option B: lanes |
|---|---|---|
| Strength | Simple. Best passages win, whatever the source. | The law is never pushed out by long guidance. Claude sees law versus guidance at once. |
| Risk | Guidance (most of the corpus) crowds out the law. | More passages to read. A lane with only weak hits still returns them. |
| Size | k = 5, 10 or 20 | n per lane, tuned on dev (2 is a placeholder) |
| Status | Live today | Built in code and eval only (S143) |

Mixed documents (L143, HSG248) are split by section: the ACoP parts go to lane 3, the plain guidance to lane 4.

## Where agent queries fit (optional, on top of A or B)

```mermaid
flowchart LR
    q["Builder's question"] --> d{"Decomposer?<br/>(Claude, in the plugin)"}
    d -->|no| one["One query,<br/>the question as asked"]
    d -->|yes| many["Two or three queries,<br/>one per need, each tagged<br/>law / approved code / guidance"]
    many -.->|"optional: library map<br/>(titles of what we hold)"| many
    one --> s["search (A or B)"]
    many --> s
    s --> f["Fuse the lists (RRF)"]
```

- The decomposer runs in Claude on the user's plan, never on our server (ADR 0006, ADR 0017).
- Its tags map onto the lanes, so B and the decomposer fit together.
- The library map is tested later as its own experiment, against the decomposer without it.

## How we decide: measure, then tune

```mermaid
flowchart TB
    gs["Golden set: 342 dev questions<br/>(65 holdout, never used for tuning)"] --> runs

    subgraph runs["Run search on every dev question"]
        direction LR
        B1["B1 mixed"]
        B2["B2 four lanes"]
        B3["B3 mixed + saved agent queries"]
    end

    runs --> pool["Pool: every top-10 passage<br/>that is not already an expected section"]
    pool --> judge["Judges grade each passage<br/>2 answers / 1 related / 0 not relevant"]
    judge --> score["Score recall at 5, 10, 20<br/>strict and pooled, mixed and per lane"]
    score --> miss["Read the misses"]
    miss --> why{"Why missed?"}
    why -->|"query words differ"| fq["Fix the query side<br/>(decomposer, terms)"]
    why -->|"found but ranked low"| fr["Fix ranking<br/>(lane sizes, re-rank, k)"]
    why -->|"passage cut badly"| fc["Rechunk<br/>(only if the numbers show it)"]
    fq & fr & fc --> rerun["Run again on dev"]
    rerun --> score
    score -->|"best setting chosen"| hold["One final check on holdout"]
    hold --> live["Switch the live tool"]
```

## How the judging works

Two judges, two questions. The passage judge asks "does this one passage answer it?" (finds the right material). The answer-set judge asks "could a builder get the full answer from everything this search returned?" (what the firms will feel). Only the second sees a set with the law but no guidance, or one rule of two.

### Passage judge (every pooled pair)

```mermaid
flowchart LR
    pool["Pooled pairs<br/>(question, passage)"] --> shuf["Shuffle across questions,<br/>hide which run found them,<br/>packets of 10"]
    shuf --> op["Opus judge<br/>(fresh agent per packet)<br/>ALL pairs"]
    shuf --> s10["10% sample,<br/>reshuffled into other packets"]
    s10 --> op2["Second Opus judge"]
    s10 --> son["Sonnet judge"]
    op --> agree["Agreement"]
    op2 --> agree
    son --> agree
    agree --> fl["Florin checks about 15 pairs<br/>(tie-breaker)"]
    op -->|"grade 2"| aa["also_acceptable<br/>in the golden set"]
```

- Opus against Opus shows drift and noise. Opus against Sonnet shows the model gap. If Sonnet agrees as well as Opus agrees with itself, future pools use Sonnet.
- If agreement is poor, packets shrink to one question per judge.
- The pool is a test tool only. Nothing of it runs in the live search.

### Answer-set judge (80 dev questions, `evals/golden/answer_set.py`)

```mermaid
flowchart LR
    q["80 dev questions<br/>(spread over the six roles)"] --> sets
    subgraph sets["Same size for each run: 8 passages"]
        direction TB
        m8["Mixed: top 8"]
        l2["Lanes: 2 per lane"]
        f8["Mixed + agent queries: top 8"]
    end
    sets --> blind["Flatten and shuffle each set,<br/>hide the run, packets of 4,<br/>never one question twice in a packet"]
    blind --> j["Opus judge, all 240 sets<br/>2 full / 1 partly (says what is missing) / 0 none"]
    blind --> r["10% re-check:<br/>second Opus and Sonnet"]
    j --> sc["Share of full answers per run<br/>+ what is most often missing"]
    r --> sc
```

- Same number of passages per run, so lanes don't win only by showing more.
- "What is missing" tells us the fix: a missing law points at lanes, a missing second rule at the decomposer.
