# Flow: pool judging

Passages search found that are not in the labels get a verdict, rule by rule. Up: [eval design](../design.md).
Brief: `evals/golden/POOL-JUDGE-BRIEF.md`. The pool is a test tool only; nothing of it runs in live search.

```mermaid
flowchart TB
    runs[("Run results")] --> p["1. pool_local.py packets<br/>pool(): every top-k passage with no verdict"]
    p --> sh["2. Shuffle across questions, hide the run,<br/>plant one yes and one no line per packet"]
    sh --> pk[("Packets in the scratchpad,<br/>never in git")]
    pk --> j["3. One fresh Opus sub-agent per packet:<br/>which of the question's rules does the passage state,<br/>with a word-for-word quote"]
    j --> m["4. pool_local.py merge<br/>check_line(): planted lines right,<br/>every quote found in the passage"]
    m -->|"INVALID"| pk
    m --> v[("pooled/judgments.jsonl")]
    v --> aa["5. A passage that states a rule:<br/>also_acceptable in the golden set"]
    v --> rc["6. Re-check sample: second Opus and Sonnet<br/>pooled/recheck.jsonl"]
```

- **Bad packets** (a planted line wrong, a quote not in the passage) are judged again in a new packet.
- **Re-check.** Opus against Opus shows noise; Opus against Sonnet shows the model gap. If Sonnet agrees as well as
  Opus agrees with itself, later pools can use Sonnet. Florin checks a small sample as tie-breaker.
