# Flow: check a document tree

The three checks on a tree, coverage, model checks, crop check and semantic check. Up: [ingest design](../design.md).
Details: [coverage](../checks/coverage.md), [model checks](../checks/model-check.md), [semantic](../checks/semantic.md).

```mermaid
flowchart TB
    tree(["parsed tree"]) --> mx["1. checks export<br/>one packet per open check"]
    mx --> sub["2. one Claude Code sub-agent<br/>per packet"]
    sub --> sv{"3. checks save<br/>rules pass?"}
    sv -->|"refused"| sub
    sv --> fx[("corpus/fixes (git)<br/>parse again: 0 checks")]
    fx --> cov{"4. coverage.audit()<br/>words, images, tables lost?"}
    cov -->|"flagged"| fix(["fix the parser,<br/>or accept with a reason"])
    cov --> crop["5. cropcheck<br/>figure crops"]
    crop --> sem["6. semcheck export, run, save<br/>a model judges a sample"]
    sem --> rep(["7. semcheck report<br/>per family, judge named"])
```

- **Steps 1 to 3** are `system/rag/checks.py`; `checks lint` is also a test.
- **Step 4** is plain code and a test: an item fails until it is fixed or accepted by a person (`corpus/coverage/`).
- **Step 6** is not a gate. Open findings stay in the report until a parser fix or a reasoned accept; one store per
  judge (`corpus/semchecks/`).
