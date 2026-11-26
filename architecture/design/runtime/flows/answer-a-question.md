# Flow: answer a question

One question from the builder's words to a verified reply. Up: [runtime design](../design.md).
Steps follow `plugin/skills/builders-workflow/SKILL.md`.

```mermaid
flowchart TB
    q(["Builder asks,<br/>Romanian or English"]) --> lang["1. Language in<br/>builders-translate: lookup_terms"]
    lang -->|"unclear"| ask(["Ask one clarifying question"])
    lang --> route["2. Route<br/>kind of question, job"]
    route -->|"decision about a person"| refuse(["Plain refusal"])
    route --> status["3. Status line<br/>'Checking the Riverside emails'"]
    status --> work["4. Work<br/>task skill calls the tools;<br/>sub-agent only for big jobs"]
    work --> draft["5. Draft<br/>Answer: text + claims with quotes"]
    draft --> verify{"6. verify_answer<br/>service/verify.py"}
    verify -->|"fail, round 1 or 2"| draft
    verify -->|"pass, or limits said"| out["7. Language out<br/>builders-translate, if Romanian"]
    out --> reply(["8. Reply in chunks<br/>first chunk short, then 'next'"])
```

1. **Language in.** A Romanian question becomes English with the official UK terms from `lookup_terms`.
2. **Route.** The workflow skill picks the task skill and the job. Ranking, scoring or monitoring people is refused.
3. **Status.** One line, no facts, so the builder hears something at once.
4. **Work.** The task skill calls the firm or regulations tools. `get_firm_profile` runs once per conversation.
5. **Draft.** Only from what the tools returned. Each fact is a claim with an exact quote and a source.
6. **Verify.** `verify_answer` checks sources exist, quotes are word for word, £ amounts and dates appear in the
   sources, and no banned phrase. Two fix rounds at most, then the reply says what could not be checked.
7. **Language out.** Romanian, with UK terms and quotes kept in English.
8. **Reply.** Layout in `answer-format.md`. Drafts that leave the firm are in English.
