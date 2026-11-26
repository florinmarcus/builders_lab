# Flow: build the golden set

Questions a builder would ask, the sections that answer them, and the rules each answer needs.
Up: [eval design](../design.md). Briefs for each pass: `evals/golden/*-BRIEF.md`.

```mermaid
flowchart TB
    raw[("Raw documents")] --> biz["1. Business pass (one agent per role)<br/>tools/read_source.py<br/>golden/business/&lt;role&gt;.jsonl"]
    biz --> lab["2. Labelling pass (separate agents)<br/>tools/find_sections.py<br/>golden/labelled/&lt;role&gt;.jsonl"]
    lab --> b["3. build.py build()<br/>copy filter: shared_run() drops a question<br/>with 5+ words in a row from its section"]
    b --> split["4. is_holdout(): stable hash,<br/>about 20% per role -> holdout-ids.txt"]
    split --> q[("golden/questions.jsonl<br/>dropped.jsonl")]
    q --> fix["5. Label fixes, logged:<br/>remap.py (new section ids, v3)<br/>relabel.py (v4)"]
    q --> rules["6. Rules pass (RULES-BRIEF.md)<br/>golden/pooled/rules.jsonl"]
```

- **Blind on purpose.** The business pass never sees section ids, so questions are not written from the parser's
  view. The labelling pass never writes questions.
- **The holdout** is fixed by the hash, so a rebuild keeps the same split. It is never used for tuning.
- **Rules** are the facts an answer depends on, one per line. The pool judge and rule coverage use them.
